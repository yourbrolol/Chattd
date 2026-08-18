#!/usr/bin/env python3
"""
Scan test files and replace calls to the legacy `new_credentials(...)`
helper with the `Credentials(...)` class from tests.conftest, producing
`.as_dict()` results to preserve the old return type.

Usage:
  - Dry-run (default): shows proposed diffs without modifying files
      python3 dev/scripts/replace_newcredentials_with_credentials.py --path app/tests

  - Apply changes:
      python3 dev/scripts/replace_newcredentials_with_credentials.py --path app/tests --apply

The script tries to handle common call shapes:
  - new_credentials() -> Credentials().as_dict()
  - new_credentials(credentials={...}) -> Credentials(**{...}).as_dict()
  - new_credentials(credentials={...}, requirements={...}) -> Credentials(**{...}, userlen=(req).get('ulen',8), passlen=(req).get('passlen',12)).as_dict()

This is heuristic-based; review changes before applying.
"""
from __future__ import annotations

import argparse
import io
import os
import re
import sys
from typing import List, Tuple
import difflib


def find_matching(text: str, start: int, open_ch: str, close_ch: str) -> int:
    """Find index of matching close character starting from start (index of open_ch)."""
    depth = 0
    i = start
    in_squote = False
    in_dquote = False
    while i < len(text):
        ch = text[i]
        # handle quotes to avoid matching braces inside strings
        if ch == "'" and not in_dquote:
            in_squote = not in_squote
            i += 1
            continue
        if ch == '"' and not in_squote:
            in_dquote = not in_dquote
            i += 1
            continue

        if in_squote or in_dquote:
            i += 1
            continue

        if ch == open_ch:
            depth += 1
        elif ch == close_ch:
            depth -= 1
            if depth == 0:
                return i
        i += 1
    return -1


def extract_arg_block(text: str, start_paren: int) -> Tuple[int, int, str]:
    """Given index of `(`, return (start_idx, end_idx, inner_text)."""
    end = find_matching(text, start_paren, '(', ')')
    if end == -1:
        return start_paren, start_paren + 1, ''
    inner = text[start_paren + 1:end]
    return start_paren, end, inner


def replace_call_args(inner: str) -> str:
    s = inner.strip()
    # correct common misspelling
    s = re.sub(r'\bcredentails\b', 'credentials', s)

    if not s:
        return 'Credentials().as_dict()'

    # find credentials=... block
    cred_match = re.search(r'\bcredentials\s*=\s*', s)
    req_match = re.search(r'\brequirements\s*=\s*', s)

    def extract_literal(s: str, name_idx: int) -> Tuple[str, str]:
        """Return (literal_text, rest_after_literal) starting from name_idx in s."""
        # name_idx points at the start of 'credentials=' (the match.start)
        eq_idx = s.find('=', name_idx)
        if eq_idx == -1:
            return '', s
        i = eq_idx + 1
        # skip whitespace
        while i < len(s) and s[i].isspace():
            i += 1
        if i >= len(s):
            return '', s
        ch = s[i]
        if ch == '{':
            j = find_matching(s, i, '{', '}')
            if j == -1:
                return s[i:], ''
            return s[i:j+1].strip(), s[j+1:].lstrip(',').strip()
        # for simple tokens like None or a name or expression, take until comma or end
        j = i
        depth = 0
        in_sq = False
        in_dq = False
        while j < len(s):
            c = s[j]
            if c == "'" and not in_dq:
                in_sq = not in_sq
            elif c == '"' and not in_sq:
                in_dq = not in_dq
            elif not in_sq and not in_dq:
                if c in '([{':
                    depth += 1
                elif c in ')]}':
                    depth -= 1
                elif c == ',' and depth == 0:
                    break
            j += 1
        return s[i:j].strip(), s[j+1:].strip()

    creds_text = None
    reqs_text = None
    rest = s
    if cred_match:
        creds_text, rest = extract_literal(s, cred_match.start())
    if req_match:
        reqs_text, _ = extract_literal(s, req_match.start())

    # if both credentials and requirements found
    if creds_text and reqs_text:
        return f"Credentials(**{creds_text}, userlen=({reqs_text}).get('ulen', 8), passlen=({reqs_text}).get('passlen', 12)).as_dict()"

    if creds_text:
        return f"Credentials(**{creds_text}).as_dict()"

    if reqs_text:
        return f"Credentials(userlen=({reqs_text}).get('ulen', 8), passlen=({reqs_text}).get('passlen', 12)).as_dict()"

    # fallback: attempt to use positional args by passing them through as-is
    return f"Credentials({s}).as_dict()"


