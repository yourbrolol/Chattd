#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JS_DIR = ROOT / "app/chat/static/chat/js"
EXCLUDED_FILES = {"api.js", "factories.js"}


def ensure_api_import(text: str) -> str:
    if "from './api.js'" in text or "from \"./api.js\"" in text:
        return text

    lines = text.splitlines()
    insert_at = 0
    for idx, line in enumerate(lines):
        if line.strip().startswith("import "):
            insert_at = idx + 1
            break

    if insert_at == 0:
        return "import { api } from './api.js';\n\n" + text

    lines.insert(insert_at, "import { api } from './api.js';")
    return "\n".join(lines) + "\n"


def replace_in_file(path: Path) -> bool:
    text = path.read_text(encoding="utf-8")
    original = text

    if path.name in EXCLUDED_FILES:
        return False

    replacements = []

    if path.name == "applications.js":
        replacements.extend([
            (
                "const response = await fetch('/rooms/apply/', {\n            method: 'POST',\n            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },\n            body,\n        });",
                "const response = await api.applications.apply(trimmed, { headers: { 'Content-Type': 'application/x-www-form-urlencoded' } });",
            ),
            (
                "const response = await fetch(`/rooms/applications/${applicationId}/review/`, {\n            method: 'POST',\n            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },\n            body,\n        });",
                "const response = await api.applications.review(applicationId, action, { headers: { 'Content-Type': 'application/x-www-form-urlencoded' } });",
            ),
            (
                "const response = await fetch(`/rooms/${encodeURIComponent(roomName)}/applications/`);",
                "const response = await api.applications.list(roomName);",
            ),
            (
                "const response = await fetch('/rooms/applications/');",
                "const response = await api.applications.pending();",
            ),
        ])
    elif path.name == "overview.js":
        replacements.extend([
            (
                "const delRes = await fetch(`/rooms/${encodeURIComponent(roomName)}/delete/`, {\n            method: 'POST',\n            headers: {\n                'X-CSRFToken': csrfToken,\n            },\n        });",
                "const delRes = await api.rooms.delete(roomName, { headers: { 'X-CSRFToken': csrfToken } });",
            ),
            (
                "const leaveRes = await fetch(`/rooms/${encodeURIComponent(roomName)}/leave/`, {\n            method: 'POST',\n            headers: {\n                'X-CSRFToken': csrfToken,\n            },\n        });",
                "const leaveRes = await api.rooms.leave(roomName, { headers: { 'X-CSRFToken': csrfToken } });",
            ),
            (
                "const response = await fetch(`/rooms/${encodeURIComponent(oldName)}/edit/`, {\n            method: 'POST',\n            headers: {\n                'Content-Type': 'application/json',\n                'X-CSRFToken': csrfToken,\n            },\n            body: JSON.stringify({ name: newName.trim() })\n        });",
                "const response = await api.rooms.update(oldName, { name: newName.trim() }, { headers: { 'X-CSRFToken': csrfToken } });",
            ),
            (
                "const res = await fetch(`/rooms/${encodeURIComponent(state.currentRoom)}/kick/`, {\n            method: 'POST',\n            headers: {\n                'Content-Type': 'application/json',\n                'X-CSRFToken': csrfToken,\n            },\n            body: JSON.stringify({ username: member.username })\n        });",
                "const res = await api.rooms.kick(state.currentRoom, member.username, { headers: { 'X-CSRFToken': csrfToken } });",
            ),
            (
                "const res = await fetch(`/rooms/${encodeURIComponent(targetRoom)}/`);",
                "const res = await api.rooms.get(targetRoom);",
            ),
        ])
    elif path.name == "room.js":
        replacements.extend([
            (
                "const response = await fetch('/rooms/create/', {\n            method: 'POST',\n            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },\n            body: formData\n        });",
                "const response = await api.rooms.create(formData);",
            ),
        ])
    elif path.name == "rooms.js":
        replacements.extend([
            (
                "const response = await fetch('/rooms/join/', {\n            method: 'POST',\n            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },\n            body: formData,\n        });",
                "const response = await api.rooms.join(formData);",
            ),
            (
                "fetch('/rooms/')",
                "api.rooms.list()",
            ),
        ])
    elif path.name == "search.js":
        replacements.extend([
            (
                "const response = await fetch(`/rooms/search/?q=${encodeURIComponent(query)}`);",
                "const response = await api.rooms.search(query);",
            ),
        ])
    elif path.name == "settings.js":
        replacements.extend([
            (
                "const response = await fetch('/settings/edit/', {\n                method: 'POST',\n                headers: {\n                    'X-CSRFToken': csrfToken\n                },\n                body: formData\n            });",
                "const response = await api.settings.edit(formData, { headers: { 'X-CSRFToken': csrfToken } });",
            ),
        ])

    for old, new in replacements:
        if old in text:
            text = text.replace(old, new)

    if replacements:
        text = ensure_api_import(text)

    if text != original:
        path.write_text(text, encoding="utf-8")
        return True
    return False


def main() -> None:
    changed = []
    for path in sorted(JS_DIR.glob("*.js")):
        if replace_in_file(path):
            changed.append(path.name)

    print(f"Updated {len(changed)} file(s): {', '.join(changed) if changed else 'none'}")


if __name__ == "__main__":
    main()
