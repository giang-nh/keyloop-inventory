# AI Collaboration Log

This log records how AI was used in this project, written as the work happens.
It is the source for the "AI Collaboration Narrative" in the README.

- **Project:** Keyloop Technical Assessment, Scenario B: Intelligent Inventory Dashboard
- **AI tool:** Claude Code (Claude Opus 5.5)
- **Framework:** Anthropic's AI Fluency 4D framework

The 4Ds, in short:

| D | Question it answers |
|---|---|
| **Delegation** | What should the AI do, and what should the human keep? |
| **Description** | How do I tell the AI clearly what I need? |
| **Discernment** | Is what the AI gave me actually good? |
| **Diligence** | Have I verified, disclosed and taken ownership of the result? |

Each entry is tagged with the D it relates to.

---

## Entry 1 · [Delegation] Scenario, layer and stack

**Decisions (human):**

- **Scenario B.** I chose to go deep rather than wide: a small scope built to production
  quality: tested, observable and documented.
- **Backend only.** A REST API with a real database. The client side is mocked with an
  OpenAPI contract and cURL examples, as the challenge allows.
- **Stack:** Python, FastAPI, SQLite and pytest. FastAPI generates the OpenAPI contract
  for free. SQLite keeps setup to zero, with a clear path to PostgreSQL.
- **Not Power BI.** I considered a BI dashboard for the visual layer. I rejected it as the
  main deliverable: it has no standard build or test story and cannot write data back.
  An Excel-friendly export stays as a possible future extension.

**AI's part:** compared the four scenarios and listed trade-offs for each. It recommended a
different scenario (D). I chose B for the reasons above.

---

## Entry 2 · [Delegation] Human–AI delegation plan (issue #2)

**Principle:** Execution can be delegated. Responsibility cannot. The human owns every
decision and signs off every result.

| Kind of work | Owner | What the AI does | What the human does | Why |
|---|---|---|---|---|
| **Understanding the user** | Human | Suggests possible unsaid needs | Writes the user voice; keeps or rejects each idea | There are no real users to interview. Judging what a dealership manager needs takes human context. |
| **Deciding what to build** | Human | Lists options and trade-offs | Sets scope, makes assumptions, decides what is out of scope | Trade-offs depend on goals the AI cannot see. |
| **Architecture** | Human decides, AI advises | Proposes options and evaluates each one (pros, cons, risks) | Chooses, and signs off each ADR | The AI knows many patterns but not our constraints. The final call stays with the human. |
| **Implementation** | AI (most delegated) | Writes code and tests together, runs them, fixes its own failures, commits and pushes when tests pass | Reviews at checkpoints | This is where the AI is strongest, but only after the acceptance criteria exist. |
| **Judging quality** | Human + AI | Answers the human's review questions and backs each answer with evidence: test output, a command the human can run, or the exact file and line | Asks targeted questions using five review lenses; checks the evidence; spot-checks the riskiest parts; makes the final call | The human judges by questioning, like an engineering manager, instead of reading every line. |
| **Shipping** | Human | Drafts build and run steps | Writes the narrative, records the video, submits | The candidate is accountable for what is sent. |

**Rules for judging quality** (because AI tends to agree too easily and to sound more
certain than it is):

1. No answer is accepted without evidence.
2. The human spot-checks the riskiest parts in person: the 90/91-day aging boundary and the
   append-only action history.
3. Every checkpoint uses a fixed set of questions, including *"What would break this?"* and
   *"What did you assume that I didn't ask for?"*

