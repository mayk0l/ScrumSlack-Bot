---
name: atomic-commits
description: Use when preparing, structuring, or writing git commits. Enforces atomic commits with conventional messages, tests, and documentation updates.
---

# Atomic Commits

## Principle

One commit = one logical change that compiles and passes its own tests.

## Commit Message Format

```
<type>(<scope>): <short description>

<body: why and what>

<references>
```

## Types

| Type | Use |
|------|-----|
| `feat` | New feature |
| `fix` | Bug fix |
| `docs` | Documentation only |
| `test` | Adding or updating tests |
| `refactor` | Code restructuring, no behavior change |
| `chore` | Maintenance, deps, config |
| `style` | Formatting only |

## Examples

```
feat(domain): add StandupResponse and SessionStatus enums

fix(github): handle 429 rate limit with exponential backoff

docs(kanban): mark 0.1 scaffolding as done

test(standup): reject duplicate daily responses
```

## Rules

- Do not mix unrelated changes in one commit.
- Do not mix refactor with feature implementation.
- Each commit must have passing tests for the changed code.
- Update docs in the same commit if the change affects architecture, setup, or public behavior.
- Commit messages in English, imperative present tense.

## Pre-commit Checklist

- [ ] Code passes existing and new tests.
- [ ] Documentation updated if needed.
- [ ] `docs/02-kanban.md` reflects the new status.
- [ ] Commit is atomic.
- [ ] Message follows conventional format.
