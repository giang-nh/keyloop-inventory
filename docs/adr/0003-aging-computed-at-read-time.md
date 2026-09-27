# ADR 0003: Days in stock and stock status are worked out when asked

**Status:** Accepted · 2026-09-27

## Context

A car's status changes every day even when nothing about the car changes. A car that
arrived on 1 July is `approaching` on 27 September and `aging` on 30 September. The spec
reads "real-time" as *correct at the moment you ask* (SPEC D-1).

## Decision

Store only the stock-in date. Work out days in stock and status on every request, from the
stock-in date and the reference date (today, in UTC).

To filter by status or age, turn the request into a **range of stock-in dates** so the
database can use its index. For example, "aging" means "stock-in date on or before today
minus 91 days".

## Why

- **Always correct.** On the morning a car crosses day 90, it shows as aging. Nobody has to
  update anything.
- **One rule in one place.** The thresholds live in `app/services/aging.py`.
- **Fast.** The database filters with an index instead of the service loading every car.

## Considered

- **Store the status and update it every night.** The simplest queries, but the data is
  wrong between runs, a failed job leaves it wrong without anyone noticing, and it adds a
  job to run and watch.
- **Load all cars and filter in Python.** The simplest code, but it gets slower with every
  car added. Finding 30 aging cars among 5,000 would mean loading all 5,000.

## Consequences

- The thresholds are used in two ways: to label each car, and to build the date ranges for
  filters. A test checks that both always agree, including on days 75, 76, 90 and 91.
