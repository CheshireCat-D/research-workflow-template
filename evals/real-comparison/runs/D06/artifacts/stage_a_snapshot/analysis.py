#!/usr/bin/env python3
"""Frozen calendar baselines and chronological, date-block evaluation (stdlib only)."""
import argparse
import collections
import csv
import datetime as dt
import hashlib
import json
import math
from pathlib import Path
import random

SEED = 20261029
B = 2000


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path, obj):
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def read_csv(path):
    with path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        return reader.fieldnames, rows


def csv_write(path, rows, fields):
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def audit_data(input_dir, output_dir, hours, days, hfields, dfields):
    hd = collections.defaultdict(list)
    for r in hours:
        hd[r["dteday"]].append(r)
    daymap = {r["dteday"]: r for r in days}
    coverage = []
    mismatch = []
    for date, rows in sorted(hd.items()):
        present = {int(r["hr"]) for r in rows}
        coverage.append({"date": date, "n_rows": len(rows), "n_unique_hours": len(present),
                         "missing_hours": ";".join(map(str, sorted(set(range(24)) - present)))})
        if date in daymap:
            for col in ["casual", "registered", "cnt"]:
                htotal = sum(int(r[col]) for r in rows)
                dtotal = int(daymap[date][col])
                if htotal != dtotal:
                    mismatch.append({"date": date, "column": col, "hour_sum": htotal, "day_value": dtotal})
    csv_write(output_dir / "date_coverage.csv", coverage,
              ["date", "n_rows", "n_unique_hours", "missing_hours"])
    csv_write(output_dir / "daily_count_mismatches.csv", mismatch,
              ["date", "column", "hour_sum", "day_value"])
    dates = sorted(hd)
    first, last = dt.date.fromisoformat(dates[0]), dt.date.fromisoformat(dates[-1])
    expected_dates = [(first + dt.timedelta(days=i)).isoformat() for i in range((last-first).days+1)]
    def empty_cells(rows):
        return sum(v is None or v.strip() == "" for r in rows for v in r.values())
    def duplicates(rows, keys):
        return len(rows) - len({tuple(r[k] for k in keys) for r in rows})
    consistency = []
    for date, rows in sorted(hd.items()):
        for col in ["workingday", "weekday", "holiday", "yr", "mnth"]:
            vals = {r[col] for r in rows}
            if len(vals) != 1 or (date in daymap and vals != {daymap[date][col]}):
                consistency.append({"date": date, "column": col})
    result = {
        "hour_rows": len(hours), "day_rows": len(days), "hour_columns": hfields,
        "day_columns": dfields, "date_start": dates[0], "date_end": dates[-1],
        "hour_date_count": len(hd), "day_date_count": len(daymap),
        "hour_duplicate_keys": duplicates(hours, ["dteday", "hr"]),
        "day_duplicate_keys": duplicates(days, ["dteday"]),
        "hour_duplicate_full_rows": duplicates(hours, hfields),
        "day_duplicate_full_rows": duplicates(days, dfields),
        "hour_empty_cells": empty_cells(hours), "day_empty_cells": empty_cells(days),
        "hour_count_identity_failures": sum(int(r["cnt"]) != int(r["casual"]) + int(r["registered"]) for r in hours),
        "day_count_identity_failures": sum(int(r["cnt"]) != int(r["casual"]) + int(r["registered"]) for r in days),
        "hour_count_negative_values": sum(int(r[k]) < 0 for r in hours for k in ["casual", "registered", "cnt"]),
        "hour_out_of_range": sum(int(r["hr"]) not in range(24) for r in hours),
        "hour_yr_values": sorted({int(r["yr"]) for r in hours}),
        "day_yr_values": sorted({int(r["yr"]) for r in days}),
        "hour_wrong_calendar_year": sum(not r["dteday"].startswith("2011-") for r in hours),
        "day_wrong_calendar_year": sum(not r["dteday"].startswith("2011-") for r in days),
        "hour_count_distribution": dict(sorted(collections.Counter(len(r) for r in hd.values()).items())),
        "complete_24h_dates": sum(len(rows)==24 and {int(r["hr"]) for r in rows} == set(range(24)) for rows in hd.values()),
        "missing_calendar_hours": sum(24-len({int(r["hr"]) for r in rows}) for rows in hd.values()),
        "missing_whole_dates": sorted(set(expected_dates)-set(hd)),
        "hour_only_dates": sorted(set(hd)-set(daymap)), "day_only_dates": sorted(set(daymap)-set(hd)),
        "daily_count_mismatches": mismatch, "calendar_field_mismatches": consistency,
        "source_sha256": {f: sha(input_dir / f) for f in ["TASK.md", "SOURCES.md", "ORIGINAL_README.txt", "UCI_PAGE_EXCERPT.txt", "INPUT_MANIFEST.json", "data/hour_2011.csv", "data/day_2011.csv"]},
    }
    manifest = json.loads((input_dir / "INPUT_MANIFEST.json").read_text(encoding="utf-8"))
    result["manifest_checks"] = {name: {"hash_match": sha(input_dir/name)==meta["sha256"],
                                            "rows_match": (len(hours) if "hour_" in name else len(days))==meta["data_rows"]}
                                 for name, meta in manifest.items()}
    write_json(output_dir / "data_audit.json", result)
    return result


