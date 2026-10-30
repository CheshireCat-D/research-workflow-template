import sys, os, json, hashlib, runpy
from pathlib import Path

log_path = Path(sys.argv[1])
target = Path(sys.argv[2])
target_args = sys.argv[3:]
seen = {}
active = False
def audit(event, args):
    global active
    if active or event != 'open':
        return
    name, mode, flags = args
    if not isinstance(name, (str, bytes, os.PathLike)):
        return
    if isinstance(mode, str) and not ('r' in mode or '+' in mode):
        return
    if mode is None and flags & (os.O_WRONLY | os.O_RDWR):
        return
    active = True
    try:
        p = Path(name).absolute()
        if p.is_file():
            data = p.read_bytes()
            digest = hashlib.sha256(data).hexdigest()
            seen[(str(p), digest)] = {'path': str(p), 'sha256': digest, 'bytes': len(data)}
    finally:
        active = False
sys.addaudithook(audit)
sys.argv = [str(target), *target_args]
try:
    runpy.run_path(str(target), run_name='__main__')
finally:
    active = True
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_text(json.dumps(list(seen.values()), ensure_ascii=False, indent=2)+'\n')
