from pathlib import Path
import argparse, hashlib, json, sys

def main():
    a=argparse.ArgumentParser(description='Read-only project identity and dependency recovery; no scientific certification')
    a.add_argument('--root',type=Path,default=Path(__file__).resolve().parent.parent)
    args=a.parse_args(); root=args.root.resolve()
    state=json.loads((root/'management/state.json').read_text(encoding='utf-8'))
    changes=[]; current={}
    for rel,ref in state['tracked_files'].items():
        p=root/rel
        if not p.is_file(): changes.append({'path':rel,'state':'missing','expected_sha256':ref['sha256']}); continue
        b=p.read_bytes(); h=hashlib.sha256(b).hexdigest(); current[rel]={'sha256':h,'bytes':len(b)}
        if h!=ref['sha256'] or len(b)!=ref['bytes']: changes.append({'path':rel,'state':'changed','expected_sha256':ref['sha256'],'current_sha256':h,'current_bytes':len(b)})
    changed_paths={c['path'] for c in changes}
    directly_changed=set()
    for node in state['logical_nodes']:
        if set(node.get('material_paths',[])) & changed_paths: directly_changed.add(node['id'])
    affected=set(directly_changed)
    while True:
        nxt=affected|{n['id'] for n in state['logical_nodes'] if set(n.get('dependencies',[])) & affected}
        if nxt==affected: break
        affected=nxt
    activities=state['activities']
    affected_activities=sorted(a for a in activities if a in affected)
    unaffected=sorted(a for a in activities if a not in affected)
    constraint_changes=changed_paths & {'management/constraints.json','management/obligations.json','management/source-identities.json','management/state.json'}
    if constraint_changes:
        affected_activities=sorted(activities); unaffected=[]
    snapshots=[]
    for version in state['versions']:
        p=root/version['snapshot_path']
        h=hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else None
        snapshots.append({'logical_path':version['logical_path'],'snapshot_path':version['snapshot_path'],'intact':h==version['sha256']})
    actual_parameters=None
    try: actual_parameters=json.loads((root/'notes/parameters.json').read_text(encoding='utf-8'))
    except (ValueError,OSError) as e: actual_parameters={'read_error':str(e)}
    answer={'case_id':state['case_id'],'state_authority':'management/state.json with supplied governance; current bytes take precedence over old recorded completion','active_parameters_observed':actual_parameters,'authoritative_constraints_at_checkpoint':state['active_constraints'],'changed_or_missing_paths':changes,'affected_activities':affected_activities,'unaffected_activities':unaffected,'checkpoint_freshness':'fresh-for-registered-local-files' if not changes else 'stale-requires-reconciliation','scientific_scope':state['scientific_scope'],'source_tracking_limits':state['source_tracking_limits'],'versions':snapshots,'next_action':state['next_action'] if not changes else '先按changed_or_missing_paths核对当前作者依据，保留旧内容；对受影响活动重新核验并更新权威状态。旧done/checkpoint不代表当前结果仍有效。','writes_project':False}
    print(json.dumps(answer,ensure_ascii=False,indent=2)); return 0 if not changes and all(v['intact'] for v in snapshots) else 3
if __name__=='__main__': raise SystemExit(main())
