# ADR 0001: Python and FastAPI, backend only

**Status:** Accepted · 2026-09-27

## Context

The challenge asks for one layer only: a backend or a frontend. We chose the backend,
because the core of the problem (the aging rule and a trustworthy action history) lives
there. The client side is mocked by the API contract.

To choose a stack, we assumed a realistic setting:

- **Assumed:** this is a **new service**, with no existing codebase it has to fit into.
- **Assumed:** the **team** that will build and run it is **strongest in Python**.

## Decision

Python 3.12+, FastAPI, SQLAlchemy 2, Pydantic 2, pytest.

## Why

- **Fits the assumed team.** A team works fastest and safest in the language it knows.
- **The API contract comes for free.** FastAPI generates an OpenAPI description from the
  code, which is exactly what the challenge asks for to mock the client.
- **Input checking is built in.** Pydantic models reject bad input before it reaches the
  business rules.
- **Simple testing.** pytest keeps tests short and readable, which matters when every test
  is tied to an acceptance criterion.

## Considered

- **Java with Spring Boot.** A strong enterprise choice, and the owner's own strongest
  background. Not chosen because it does not match the assumed team, and it needs more
  setup for a small new service.
- **Node.js with TypeScript.** Also a good fit for a small API. Not chosen because it does
  not match the assumed team.

## Consequences

- If the real owning team works mainly in Java or .NET, this decision should be revisited.
  The API contract and the spec would carry over unchanged.
