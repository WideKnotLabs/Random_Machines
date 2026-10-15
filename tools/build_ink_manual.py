#!/usr/bin/env python3
"""Export the INK manual as a static reader-only site, without review tools or data.
Usage: python3 tools/build_ink_manual.py [path/to/RM INK]
"""
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
source = Path(sys.argv[1]).expanduser().resolve() if len(sys.argv) > 1 else Path.home() / 'Desktop/RM INK'
builder = source / 'documentation/guide/build/build.py'
if not builder.is_file():
    sys.exit(f'INK guide builder not found: {builder}')
subprocess.run([sys.executable, str(builder), '--public', '--out', str(ROOT / 'ink/manual')], check=True)
