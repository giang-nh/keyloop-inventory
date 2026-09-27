# Specification: Intelligent Inventory Dashboard

This document says what the service must do and how we will know it works.
It is the single source of truth for behaviour. Code and tests follow it.

It follows one chain: **user voice → requirements → acceptance criteria → tests**.
Every acceptance criterion has an ID, and every test names the ID it proves.

| Section | Contents | Status |
|---|---|---|
| 1. User voice | The problem, from the manager's point of view | Done (#3) |
| 2. Product requirements | What the service lets a manager do | To do (#4) |
| 3. Acceptance criteria | Checkable statements, each with an ID | To do (#4) |
| 4. Assumptions and open questions | Decisions made where the brief is unclear | To do (#5) |
| 5. Out of scope | What we deliberately do not build | To do (#5) |

---

## 1. User voice

The user is a **dealership manager** who is responsible for the vehicles in stock.

There are no real users to interview for this assessment. So this section keeps two
things apart: what the challenge states, and what we assume.

### 1.1 Stated need

Dealership managers need a clear, up-to-date view of the vehicles in their stock.
They want to find vehicles that have been in stock for more than 90 days, and record
what they plan to do about each one, for example a price reduction.

### 1.2 What goes unsaid (assumed)

These are needs the challenge does not state, but a manager very likely has.
Each one is an assumption and leads to at least one requirement in section 2.

| ID | Assumed need | Why we think it is real | Leads to |
|---|---|---|---|
| U1 | *"How much money is tied up in aging stock?"* | A car that sits in stock loses value, and the dealership usually pays interest on the loan used to buy it. The number of aging cars alone does not show the size of the problem. | Total value of aging stock |
| U2 | *"Which cars are about to become aging?"* | Acting before day 90 is cheaper than acting after it. | An early-warning group of vehicles that are close to 90 days |
| U3 | *"Show me my dealership."* | A manager is usually responsible for one site, not the whole group. | Filter by dealership |

U1 and U2 go slightly beyond the brief, which only asks for the over-90-day view.
They are kept small so they add value without changing the core scope.

### 1.3 Considered, but not treated as user needs

We also considered the items below. They are real, but they are design or quality
decisions rather than things a manager would ask for. They stay in the product and are
covered in section 4 (assumptions) and in the system design.

| Item | Where it is handled |
|---|---|
| List the oldest vehicles first by default | Design decision (section 4) |
| Show the latest action next to each vehicle | Design decision (section 4) |
| Show whether actions lead to a sale | Dashboard trend view (issue #27) |
| Report a missing stock-in date as unknown, not as zero days | Data-quality rule (section 4) |
| Keep lists fast with large stock (paging, filtering in the database) | Non-functional design (system design document) |

---

## 2. Product requirements

*To do in issue #4.*

## 3. Acceptance criteria

*To do in issue #4.*

## 4. Assumptions and open questions

*To do in issue #5.*

Open question carried from section 1: what counts as "close to 90 days" for the
early-warning group (U2)?

## 5. Out of scope

*To do in issue #5.*