def fit(rows, input_hash):
    sums0, nums0 = collections.defaultdict(int), collections.defaultdict(int)
    sums1, nums1 = collections.defaultdict(int), collections.defaultdict(int)
    for r in rows:
        h, w, y = int(r["hr"]), int(r["workingday"]), int(r["cnt"])
        sums0[h] += y
        nums0[h] += 1
        sums1[(w,h)] += y
        nums1[(w,h)] += 1
    return {
        "model_version": 1, "frozen_at": "2011-09-30 end of day",
        "train_start": min(r["dteday"] for r in rows), "train_end": max(r["dteday"] for r in rows),
        "train_n_rows": len(rows), "train_n_dates": len({r["dteday"] for r in rows}),
        "training_source_sha256": input_hash, "target": "cnt", "features_c0": ["hr"],
        "features_c1": ["workingday", "hr"], "round_predictions": False,
        "unseen_c1_rule": "fall back to C0 same hour; unseen hour raises an error",
        "C0": {str(h): {"sum": sums0[h], "n": nums0[h], "mean": sums0[h]/nums0[h]} for h in sorted(nums0)},
        "C1": {f"{w},{h}": {"sum": sums1[(w,h)], "n": nums1[(w,h)], "mean": sums1[(w,h)]/nums1[(w,h)]} for w,h in sorted(nums1)},
    }


def predict(rows, model):
    out = []
    for r in rows:
        date, h, w = r["dteday"], int(r["hr"]), int(r["workingday"])
        p0 = model["C0"][str(h)]["mean"]
        key = f"{w},{h}"
        fallback = key not in model["C1"]
        p1 = p0 if fallback else model["C1"][key]["mean"]
        y = int(r["cnt"])
        out.append({"date": date, "hr": h, "workingday": w, "actual": y,
                    "C0": p0, "C1": p1, "C1_fallback": int(fallback),
                    "abs_error_C0": abs(p0-y), "abs_error_C1": abs(p1-y),
                    "error_C0": p0-y, "error_C1": p1-y})
    return out


def metrics(preds):
    if not preds:
        raise ValueError("Empty scoring set")
    days = collections.defaultdict(list)
    for r in preds:
        days[r["date"]].append(r)
    n = len(preds)
    result = {"n_hours": n, "n_dates": len(days), "date_start": min(days), "date_end": max(days)}
    for model in ["C0", "C1"]:
        result[model] = {
            "MAE": math.fsum(r[f"abs_error_{model}"] for r in preds)/n,
            "RMSE": math.sqrt(math.fsum(r[f"error_{model}"]**2 for r in preds)/n),
            "bias_prediction_minus_actual": math.fsum(r[f"error_{model}"] for r in preds)/n,
            "day_equal_MAE": math.fsum(math.fsum(r[f"abs_error_{model}"] for r in rows)/len(rows) for rows in days.values())/len(days),
        }
    m0, m1 = result["C0"]["MAE"], result["C1"]["MAE"]
    d0, d1 = result["C0"]["day_equal_MAE"], result["C1"]["day_equal_MAE"]
    result["hour_weighted_absolute_improvement"] = m0-m1
    result["hour_weighted_relative_improvement"] = 1-m1/m0
    result["day_equal_absolute_improvement"] = d0-d1
    result["day_equal_relative_improvement"] = 1-d1/d0
    result["C1_fallback_rows"] = sum(r["C1_fallback"] for r in preds)
    return result


