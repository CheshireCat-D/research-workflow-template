#!/usr/bin/env python3
"""Offline descriptive analysis of Palmer penguin mass; Python 3.11+, stdlib only.

No input or existing output is overwritten. Missing data are never set to zero.
The fixed factor levels describe this example, not every possible penguin dataset.
"""
import argparse
import csv
import hashlib
import html
import itertools
import json
import math
from pathlib import Path
import statistics
import sys

SPECIES = ("Adelie", "Chinstrap", "Gentoo")
ISLANDS = ("Biscoe", "Dream", "Torgersen")
YEARS = ("2007", "2008", "2009")
SEXES = ("female", "male")
MISSING = ("", "NA")
REQUIRED = ("species", "island", "year", "sex", "body_mass_g")
PUBLIC_INPUT_SHA256 = "f204db2c753b0937caac3cb35258562c14f073e4bbc76be24b4c51ce22767a93"


def read_rows(path):
    rows = []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames or len(set(reader.fieldnames)) != len(reader.fieldnames):
            raise ValueError("Missing or duplicate CSV header")
        if not set(REQUIRED).issubset(reader.fieldnames):
            raise ValueError("Required columns: " + ", ".join(REQUIRED))
        for line, raw in enumerate(reader, 2):
            if None in raw or any(v is None for v in raw.values()):
                raise ValueError(f"CSV field count mismatch at row {line}")
            row = {k: raw[k].strip() for k in REQUIRED}
            for key, levels in (("species", SPECIES), ("island", ISLANDS),
                                ("year", YEARS), ("sex", SEXES)):
                if row[key] in MISSING:
                    row[key] = None
                elif row[key] not in levels:
                    raise ValueError(f"Unexpected {key} at CSV row {line}: {row[key]!r}")
            if row["body_mass_g"] in MISSING:
                row["body_mass_g"] = None
            else:
                try:
                    mass = float(row["body_mass_g"])
                except ValueError as exc:
                    raise ValueError(f"Non-numeric mass at CSV row {line}") from exc
                if not math.isfinite(mass) or mass <= 0:
                    raise ValueError(f"Mass must be finite and positive at CSV row {line}")
                row["body_mass_g"] = mass
            row["csv_row"] = line
            rows.append(row)
    if not rows:
        raise ValueError("Input has no data rows")
    return rows


def usable(row):
    return all(row[k] is not None for k in ("species", "sex", "body_mass_g"))


def stats(values):
    return {"n": len(values), "mean_g": statistics.mean(values) if values else None,
            "sd_g": statistics.stdev(values) if len(values) >= 2 else None,
            "median_g": statistics.median(values) if values else None,
            "min_g": min(values) if values else None,
            "max_g": max(values) if values else None}


def values(rows, sex):
    return [r["body_mass_g"] for r in rows if r["sex"] == sex and r["body_mass_g"] is not None]


def contrast(rows):
    female, male = (stats(values(rows, sex)) for sex in SEXES)
    delta = male["mean_g"] - female["mean_g"] if female["n"] and male["n"] else None
    return {"n_female": female["n"], "n_male": male["n"],
            "mean_female_g": female["mean_g"], "mean_male_g": male["mean_g"],
            "male_minus_female_g": delta,
            "difference_pct_female_mean": 100 * delta / female["mean_g"] if delta is not None else None,
            "median_difference_g": male["median_g"] - female["median_g"] if delta is not None else None}


def assignment_bounds(rows):
    """Exact descriptive extremes after assigning known masses of unknown sex."""
    unknown = [r["body_mass_g"] for r in rows if r["sex"] is None and r["body_mass_g"] is not None]
    if len(unknown) > 16:
        return {"unknown_sex_known_mass_n": len(unknown), "evaluated": False,
                "reason": "More than 16 unknown-sex masses; exact enumeration skipped"}
    base_f, base_m = values(rows, "female"), values(rows, "male")
    differences = []
    for assignment in itertools.product((0, 1), repeat=len(unknown)):
        female = base_f + [x for x, sex in zip(unknown, assignment) if sex == 0]
        male = base_m + [x for x, sex in zip(unknown, assignment) if sex == 1]
        if female and male:
            differences.append(statistics.mean(male) - statistics.mean(female))
    return {"unknown_sex_known_mass_n": len(unknown), "evaluated": True,
            "assignments": 2 ** len(unknown), "valid_assignments": len(differences),
            "min_difference_g": min(differences) if differences else None,
            "max_difference_g": max(differences) if differences else None}


