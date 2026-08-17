#!/usr/bin/env python3
"""Find and fix incorrect `endpoints.api` usages in tests.

Usage: run from repository root: `python3 dev/fix_endpoints.py`

What it does:
- Scans repo for `.get(` and `.post(` calls and prints matches.
- Applies a set of targeted regex replacements for known incorrect
  endpoint references (e.g. `endpoints.api.rooms.room_create` -> `endpoints.api.rooms.room_create`).
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PY_FILES = list(ROOT.rglob('*.py'))

def find_calls():
    pattern = re.compile(r"\.(get|post|delete)\(")
    hits = []
    for p in PY_FILES:
        try:
            text = p.read_text()
        except Exception:
            continue
        for i, line in enumerate(text.splitlines(), start=1):
            if pattern.search(line):
                hits.append((p.relative_to(ROOT), i, line.strip()))
    return hits

def apply_replacements(text: str) -> str:
    # 1) basic room collection fixes
    text = re.sub(r"\bendpoints\.api\.room_create\b", "endpoints.api.rooms.room_create", text)
    text = re.sub(r"\bendpoints\.api\.room_join\b", "endpoints.api.rooms.room_join", text)
    text = re.sub(r"\bendpoints\.api\.room_list\b", "endpoints.api.rooms.room_list", text)

    # 2) .format(room_name=...) -> placeholder attribute call
    def repl_format(match):
        name = match.group(1)
        arg = match.group(2)
        return f"endpoints.api.rooms.room_name.{name}(room_name={arg})"

    text = re.sub(r"endpoints\.api\.(room_detail|room_kick|room_delete)\.format\(\s*room_name\s*=\s*([^\)]+)\)", repl_format, text)

    return text

def run(dry=False):
    hits = find_calls()
    print(f"Found {len(hits)} files/lines with get/post/delete calls (sample):")
    for f, ln, line in hits[:60]:
        print(f"{f}:{ln}: {line}")

    # Now apply replacements to files that contain known incorrect patterns
    changed = []
    patterns = [r"endpoints.api.rooms.room_create", r"endpoints.api.rooms.room_join", r"endpoints.api.room_kick.format", r"endpoints.api.room_detail.format", r"endpoints.api.room_delete.format"]
    for p in PY_FILES:
        text = p.read_text()
        if any(pat in text for pat in patterns):
            new = apply_replacements(text)
            if new != text:
                changed.append(p.relative_to(ROOT))
                if not dry:
                    p.write_text(new)

    print('\nFiles modified:')
    for c in changed:
        print('-', c)
    if not changed:
        print('No files changed.')

if __name__ == '__main__':
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('--dry', action='store_true', help='Do not write files; only report')
    args = ap.parse_args()
    run(dry=args.dry)
