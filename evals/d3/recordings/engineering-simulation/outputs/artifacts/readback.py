"""Independent default-CSV arithmetic readback; run from any cwd."""
import csv
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
packet=json.loads((ROOT/'inputs/scenarios.json').read_text());m=packet['model'];checked=[]
for s in packet['scenarios']:
    with (ROOT/'artifacts/traces'/f"{s['id']}.csv").open() as stream:
        rows=[{k:float(v) for k,v in r.items()} for r in csv.DictReader(stream)]
    errors=[0.0]*4;delay=round(s['sensor_delay_s']/m['dt_s'])
    for i,r in enumerate(rows):
        measured=s['initial_C'] if i-delay<0 else rows[i-delay]['temperature_C']
        request=m['loss_W_per_K']*(m['target_C']-s['ambient_C'])+m['gain_W_per_K']*(m['target_C']-measured)
        actual=max(0,min(80,request))
        e=[abs(r['measured_C']-measured),abs(r['requested_W']-request),abs(r['actual_W']-actual),0.0]
        if i+1<len(rows):
            expected=r['temperature_C']+m['dt_s']*(actual-m['loss_W_per_K']*(r['temperature_C']-s['ambient_C']))/m['capacity_J_per_K']
            e[3]=abs(rows[i+1]['temperature_C']-expected)
        errors=[max(a,b) for a,b in zip(errors,e)]
    checked.append(dict(zip(['scenario','rows','max_delay_read_error_C','max_request_error_W','max_clamp_error_W','max_euler_update_error_C'],[s['id'],len(rows),*errors])))
result={'scope':'Independent arithmetic readback of default CSV records; not physical validation or numerical convergence proof. All tested delays align with grid; non-grid interpolation code not separately exercised.','scenarios':checked,'threshold':1e-10,'passed':all(max(v for k,v in s.items() if k.startswith('max_'))<1e-10 for s in checked)}
(ROOT/'checks/trace-readback.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(result,ensure_ascii=False,indent=2))
raise SystemExit(0 if result['passed'] else 1)
