#!/usr/bin/env python3
"""From PROJECT: python3 artifacts/run.py. Standard library, deterministic."""
import csv
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import platform
import sys
import time
from simulator import simulate

ROOT = Path(__file__).resolve().parents[1]


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n')


def metrics(rows):
    late = [r for r in rows if r['time_s'] >= 120.0]
    temp = [r['temperature_C'] for r in rows]
    minimum = min(r['temperature_C'] for r in late)
    maximum = max(r['temperature_C'] for r in late)
    actual = [r['actual_W'] for r in rows]
    request = [r['requested_W'] for r in rows]
    return {'temperature_at_120_C': late[0]['temperature_C'], 'temperature_final_C': temp[-1], 'temperature_min_late_C': minimum, 'temperature_max_late_C': maximum, 'temperature_max_all_C': max(temp), 'late_band_pass': minimum >= 24.5 and maximum <= 25.5, 'over_28_pass': max(temp) <= 28.0, 'power_min_W': min(actual), 'power_max_W': max(actual), 'requested_min_W': min(request), 'requested_max_W': max(request), 'power_limits_pass': min(actual) >= 0 and max(actual) <= 80, 'saturated_update_fraction': sum(r['actual_W'] != r['requested_W'] for r in rows[:-1]) / (len(rows) - 1), 'rows': len(rows)}


