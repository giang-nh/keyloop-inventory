# Specification: Intelligent Inventory Dashboard

This document explains what we are building, for whom, and why. It is the single source
of truth for behaviour: code and tests follow it.

It is written as the story of how we got from the user's problem to a precise list of
things to build and test. Each step ends with **acceptance criteria**: short statements
that a test can prove. Every criterion has an ID (for example `AC-2.2`), and every test
names the ID it proves. That is how we check that nothing in the story was lost on the way
to the code.

**Contents**

1. [The problem](#1-the-problem)
2. [Thinking it through](#2-thinking-it-through)
3. [Decisions where the brief is unclear](#3-decisions-where-the-brief-is-unclear)
4. [What we build, and what we leave out](#4-what-we-build-and-what-we-leave-out)
5. [From this document to the tests](#5-from-this-document-to-the-tests)

---

## 1. The problem

### The manager's day

Our user is a **dealership manager**. They are responsible for the cars on the lot.
Every car that is not sold costs money: it loses value each week, and the dealership
usually pays interest on the loan it used to buy the car. The longer a car sits, the
harder it is to sell and the more it costs.

The challenge describes what this manager needs, in short: *a clear, up-to-date view of
the vehicles in stock, a way to spot the ones that have been there for more than 90 days,
and a way to record what they plan to do about each one*, for example a price reduction.

### What the manager does not say

There are no real users to interview for this assessment. So we asked what a manager in
this position would also want, without saying it. We kept three ideas. Each one is an
**assumption**, and each one shapes a requirement later.

- **U1: "How much money is tied up in aging stock?"** Ten aging cars can be a small
  problem or a big one, depending on their value. The count alone does not show the size
  of the problem. The total value does.
- **U2: "Which cars are about to become aging?"** Acting on day 80 is cheaper than acting
  on day 120. A manager would rather see trouble coming than find it after the fact.
- **U3: "Show me my dealership."** A manager is usually responsible for one site, not the
  whole group. A list of every car in every dealership is noise.

U1 and U2 go slightly beyond the brief, which only asks for the over-90-day view. We keep
them small so they add value without changing the core of the task.

### What we noticed but did not treat as user needs

While thinking about the manager, we also noted some things that matter but are not
things a manager would ask for. They are **design and quality decisions**: listing the
oldest cars first, showing the latest action next to each car, showing whether actions
lead to sales, handling a missing stock-in date honestly, and keeping lists fast. We keep
all of them in the product. They appear in the steps below as our own design choices,
not as the user's words.

---

## 2. Thinking it through

We followed the manager's own sequence: first see the stock, then find the problem cars,
then decide what to do, and finally look back at the bigger picture.

### Step 1: "What do I have in stock?"

Everything starts with a list of the cars on the lot. A list of hundreds of cars is only
useful if the manager can narrow it down, so the list needs filters: by dealership (U3),
by make and model, and by how long each car has been in stock.

Two design choices follow from the manager's real question, which is *"which cars should
I deal with first?"*. First, the list puts the cars with the most days in stock at the
top. Second, each car shows its latest recorded action, so the manager can see at a glance
what has already been decided and avoid repeating work.

Cars with no stock-in date go to the very top, above the oldest cars. We cannot tell how
old they are, so the safest thing is to make sure someone sees them and fixes the record.

A large dealership group can have thousands of cars, so the list comes back in pages.
Many cars arrive on the same day, so cars with the same days in stock are always put in the
same order (by their ID). Without that, a car could appear on two pages, or on none.

> **R1.** A dealership manager can see the vehicles in stock, filter them by dealership,
> make, model and days in stock, and see how long each one has been in stock.

| ID | Acceptance criterion |
|---|---|
| AC-1.1 | The list shows only vehicles that are in stock. Sold vehicles are not shown. |
| AC-1.2 | Each vehicle shows: ID, VIN, dealership, make, model, model year, price, stock-in date, days in stock, stock status and its latest action (if any). |
| AC-1.3 | The list can be filtered by dealership. |
| AC-1.4 | The list can be filtered by make. The match is exact but ignores upper and lower case: "toyota" finds "Toyota", "Toy" does not. |
| AC-1.5 | The list can be filtered by model. The match is exact but ignores upper and lower case: "corolla" finds "Corolla", "Cor" does not. |
| AC-1.6 | The list can be filtered by a minimum and a maximum number of days in stock. Both limits are included. |
| AC-1.7 | The list can be filtered by stock status. |
| AC-1.8 | When several filters are used, a vehicle must match all of them. |
| AC-1.9 | By default, vehicles with no stock-in date come first. After them, vehicles with the most days in stock come first. Vehicles with the same days in stock are ordered by ID, so paging never repeats or skips a vehicle. |
| AC-1.10 | The list is returned in pages. The default page size is 50 and the largest is 200. The response includes the total number of matching vehicles. |
| AC-1.11 | An invalid filter returns error 422 with a message that says what is wrong. Examples: a negative number of days, a minimum larger than the maximum, a page size over 200. |

### Step 2: "Which cars are a problem?"

This is the heart of the task, so the rule has to be exact.

**Days in stock** is the number of whole days from the day the car arrived to today. We
count in UTC so the answer does not change with the server's time zone. "Today" is called
the **reference date**. Tests set it to a fixed date, so the same test gives the same
answer on any day.

The brief says *more than* 90 days. So day 90 is not aging and day 91 is. This boundary
is where a bug is most likely, so it gets its own tests.

To give the manager an early warning (U2), each car in stock gets a **stock status**
instead of a simple yes or no:

| Status | Days in stock | Meaning for the manager |
|---|---|---|
| `fresh` | 0 to 75 | Nothing to do yet |
| `approaching` | 76 to 90 | Plan now, before it becomes a problem |
| `aging` | more than 90 | Needs a decision |
| `unknown` | no stock-in date | The data is incomplete; someone should fix the record |

The `unknown` status matters. If a car has no stock-in date, the easy mistake is to treat
it as zero days, which quietly hides it among the fresh cars. We would rather show the
gap than hide it. For the same reason, a stock-in date in the future is a data error, and
we reject it when the data is loaded.

Finally, a summary answers the money question (U1): how many cars are aging or
approaching, and what each group is worth in total. The approaching total shows how much
money is about to be tied up, which is what the early warning is for.

> **R2.** A dealership manager can see which vehicles have been in stock for more than 90
> days, which ones are close to 90 days, and how much money is tied up in aging stock.

| ID | Acceptance criterion |
|---|---|
| AC-2.1 | Days in stock is the number of whole days from the stock-in date to the reference date, both in UTC. |
| AC-2.2 | A vehicle with more than 90 days in stock is `aging`. Day 90 is not aging. Day 91 is. |
| AC-2.3 | A vehicle with 76 to 90 days in stock is `approaching`. |
| AC-2.4 | A vehicle with 0 to 75 days in stock is `fresh`. |
| AC-2.5 | A vehicle with no stock-in date has no days in stock and the status `unknown`. It still appears in the list and is never counted as aging. |
| AC-2.6 | The data loader rejects a vehicle whose stock-in date is after the reference date, and says which vehicle and why. |
| AC-2.7 | Stock status applies only to vehicles in stock. Sold vehicles have no stock status. |
| AC-2.9 | A vehicle in stock whose stock-in date is after the reference date (bad data that got past the loader) is treated like a missing date: status `unknown`, no days in stock, found by the `unknown` filter and by no days-in-stock filter. Recording an action for it returns error 422 with a message that says the date is in the future. |
| AC-2.8 | A summary shows, for one dealership or for all: vehicles in stock, number `aging`, number `approaching`, the total price of `aging` vehicles, and the total price of `approaching` vehicles. |

### Step 3: "What am I going to do about it?"

Once the manager has found an aging car, or one that is about to become aging, they
decide what to do: cut the price, move it to
another dealership, send it to auction, and so on. The brief asks us to let them record
that decision and keep it.

We treat these records as a **history**, not a single field that gets overwritten. The
reason is trust. If a manager wrote "price reduction planned" last month and "send to
auction" today, both facts matter: they show what was tried and in what order. So actions
can be added but never changed or deleted.

Each action records who made it. There is no login in this service (see section 4), so
the manager types their name.

> **R3.** A dealership manager can record a status or planned action for an aging or
> approaching vehicle, and later see every action recorded for it.

| ID | Acceptance criterion |
|---|---|
| AC-3.1 | A manager can record an action for an `aging` or `approaching` vehicle with: an action type, the manager's name (up to 100 characters), and an optional note of up to 500 characters. The service sets the time the action was recorded; a client cannot set or change it. The response includes the saved action and that time. |
| AC-3.2 | The action type must be one of the types listed in decision D-7. Any other type returns error 422. |
| AC-3.3 | Recording an action for a vehicle that is `fresh` or `unknown`, or that has been sold, returns error 422. |
| AC-3.4 | Recording or reading actions for a vehicle that does not exist returns error 404. |
| AC-3.5 | A vehicle's action history is returned newest first. |
| AC-3.6 | Actions cannot be changed or deleted. Recording a new action leaves earlier ones as they were. |
| AC-3.7 | Recorded actions are still there after the service restarts. |

### Step 4: "Is it getting better or worse?"

Steps 1 to 3 answer the manager's questions about today. A manager also wants to step
back and ask: is our aging stock growing or shrinking, and do our actions actually help
cars sell?

Answering that needs history over time, and a reporting tool is better at charts than an
API is. So we add one small thing to the backend: **CSV exports** of all vehicles (sold
ones included) and all actions. A tool such as Power BI or Excel can read them directly.

The exports use the **same aging rule** as the API. The dashboard never works out aging on
its own, so the dashboard and the API can never disagree.

> **R4.** A reporting tool such as Power BI or Excel can read all vehicles and actions as
> CSV files.

| ID | Acceptance criterion |
|---|---|
| AC-4.1 | A vehicles CSV includes all vehicles, in stock and sold, with days in stock and stock status worked out by the same rule as the API. For a sold vehicle, days in stock is the number of days from arrival to sale (D-13). |
| AC-4.2 | An actions CSV includes every recorded action. |
| AC-4.3 | Both files have a header row, use ISO dates (YYYY-MM-DD), and their columns are listed in the API documentation. |

---

## 3. Decisions where the brief is unclear

The brief asks us to make reasonable assumptions where it is unclear, and to write them
down. Each decision below says what was unclear, what we chose, and why.

**D-1 · What does "real-time" mean?**
We read it as *correct at the moment you ask*. Every request works out days in stock and
status from the current data and the reference date. Nothing is cached or calculated
overnight. Live push updates to a screen are out of scope.

**D-2 · How are days counted?**
Whole days from the stock-in date to the reference date, in UTC. A car that arrived today
has 0 days in stock.

*Known limit:* a dealership in another time zone may see a status change a few hours late
or early on the day a car crosses a threshold. For a dealership in Vietnam (UTC+7), a car
that reaches day 91 at midnight local time shows as aging from 7 a.m. We accept this: the
difference is a few hours on one day, and one clock for everyone keeps the rule simple.

**D-3 · Is day 90 aging?**
No. The brief says *more than* 90 days, so aging starts on day 91.

**D-4 · What counts as "close to 90 days"?**
76 to 90 days, which gives the manager about two weeks of warning. The window is a single
setting, so it is easy to change.

**D-5 · What about sold cars?**
Aging is about cars that are still costing money, so it applies only to cars in stock.
Sold cars are left out of the list and have no status. They stay in the data and in the
CSV export, because the trend view needs them.

**D-6 · What if the stock-in date is missing or wrong?**
Missing: the car is shown with status `unknown`, never as zero days. In the future: the
record is rejected when the data is loaded, with a clear message.

The database itself cannot stop a future date (the check depends on today's date), so a
bad record could still arrive another way, for example from another tool writing to the
database. Such a car is treated like one with a missing date: `unknown` means *the
stock-in date is missing or cannot be right*. It is shown, never hidden, so someone fixes
it (AC-2.9). This was found in the code review (issue #20).

**D-7 · Which action types can a manager record?**
A fixed list, so the actions can be counted and compared:
`PRICE_REDUCTION_PLANNED`, `MARKETING_PROMOTION`, `TRANSFER_TO_ANOTHER_DEALERSHIP`,
`SEND_TO_AUCTION`, `UNDER_REVIEW`, `OTHER`. The optional note carries any detail. A fixed
list is less flexible than free text, but free text cannot be counted in a report.

**D-8 · Can a manager record an action for a car that is not aging yet?**
Yes, if it is `approaching`. The brief ties actions to aging vehicles, but the point of
the early warning (U2) is to act before day 90. Blocking actions on those cars would
defeat it. Actions on `fresh` or `unknown` cars, or on sold cars, are still refused:
there is nothing to act on yet, or the record needs fixing first.

**D-9 · Who is the manager?**
There is no login. The manager types their name when recording an action. In a real
system this would come from the company's sign-in.

**D-10 · Money**
Prices are list prices in Vietnamese dong (VND), stored as whole numbers. The total
value of aging stock is the sum of their list prices. It is a measure of size, not an
accounting valuation.

**D-11 · Can the same car be in stock more than once?**
Yes. A car we sold can come back later, for example as a trade-in. Each stay in stock is
its own vehicle record with its own ID, so the VIN is not required to be unique. The cost:
the database can no longer stop the same car from being loaded twice by mistake. We accept
that and note it as a known limit in the system design.

**D-12 · Who sets the time of an action?**
The service does, when the action is saved. A client cannot backdate an action. This keeps
the history trustworthy: the order of events is the order in which they were recorded.

**D-13 · What does "days in stock" mean for a sold car in the CSV export?**
The number of days from arrival to sale. It lets a reporting tool show how long cars took
to sell. Sold cars still have no stock status (AC-2.7).

**D-14 · What is "today" for an export?**
The reference date is read once, when the export starts. A long export that runs past
midnight uses the same date for every row, so the file is consistent.

**D-15 · How far does the sample data go?**
The data generator knows the Lunar New Year dates up to 2027. For a reference date after
that, the sample data has no Tet slowdown. This affects only the simulated data, not the
service.

---

## 4. What we build, and what we leave out

### What we build

A backend service for the dealership manager's four questions: *what do I have, which
cars are a problem, what am I going to do about them, and is it getting better?* It has a
REST API with a real database, automated tests for every acceptance criterion, CSV exports
for reporting tools, and three years of realistic sample data so the whole story can be
shown working. A Power BI dashboard sits on top for the demo.

### What we deliberately leave out, and why

Each item below is left out on purpose. None of them is needed to answer the manager's
questions in this assessment, and each one would add work without making the core better.

| Left out | Why |
|---|---|
| **A user interface for the manager** | The challenge asks for one layer only. We chose the backend. The API contract (OpenAPI) and cURL examples stand in for the client. The Power BI dashboard is a demo view, not a product screen. |
| **Login and permissions** | Not needed to show the core logic. The manager types their name (D-9). A real system would use the company's sign-in. |
| **Adding or editing vehicles through the API** | In a real dealership, stock data comes from the dealer management system. Here it is loaded by a script. The API only reads vehicles. |
| **Changing or deleting actions** | On purpose: the history must be trustworthy (Step 3). |
| **Automatic price advice** | The brief asks for decisions made and recorded by people. Automated advice would also carry a risk: if the system nudged every aging car toward a price cut, it could push prices down across the board. That needs more care than this task allows. |
| **Alerts and notifications** | The early warning is shown in the list and summary (Step 2). Pushing emails or messages is a separate feature. |
| **Live screen updates** | "Real-time" here means correct at the moment you ask (D-1). |
| **Several currencies or countries** | One currency (VND) keeps the money question simple (D-10). |
| **Production hosting** | The service runs locally. The system design document explains how it would move to PostgreSQL and a hosted setup. |

---

## 5. From this document to the tests

Every acceptance criterion above has an ID. Every test includes the ID of the criterion it
proves in its name, for example `test_ac_2_2_day_91_is_aging`.

An automated check (`tests/test_traceability.py`) reads this file and fails the build if
any criterion has no test, or if a test points to a criterion that does not exist. So if
this document changes, the tests have to change with it.