def quantile(values, p):
    ordered = sorted(values)
    x = (len(ordered)-1)*p
    lo, hi = math.floor(x), math.ceil(x)
    return ordered[lo] + (x-lo)*(ordered[hi]-ordered[lo])


def block_bootstrap(preds, length):
    byday = collections.defaultdict(list)
    for r in preds:
        byday[r["date"]].append(r)
    dates = sorted(byday)
    D = len(dates)
    daily = [(len(byday[d]), math.fsum(r["abs_error_C0"] for r in byday[d]),
              math.fsum(r["abs_error_C1"] for r in byday[d])) for d in dates]
    rng = random.Random(SEED)
    result = []
    for b in range(B):
        indexes = []
        while len(indexes) < D:
            start = rng.randrange(D)
            indexes.extend((start+j) % D for j in range(length))
        selected = [daily[i] for i in indexes[:D]]
        n = sum(r[0] for r in selected)
        m0 = math.fsum(r[1] for r in selected)/n
        m1 = math.fsum(r[2] for r in selected)/n
        result.append({"replicate": b+1, "n_sampled_dates": D, "n_sampled_hours": n,
                       "MAE_C0": m0, "MAE_C1": m1, "absolute_improvement": m0-m1,
                       "relative_improvement": 1-m1/m0})
    summary = {"block_length_days": length, "B": B, "seed": SEED, "D": D,
               "quantile_rule": "sorted linear interpolation at (B-1)*p",
               "absolute_improvement_95ci": [quantile([r["absolute_improvement"] for r in result],p) for p in [.025,.975]],
               "relative_improvement_95ci": [quantile([r["relative_improvement"] for r in result],p) for p in [.025,.975]]}
    return summary, result


def evaluate(preds, output_dir):
    byday = collections.defaultdict(list)
    for r in preds:
        byday[r["date"]].append(r)
    complete = {d for d, rows in byday.items() if len(rows)==24 and {r["hr"] for r in rows}==set(range(24))}
    result = {"overall": metrics(preds),
              "complete_24h_dates": metrics([r for r in preds if r["date"] in complete]),
              "by_workingday": {str(w): metrics([r for r in preds if r["workingday"]==w]) for w in [0,1]},
              "bootstrap": {}}
    for length in [7,28]:
        summary, replicates = block_bootstrap(preds, length)
        result["bootstrap"][str(length)] = summary
        csv_write(output_dir / f"bootstrap_L{length}.csv", replicates, list(replicates[0]))
    daily = []
    for d, rows in sorted(byday.items()):
        daily.append({"date": d, "n_hours": len(rows), "workingday": rows[0]["workingday"],
                      "sum_abs_error_C0": math.fsum(r["abs_error_C0"] for r in rows),
                      "sum_abs_error_C1": math.fsum(r["abs_error_C1"] for r in rows),
                      "MAE_C0": math.fsum(r["abs_error_C0"] for r in rows)/len(rows),
                      "MAE_C1": math.fsum(r["abs_error_C1"] for r in rows)/len(rows)})
    csv_write(output_dir / "daily_errors.csv", daily, list(daily[0]))
    csv_write(output_dir / "predictions.csv", preds, list(preds[0]))
    write_json(output_dir / "results.json", result)
    return result


