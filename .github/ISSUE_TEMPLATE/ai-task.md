---
name: AI task
about: A task delegated to the AI coding assistant. Fill in every section so the AI does not have to guess.
labels: ["owner:ai"]
---

## Task
<!-- One or two sentences: what to build or change. -->

## Context
<!-- Who uses this, when, and what decision it supports. Link the requirement in docs/SPEC.md. -->

## Tech environment
<!-- Files and modules involved, libraries to use, anything that must not change. -->

## Data shape
<!-- Inputs and outputs: fields, types, example JSON or CSV rows. -->

```json
{
}
```

## Constraints and edge cases
<!-- Boundary values, missing data, invalid input, errors. Say what should happen in each case.
     Missing is not the same as zero. -->
- 

## Verification
<!-- How we will know it is done. List the acceptance criteria IDs the tests must prove. -->
- Acceptance criteria covered: AC-
- `ruff check .` and `pytest` pass
- The AI reports every assumption it made that this issue did not ask for