def compute(rows, input_sha256):
    grouped, strata, species_rows, audits = [], [], [], []
    for row in rows:
        missing = [k for k in REQUIRED if row[k] is None]
        audits.append({"csv_row": row["csv_row"], **{k: row[k] for k in REQUIRED},
                       "missing_fields": ";".join(missing),
                       "included_overall": usable(row),
                       "included_stratified": usable(row) and row["island"] is not None and row["year"] is not None})
    for species in SPECIES:
        sub = [r for r in rows if r["species"] == species]
        for sex in SEXES:
            selected = [r for r in sub if r["sex"] == sex]
            grouped.append({"species": species, "sex": sex, "n_raw": len(selected),
                            "n_mass_missing": sum(r["body_mass_g"] is None for r in selected),
                            **stats(values(sub, sex))})
        local_strata = []
        for island, year in itertools.product(ISLANDS, YEARS):
            subcell = [r for r in sub if r["island"] == island and r["year"] == year]
            c = contrast(subcell)
            status = "comparable" if c["male_minus_female_g"] is not None else (
                "no_observations" if not subcell else "no_complete_sex_comparison")
            cell = {"species": species, "island": island, "year": year,
                    "n_raw": len(subcell), "n_excluded": sum(not usable(r) for r in subcell),
                    "status": status, **c}
            strata.append(cell)
            if status == "comparable":
                local_strata.append(cell)
        denomin = sum(s["n_female"] + s["n_male"] for s in local_strata)
        deltas = [s["male_minus_female_g"] for s in local_strata]
        # Shared sample-size weights for the same set of common strata in both sexes.
        standardized = (sum((s["n_female"] + s["n_male"]) * s["male_minus_female_g"]
                            for s in local_strata) / denomin) if denomin else None
        bounds = assignment_bounds(sub)
        species_rows.append({"species": species, "n_raw": len(sub),
                             "n_excluded": sum(not usable(r) for r in sub),
                             "n_missing_sex": sum(r["sex"] is None for r in sub),
                             "n_missing_mass": sum(r["body_mass_g"] is None for r in sub),
                             **contrast(sub), "comparable_strata_n": len(deltas),
                             "stratum_min_difference_g": min(deltas) if deltas else None,
                             "stratum_max_difference_g": max(deltas) if deltas else None,
                             "positive_strata_n": sum(d > 0 for d in deltas),
                             "standardized_difference_g": standardized,
                             "standardization_rows_n": denomin,
                             "unknown_sex_known_mass_n": bounds["unknown_sex_known_mass_n"],
                             "unknown_sex_min_difference_g": bounds.get("min_difference_g"),
                             "unknown_sex_max_difference_g": bounds.get("max_difference_g")})
    complete = sum(usable(r) for r in rows)
    summary = {
        "schema_version": "1", "analysis": "descriptive, observational secondary analysis",
        "input_sha256": input_sha256, "n_raw": len(rows), "n_complete_overall": complete,
        "matches_pinned_public_input": input_sha256 == PUBLIC_INPUT_SHA256,
        "observed_islands": sorted({r['island'] for r in rows if r['island'] is not None}),
        "observed_years": sorted({r['year'] for r in rows if r['year'] is not None}),
        "species_island_coverage": {sp: sorted({r['island'] for r in rows if r['species'] == sp and r['island'] is not None}) for sp in SPECIES},
        "n_excluded_overall": len(rows) - complete,
        "n_complete_stratified": sum(a["included_stratified"] for a in audits),
        "missing_counts": {k: sum(r[k] is None for r in rows) for k in REQUIRED},
        "n_missing_sex_and_mass": sum(r["sex"] is None and r["body_mass_g"] is None for r in rows),
        "missing_tokens": list(MISSING), "mass_unit": "g",
        "difference_definition": "mean(male) - mean(female), computed within species",
        "stratum_grid": "3 species x 3 islands x 3 years, including empty cells",
        "stratum_status_counts": {status: sum(s["status"] == status for s in strata)
                                   for status in ("comparable", "no_observations", "no_complete_sex_comparison")},
        "standardization": "Within species: same weights for each sex; weight proportional to n_female+n_male in each comparable island-year stratum; renormalize over comparable strata only",
        "inferential_statistics": "none: independence/pairing cannot be verified from this simplified CSV",
        "species": species_rows,
        "missing_sex_sensitivity": {sp: assignment_bounds([r for r in rows if r['species'] == sp]) for sp in SPECIES},
    }
    return summary, grouped, strata, audits


