from pathlib import Path
import argparse, hashlib, json, sys

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def logical(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True).encode()).hexdigest()

def status(root):
    state = json.loads((root / '.research/state.json').read_text(encoding='utf-8'))
    changed, missing, current = [], [], {}
    for relative, expected in state['tracked_materials'].items():
        path = root / relative
        if not path.is_file():
            missing.append(relative)
        else:
            current[relative] = digest(path)
            if current[relative] != expected['sha256']:
                changed.append(relative)
    activities = {}
    for name, activity in state['activities'].items():
        reasons = []
        for relative, expected in activity['completed_material_sha256'].items():
            if current.get(relative) != expected:
                reasons.append('missing or changed material: ' + relative)
        for key, expected in activity.get('completed_logical_sha256', {}).items():
            if logical(state[key]) != expected:
                reasons.append('changed logical state: ' + key)
        activities[name] = {'recorded_status': activity['status'], 'effective_status': 'needs_recheck' if reasons else activity['status'], 'reasons': reasons}
    progress = True
    while progress:
        progress = False
        for name, activity in state['activities'].items():
            for dependency in activity['depends_on']:
                if activities[dependency]['effective_status'] != 'done':
                    reason = 'dependency needs recheck: ' + dependency
                    if reason not in activities[name]['reasons']:
                        activities[name]['reasons'].append(reason)
                        activities[name]['effective_status'] = 'needs_recheck'
                        progress = True
    result = {'case_id': state['case_id'], 'authoritative_state': '.research/state.json', 'revision': state['revision'], 'active_constraints': state['active_constraints'], 'next_action': state['next_action'], 'changed_paths': changed, 'missing_paths': missing, 'activities': activities, 'checkpoint_freshness': 'fresh_for_registered_bytes' if all(current.get(p) == expected for p, expected in state['checkpoint']['material_sha256'].items()) else 'stale_for_registered_bytes', 'coverage_limits': state['coverage_limits'], 'source_access': state['source_access'], 'scientific_scope': state['statement'], 'author_review': state['author_review']}
    return result

def main():
    parser = argparse.ArgumentParser(description='Offline durable project status and guarded exact-byte restoration. Status is read-only.')
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('status')
    restore = sub.add_parser('restore-initial')
    restore.add_argument('relative_path')
    restore.add_argument('--expected-current', required=True, help='Current complete SHA256, or MISSING. Refuses conflicts.')
    restore.add_argument('--write', action='store_true', help='Required to actually restore; default is a preview.')
    args = parser.parse_args()
    root = args.root.resolve()
    if args.command == 'status':
        print(json.dumps(status(root), ensure_ascii=False, indent=2))
        return 0
    state = json.loads((root / '.research/state.json').read_text(encoding='utf-8'))
    if args.relative_path not in state['versions']:
        raise ValueError('No preserved initial content for requested path')
    version = state['versions'][args.relative_path]
    source = root / version['content_path']
    target = root / args.relative_path
    if not target.resolve().is_relative_to(root) or not source.resolve().is_relative_to(root):
        raise ValueError('Path escapes project')
    if digest(source) != version['sha256']:
        raise ValueError('Preserved content hash mismatch')
    current = digest(target) if target.is_file() else 'MISSING'
    if current != args.expected_current:
        raise ValueError('Conflict: current hash differs from explicitly expected current')
    if args.write:
        if target.exists():
            archive = root / '.research/versions/pre-restore' / current / args.relative_path
            if archive.exists() and archive.read_bytes() != target.read_bytes():
                raise ValueError('Archive collision')
            archive.parent.mkdir(parents=True, exist_ok=True)
            if not archive.exists():
                archive.write_bytes(target.read_bytes())
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(source.read_bytes())
    print(json.dumps({'operation': 'restore-initial', 'written': args.write, 'target': args.relative_path, 'previous_sha256': current, 'restored_sha256': version['sha256'], 'note': 'Restoration does not mark activities completed or revise authoritative metadata.'}, ensure_ascii=False))
    return 0

if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (ValueError, OSError, KeyError) as error:
        print(json.dumps({'passed': False, 'error': type(error).__name__, 'message': str(error)}, ensure_ascii=False), file=sys.stderr)
        raise SystemExit(2)
