# CLAUDE.md

Instructions for the AI coding assistant working in this repository.
The human owner reads this file too. Keep it short and keep it true.

## What this project is

A backend service for dealership managers: see vehicles in stock, spot the ones that
have been in stock too long, and record what to do about them. Built for the Keyloop
technical assessment, Scenario B.

**`docs/SPEC.md` is the single source of truth for behaviour.** Read it before any task.
If the code and the spec disagree, the spec wins. If the spec seems wrong or unclear,
stop and ask. Do not change behaviour the spec does not describe.

## Stack

- Python 3.12+, FastAPI, SQLAlchemy 2.x, Pydantic 2.x, SQLite, pytest, ruff
- Use current APIs only. In particular:
  - FastAPI: use `lifespan`, not `@app.on_event`
  - SQLAlchemy: 2.0 style (`select()`, `Mapped[...]`, `mapped_column`), not the legacy `Query` API
  - Pydantic: v2 (`model_config`, `field_validator`), not v1 (`class Config`, `@validator`)
- Dev machine is Windows. Commands in docs must also work on macOS and Linux.

## Layout

```
app/            FastAPI service
  services/     business rules, no FastAPI or database imports (aging.py lives here)
  api/          HTTP routes
scripts/        data loading and generation
tests/          unit/ and api/ tests
docs/           SPEC, system design, ADRs, API contract, AI collaboration log
bi/             Power BI project (.pbip)
```

## How to work

1. **Start from the issue.** Each task is a GitHub issue with acceptance criteria.
   Do only what the issue asks.
2. **Write tests with the code, not after it.** Every test name includes the ID of the
   acceptance criterion it proves, for example `test_ac_2_2_day_91_is_aging`.
3. **Cover the edges.** For every rule, test the happy path, invalid input, the boundary
   values, and what happens when data is missing.
4. **Dates:** count in UTC. "Today" is always passed in as a reference date; never call
   `date.today()` or `datetime.now()` inside business logic.
5. **Run the checks before every commit:** `ruff check .` and `pytest`. Both must pass.
6. **Commit and push** straight to `main` when checks pass. Use a short conventional
   message (`feat:`, `fix:`, `test:`, `docs:`, `chore:`), add `Closes #N` for the issue,
   and end with the `Co-Authored-By` line for the AI.

## When you finish a task, report

- What you built, and which acceptance criteria it covers
- **Every assumption or default you chose that the issue did not ask for**
  (for example error handling, limits, time zones, validation)
- Any security risk you can see
- Anything you are unsure about, and how sure you are

## Answering review questions

The owner reviews by asking questions, not by reading every line. So every answer must
come with evidence the owner can check:

- test output, or
- a command the owner can run, or
- the exact file and line.

Do not answer "yes, it works" without evidence. If you do not know, say so.

## Be a critical partner, not an agreeable one

- If a request conflicts with the spec, a test, or good practice, say so before doing it.
- Do not invent behaviour for cases the spec does not cover. Ask.
- Say how confident you are. "I think" and "I have verified" are different things.

## Writing style

Plain English in everything: code comments, docstrings, error messages, API
descriptions, docs, issues and commit messages. Short sentences. Common words.
Explain a technical term the first time it appears.

## Keep the AI collaboration log honest

`docs/AI_COLLABORATION_LOG.md` records how the AI was used. When something worth noting
happens (the owner corrects you, you find a bug in your own output, a hidden assumption
comes to light), propose a short entry. Record only what actually happened.

## Never commit

- Secrets, `.env` files, local settings (`.claude/settings.local.json`)
- Generated files: virtual environments, caches, `*.db`, Power BI `cache.abf` and `localSettings.json`
- The original challenge brief, or any personal notes that are not part of the project
