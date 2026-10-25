#!/usr/bin/env python3
"""Deterministic stdlib calculation; paths resolve from this project, not cwd."""
from pathlib import Path
import csv, hashlib, json, math, platform, sys, time
ROOT=Path(__file__).resolve().parents[1]
NAMES=('C','Qc','D','P','Ta','T0')
def model(t,C,H,P,Ta,T0):
    if C<=0 or H<0 or t<0: raise ValueError('requires C>0,H>=0,t>=0')
    if H==0: return T0+P*t/C
    x=H*t/C
    # expm1 avoids catastrophic cancellation in the H -> 0 limit.
    return T0+(Ta-T0)*(-math.expm1(-x))+(P*t/C)*(-math.expm1(-x)/x if x else 1.0)
def predict(t,values):
    C,Qc,D,P,Ta,T0=values
    return model(t,C,Qc/D,P,Ta,T0)
def gradient(t,v):
    C,Qc,D,P,Ta,T0=v;H=Qc/D;E=math.exp(-H*t/C);b=P/H
    dH=-P/H**2*(1-E)-(T0-Ta-b)*t/C*E
    return [(T0-Ta-b)*E*H*t/C**2,dH/D,-dH*Qc/D**2,(1-E)/H,1-E,E]
def dotvar(g,h,u):return sum(a*b*s*s for a,b,s in zip(g,h,u))
def main():
    started=time.perf_counter()
    inp=ROOT/'inputs';cfg=json.loads((inp/'calibration.json').read_text())
    fields=[cfg['calibration'][k] for k in ('heat_capacity','steady_electrical_power','steady_excess_temperature')]+[cfg['operation'][k] for k in ('heater_power','ambient_temperature','initial_temperature')]
    v=[f['value'] for f in fields];u=[f['u'] for f in fields]
    C,Qc,D,P,Ta,T0=v;H=Qc/D;tau=C/H;b=P/H
    relH2=(u[1]/Qc)**2+(u[2]/D)**2
    uH=H*math.sqrt(relH2);utau=tau*math.sqrt((u[0]/C)**2+relH2);ub=b*math.sqrt((u[3]/P)**2+relH2)
    cov_tau_b=tau*b*relH2
    obs={float(r['time_s']):float(r['temperature_C']) for r in csv.DictReader((inp/'observations.csv').open())}
    pilot={float(r['time_s']):float(r['temperature_C']) for r in csv.DictReader((inp/'pilot.csv').open())}
    times=cfg['requested_times_s'];jac=[gradient(t,v) for t in times]
    rows=[]
    for t,g in zip(times,jac):
        T=predict(t,v);uT=math.sqrt(dotvar(g,g,u));trial=Ta+(T0-Ta)*math.exp(-H*t)
        row={'time_s':t,'predicted_C':T,'u_prediction_K':uT,'sensitivity_by_base_input':dict(zip(NAMES,g)),
             'variance_contribution_K2':dict(zip(NAMES,[(a*s)**2 for a,s in zip(g,u)])),
             'trial_recomputed_C':trial,'pilot_C':pilot.get(t),'trial_minus_pilot_K':trial-pilot[t],
             'corrected_minus_pilot_K':T-pilot[t]}
        if t in obs:
            residual=obs[t]-T
            row.update({'observed_C':obs[t],'observed_minus_prediction_K':residual,'observed_minus_pilot_K':obs[t]-pilot[t]})
            if t>0:
                combined=math.hypot(uT,cfg['observation_u']['value'])
                row.update({'u_residual_K_assuming_independent_readout':combined,'descriptive_standardized_residual':residual/combined})
        rows.append(row)
    # Check analytic Jacobian by two central-difference steps; not a statistical experiment.
    fd=[]
    for scale in (1e-4,1e-5):
        worst=0.0
        for t,g in zip(times,jac):
            for j,analytic in enumerate(g):
                h=max(abs(v[j]),1)*scale;hi=v.copy();lo=v.copy();hi[j]+=h;lo[j]-=h
                numeric=(predict(t,hi)-predict(t,lo))/(2*h)
                worst=max(worst,abs(numeric-analytic))
        fd.append({'relative_step':scale,'max_absolute_gradient_error':worst})
    limits=[]
    limits.append({'case':'initial','T_C':model(0,C,H,P,Ta,T0),'target_C':T0})
    limits.append({'case':'heater_off_t100','T_C':model(100,C,H,0,Ta,T0),'target_C':Ta+(T0-Ta)*math.exp(-H*100/C)})
    limits.append({'case':'long_time_50tau','time_s':50*tau,'T_C':model(50*tau,C,H,P,Ta,T0),'target_C':Ta+b,'trial_limit_C':Ta})
    for h in (1.0,0.01,1e-5,1e-9,0.0):
        got=model(100,C,h,P,Ta,T0);target=T0+P*100/C
        limits.append({'case':'insulation_fixed_time','H_W_per_K':h,'time_s':100,'T_C':got,'H0_target_C':target,'absolute_error_to_limit_K':abs(got-target)})
    finite_energy=[]
    for dt in (0.01,0.001):
        errs=[]
        for t in (1,5,20,50,100):
            derivative=(model(t+dt,C,H,P,Ta,T0)-model(t-dt,C,H,P,Ta,T0))/(2*dt)
            errs.append(abs(C*derivative-(-H*(model(t,C,H,P,Ta,T0)-Ta)+P)))
        finite_energy.append({'derivative_step_s':dt,'max_balance_residual_W':max(errs)})
    results={'config':{'base_order':list(NAMES),'base_values':v,'base_standard_u':u,'uncertainty':'first-order delta method; independent base inputs, shared across all times; observation residual readout independence assumed only for descriptive scales','seed_from_input':cfg['seed'],'seed_used':False,'seed_reason':'fully deterministic; no random sampling','time_u':'not provided; exact time treated as an assumption'},
      'calibration':{'H_W_per_K':H,'u_H_W_per_K':uH,'tau_s':tau,'u_tau_s':utau,'steady_excess_K':b,'u_steady_excess_K':ub,'steady_temperature_C':Ta+b,'u_steady_temperature_K':math.hypot(u[4],ub),'cov_tau_steady_excess_sK':cov_tau_b,'corr_tau_steady_excess':cov_tau_b/utau/ub,'steady_only_identifies_H_not_C':True},
      'predictions':rows,'prediction_covariance_K2':[[dotvar(g,h,u) for h in jac] for g in jac],
      'jacobian_finite_difference_checks':fd,'limit_checks':limits,'energy_finite_difference_checks':finite_energy,
      'initial_slope_K_per_s':(-H*(T0-Ta)+P)/C,'dimensionally_invalid_trial_numerical_initial_slope':-H*(T0-Ta),
      'failures_found':['Trial exponent H*t is dimensionful; missing C.','Trial omits heater forcing and has wrong powered steady limit.','Pilot disagreement with three noninitial observations is large.','Universal negligibility of calibration uncertainty unsupported.'],
      'execution_failures':[],'scope':'one supplied offline synthetic system; analytic model and local first-order input uncertainty only; no mechanism uniqueness or hardware certification'}
    out=ROOT/'artifacts/results.json';out.write_text(json.dumps(results,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
    elapsed=time.perf_counter()-started
    meta={'command':['python3','artifacts/run.py'],'python':platform.python_version(),'platform':platform.platform(),'elapsed_s':elapsed,'exit_code':0,'error':None,'input_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(inp.iterdir()) if p.is_file()},'output':'artifacts/results.json'}
    (ROOT/'artifacts/run-metadata.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'elapsed_s':elapsed,'calibration':results['calibration'],'predictions':[{k:r[k] for k in ('time_s','predicted_C','u_prediction_K')} for r in rows],'jacobian_checks':fd,'energy_checks':finite_energy},ensure_ascii=False,indent=2))
    if elapsed>=10:raise RuntimeError('formal run exceeded 10 seconds')
if __name__=='__main__':main()
