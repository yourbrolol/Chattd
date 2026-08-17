#!/usr/bin/env python3
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
JS_DIR = ROOT / "app/chat/static/chat/js"
OUTPUT_FILE = ROOT / "dev/fetch_endpoints.txt"
EXCLUDED_FILES = {"api.js"}


def strip_comments(text: str) -> str:
    result = []
    i = 0
    in_string = None
    escape_next = False

    while i < len(text):
        ch = text[i]
        nxt = text[i + 1] if i + 1 < len(text) else ""

        if in_string is not None:
            result.append(ch)
            if escape_next:
                escape_next = False
            elif ch == "\\":
                escape_next = True
            elif ch == in_string:
                in_string = None
            i += 1
            continue

        if ch in {'"', "'", "`"}:
            in_string = ch
            result.append(ch)
            i += 1
            continue

        if ch == "/" and nxt == "/":
            while i < len(text) and text[i] != "\n":
                i += 1
            continue

        if ch == "/" and nxt == "*":
            i += 2
            while i < len(text) and not (text[i] == "*" and i + 1 < len(text) and text[i + 1] == "/"):
                i += 1
            if i < len(text):
                i += 2
            continue

        result.append(ch)
        i += 1

    return "".join(result)


def extract_fetch_calls(text: str):
    clean = strip_comments(text)
    matches = []
    pattern = re.compile(r"\bfetch\b\s*\(")

    for match in pattern.finditer(clean):
        cursor = match.end()
        while cursor < len(clean) and clean[cursor].isspace():
            cursor += 1

        if cursor >= len(clean):
            continue

        start = cursor
        quote = clean[cursor]
        if quote in {"'", '"', "`"}:
            end = cursor + 1
            escaped = False
            while end < len(clean):
                ch = clean[end]
                if escaped:
                    escaped = False
                elif ch == "\\":
                    escaped = True
                elif ch == quote:
                    break
                end += 1
            if end < len(clean):
                matches.append(clean[start + 1:end])
                continue

        # Fallback for non-literal arguments
        end = cursor
        depth = 0
        while end < len(clean):
            ch = clean[end]
            if ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1
                if depth < 0:
                    break
            elif ch == "," and depth == 0:
                break
            end += 1
        matches.append(clean[cursor:end].strip())

    return matches


def main():
    js_files = sorted(JS_DIR.glob("*.js"))

    collected = []
    for path in js_files:
        if path.name in EXCLUDED_FILES:
            continue
        text = path.read_text(encoding="utf-8")
        calls = extract_fetch_calls(text)
        for call in calls:
            collected.append((path.relative_to(ROOT).as_posix(), call))

    OUTPUT_FILE.write_text(
        "\n".join(f"{rel}: {call}" for rel, call in collected) + ("\n" if collected else ""),
        encoding="utf-8",
    )

    print(f"Collected {len(collected)} fetch call(s) from {len(js_files) - 1} file(s)")
    print(f"Output written to {OUTPUT_FILE.relative_to(ROOT).as_posix()}")
    print("\n---")
    for rel, call in collected:
        print(f"{rel}: {call}")


if __name__ == "__main__":
    main()
