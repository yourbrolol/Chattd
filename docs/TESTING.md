# Testing

Tests live in `app/tests/`. Per `CONTRIBUTING.md`, medium and major changes
require tests to be written and run before a PR.

```bash
source .venv/bin/activate
pytest app/tests/ -v
pytest app/tests/test_rooms.py -v   # single module
```

Conventions:

- Name files `test_*.py`, one module per service/router area.
- Cover the `Router → Service → DB` path, plus WS edge cases:
  unauthenticated close, non-member close, malformed JSON, rate-limit frames.
- Use conventional commits (`test(scope): ...`) for test-only changes.

Docs check (add to CI alongside `pytest`):

```bash
pip install -r docs-requirements.txt
mkdocs build --strict
```
