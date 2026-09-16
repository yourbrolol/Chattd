# Contributing

This guide defines the rules and recommendations for contributing to this project.
The required sections are mandatory; the recommended ones are strongly encouraged.

## Required

### Conventional Commits (v2, at all times)

Use conventional commits **at all times**. If you cannot follow the style in the
moment, rename the commits afterwards so the history still complies.

Format:

```
type(scope1, scope2, ..., scopeN): description1; description2; ...; descriptionN.
(optional body, markdown allowed)
(optional footer(s) / tags)
```

Where:

- **type** — the kind of change, one of:
  - `feat`: new feature available to the users,
  - `fix`: bug fix,
  - `refactor`: code change that neither adds a feature nor a decorative one,
  - `style`: code change that is purely decorative,
  - `test`: implementing / fixing a test,
  - `perf`: code change that affects performance,
  - `chore`: updating internal tool dependencies (say, docker) or overall project maintenance,
  - `docs`: writing / changing project documentation,
  - `ci`: changes to CI / CD pipeline(s),
  - `revert`: reverting a code change,
  - `merge`: merging one branch into another.
- **scope** — the component, subsystem, feature, or area affected by the change.
  It may correspond to a directory, file, module, or conceptual part of the project.
- **description** — what was changed, shortly.
- **body** — optional body to better describe the changes, leave notes, or TODOs.
- **footer(s) / tags** — optional tags (`#tag`) that can classify a commit.

Example:

```
feat(chat, ws): add typing indicator; throttle presence updates.
```

### Conventional Branches (at all times)

Use conventional branches, again, **at all times**.

Format:

```
type/scope/(etc.)
```

Where:

- **type** — same set as in conventional commits.
- **scope** — same meaning as in conventional commits.
- **etc.** — optional extra details to denote.

Example: `feat/chat/typing-indicator`.

### Tests

For all medium and major changes, **tests must be written and run** before opening
a PR (pull request). See [Testing](TESTING.md) for how to run the suite.

## Recommended

### PEP 8 Style

Not mandatory, but heavily recommended. Other styles are accepted as long as they
stay consistent with the surrounding project structure.
