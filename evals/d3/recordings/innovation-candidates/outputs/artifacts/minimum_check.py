"""A cheap deterministic falsification, run from project root."""
import json
from fractions import Fraction as F
from pathlib import Path
W=json.loads(Path('inputs/workloads.json').read_text())
w=next(w for w in W['workloads'] if w['id']=='new_hotspot')
n=len(w['x_old']);d=[F(x-y) for x,y in zip(w['x_current'],w['x_old'])];D=sum(d);s=w['history_scores'];S=sum(s)
p=[F(1,2*n)+F(x,2*S) for x in s]
out=[]
for k in W['budgets']:
 va=F(n*n,k)*(1-F(k,n))*sum((x-D/n)**2 for x in d)/(n-1)
 vc=(sum(x*x/pi for x,pi in zip(d,p))-D*D)/k
 out.append({'k':k,'A_mse':str(va),'C_mix_mse':str(vc),'ratio':str(vc/va),'claim_falsified':vc>va})
result={'workload':'new_hotspot','alpha':'1/2','evaluation':'exact rational moments; no simulation seed needed','rows':out}
Path('artifacts/minimum-check.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
