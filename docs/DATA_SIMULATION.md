# Data Simulation Rules

This document explains how `scripts/generate_data.py` builds three years of sample
dealership data for the API demo and the Power BI dashboard.

> **Status: proposed by the AI, waiting for the owner's approval (issue #25).**

## Why simulated data

There is no real dealership data in this assessment. A handful of hand-made records can
test the rules, but cannot show trends. Three years of simulated data lets the dashboard
answer the manager's fourth question, *"Is it getting better or worse?"*

## ⚠️ Read this before drawing conclusions from the dashboard

**Every pattern in this data was put there by the rules below.** In particular, the rules
*assume* that a price reduction or a promotion helps a car sell sooner. So when the
dashboard shows that actions help, it is showing our assumption, not evidence.

The data is good for showing that the service and the dashboard work. It says nothing
about how real dealerships behave.

## The rules

Everything is driven by one random seed (default 42). The same seed and the same
reference date always give exactly the same data.

### Time span

- The data covers the **three years up to the reference date** (default: today, UTC).
- The simulation starts six months earlier and keeps only the cars still in stock when
  the three years begin. So the first month already has a normal amount of stock, instead
  of starting from an empty lot.

### Dealerships

| Dealership | City | New cars per day (average) | Managers |
|---|---|---|---|
| Riverside Motors | Ho Chi Minh City | 3.0 | An Nguyen, Linh Tran |
| Lakeside Cars | Hanoi | 2.2 | Minh Pham, Hoa Le |
| Harbour Auto | Da Nang | 1.6 | Quang Vo, Thu Dang |
| Hilltop Autos | Can Tho | 1.0 | Bao Huynh, Mai Do |

All names are made up.

### Arrivals

- Each day, each dealership receives a random number of cars around its average.
- **Seasons:** fewer arrivals in February (around the Lunar New Year), more in the last
  quarter, when dealers stock up for year-end sales.
- **Growth:** arrivals grow by about 5% a year, so the trend view has a direction.

### Cars

About 14 common models across Toyota, Honda, Hyundai, Kia, Mazda, Ford and Mitsubishi.
Each model has a typical list price, a share of arrivals, and a selling speed (popular
models sell faster). Each car's price varies by up to 8% around its model's price.
Prices are whole units of one currency (SPEC D-10).

### Selling

- How long a car takes to sell is random, with a long tail of slow sellers. The typical
  time depends on the model's speed and on price (dearer cars take a little longer).
- Measured on the default data (seed 42, reference date 2026-09-27): half of the cars
  sell within **about five weeks**, the middle half within **three to nine weeks**, and
  about **one stay in eight** (12.7%) lasts more than 90 days. About 95% of the cars in
  the data have been sold; a little under 500 are in stock.
- A car not sold by the reference date is still in stock.

### Actions

Actions only happen while a car is in stock and at least 76 days old, matching the
service's own rule (SPEC D-8).

| When | What may happen |
|---|---|
| Day 76 to 85 | Half the time, a manager marks it `UNDER_REVIEW`. |
| Day 91 to 100 | Most of the time, a manager picks an action: usually a price reduction, sometimes a promotion, a transfer or something else. |
| Day 150 onwards | If still unsold, it is often sent to auction. |

**Assumed effect of actions** (this is the part the warning above is about):

| Action | Effect on the remaining time to sell |
|---|---|
| Price reduction planned | About half as long |
| Marketing promotion | About 30% shorter |
| Transfer to another dealership | About 20% shorter. The car stays recorded at its first dealership; moves between dealerships are not modelled. |
| Send to auction | Sold within one to three weeks |
| Under review, other | No effect |

### Unusual cases, on purpose

- **Trade-ins:** about 2% of sold cars come back later with the same VIN, at a lower price.
  Each return is a new stay in stock (SPEC D-11).
- **Missing stock-in dates:** a few cars in stock have no stock-in date, so the `unknown`
  status appears in the data (SPEC D-6). Only cars without actions are chosen.

## Checks

The data goes through the same loader checks as any other data (SPEC AC-2.6), and
`tests/test_simulation.py` checks that:

- No car is sold before it arrives, and nothing happens after the reference date.
- Every action happens while its car is in stock and at least 76 days old.
- Counts land in realistic ranges (cars in stock, share of aging cars).
- Trade-ins and missing dates are present.
- The same seed always gives the same data.