def process_file(path: str) -> Tuple[bool, str, str]:
    """Return (changed, original_text, new_text)."""
    with open(path, 'r', encoding='utf-8') as f:
        src = f.read()

    new = src

    # Replace import of new_credentials with Credentials in various import styles
    # Examples handled:
    # from ..conftest import new_credentials
    # from ..conftest import new_credentials, other
    new = re.sub(r"from\s+(\.{1,2}conftest)\s+import\s+([^\n]+)",
                 lambda m: _replace_imports(m.group(1), m.group(2)), new)

    # Replace calls to new_credentials(...)
    offsets = []
    for match in re.finditer(r'new_credentials\s*\(', new):
        start = match.start()
        paren_idx = new.find('(', start)
        astart, aend, inner = extract_arg_block(new, paren_idx)
        if aend == -1:
            continue
        # compute absolute indices
        call_start = start
        call_end = aend + 1
        replacement = replace_call_args(inner)
        offsets.append((call_start, call_end, replacement))

    # perform replacements from end->start so indices remain valid
    if offsets:
        parts = []
        last = 0
        for sidx, eidx, repl in offsets:
            parts.append(new[last:sidx])
            parts.append(repl)
            last = eidx
        parts.append(new[last:])
        new = ''.join(parts)

    changed = new != src
    return changed, src, new


def _replace_imports(mod: str, what: str) -> str:
    # split the import list by commas, replace new_credentials with Credentials
    items = [i.strip() for i in what.split(',')]
    new_items = []
    replaced = False
    for item in items:
        # handle "name as alias"
        parts = item.split()
        if parts and parts[0] == 'new_credentials':
            # preserve alias if present
            if len(parts) > 2 and parts[1].lower() == 'as':
                alias = parts[2]
                new_items.append(f'Credentials as {alias}')
            else:
                new_items.append('Credentials')
            replaced = True
        else:
            new_items.append(item)
    if not replaced:
        return f'from {mod} import {what}'
    return f'from {mod} import {", ".join(new_items)}'


def scan_and_replace(root: str, apply: bool = False) -> List[Tuple[str, str]]:
    changed_files = []
    for dirpath, dirnames, filenames in os.walk(root):
        for fn in filenames:
            if not fn.endswith('.py'):
                continue
            path = os.path.join(dirpath, fn)
            changed, src, new = process_file(path)
            if changed:
                changed_files.append((path, (src, new)))
                if apply:
                    # backup
                    with open(path + '.bak', 'w', encoding='utf-8') as bf:
                        bf.write(src)
                    with open(path, 'w', encoding='utf-8') as wf:
                        wf.write(new)
    return changed_files


def show_diffs(changed_files: List[Tuple[str, Tuple[str, str]]]):
    for path, (old, new) in changed_files:
        print('---', path)
        diff = difflib.unified_diff(old.splitlines(keepends=True), new.splitlines(keepends=True), fromfile=path + '.orig', tofile=path + '.new')
        sys.stdout.writelines(diff)


def main(argv: List[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument('--path', '-p', default='app/tests', help='Root tests path to scan')
    p.add_argument('--apply', action='store_true', help='Write changes to files (otherwise dry-run)')
    args = p.parse_args(argv)

    root = args.path
    apply = args.apply

    if not os.path.isdir(root):
        print(f'Path not found: {root}', file=sys.stderr)
        return 2

    changed = scan_and_replace(root, apply=apply)
    if not changed:
        print('No changes detected.')
        return 0

    show_diffs(changed)

    if apply:
        print('\nApplied changes to the files above. Backups saved with .bak extension.')
    else:
        print('\nDry-run complete. To apply changes, re-run with --apply')

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