def make_report(audit, model, res, output_dir):
    o = res["overall"]
    complete = res["complete_24h_dates"]
    def f(x): return f"{x:.6f}"
    def pct(x): return f"{100*x:.3f}%"
    def metric_row(label, q):
        return f"|{label}|{q['n_dates']}|{q['n_hours']}|{f(q['C0']['MAE'])}|{f(q['C1']['MAE'])}|{f(q['hour_weighted_absolute_improvement'])}|{pct(q['hour_weighted_relative_improvement'])}|"
    rows = "\n".join([metric_row("全部留出日期",o),metric_row("仅24小时完整日期",complete)] +
                      [metric_row(f"workingday={w}",res["by_workingday"][str(w)]) for w in [0,1]])
    bootrows = []
    for L in [7,28]:
        z = res["bootstrap"][str(L)]
        bootrows.append(f"|{L}|[{f(z['absolute_improvement_95ci'][0])}, {f(z['absolute_improvement_95ci'][1])}]|[{pct(z['relative_improvement_95ci'][0])}, {pct(z['relative_improvement_95ci'][1])}]|")
    conclusion = "达到" if o["hour_weighted_relative_improvement"]>=.10 else "没有达到"
    text = f"""# 单系统日历预测的历史外推审查

## 结论

模拟在2011年9月30日结束时冻结规则，在2011-10-01至2011-12-31的实际已记录小时上，C1的小时加权MAE比C0减少{f(o['hour_weighted_absolute_improvement'])}辆/小时，相对降低{pct(o['hour_weighted_relative_improvement'])}，{conclusion}预先规定的至少10%实务门槛。因此本留出期内，“C1改善”与“超过10%”两项均成立；它们是不同问题，后者不能由前者自动推出。未读取2012观测，尚无跨年实测结论。

## 数据身份与完整性

数据为Fanaee-T, H. (2013), Bike Sharing，UCI，DOI [10.24432/C5W894](https://doi.org/10.24432/C5W894)，Capital Bikeshare（华盛顿特区）单一系统的聚合计数。当前[UCI页面](https://archive.ics.uci.edu/dataset/275/bike+sharing+dataset)及许可信息使用随附2026-10-29离线摘录，[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)。输入CSV由原表按年份切片，保留原行字节；本分析未改动、补零或插补观测。两份切片SHA-256及行数均与INPUT_MANIFEST.json匹配。这里验证的是材料内部身份和一致性，没有重新下载原ZIP。原README所列介绍论文：Fanaee-T and Gama, “Event labeling combining ensemble detectors and background knowledge”, DOI 10.1007/s13748-013-0040-3；未提供论文正文，构造草稿不代表原作者论断。

hour_2011.csv的样本单位是一个系统的一个已记录(date,hr)小时，共{audit['hour_rows']}行、{audit['hour_date_count']}日期；day_2011.csv是系统的一天，共{audit['day_rows']}行。两者日期均覆盖{audit['date_start']}至{audit['date_end']}，年份编码均只有0，日期无整日缺口。小时(date,hr)键重复{audit['hour_duplicate_keys']}，日日期键重复{audit['day_duplicate_keys']}，整行重复分别{audit['hour_duplicate_full_rows']}/{audit['day_duplicate_full_rows']}；空单元格分别{audit['hour_empty_cells']}/{audit['day_empty_cells']}。小时范围异常{audit['hour_out_of_range']}，租车计数负值{audit['hour_count_negative_values']}。小时/日的cnt=casual+registered不成立的行数分别{audit['hour_count_identity_failures']}/{audit['day_count_identity_failures']}。

每日期记录小时数分布为{audit['hour_count_distribution']}；完整24小时日期{audit['complete_24h_dates']}个。在365×24的名义网格上少{audit['missing_calendar_hours']}个小时键，详细日期及小时在date_coverage.csv。无空单元格只描述已有行；不能推出每天24行，更不能把缺少的行解释成零需求。缺失原因无法由这两表确定，时区及夏令时的处理也未获充分说明，因此此处只审查名义日期小时键。

按日期汇总小时表的casual、registered、cnt，与日表逐列比较，差异项共{len(audit['daily_count_mismatches'])}个；两表日期集合差异为0，小时内以及两表间的日历字段不一致项{len(audit['calendar_field_mismatches'])}个。日计数一致不能反向证明每个日历小时都有记录。审核数值在data_audit.json，所有日期覆盖在date_coverage.csv。

## 来源文档的冲突处理

原README称完整小时表17379行、日表731行；当前UCI元数据称实例数17389。两者小时规模相差10，2011切片只有8645行，不足以独立核对完整两年总数，保留两个来源各自说法，不默默改数。

season的旧README为1春、2夏、3秋、4冬，当前摘录为1冬、2春、3夏、4秋；保留原始整数，不用其作本次特征，也不借助冲突文档重新编码。旧README温度说明为temp=T/41、atemp=A/50；当前摘录只针对小时尺度给temp=(T+8)/47、atemp=(A+16)/66。因此候选逆式分别为41×temp与47×temp−8、50×atemp与66×atemp−16，它们并不等价。来源不足以无条件决定日尺度逆式。未选择逆式、反归一化或改观测，且模型不用温度。当前许可是CC BY 4.0；原README另有论文引用请求，两项均保留。

## 冻结规则与评价口径

训练只用date<2011-10-01的已有小时，实际{model['train_start']}至{model['train_end']}，{model['train_n_dates']}天、{model['train_n_rows']}小时。C0(h)=训练中hr=h的cnt算术均值；C1(w,h)=训练中(workingday,hr)=(w,h)的cnt算术均值。C1未见组合回退同小时C0；未见小时直接报错。冻结模型含24个C0和{len(model['C1'])}个C1单元及各自和、样本数和未舍入均值，保存model.json。留出实际{o['date_start']}至{o['date_end']}，{o['n_dates']}天、{o['n_hours']}小时，回退{o['C1_fallback_rows']}次。未随机拆行、未调参、未用留出重估参数。预测输入仅hr及workingday，日期只用于切分和评价索引，不是数值特征。天气、instant、casual、registered、yr均不输入模型。workingday依据预先已知的周末及节假日日历；部署时须在预测前获得这个日历，不能事后用需求推断。

设e_m=预测_m−实际。小时MAE=Σ|e_m|/N，RMSE=√(Σe_m²/N)，偏差=Σe_m/N。绝对改善=MAE0−MAE1，相对改善=1−MAE1/MAE0。正值代表C1好。按日等权MAE先在每个日期对已有小时取MAE，再对D天等权平均，与所有小时合并加权的指标是不同问题；两者不混用。预测未四舍五入，报告仅显示舍入。

|模型|小时MAE|小时RMSE|平均偏差（预测−真实）|按日等权日内MAE均值|
|---|---:|---:|---:|---:|
|C0|{f(o['C0']['MAE'])}|{f(o['C0']['RMSE'])}|{f(o['C0']['bias_prediction_minus_actual'])}|{f(o['C0']['day_equal_MAE'])}|
|C1|{f(o['C1']['MAE'])}|{f(o['C1']['RMSE'])}|{f(o['C1']['bias_prediction_minus_actual'])}|{f(o['C1']['day_equal_MAE'])}|

按日等权的MAE均值差为{f(o['day_equal_absolute_improvement'])}，相对降低{pct(o['day_equal_relative_improvement'])}。

|评价子集|日期数|小时数|C0 MAE|C1 MAE|绝对改善|相对改善|
|---|---:|---:|---:|---:|---:|---:|
{rows}

完整日分析只改变留出评价子集，不重新训练。工作日分组也是使用同一冻结模型，组内为小时加权MAE。主结论针对记录的小时；对没有目标记录的小时不能打分。即使完整日子集方向一致，也不能证成未记录小时的误差相同。

## 日期配对循环移动块bootstrap

将留出日期排序，D={o['n_dates']}。每次从random.Random(20261029)调用randrange(D)等概率选块起点，连续取L天并在末尾循环；反复抽块至至少D天后截断为D。对两模型使用同一日期样本，并保留每次抽中日期内全部小时，按抽样后的总绝对误差/总小时数计算MAE。B=2000，L=7和L=28分别重置同一seed。95%百分位区间对排序后的2000个量在(B−1)p处线性插值。没有把小时当独立重采样。

|块长（天）|MAE0−MAE1的95%区间|1−MAE1/MAE0的95%区间|
|---:|---|---|
{chr(10).join(bootrows)}

两个块长的相对降幅区间下端也均高于10%，在以下重采样条件成立时，结果支持本留出期的改善超过门槛。

这些区间描述：在模型固定、以本留出期日期块经验分布代表可重复时间过程时，两模型误差差异的抽样波动。它们保留日内配对关系和块内时间关联，但不包含重新训练不确定性，也不能覆盖所有潜在长期关联。解释依赖块长足以代表相关长度、误差差异在评价期内大致稳定及日期块可交换等近似条件；92天对28天块尤其有限。循环会把期末接到期初，这是指定算法中的近似，季节趋势或系统增长会破坏稳定性。跨年需求规模、日历组成和运行条件可变，区间不能保证2012结果。区间是否高于零只回应改善；是否高于10%才涉及门槛的不确定性，主实务判断仍使用预先约定的实际留出点估计，不为越过门槛挑选块长。

## 对构造草稿逐项审核

1. **保留但限定**：随附当前官方元数据确称无缺失值；实测两表没有空单元格。**纠正**：这不等于每天完整24小时，实际缺{audit['missing_calendar_hours']}个名义小时键。
2. **纠正**：随机拆小时行不模拟9月30日冻结后预报未来，会混合时间环境且忽视相关性。本分析以严格未来时间留出替代。
3. **纠正**：casual与registered是目标cnt的同期组成，求和得到零误差是计数恒等式和目标泄漏，不是未来预测能力。实际天气一般在日前未知；若要用天气必须另给当时可获得的预报，本题排除天气。
4. **未获支持**：历史零拟合误差无法推出未来精确。此处冻结日历模型在留出有明确非零误差。
5. **未获支持**：相邻小时及相邻日期存在共同日历和运行环境，不能据此假设逐小时独立；本次按日期配对、以时间块重采样，仍需审查较长依赖。
6. **未获支持**：workingday差异是聚合观察关联，含周末、节假日及其他混杂，不是改变安排的干预效应；不能推断个体行为。
7. **未获支持**：2011结果不能直接推广下一年。下一阶段应原样载入已冻结模型，在新观测上先预测再按同一口径评价，不能用2012重训后再称原模型外推成功。

本审查只验证所提供CSV的身份、一致性、指定预测与评价程序的执行结果，不构成原始采集质量、个体机制或论文正文的验证。
"""
    assert len(text) <= 12000, len(text)
    (output_dir / "report.md").write_text(text, encoding="utf-8")
    return len(text)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--mode", choices=["train-score", "score"], default="train-score")
    parser.add_argument("--model", type=Path)
    parser.add_argument("--hour-file", default="hour_2011.csv")
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    hpath = args.input_dir / "data" / args.hour_file
    hfields, hours = read_csv(hpath)
    if args.mode == "score":
        if args.model is None:
            parser.error("--model required for score mode")
        model = json.loads(args.model.read_text(encoding="utf-8"))
        preds = predict(hours, model)
        res = evaluate(preds, args.output_dir)
        write_json(args.output_dir / "score_provenance.json", {"model_sha256": sha(args.model),
                   "hour_input_sha256": sha(hpath), "rows": len(hours), "trained": False})
        print(json.dumps(res["overall"], ensure_ascii=False, indent=2))
        return
    if args.hour_file != "hour_2011.csv":
        parser.error("train-score is limited to hour_2011.csv")
    dfields, days = read_csv(args.input_dir / "data" / "day_2011.csv")
    audit = audit_data(args.input_dir, args.output_dir, hours, days, hfields, dfields)
    train = [r for r in hours if r["dteday"] < "2011-10-01"]
    test = [r for r in hours if "2011-10-01" <= r["dteday"] <= "2011-12-31"]
    model = fit(train, sha(hpath))
    write_json(args.output_dir / "model.json", model)
    preds = predict(test, model)
    res = evaluate(preds, args.output_dir)
    report_chars = make_report(audit, model, res, args.output_dir)
    write_json(args.output_dir / "run_summary.json", {"report_characters": report_chars,
               "model_sha256": sha(args.output_dir / "model.json"),
               "code_sha256": sha(Path(__file__)), "seed": SEED, "bootstrap_B": B})
    print(json.dumps({"audit": audit, "results": res, "report_characters": report_chars}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
