# Contributing to the project
**This guide explains the rules / recommendations for contributing to this project**

## Required
### Conventional commits (v2, at all times):
Use conventional commits **at all times** unless absolutely cannot (even then, rename those later).
**Conventional commiting style:**
type(scope1, scope2, ..., scopeN): description1; description2; ...; descriptionN.
(optional body, markdown allowed).
(optional footer(s) / tags)
**Where:**
- type:
- - feat: new feature available to the users,
- - fix: bug fix,
- - refactor: code change that neither adds a feature nor a decorative one,
- - style: code change that is purely decorative,
- - test: implementing / fixing a test,
- - perf: code change that affects performance,
- - chore: updating internal tool dependencies (say, docker) or overall project maintenance,
- - docs: writing / changing project documentation,
- - ci: Changes to CI / CD pipeline(s),
- - revert: reverting a code change,
- - merge: merging one branch into another.
- scope: the component, subsystem, feature, or area affected by the change. It may correspond to a directory, file, module, or conceptual part of the project.
- description: what was changed, shortly.
- body: optional body to better describe the changes / leave notes or TODOs.
- footer(s) / tags: optional tags (#tag) that can classify a commit.

### Conventional branches
Use conventional branches, again, **at all times**.
**Conventional branching style:**
type/scope/(etc.), where:
- type: same as in conventional commits.
- scope: same as in conventional commits.
- etc.: optional, other details to denote.

### Tests
To all medium and major changes, **tests are required to be written and ran** before making a PR (pull request).

## Recommended
### PEP 8 style
Not necessary, but heavily recommended.
Other styles that are consistent with the project structure are accepted as well.