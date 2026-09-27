# ADR 0004: The latest action is read from the history

**Status:** Accepted · 2026-09-27

## Context

The vehicle list shows each car's latest action, so a manager can see at a glance what has
already been decided. Actions are kept as a history that can only grow (SPEC AC-3.6).

## Decision

Keep actions only in the action history table. When a page of vehicles is listed, look up
the latest action for the vehicles on that page, using an index on
`(vehicle_id, created_at)`.

## Why

- **Each fact lives in one place**, so the list and the history can never disagree.
- **The history stays purely append-only.** Recording an action only ever adds a row; it
  never has to change the vehicle record as well.
- **Fast enough.** It is one extra query per page (at most 200 vehicles), served by an index.

## Considered

- **Copy the latest action onto the vehicle record.** The fastest reads, but the same
  information would live in two places. If one write failed halfway, they could disagree,
  and every action would also have to change the vehicle record.

## Consequences

- If lists ever become very large or very frequent, a short-lived cache is the next step,
  rather than copying data onto the vehicle.
