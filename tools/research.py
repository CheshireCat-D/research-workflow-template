#!/usr/bin/env python3
"""Run the repository-local D1 core without installation or API credentials."""
from pathlib import Path
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

if sys.version_info < (3, 11):
    raise SystemExit('Python 3.11 or newer is required')

from core.cli import main

if __name__ == '__main__':
    raise SystemExit(main())