def main():
    start = time.perf_counter()
    packet = json.loads((ROOT/'inputs/scenarios.json').read_text())
    model = packet['model']
    dts = [0.2, 0.1, 0.05, 0.025, 0.0125]
    spec = importlib.util.spec_from_file_location('original_baseline', ROOT/'inputs/simulator.py')
    original = importlib.util.module_from_spec(spec); spec.loader.exec_module(original)
    nominal = packet['scenarios'][0]
    baseline_rows = original.simulate(model, nominal)
    baseline = {'source': 'inputs/simulator.py', 'scenario': nominal, 'config': model, 'limitations': 'Original algorithm ignores sensor delay and sends unbounded requested_W directly to model; only nominal executed as original main.', 'rows': len(baseline_rows), 'final_temperature_C': baseline_rows[-1]['temperature_C'], 'max_temperature_C': max(r['temperature_C'] for r in baseline_rows)}
    runs = []; trajectories = {}; failures = []
    traces = ROOT/'artifacts/traces'; traces.mkdir(exist_ok=True)
    for scene in packet['scenarios']:
        trajectories[scene['id']] = []
        for dt in dts:
            try:
                rows = simulate(model, scene, dt)
                summary = {'scenario': scene['id'], 'dt_s': dt, 'config': {**model, 'dt_s': dt}, 'scenario_config': scene, 'metrics': metrics(rows), 'execution_status': 'complete'}
                trajectories[scene['id']].append(rows)
                if dt == model['dt_s']:
                    relative = 'artifacts/traces/' + scene['id'] + '.csv'
                    with (ROOT/relative).open('w', newline='') as stream:
                        writer = csv.DictWriter(stream, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
                    summary['trajectory_path'] = relative
                runs.append(summary)
            except Exception as exc:
                failure = {'scenario': scene['id'], 'dt_s': dt, 'type': type(exc).__name__, 'message': str(exc)}
                failures.append(failure); runs.append({**failure, 'execution_status': 'failed'})
    convergence=[]; analytic=[]
    for scene in packet['scenarios']:
        sid=scene['id']; traces_at_steps=trajectories[sid]
        if len(traces_at_steps) != len(dts): continue
        fine=traces_at_steps[-1]
        differences=[]
        for i, dt in enumerate(dts[:-1]):
            coarse=traces_at_steps[i]; finer=traces_at_steps[i+1]
            ratio=round(dt/dts[-1]); adjacent=round(dt/dts[i+1])
            differences.append({'dt_s':dt,'max_difference_from_finest_C':max(abs(r['temperature_C']-fine[j*ratio]['temperature_C']) for j,r in enumerate(coarse)), 'max_difference_from_next_C':max(abs(r['temperature_C']-finer[j*adjacent]['temperature_C']) for j,r in enumerate(coarse))})
        labels=[(metrics(rows)['late_band_pass'], metrics(rows)['over_28_pass'], metrics(rows)['power_limits_pass']) for rows in traces_at_steps]
        stable=len(set(labels))==1
        convergence.append({'scenario':sid,'comparisons':differences,'acceptance_labels_stable':stable,'finest_pair_difference_le_0_05_C':differences[-1]['max_difference_from_next_C']<=0.05,'resolution_criterion_pass':stable and differences[-1]['max_difference_from_next_C']<=0.05})
        if sid in ('nominal','cold','hot'):
            if sid=='nominal':
                exact=lambda t:25.0-math.exp(-0.09*t)
                description='25-exp(-0.09t); unclipped no-delay control, requests initially65 W and fall to25 W'
            elif sid=='cold':
                exact=lambda t:21+3*math.exp(-0.01*t)
                description='21+3exp(-0.01t); all actual powers80 W'
            else:
                exact=lambda t:35-11*math.exp(-0.01*t)
                description='35-11exp(-0.01t); all actual powers0 W'
            analytic.append({'scenario':sid,'formula':description,'dt_errors':[{'dt_s':dt,'max_grid_error_C':max(abs(r['temperature_C']-exact(r['time_s'])) for r in rows)} for dt,rows in zip(dts,traces_at_steps)],'exact_120_C':exact(120),'exact_240_C':exact(240)})
    bounds={'required_power_target_5C_W':100,'required_power_target_35C_W':-50,'cold_max_equilibrium_C':21,'hot_min_equilibrium_C':35,'cold_best_120_C':21+3*math.exp(-1.2),'hot_best_120_C':35-11*math.exp(-1.2),'hot_best_240_C':35-11*math.exp(-2.4),'hot_28_crossing_s':-100*math.log(7/11),'necessary_ambient_band_for_invariance_C':[8.5,25.5],'ambient_range_exact_target_equilibrium_C':[9,25],'status':'Manual scalar ODE comparison/energy-balance derivation; independently numerically evaluated, no formal proof tool.'}
    selected=[run for run in runs if run.get('dt_s')==model['dt_s']]
    requirement_results=[{'id':'R1','status':'pass-in-model' if next(r for r in selected if r['scenario']=='nominal')['metrics']['late_band_pass'] else 'fail','criterion':'Nominal120–240 s inclusive within[24.5,25.5] C','evidence':'runs:nominal; convergence; analytic_checks'}, {'id':'R2','status':'fail','criterion':'All four mandatory scenes meet same late band','failing_scenarios':[r['scenario'] for r in selected if not r['metrics']['late_band_pass']],'evidence':'runs; actuator_feasibility; notes/analytic.md'}, {'id':'R3','status':'pass-in-implementation' if all(r['metrics']['power_limits_pass'] for r in selected) else 'fail','criterion':'actual_W in[0,80] at all evaluated times','evidence':'runs; artifacts/simulator.py; default traces'}, {'id':'R4','status':'fail-in-model; hardware-insufficient','criterion':'all times T<=28 C','failing_scenarios':[r['scenario'] for r in selected if not r['metrics']['over_28_pass']],'evidence':'runs; analytic_checks:hot','limitation':'No hardware protection/fault evidence exists'}, {'id':'R5','status':'pass-in-tested-resolution-scope' if all(x['resolution_criterion_pass'] for x in convergence) else 'inconclusive','criterion':'Five steps, finest pair difference<=0.05 C and stable acceptance labels','evidence':'convergence; analytic_checks','limitation':'No arbitrary-step stability or continuum error certificate'}]
    result={'schema_version':'1','executor':'Codex agent','scope':'Offline synthetic lumped thermal model, fixed four scenarios, Euler with delayed interpolated history and clipped actual power; no hardware data.', 'command':['python3','artifacts/run.py'],'cwd':'.','seed':'not applicable; deterministic','python':sys.version,'platform':platform.platform(),'input_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((ROOT/'inputs').glob('*')) if p.is_file()},'source_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/'artifacts/run.py',ROOT/'artifacts/simulator.py')},'baseline':baseline,'method':{'integrator':'forward Euler','history':'linear interpolation for non-grid delayed past; T(t<0)=initial; all tested delays align with grid','sampling':'endpoint metrics on full grid; explicit-Euler interpolated trajectory linear between states','dts_s':dts,'resolution_tolerance_C':0.05},'runs':runs,'convergence':convergence,'analytic_checks':analytic,'actuator_feasibility':bounds,'requirements':requirement_results,'execution_failures':failures,'elapsed_s':time.perf_counter()-start}
    write_json(ROOT/'artifacts/results.json',result)
    print(json.dumps({'results':'artifacts/results.json','scenarios':len(packet['scenarios']),'runs':len(runs),'failures':failures,'elapsed_s':result['elapsed_s'],'requirements':requirement_results},ensure_ascii=False,indent=2))
    return 0 if not failures else 1

if __name__=='__main__':
    sys.exit(main())
