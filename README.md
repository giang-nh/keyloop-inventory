# Intelligent Inventory Dashboard

A backend service that helps dealership managers see their vehicle stock, find the cars
that have been in stock for more than 90 days, and record what they plan to do about them.

Built for the Keyloop technical assessment, Scenario B. Backend layer, with the client
mocked by an API contract.

> **The problem in one paragraph.** Every car that sits unsold costs a dealership money: it
> loses value, and the dealership pays interest on the loan used to buy it. A manager
> needs to see what is in stock, spot the cars that have stayed too long (or are about
> to), decide what to do about each one, and see whether things are getting better. This
> service answers those four questions. The full story is in [`docs/SPEC.md`](docs/SPEC.md).

**Video walkthrough:** *link added when recorded*

---

## Contents

1. [What is in this repository](#what-is-in-this-repository)
2. [Build, run and test](#build-run-and-test)
3. [Using the API](#using-the-api)
4. [AI Collaboration Narrative](#ai-collaboration-narrative)

---

## What is in this repository

| Where | What |
|---|---|
| [`docs/SPEC.md`](docs/SPEC.md) | What the service does and why: the user's problem, requirements, 30 acceptance criteria, and every decision made where the brief was unclear |
| [`docs/SYSTEM_DESIGN.md`](docs/SYSTEM_DESIGN.md) | The System Design Document: architecture, data model, data flows, key decisions, non-functional design, observability, security |
| [`docs/adr/`](docs/adr/) | Architecture Decision Records: short notes on why each big choice was made |
| [`docs/api/`](docs/api/) | The API contract ([`openapi.json`](docs/api/openapi.json)) and [cURL examples](docs/api/curl-examples.md) run against a live server |
| [`docs/DATA_SIMULATION.md`](docs/DATA_SIMULATION.md) | How the three years of sample data are built, what is real market data and what is assumed |
| [`docs/AI_COLLABORATION_LOG.md`](docs/AI_COLLABORATION_LOG.md) | How AI was used, written as the work happened |
| `app/` | The service. The aging rule is in [`app/services/aging.py`](app/services/aging.py) |
| `tests/` | 518 automated tests. Every acceptance criterion has at least one |
| `scripts/` | Load the seed data, generate three years of data, export the API contract |
| `bi/` | Power BI dashboard (demo view on top of the CSV exports) |
| [`CLAUDE.md`](CLAUDE.md) | The standing instructions given to the AI coding assistant |

---

## Build, run and test

You need **Python 3.12 or newer** and **Git**. Nothing else: the database is a single
SQLite file.

### 1. Install

```bash
git clone https://github.com/giang-nh/keyloop-inventory.git
cd keyloop-inventory
python -m venv .venv
```

Activate the virtual environment:

```bash
# macOS / Linux
source .venv/bin/activate
```

```powershell
# Windows (PowerShell)
.venv\Scripts\Activate.ps1
```

Then install:

```bash
pip install -e ".[dev]"
```

For the exact versions the tests passed with, use
`pip install -r requirements.lock && pip install -e . --no-deps` instead.

### 2. Test

```bash
ruff check .
pytest
```

Expected: `All checks passed!` and every test passing (518 at the time of writing). Warnings
are treated as errors, so an
outdated library call fails the run.

### 3. Create the database and load data

```bash
alembic upgrade head
```

Then load **one** of these:

```bash
python scripts/seed.py            # 13 hand-made vehicles with every edge case
python scripts/generate_data.py   # 3 years of simulated data, about 10,000 vehicles
```

The database is `inventory.db` in the project folder. Set `DATABASE_URL` to use another
one, for example PostgreSQL.

### 4. Run

```bash
uvicorn app.main:app
```

- Interactive API documentation: <http://127.0.0.1:8000/docs>
- Health check: <http://127.0.0.1:8000/health>
- Metrics: <http://127.0.0.1:8000/metrics>

If port 8000 is already in use, pick another: `uvicorn app.main:app --port 8010`.
On Windows, use `127.0.0.1` rather than `localhost`: `localhost` tries IPv6 first and adds
about 0.2 seconds to every request.

### Checks before every push

Lint and the full test suite run automatically before every `git push`, through a Git
hook stored in the repository. Turn it on once per clone:

```bash
git config core.hooksPath .githooks
```

A GitHub Actions workflow with the same checks is in `.github/workflows/ci.yml`.
GitHub-hosted runners were not available on this account, so it is set to run only when
started by hand, and the checks run locally through the hook instead.

---

## Using the API

| Question the manager asks | Endpoint |
|---|---|
| What do I have in stock? | `GET /api/v1/vehicles` with filters for dealership, make, model, days in stock and status |
| Which cars are a problem? | `GET /api/v1/vehicles?status=aging` and `GET /api/v1/inventory/summary` |
| What am I going to do about it? | `POST /api/v1/vehicles/{id}/actions`, and the history at `GET /api/v1/vehicles/{id}/actions` |
| Is it getting better or worse? | `GET /api/v1/exports/vehicles.csv` and `actions.csv`, read by Power BI or Excel |

Stock status: `fresh` (0–75 days), `approaching` (76–90), `aging` (more than 90), `unknown`
(stock-in date missing or impossible). Day 90 is not aging; day 91 is.

Ten worked examples with real responses: [`docs/api/curl-examples.md`](docs/api/curl-examples.md).

---

## AI Collaboration Narrative

I built this with Claude Code (Claude Opus 5.5) as my collaborator, and structured the work
with Anthropic's **AI Fluency 4D framework**: Delegation, Description, Discernment and
Diligence. My rule throughout: **the AI can do the work, but I own the decisions.**

Every example below is recorded in the
[AI Collaboration Log](docs/AI_COLLABORATION_LOG.md), written as the work happened.

### Delegation: deciding who does what

Before any code, I wrote down who owns each kind of work (Entry 2). The AI wrote most of
the code and tests. I kept understanding the user, deciding scope, every design choice and
the final judgment. I changed two rows of the AI's draft plan: I judge quality by *asking
questions and checking evidence* rather than reading every line, and for architecture *the
AI proposes and weighs options, and I decide*.

In practice, that meant overruling the AI where it mattered:

- It recommended a different, more impressive scenario. I chose this one, to go deep rather
  than wide (Entry 1).
- It justified Python by my own familiarity with it. My strongest background is Java
  enterprise. I made the stack decision rest on the product and the team instead, and
  wrote those as stated assumptions (Entry 6, ADR 0001).
- It proposed allowing actions only on cars over 90 days, as the brief literally says. I
  allowed cars *approaching* 90 days too, because the point of an early warning is to act
  before the deadline. **The AI followed the words; I followed the purpose** (Entry 5).

### Description: making intent explicit

The work runs along one chain: the manager's problem → requirements → 30 acceptance
criteria, each with an ID → tests named after those IDs. A test fails the build if any
criterion has no test (Entry 13).

- **The spec is written as a story.** The AI's first draft was tables and bullets: it said
  *what* but not *why*. I asked for it to follow the manager's own questions, so a reader
  can trace every requirement back to the user (Entry 5).
- **User needs stayed separate from engineering choices.** The AI suggested eight "unsaid"
  user needs; five were really design decisions, such as "keep lists fast". I kept three
  (Entry 4).
- **[`CLAUDE.md`](CLAUDE.md) holds the standing instructions**: the spec is the source of
  truth; named outdated APIs are banned; after every task, list every assumption nobody
  asked for; answer review questions with evidence; push back instead of agreeing.

### Discernment: telling "it runs" from "it is right"

I did not read every line. I asked questions, and required evidence for each answer: test
output, a command I could run, or a file and line. The two questions I asked at every
checkpoint: *"What would break this?"* and *"What did you assume that I didn't ask for?"*

- **The design review found 5 problems and 13 hidden assumptions before any code existed**
  (Entry 10). For example: pages could repeat or skip cars; SQLite and PostgreSQL sort
  missing dates to opposite ends, so moving database would have silently changed the list;
  a caller could forge log lines through the request ID.
- **Passing tests were not taken as proof.** The AI broke key rules on purpose to see if the
  tests noticed. One test was passing by luck: SQLite happened to return rows in the right
  order, and PostgreSQL would not (Entry 12).
- **Generated output was read, not trusted.** The auto-generated database migration was
  missing an index and duplicated a constraint (Entry 11). The generated API contract
  described an error format the API never sends (Entry 13).
- **Numbers were measured, not assumed.** A first timing showed every endpoint at 0.22 s.
  Equal times for very different work was suspicious; the cause was Windows' `localhost`
  lookup, not the API. Real figures: about 12 ms for a list of 10,000 cars (Entry 13).
- **The code review found one edge case in three places** (Entry 18). A car with a future
  stock-in date was labelled `unknown` but missed by the `unknown` filter. The AI had made
  that choice earlier and reported it; the review turned it into a decided rule.

### Diligence: owning the result

- **Systems that catch what I miss.** Warnings are errors, so a deprecated library was
  caught during setup (Entry 7). The data loader rejects bad records. A pre-push hook runs
  lint and all tests.
- **Honest about limits.** GitHub-hosted CI was unavailable on this account; the README
  says so instead of leaving failed runs to be found (Entry 14). The sample data uses
  public Vietnamese market figures with sources, and labels what is assumed: the dashboard
  showing that price cuts help is *our assumption*, not a finding (Entry 16).
- **The record is honest too.** The AI removed a claim from the design document that the
  log could not support (Entry 9). When two AI sessions in the same folder mixed their
  commits, it was recorded rather than rewritten (Entry 16).
- **Understanding is a separate step.** AI writes code faster than a person can read it, so
  walking through every module until I can explain it is its own task (issue #22), done
  before recording the video. **A decision I cannot explain is not a decision I own.**

### What I learned

- **The AI is fast at options and slow at purpose.** It lays out trade-offs well but reads
  requirements literally. The judgment about what the user needs stayed with me.
- **Standing rules beat one-off questions.** Because `CLAUDE.md` requires the AI to report
  every choice nobody asked for, the most useful findings (the CSV formula-injection risk,
  the future-date edge case) came to me without my having to remember to ask.
- **A reported assumption is not a decided one.** The review's job was to turn the AI's
  reported choices into rules I had actually decided.