def write_csv(path, rows):
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)


def fmt(value):
    return "NA" if value is None else f"{value:,.1f}"


def text(x, y, value, size=15, fill="#222", anchor="start", weight="normal"):
    return f'<text x="{x:.2f}" y="{y:.2f}" font-size="{size}" fill="{fill}" text-anchor="{anchor}" font-weight="{weight}">{html.escape(str(value))}</text>'


def svg_start(width, height, title, description):
    return [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}px" height="{height}px" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">',
            f'<title id="title">{html.escape(title)}</title>', f'<desc id="desc">{html.escape(description)}</desc>',
            f'<rect width="{width}" height="{height}" fill="white"/>', '<g font-family="Arial, Helvetica, sans-serif">']


def figures(output, summary, strata):
    data = summary["species"]
    means = [s[k] for s in data for k in ("mean_female_g", "mean_male_g") if s[k] is not None]
    low = 500 * math.floor((min(means) - 200) / 500) if means else 0
    high = 500 * math.ceil((max(means) + 200) / 500) if means else 1000
    scale = lambda v: 185 + (v - low) / (high - low) * 620
    svg = svg_start(1150, 440, "Body mass by species and sex", "Means of available body masses; circles are female and squares are male. No error bars.")
    svg.extend([text(25, 38, "Body mass within each species", 24, weight="bold"),
                text(25, 65, "Complete sex and mass records; dots/squares are means; no error bars", 15)])
    for tick in range(int(low), int(high) + 1, 500):
        x = scale(tick)
        svg += [f'<line x1="{x}" y1="90" x2="{x}" y2="340" stroke="#ddd"/>', text(x, 367, tick, 14, anchor="middle")]
    for i, s in enumerate(data):
        y = 130 + i * 90
        svg.append(text(25, y + 5, s["species"], 19, weight="bold"))
        f, m = s["mean_female_g"], s["mean_male_g"]
        if f is not None and m is not None:
            svg.append(f'<line x1="{scale(f)}" y1="{y}" x2="{scale(m)}" y2="{y}" stroke="#777" stroke-width="2"/>')
        if f is not None:
            svg += [f'<circle cx="{scale(f)}" cy="{y}" r="6" fill="#B44B00"/>',text(scale(f),y+27,fmt(f),14,anchor="middle")]
        if m is not None:
            svg += [f'<rect x="{scale(m)-6}" y="{y-6}" width="12" height="12" fill="#166491"/>',text(scale(m),y-14,fmt(m),14,anchor="middle")]
        svg += [text(840,y-10,f"female n={s['n_female']}; male n={s['n_male']}",15),
                text(840,y+15,f"male - female: {fmt(s['male_minus_female_g'])} g",15)]
    svg += [text(495,398,"Mean body mass (g)",17,anchor="middle"),text(25,427,"Female: orange circle. Male: blue square. Data: palmerpenguins; analysis of the supplied CSV.",14), '</g></svg>']
    (output/'species-mass.svg').write_text('\n'.join(svg)+'\n', encoding='utf-8')
    differences = [s['male_minus_female_g'] for s in strata if s['male_minus_female_g'] is not None]
    low = min(0, 200*math.floor(min(differences)/200)) if differences else 0
    high = max(200, 200*math.ceil(max(differences)/200)) if differences else 200
    scale = lambda v: 400 + (v-low)/(high-low)*480
    height = 1050
    svg = svg_start(1190,height,"Male minus female mass within island-year strata", "All 27 species-island-year combinations are shown; no observations are labelled, never shown as zero differences. No error bars.")
    svg += [text(25,35,"Does the direction persist across island-year strata?",24,weight="bold"),
            text(25,62,"Mean male - mean female (g); full 27-cell grid; no error bars",16),
            text(25,91,"Species / island / year",15,weight="bold"),text(917,91,"Female n / Male n",15,weight="bold")]
    for tick in range(int(low),int(high)+1,200):
        x=scale(tick)
        svg += [f'<line x1="{x}" y1="105" x2="{x}" y2="945" stroke="{chr(35)}ddd"/>',text(x,974,tick,14,anchor="middle")]
    for i,s in enumerate(strata):
        y=124+i*31
        label=f"{s['species']} / {s['island']} / {s['year']}"
        svg.append(text(25,y+5,label,14))
        delta=s['male_minus_female_g']
        if delta is None:
            label="no observations" if s['status']=='no_observations' else 'no complete sex comparison'
            svg.append(text(430,y+5,label,14,fill="#666"))
        else:
            x=scale(delta)
            svg += [f'<circle cx="{x}" cy="{y}" r="5" fill="#166491"/>',text(x+11,y+5,fmt(delta),13),text(940,y+5,f"{s['n_female']} / {s['n_male']}",14)]
    svg += [text(640,1007,"Male - female mean body mass (g)",17,anchor="middle"),
            text(25,1038,"Empty cells reflect this sample's coverage. Positive values indicate higher mean mass among observed males.",14),'</g></svg>']
    (output/'stratum-differences.svg').write_text('\n'.join(svg)+'\n',encoding='utf-8')


