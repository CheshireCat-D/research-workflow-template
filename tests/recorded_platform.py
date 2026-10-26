"""Run frozen numerical fixtures on Windows without rewriting reviewed bytes.

Only missing POSIX instrumentation is adapted. CPU quotas, peak RSS and alarm
signals are explicitly unavailable; the calling test still enforces its real
subprocess wall timeout and compares all scientific result fields.
"""
from pathlib import Path
import json
import os
import runpy
import sys
import types


def install_windows_instrumentation():
    if os.name != 'nt':
        raise RuntimeError('The frozen-fixture adapter is Windows-only')
    resource = types.ModuleType('resource')
    resource.RLIMIT_CPU = 'unavailable-on-windows'
    resource.RUSAGE_SELF = 0

    def setrlimit(kind, limits):
        raise OSError('POSIX CPU resource limits are unavailable on Windows; outer wall timeout remains active')

    def getrlimit(kind):
        if kind != resource.RLIMIT_CPU:
            raise ValueError('Unsupported resource selector')
        return None, None

    def getrusage(kind):
        if kind != resource.RUSAGE_SELF:
            raise ValueError('Unsupported usage selector')
        return types.SimpleNamespace(ru_maxrss=None)

    resource.setrlimit = setrlimit
    resource.getrlimit = getrlimit
    resource.getrusage = getrusage
    sys.modules['resource'] = resource

    import signal
    original_signal = signal.signal
    sentinel = object()
    if not hasattr(signal, 'SIGALRM'):
        signal.SIGALRM = sentinel

        def signal_handler(signum, handler):
            if signum is sentinel:
                # No signal is installed: the parent subprocess owns timeout.
                return signal.SIG_DFL
            return original_signal(signum, handler)

        def alarm(seconds):
            if not isinstance(seconds, int) or seconds < 0:
                raise ValueError('Alarm duration must be a nonnegative integer')
            return 0

        signal.signal = signal_handler
        signal.alarm = alarm
    receipt = {
        'adapter': 'windows-frozen-fixture-instrumentation',
        'scientific_source_bytes_changed': False,
        'posix_cpu_limit': 'unavailable',
        'peak_rss': 'unmeasured-null',
        'sigalrm': 'unavailable; delegated to outer subprocess wall timeout',
    }
    print(json.dumps(receipt, sort_keys=True), file=sys.stderr, flush=True)


def main():
    if len(sys.argv) < 2:
        raise SystemExit('Usage: recorded_platform.py FROZEN_SCRIPT [SCRIPT_ARGS ...]')
    script = Path(sys.argv[1]).resolve()
    sys.argv = [str(script), *sys.argv[2:]]
    sys.path.insert(0, str(script.parent))
    install_windows_instrumentation()
    runpy.run_path(str(script), run_name='__main__')


if __name__ == '__main__':
    main()
