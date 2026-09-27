# ADR 0002: SQLite now, PostgreSQL later, Alembic migrations

**Status:** Accepted · 2026-09-27

## Context

The challenge asks for a real, persistent database. Reviewers should be able to run the
service without installing a database server. In production, several copies of the service
would share one database.

## Decision

- Use **SQLite** for this assessment.
- Write all database code through **SQLAlchemy**, so the same code runs on **PostgreSQL**.
- Manage the schema with **Alembic** migrations from the start.

## Why

- **Zero setup for reviewers.** SQLite is a single file; there is nothing to install.
- **A clear production path.** Moving to PostgreSQL means changing the connection setting,
  not the code.
- **Safe schema changes.** Alembic keeps a numbered history of every change, so every
  database (a laptop, a test server, production) can be brought to the same version the
  same way. Letting the app create tables on start-up is quicker, but cannot change an
  existing schema safely.

## Considered

- **PostgreSQL in Docker from day one.** Closer to production, but every reviewer would
  need Docker running.
- **Create tables on start-up instead of migrations.** About 30 minutes faster to set up,
  but leaves no safe way to change the schema later.

## Consequences

- SQLite allows only one writer at a time. That is fine for this assessment and a single
  service, but it is the first thing to change before real use.
- We avoid SQLite-only features so the move to PostgreSQL stays simple.
