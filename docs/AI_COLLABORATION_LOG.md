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

## Entry 1 · 2026-09-27 · [Delegation] Scenario, layer and stack

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

## Entry 2 · 2026-09-27 · [Delegation] Human–AI delegation plan (issue #2)

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

## Entry 3 · 2026-09-27 · [Delegation] 3-year dataset and a Power BI demo view

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

## Entry 4 · 2026-09-27 · [Delegation] User voice (issue #3)

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
