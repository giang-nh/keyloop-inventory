# ADR 0005: Prometheus metrics and request IDs now, OpenTelemetry later

**Status:** Accepted · 2026-09-27

## Context

The challenge asks for an observability strategy covering logs, metrics and tracing. This
is a single service today.

## Decision

- **Logs:** one JSON line per request, plus lines for business events.
- **Metrics:** the `prometheus_client` library, exposed at `/metrics`.
- **Tracing:** a request ID on every request, returned in the response and written on every
  log line. **OpenTelemetry** is the documented next step when other services are involved.

## Why

- **Standard and light.** The Prometheus format is read by most monitoring tools, and the
  library is one small dependency.
- **Right-sized.** With one service, a request ID already lets us follow a request from
  start to end. Distributed tracing adds value when a request crosses services.

## Considered

- **Full OpenTelemetry now.** More impressive, but more dependencies and setup for little
  gain while there is only one service.
- **Standard library only.** No new dependencies, but home-made metrics that monitoring
  tools cannot read.

## Consequences

- Adding OpenTelemetry later does not change the logs or metrics; it adds trace context on
  top of the request ID.
