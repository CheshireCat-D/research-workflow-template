"""Bounded file/record checks; no mathematical correctness certification."""
from pathlib import Path
from fractions import Fraction
import csv, io, json, hashlib, re
root=Path(__file__).resolve().parents[1]
text=(root/'inputs/observations.csv').read_text()
rows=list(csv.DictReader(io.StringIO('\n'.join(line for line in text.splitlines() if not line.startswith('#')))))
xs=[Fraction(r['x']) for r in rows]
ys=[Fraction(r['recorded_F_x']) for r in rows]
assert len(rows)==9 and len(set(xs))==9
assert xs==[Fraction(k,8) for k in range(9)]
assert all(y==0 for y in ys)
assert Fraction(1,16) not in xs
# Exact finite input identities; not the integral or unknown F.
assert min(abs(Fraction(1,32)-s) for s in xs)==Fraction(1,32)
assert min(abs(Fraction(3,32)-s) for s in xs)==Fraction(1,32)
assert Fraction(1,32)*(Fraction(3,32)-Fraction(1,32))==Fraction(1,512)
manifest=json.loads((root/'notes/source-map.json').read_text())
for item in manifest:
    assert hashlib.sha256((root/item['path']).read_bytes()).hexdigest()==item['sha256']
report=(root/'manuscript/report.md').read_text()
without_display=re.sub(r'\\\[.*?\\\]','',report,flags=re.S)
result={
 'scope':'CSV records, exact finite rational arithmetic, copied-input hashes and report length only; no proof certification or identification of F',
 'rows':len(rows),'unique_sample_points':len(set(xs)),'all_recorded_values_zero':all(y==0 for y in ys),
 'sample_points_rational':[str(x) for x in xs],
 'unobserved_counterexample_point':'1/16','all_copied_input_hashes_match':True,
 'report_han_characters_excluding_display_formulas':len(re.findall(r'[\u4e00-\u9fff]',without_display)),
 'report_characters_excluding_display_formulas':len(without_display),
 'report_within_approx_1000_han_limit':len(re.findall(r'[\u4e00-\u9fff]',without_display))<=1000,
 'mathematical_derivations':'notes/work.md',
}
assert result['report_within_approx_1000_han_limit']
(root/'notes/input-check.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(result,ensure_ascii=False,indent=2))
