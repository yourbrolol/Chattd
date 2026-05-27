#!/usr/bin/env python3
"""Split a combined CSS file by special section markers.

The script reads a CSS file and writes one output file per marker of the
form:

    /*!!filename.css*/

It preserves blank lines at the start and end of each generated section.
The source file is left untouched.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import DefaultDict, Dict, List

MARKER_RE = re.compile(r"^\s*/\*\s*!!\s*([^*\s][^*]*?)\s*\*/\s*$")


def parse_sections(lines: List[str]) -> Dict[str, List[str]]:
    """Parse lines and split them into section buffers keyed by filename."""
    file_sections: DefaultDict[str, List[str]] = DefaultDict(list)
    current_name: str | None = None
    current_lines: List[str] = []
    leading_blanks: List[str] = []
    seen_nonblank_before_marker = False

    def flush_section(name: str, buf: List[str]) -> None:
        if buf or name not in file_sections:
            file_sections[name].extend(buf)

    for line_number, line in enumerate(lines, start=1):
        marker_match = MARKER_RE.match(line)
        if marker_match:
            section_name = marker_match.group(1).strip()
            if current_name is None:
                current_name = section_name
                current_lines = leading_blanks.copy()
                leading_blanks.clear()
            else:
                flush_section(current_name, current_lines)
                current_name = section_name
                current_lines = []
            continue

        if current_name is None:
            if line.strip() == "":
                leading_blanks.append(line)
            else:
                seen_nonblank_before_marker = True
                leading_blanks.append(line)
        else:
            current_lines.append(line)

    if current_name is None:
        raise ValueError(
            "No section markers found. Make sure the input CSS contains lines like '/*!!filename.css*/'."
        )

    flush_section(current_name, current_lines)

    if seen_nonblank_before_marker:
        raise ValueError(
            "Found non-blank CSS before the first section marker. "
            "Move any global lines after the first marker or insert a marker at the top."
        )

    return file_sections


def write_files(base_dir: Path, sections: Dict[str, List[str]], dry_run: bool) -> None:
    for filename, content_lines in sections.items():
        target_path = base_dir / filename
        if target_path.exists() and not target_path.is_file():
            raise FileExistsError(f"Target exists and is not a file: {target_path}")

        if dry_run:
            print(f"Would write {target_path} ({len(content_lines)} lines)")
            continue

        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text("".join(content_lines), encoding="utf-8")
        print(f"Wrote {target_path}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Split a combined CSS file into multiple files using /*!!filename.css*/ markers."
    )
    parser.add_argument(
        "input",
        nargs="?",
        default="app/chat/static/chat/style.css",
        help="Path to the combined source CSS file.",
    )
    parser.add_argument(
        "--output-dir",
        help="Directory to write split CSS files into. Defaults to the source file directory.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the files that would be written without creating them.",
    )
    args = parser.parse_args()

    source_path = Path(args.input).expanduser().resolve()
    if not source_path.exists():
        raise FileNotFoundError(f"Source CSS file not found: {source_path}")
    if not source_path.is_file():
        raise ValueError(f"Source path is not a file: {source_path}")

    output_dir = Path(args.output_dir).expanduser().resolve() if args.output_dir else source_path.parent
    output_dir.mkdir(parents=True, exist_ok=True)

    source_lines = source_path.read_text(encoding="utf-8").splitlines(keepends=True)
    sections = parse_sections(source_lines)
    write_files(output_dir, sections, args.dry_run)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
