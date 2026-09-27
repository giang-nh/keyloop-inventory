---
name: Review checkpoint
about: Stop and judge the work before moving on, using five questions.
labels: ["type:checkpoint", "4d:discernment", "owner:human"]
---

## What is being reviewed
<!-- Link the issues, commits or documents under review. -->

## How to review
The owner asks the AI questions and checks the evidence, rather than reading every line.
Every answer must come with evidence: test output, a command the owner can run, or a file and line.

Always ask:
- *What would break this?*
- *What did you assume that I didn't ask for?*

## 1. Does it work?
<!-- Correctness: bugs, edge cases, boundary values (day 90 vs 91), invalid input, missing data, security holes. -->
- [ ] 

## 2. Does it work well in real use?
<!-- Performance, scale, reliability: large lists, paging, filters in the database, slow or failed calls, observability. -->
- [ ] 

## 3. Is it the right thing?
<!-- Does it solve the manager's real problem in docs/SPEC.md, not just the literal words of the requirement? -->
- [ ] 

## 4. Is it good to use?
<!-- For an API: clear names, consistent fields, error messages that say what went wrong and what to do next. -->
- [ ] 

## 5. Is it responsible?
<!-- Privacy (no personal data in logs), audit trail, unintended effects of the feature. -->
- [ ] 

## Common AI mistakes checked
- [ ] No outdated APIs (see CLAUDE.md)
- [ ] Code matches the style and patterns of the rest of the codebase
- [ ] No invented behaviour for cases the spec does not cover

## Findings and fixes
<!-- What was found, what was changed, and the evidence that it is fixed. -->

## Decision
- [ ] Accepted, or
- [ ] Needs changes (listed above)