**Push rights:** the AI commits and pushes straight to `main` when all tests pass. CI runs
on every push. Human review happens at the checkpoints (#11 and #20), not on every commit.

**How this plan was made:** the AI drafted the table. I changed two rows:

- *Judging quality*: from "Human" to "Human + AI". I will confirm quality by questioning
  the AI and checking its evidence, not by reading all the code.
- *Architecture*: from "Human + AI" to "Human decides, AI advises". The AI gives options
  and evaluates them; I make the decision.

---

## Entry 3 · [Delegation] 3-year dataset and a Power BI demo view

**Change of plan:** Entry 1 kept Power BI out of the deliverable. I brought it back, but only
as a **demo view** on top of the backend. The graded layer is still the backend.

**Decisions (human):**

- **Data:** generate three years of realistic data: arrivals, sales and action histories
  across several dealerships. A single snapshot cannot show trends; three years can.
- **How Power BI gets data:** through CSV export endpoints on the API. The aging rule stays
  in one place (the backend), so the dashboard and the API cannot disagree.
- **File format:** Power BI Project (`.pbip`), not a binary `.pbix`. The model and DAX
  measures are text files, so they can be reviewed in Git like code.

**AI's part:** listed and evaluated the options for each decision: CSV export vs. direct
database connection vs. calling the JSON API; full history vs. current stock only;
`.pbip` vs. `.pbix` vs. screenshots only. I chose from those options.

**Knock-on effect:** sold vehicles are now in scope. The data model needs a vehicle status
and a sold date, and aging applies only to vehicles still in stock (noted on issue #5).
New issues: #25 (dataset), #26 (CSV exports), #27 (dashboard), #28 (screenshots).

---

## Entry 4 · [Delegation] User voice (issue #3)

**What happened:** the AI drafted the stated need and suggested eight possible unsaid
needs, each with a reason. I decided which ones to keep.

- **Kept (3):** money tied up in aging stock, an early warning before day 90, and a
  filter for the manager's own dealership.
- **Moved out of the user voice (5):** oldest first, latest action in the list, whether
  actions lead to a sale, missing-date handling, and fast lists. These are real, but they
  are design or quality decisions, not things a manager would ask for. They stay in the
  product and move to the assumptions section and the system design.

**Why it matters:** the AI's list mixed user needs with engineering choices. Separating
them keeps the user voice honest and keeps each decision in the right place.

**Open question raised:** what counts as "close to 90 days" for the early warning. To be
decided in issue #5.

---

## Entry 5 · [Description] Requirements, acceptance criteria and scope (issues #4, #5)

**First draft (AI):** requirements and acceptance criteria as bare tables and bullets.

**My feedback:** the draft said *what* but not *why*. A reader could not follow the line
from the user's problem to each requirement, or understand why things were left out.
I asked for the spec to be rewritten as the story of how a person would think it through.

**Second draft (AI):** `docs/SPEC.md` now follows the manager's own sequence: see the
stock, find the problem cars, decide what to do, then look at the bigger picture. Each
step explains its reasons before its acceptance criteria. Assumptions are written as
*what was unclear, what we chose, why*. Every out-of-scope item has a reason.

**Decisions (human):**

- Early warning window: 76 to 90 days (accepted as proposed).
- Action types: the six proposed types (accepted as proposed).
- **Changed:** actions are allowed for `approaching` cars, not only `aging` ones. The AI
  had proposed aging only, following the brief literally. I changed it because the point
  of an early warning is to act before day 90; blocking actions there would defeat it.

**Also added by the AI and accepted:** decision D-1, reading "real-time" as *correct at
the moment you ask*, which the first draft had not addressed.

---

## Entry 6 · [Description] CLAUDE.md, and why this stack (issue #6)

**CLAUDE.md (AI draft, human approved as written).** It gives the AI the same context in
every session. Besides the usual project facts, it encodes the rules from Entry 2 and
guards against known AI habits:

- Names the outdated APIs the AI must not use (FastAPI `on_event`, the legacy SQLAlchemy
  `Query` API, Pydantic v1), because AI tools often use them with confidence.
- After each task, the AI must list every assumption it made that the issue did not ask for.
- Review answers must come with evidence: test output, a command, or a file and line.
- The AI must push back when a request conflicts with the spec, and say how sure it is.

**Why this stack.** While reviewing the draft I asked the AI why it recommended Python and
FastAPI. Its answer leaned on my personal comfort with Python. I corrected the reasoning:
my strongest background is Java enterprise. The stack should be chosen for the product and
the team, not for me. So the decision rests on two stated assumptions:

1. This is a new service, with no existing codebase to fit into.
2. The team that will build and run it is strongest in Python.

Given those, Python and FastAPI fit best: quick to build, the API contract is generated
automatically, and testing is simple. Java with Spring Boot was considered and not chosen,
because it does not match the assumed team and needs more setup for a small new service.
This reasoning goes into ADR 0001 (issue #9).

---

## Entry 7 · [Diligence] Project setup and a deprecation caught early (issues #7, #8)

The AI added the issue templates, the project skeleton and CI. One thing worth noting:

- **What happened:** the first test run passed, but with a warning. The test client
  library the AI chose (`httpx`) is now deprecated for this use; the web framework asks
  for `httpx2` instead. This is a classic AI mistake: using a library version that was
  common in its training data but is now outdated.
- **How it was caught:** the AI read the warning instead of ignoring a passing run, and
  checked that `httpx2` really exists on the package index before switching.
- **What we changed so it cannot slip through again:** pytest now treats every warning as
  an error. Any deprecated API will now fail the build instead of printing a line that is
  easy to miss.

---

## Entry 8 · [Delegation] System design and ADRs (issue #9)

**How the design was made:** the AI listed options and weighed them; I chose.

- **Four real trade-offs were put to me as options:** where aging is worked out, how the
  latest action is found, which observability tools to use, and how the database structure
  is managed. I chose Prometheus plus request IDs, and Alembic migrations, straight away.
- **For the other two I asked for a plainer explanation first.** The first version was
  written in database terms. The second used concrete examples (a car that arrived on
  1 July; a car with three actions). With those, I chose: work aging out when asked, and
  read the latest action from the history. Both keep each fact in one place.
- **I also asked for the key decisions section to be rewritten.** The first version was a
  one-line table. The final version gives each decision its question, an example, the
  options with pros and cons, and what the choice costs.

**What the AI added without being asked, and reported (per CLAUDE.md):** eight smaller
choices, including no separate status column, a dealership list endpoint, one error
shape, protection against CSV formula injection, and keeping free-text notes out of logs.
I asked for each to be explained with an example, then accepted all eight.

**Discernment note:** the CSV formula-injection risk was found by the AI while designing the
export for Power BI and Excel. It was not in the spec. It shows why "what did you assume
that I didn't ask for?" is worth asking every time.

---

## Entry 9 · [Diligence] Writing how GenAI was used in design (issue #10)

The AI drafted section 9 of the system design from Entries 1 to 8. I approved it as
written.

**One correction made by the AI before I saw it:** the first draft included a lesson,
*"once the spec existed, the AI stopped guessing and started asking"*. Nothing in this log
supports that claim, so the AI replaced it with one that is supported: standing rules in
`CLAUDE.md` made it report its own choices without being asked (Entry 8). Every claim in
section 9 now points back to an entry in this log.

---

## Entry 10 · [Discernment] Design review checkpoint (issue #11)

**How the review ran:** I asked questions; the AI answered with evidence (file and line) and
proposed fixes. Before the review, the AI read its own documents looking for weak spots, so
the suggested questions pointed at real problems rather than easy wins.

**"What would break this design?"** surfaced five problems that were not handled:

1. Paging could repeat or skip cars, because cars with the same days in stock had no fixed
   order. *Fix (AI): order ties by ID.*
2. Cars with no stock-in date had no defined place in the list, and SQLite and PostgreSQL
   put them in opposite places by default. Moving database would have changed the list
   silently. *My decision: always put them first, so the missing data gets fixed.*
3. Counting "today" in UTC shifts a status change by up to 7 hours for a dealership in
   Vietnam. *My decision: keep UTC and document the limit.*
4. A unique VIN would reject a car that comes back as a trade-in. *My decision: drop the
   uniqueness; each stay in stock is its own record. The cost is documented.*
5. The case-insensitive filter could not use a normal index. *Fix (AI): case-insensitive
   index.*

**"What did you assume that I didn't ask for?"** surfaced thirteen more choices. The most
serious was a security one: the service trusted any request ID sent by a caller and wrote it
into the logs, so a caller could forge log lines. *Fix (AI): accept only short, safe IDs.*
I also decided: make and model filters stay exact matches; the summary also shows the value
of `approaching` stock; open monitoring and exports go into the known limits.

**Result:** 10 changes to the spec, the design and three implementation issues (#13, #15,
#16), before any code was written. Every one of them would have been more expensive to find
after the code existed.

---

## Entry 11 · [Discernment] Database schema and seed data (issue #15)

From here, the owner asked the AI to work through all implementation issues on its own
and report back.

**The generated migration was wrong in two ways.** The AI used Alembic's autogenerate to
draft the first migration, then read it before using it:

1. The case-insensitive index on make and model was **missing**. Autogenerate skips
   indexes built on expressions such as `lower(make)`, without an error.
2. The check on `action_type` was **created twice** with the same name. SQLite accepts
   that; PostgreSQL would reject it, and we only would have found out on the move.

The migration was rewritten by hand, and a test now checks that the migrations create
every table and index the models describe.

**A conflict between the issue and the design.** Issue #15 asked for a vehicle "status"
column. The approved design (SYSTEM_DESIGN 5.6) says there is none: a car is in stock
while its sold date is empty. The AI followed the design, as the later decision.

**Choices the issue did not ask for, reported per CLAUDE.md:**
- Price is a whole number, not a decimal. SQLite has no exact decimal type, and car
  prices do not need cents. The design document was updated.
- The case-insensitive index uses `lower()` in both databases instead of a SQLite-only
  setting, so there is one approach to maintain.
- Two database checks were added: price is not negative, and a car is not sold before it
  arrived.
- The seed does nothing if it has already run, instead of trying to match rows one by one.

**Caught by the warnings-as-errors rule (Entry 7):** a test left a database connection
open. Python reported it as a warning, which failed the build, so it was fixed at once.

---

## Entry 12 · [Discernment] Aging rule, vehicle list and actions (issues #12, #13, #14)

**A bug the tests caught at once.** The AI wrote the shared error handler with the
arguments of `JSONResponse` in the wrong order (status code first, content second). The
first test that hit an error failed with a type error. Fixed before commit.

**A test that passed for the wrong reason.** All the new tests passed on the first run.
Passing on the first run is not proof that the tests are good, so the AI broke three key
rules on purpose to see whether the tests would notice (a "mutation check"):

| Rule broken on purpose | Caught? |
|---|---|
| Day 90 counted as aging (`>=` instead of `>`) | Yes |
| Actions blocked for `approaching` cars | Yes |
| The ID tie-break removed from the list order | **No** |

The third one slipped through because SQLite happens to return rows with the same sort
value in ID order. The paging test passed by luck, not because the rule was there.
PostgreSQL makes no such promise, so after the move in ADR 0002, pages could repeat or
skip cars and no test would fail. The AI added a test that checks the ordering rule
itself, then broke the rule again to confirm the new test fails.

**Other checks worth noting:**
- The filter and the status label are compared on every day from 0 to 399, so they cannot
  drift apart at a boundary (ADR 0003).
- A client that tries to send its own `created_at` gets a 422, so actions cannot be
  backdated (SPEC D-12).

**Choices the issues did not ask for, reported per CLAUDE.md:**
- The summary endpoint (AC-2.8) had no issue of its own; it was built with #13.
- Refusing an action gives one of three codes: `vehicle_sold`,
  `vehicle_stock_in_date_unknown` or `vehicle_not_eligible`, each with its own message.
- The summary returns 404 for an unknown dealership; the list returns an empty page.
- If a vehicle with a future stock-in date ever reaches the database (the loader stops
  this), the list shows it as `unknown` and logs a warning, instead of failing for
  everyone.
- A blank manager name (only spaces) is rejected.

---

## Entry 13 · [Discernment] Observability, exports, contract, traceability and data (issues #16, #26, #17, #18, #25)

**The API contract described errors the API never sends.** FastAPI adds its own
description of a 422 error (`{"detail": [...]}`) to the contract automatically. Our API
actually answers with `{"error": {...}}`. A client built from the contract would have read
errors wrongly. The contract now documents the real shape, and two tests guard it: one
fails if the committed contract drifts from the code, the other checks real error bodies
against the documented shape.

**Every cURL example was run, not written from memory.** The examples in
`docs/api/curl-examples.md` were run against a live server with the seed data, and the
responses shown are the real ones. The same run confirmed in the server's own logs that
managers' names and notes never appear there.

**Checking the checks.** Mutation checks were extended: trusting any request ID, logging
the note, and removing the CSV formula protection each made a test fail. The traceability
test was checked the same way: an untested criterion added to the spec, and a test renamed
to a criterion that does not exist, both failed the build.

**The simulation document said something the data did not.** The first draft of
`docs/DATA_SIMULATION.md` claimed "about one car in seven" stays more than 90 days and
"most cars sell in four to eight weeks". Measured on the generated data, it is one in eight
(12.7%), and the middle half sell in three to nine weeks. The document now states the
measured numbers.

**A misleading speed test.** The first timing of the API on 10,000 generated cars showed
about 0.22 seconds for every endpoint, even the tiny summary. Equal times for very
different work was suspicious. The cause was the test, not the API: on Windows,
`localhost` tries IPv6 first and waits before falling back. Measured on `127.0.0.1`, the
list takes about 12 ms, the summary about 7 ms, and a full export of 10,000 cars about
130 ms. The server's own logs agree.

**Honesty note on the dataset.** The simulation *assumes* that price cuts and promotions
help cars sell. Any dashboard view that shows actions working is showing that assumption.
The document says so in a warning box at the top.

**Waiting for the owner:** the simulation rules (issue #25) need the owner's approval.

---

## Entry 14 · [Diligence] Running checks without GitHub-hosted CI (issue #8)

GitHub would not start the CI job on this account: *"recent account payments have failed
or your spending limit needs to be increased."* The AI laid out four options (a
self-hosted runner, a public repo, local checks, another CI service). **I chose local
checks**, and to say so openly rather than leave failed runs for a reviewer to find.

What was done:
- A pre-push Git hook in `.githooks/` runs `ruff check .` and `pytest` and stops the push
  if either fails. It lives in the repository, so any clone can turn it on with one
  command.
- The hook was tested both ways: with a failing test it stopped the push (exit code 1);
  on the clean tree it passed (496 tests).
- The GitHub Actions workflow is kept, but set to run only by hand, so each push no
  longer creates a failed run. The README explains why.

**Honest limit:** local checks are weaker evidence than CI on an independent machine.
Anyone can see the workflow and run the same commands, but nothing outside my machine has
run them for these commits.

---

## Entry 15 · [Diligence] Hidden-decisions audit (issue #19)

I asked the question from issue #19: *"What assumptions and trade-offs did you make, and
what security risks should I know about?"* The AI went back through all the code it had
written, instead of repeating what it had already reported, and checked its three most
serious suspicions by running them before answering.

**What it found (all confirmed by running, not just reading):**

1. `/health` said "ok" on a database with **no tables**, while every real request failed
   with an error. A load balancer would have kept sending traffic to a broken service.
2. Unexpected errors came back as **plain text**, not the error shape the design promises
   for every error, and without the request ID.
3. CSV exports had **no byte order mark**, so Excel on Windows would garble Vietnamese
   text in notes and names.

It also found, by reading: the default database path depended on the folder the service
was started from (the cause of problem 1 in practice); blank notes were saved as empty
text instead of "no note"; and dependency versions were not locked.

**My decisions:** fix six (health checks the schema version; one error shape for 500s;
database path fixed to the project folder; BOM in CSVs; blank notes saved as none; a lock
file), document three (unknown fields are rejected; no rate limit; SQLite write locking),
keep one (unmatched routes share one metric label).

**How the fixes were checked:**
- A test for each fix. Mutation check: removing the schema check from `/health` made two
  tests fail.
- The lock file was installed into a brand-new virtual environment and the full suite ran
  there: 506 passed.

**Worth noting:** all three confirmed problems passed every existing test. Tests only check
what someone thought to ask. The audit question found what nobody had asked.

---

## Entry 16 · [Description] Calibrating the simulated data with the Vietnamese market (issue #25)

**My request:** make the simulated data follow the real Vietnamese market, if public data
exists. **My decisions:** calibrate with public data, use VND, and include VinFast.

**What the AI found:** there is no public dataset of dealer stock in Vietnam (how long cars
stay, when they sell). Paid reports exist; used-car listings exist but are not dealer
stock and cannot be copied under their terms. What *is* public: 2025 sales by model, the
Tet slump (January 2025 down 40%), launch dates for two models, and list prices. The data
now uses those, and the document marks each rule as public data or assumption, with
sources.

**What the new tests caught in the AI's own change:**
- Prices came out as decimals (`181000000.0`): `round(x, -6)` on a decimal number gives
  back a decimal. SQLite stored it without complaint. The loader now rejects any price that
  is not a whole number, so this cannot reach the database again.
- One model's price was rounded above its highest list price (608 million against a list
  maximum of 607.9 million). Prices are now kept inside the list after rounding.

**Honest limits written into the document:**
- VinFast is 45% of the cars in the data but 29% of the real 2025 market, because only the
  top-selling models are in the catalog.
- Three price ranges were read from search-result summaries, not from the pages
  themselves; the document says which ones.
- Selling times and the effect of actions are still assumptions.

**A mix-up between two sessions.** While this work was in progress, a second session was
working on the hidden-decisions audit (#19) in the same folder. Its commit (1a423ce) picked
up five lines of this change (the "in VND" wording in the API descriptions, the CSV column
description and the design document). The AI noticed when those files no longer showed as
changed, checked the commit, and left the pushed history as it was. The rest of the change
is in the next commit. Lesson: two sessions should not share one working folder.

---

## Entry 17 · [Discernment] Simulation rules approved (issue #25)

I approved the simulation rules in `docs/DATA_SIMULATION.md` as written, including the
catalog, the Tet rule, the known VinFast skew and the assumed effect of actions.

---

## Entry 18 · [Discernment] Code review checkpoint (issue #20)

**How it ran:** before suggesting questions, the AI tried to break its own code, then
answered eleven review questions with evidence: a probe script against the real app, a
40-request concurrency test on a live server, grep results, and earlier mutation checks.

**What held up:** 40 simultaneous action requests on SQLite all succeeded (40 × 201, all
saved); no outdated APIs; logs never contain notes or names; every error has one shape and
a next step; the API answers the manager's four questions.

**What did not:** one edge case, a car whose stock-in date is in the future. The loader
stops such records, but the database cannot (the check depends on today's date). With one
in the database:

1. The list labelled it `unknown`, but the `unknown` filter did not find it: exactly the
   label/filter drift that ADR 0003 promised could not happen.
2. A `max_days` filter did find it, because its days in stock came out negative.
3. Refusing an action for it said *"has no stock-in date"*, which was not true.

The root cause was a choice the AI had made in #13 and reported, but that the spec never
covered: treating a future date as `unknown`.

**My decision:** widen `unknown` to mean *the date is missing or cannot be right* (SPEC D-6,
new AC-2.9), make the filters agree, and give the refusal its own true message. I also
asked for three code-level assumptions to be written into the spec (D-13 to D-15).

**Proof the new tests matter:** run against the old code, 4 of the 11 new tests failed; on
the new code all pass. One of them checks, through the API, that every label (including
bad and missing dates) is found by its own filter.

---

## Entry 19 · [Diligence] README and the AI Collaboration Narrative (issue #21)

The AI drafted the README, including this narrative, from the log. I approved it and chose
to keep the line about my Java enterprise background.

**Checked on a clean clone, not assumed.** The AI cloned the repository into a new folder,
made a new virtual environment and followed the README word for word: install, lint, tests,
migrations, the 3-year data, and starting the server. Two things came out of it:
- A bug: running the seed after the data generator said *"Seed data is already there"*,
  which was not true (both use a dealership with the same name). The seed now refuses any
  non-empty database with an honest message.
- Port 8000 was taken by another program on my machine. The README now shows how to use
  another port.

**Two lines removed before I saw the draft**, because they were not true yet: one said I had
already walked through every module (that is issue #22, not done), and one said a problem
was caught "on day one".

---

## Entry 20 · [Discernment] Power BI dashboard (issue #27)

I asked the AI to build the dashboard following a Power BI project I had made before.
Before building, it raised two conflicts:
- **The spec.** The "aging trend over time" chart would need each car's status on past
  dates. The exports do not carry that, so DAX (Power BI's formula language) would have to
  recalculate the aging rule. That breaks SPEC R4. I dropped the chart.
- **The issue.** Issue #27 still described the old one-page plan and the old data source.
  It was updated to my new choices (four pages, CSV files read from a folder) before any
  work started.

**Checked, not assumed.** The AI wrote the model and pages as text files, then opened them
in Power BI Desktop, refreshed, and compared the numbers with a separate calculation from
the CSVs (440 in stock, 45 aging, 10.2% aging share, 26.2bn VND in aging stock). All four
pages matched.

**Its own mistake:** it found two layout problems (a heading that scrolled, cards showing
"2K" instead of 2,074). When I asked it to fix them, its first guess at the card format
setting was wrong and changed nothing. It found the real setting by making the change once in Power BI and reading the
file Power BI saved, then checked the result on screen.