def result_text(summary):
    identity = ("分析对象为 palmerpenguins 的公开简化 CSV；输入 SHA-256 与 source.json 中固定版本一致。数据提供者为 Kristen Gorman 与 Palmer Station LTER；原始数据为 CC0。" if summary['matches_pinned_public_input'] else "本次输入与固定的公开 palmerpenguins CSV 哈希不同；应按自备/测试数据解读，不能将本次输出当作公开数据结果。")
    lines=["# 三种企鹅样本的雌雄体质量差异", "",
           "## 问题与资料", "",
           "我们考察同物种内雄性与雌性平均体质量相差多少，以及该差异在岛屿—年份层中的方向和幅度。" + identity + "本分析生成自己的统计表与图。", "",
           "## 方法", "",
           "差异定义为雄性均值减雌性均值，单位为克；分别计算三物种，进一步按岛屿和年份共同分层。空字符串与 NA 作为缺失；只删除该比较所需变量缺失的行，不插补。标准差使用 n−1 分母；CSV 中不可计算的统计量留空，JSON 中为 null。岛屿—年份共同权重按各可比较层的两性可用样本量之和确定，两性使用同一组权重。", "",
           "## 结果", "",
           f"输入共 {summary['n_raw']} 行；物种、性别和体质量完整的行有 {summary['n_complete_overall']} 行。性别缺失 {summary['missing_counts']['sex']} 行，体质量缺失 {summary['missing_counts']['body_mass_g']} 行，其中两者同时缺失 {summary['n_missing_sex_and_mass']} 行；因此主分析共排除 {summary['n_excluded_overall']} 行。分层分析可用 {summary['n_complete_stratified']} 行。", "",
           "|物种|雌性 n|雌性均值/g|雄性 n|雄性均值/g|雄−雌/g|相对雌性均值/%|", "|---|---:|---:|---:|---:|---:|---:|"]
    for s in summary['species']:
        lines.append(f"|{s['species']}|{s['n_female']}|{fmt(s['mean_female_g'])}|{s['n_male']}|{fmt(s['mean_male_g'])}|{fmt(s['male_minus_female_g'])}|{fmt(s['difference_pct_female_mean'])}|")
    lines += ["", "图 `species-mass.svg` 展示两性均值；`grouped_by_species_sex.csv` 补充中位数、标准差及范围。图 `stratum-differences.svg` 与 `strata.csv` 同时保留所有27个层。"]
    for s in summary['species']:
        lines += ["",f"{s['species']} 有 {s['comparable_strata_n']} 个可比较层，其中 {s['positive_strata_n']} 个雄性均值较高；层内差异范围为 {fmt(s['stratum_min_difference_g'])}—{fmt(s['stratum_max_difference_g'])} g。共同层权重下的雄减雌差异为 {fmt(s['standardized_difference_g'])} g。"]
    lines += ["",f"全部网格中 {summary['stratum_status_counts']['no_observations']} 个层没有观测；没有观测的层不构成零差异。" + "；".join(f"{sp} 的岛屿覆盖为 {', '.join(islands) or '无'}" for sp,islands in summary['species_island_coverage'].items()) + "。单一岛屿记录只能比较该岛内的年份变化。各层方向与幅度应分别判断：同方向支持样本内方向一致，差异范围反映幅度变化，未进行等效性检验。", "", "## 缺失性别的敏感性", ""]
    for species,b in summary['missing_sex_sensitivity'].items():
        if b['evaluated']:
            lines.append(f"- {species}：将 {b['unknown_sex_known_mass_n']} 行体质量已知、性别缺失记录作全部 {b['assignments']} 种雌雄分配，均值差范围为 {fmt(b['min_difference_g'])}—{fmt(b['max_difference_g'])} g（可计算分配 {b['valid_assignments']} 种）。")
        else:
            lines.append(f"- {species}：{b['reason']}。")
    lines += ["", "此范围只检查缺失性别记录的潜在影响；体质量缺失行仍排除，范围不代表抽样置信区间。", "", "## 范围与下一步", "",
              f"结论描述这份输入中 {', '.join(summary['observed_years'])} 年、{', '.join(summary['observed_islands'])} 岛屿的记录。简化表没有个体和巢标识，本分析未核实个体独立性、跨年重复或配对结构，故不计算 p 值或置信区间。下一步应对照原始表与方法，确认个体/巢标识、抽样与测量时点，检查可用样本的选择过程；若建立总体推断，再按真实结构选择配对或聚类方法。", "",
              "## 来源", "",
              "- Horst AM, Hill AP, Gorman KB. palmerpenguins 项目：https://allisonhorst.github.io/palmerpenguins/ 。本例使用固定提交的简化 CSV，见 source.json。", "- Gorman KB, Williams TD, Fraser WR (2014). Ecological Sexual Dimorphism and Environmental Variability within a Community of Antarctic Penguins (Genus Pygoscelis). PLoS ONE 9(3):e90081. https://doi.org/10.1371/journal.pone.0090081 。原论文是资料背景来源；本分析只计算体质量的描述性比较。", ""]
    return '\n'.join(lines)


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True,help='new directory; must not exist')
    args=parser.parse_args(argv)
    try:
        # Check existence before expensive work, then atomic mkdir prevents overwrite races.
        if args.output.exists() or args.output.is_symlink():
            raise ValueError('Output must be a new directory')
        if not args.input.is_file():
            raise ValueError('Input must be an existing CSV file')
        digest=hashlib.sha256(args.input.read_bytes()).hexdigest()
        rows=read_rows(args.input)
        summary,grouped,strata,audits=compute(rows,digest)
        args.output.mkdir(parents=False,exist_ok=False)
        (args.output/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
        write_csv(args.output/'grouped_by_species_sex.csv',grouped)
        write_csv(args.output/'species_contrasts.csv',summary['species'])
        write_csv(args.output/'strata.csv',strata)
        write_csv(args.output/'row_audit.csv',audits)
        figures(args.output,summary,strata)
        (args.output/'results.md').write_text(result_text(summary),encoding='utf-8')
        print(json.dumps({'output':str(args.output),'n_raw':len(rows),'n_analyzed':summary['n_complete_overall'],'input_sha256':digest}))
        return 0
    except (OSError,ValueError,csv.Error) as exc:
        print(f'Analysis failed: {exc}',file=sys.stderr)
        return 2


if __name__=='__main__':
    raise SystemExit(main())
