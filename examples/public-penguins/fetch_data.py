#!/usr/bin/env python3
"""The example's only network entry: fetch the pinned CC0 CSV into a NEW directory."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import urllib.request


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path, help='new directory; parent must exist')
    args = parser.parse_args(argv)
    try:
        # Exclusive mkdir before network access; never replace another directory or input.
        args.output.mkdir(exist_ok=False, parents=False)
        source = json.loads(Path(__file__).with_name('source.json').read_text(encoding='utf-8'))
        request = urllib.request.Request(source['url'], headers={'User-Agent': 'RWT-public-penguins-example'})
        with urllib.request.urlopen(request, timeout=30) as response:
            data = response.read(1_000_001)
        if len(data) > 1_000_000 or len(data) != source['bytes']:
            raise ValueError('Downloaded length does not match the pinned input')
        if hashlib.sha256(data).hexdigest() != source['sha256']:
            raise ValueError('Downloaded SHA-256 does not match the pinned input')
        with (args.output/'penguins.csv').open('xb') as handle:
            handle.write(data)
        with (args.output/'source.json').open('x', encoding='utf-8') as handle:
            json.dump(source, handle, ensure_ascii=False, indent=2)
            handle.write('\n')
        print(json.dumps({'downloaded': str(args.output/'penguins.csv'), 'sha256': source['sha256']}))
        return 0
    except (OSError, ValueError, KeyError) as exc:
        print(f'Download failed: {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
