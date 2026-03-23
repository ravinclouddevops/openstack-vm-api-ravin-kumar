# Roadmap & Backlog

This document captures planned enhancements beyond the 2–4 hour timebox. Items are grouped by engineering theme and loosely ordered by value vs. effort.

---

## Authentication & Authorization

**API Key / Bearer Token middleware**
Add FastAPI middleware that validates an `Authorization: Bearer <token>` header. Tokens would be validated against a PostgreSQL table or Redis store. Pairs well with per-project quota enforcement.

**Role-Based Access Control (RBAC)**
Introduce an `admin` vs. `operator` vs. `viewer` role model. Destructive operations (delete VM, detach volume) require `operator` or above.

**OpenStack Keystone token passthrough**
Alternative auth model: accept the caller's Keystone token directly and proxy it to OpenStack, meaning the API inherits OpenStack's own permission model with zero duplication.

---

## Async & Performance

**Async SDK calls via `asyncio.to_thread`**
Wrap all blocking `openstacksdk` calls to free the event loop for concurrent requests. This would allow scaling to thousands of concurrent connections on a single uvicorn process.

**Redis caching layer**
Cache `GET /vms` and `GET /volumes` responses with a configurable TTL (default 10 s). Invalidate on create/delete/power operations. Reduces OpenStack API load under read-heavy traffic.

**Connection pooling**
Configure openstacksdk with a connection pool and retry policy (exponential backoff, jitter) to handle transient OpenStack API failures gracefully.

---

## Observability

**Prometheus metrics endpoint (`/metrics`)**
Expose request count, error rate, and p95/p99 latency histograms per endpoint using `prometheus-fastapi-instrumentator`. These feed directly into the Grafana dashboards.

**Distributed tracing (OpenTelemetry)**
Instrument the service with OTEL spans. Each request produces a trace that flows through the FastAPI router → service → repository → OpenStack. Jaeger or Tempo as the trace backend.

**Structured audit log**
Append-only log of every mutating operation (create/delete/start/stop) with actor, resource ID, and timestamp. Essential for compliance and incident investigation.

---

## Extended Resource Management

**Flavor and Image catalog endpoints**
`GET /api/v1/flavors` and `GET /api/v1/images` — read-only views of available Nova flavors and Glance images to support a self-service portal UI without direct OpenStack API access.

**Network and Security Group management**
`GET /api/v1/networks`, `GET /api/v1/security-groups`, and `POST /api/v1/security-groups/{id}/rules`. Completes the VM provisioning loop so a caller never needs to interact with Neutron directly.

**Floating IP allocation**
`POST /api/v1/vms/{id}/floating-ip` — allocate and associate a floating IP. Currently callers must use the Neutron API directly.

**VM resize**
`POST /api/v1/vms/{id}/resize` with `{"flavor_id": "m1.large"}` — triggers Nova's resize workflow and includes a confirm/revert cycle.

**Multi-attach volumes**
Extend the attach endpoint to support volumes with `multiattach=true` — required for shared-disk clustering scenarios (e.g., Pacemaker).

---

## Developer Experience

**Webhook / event notifications**
After-action webhooks: clients register a callback URL and receive a POST when a VM transitions to `ACTIVE`, `ERROR`, or `DELETED`. Replaces the polling pattern.

**Server-Sent Events (SSE) stream**
`GET /api/v1/vms/{id}/events` returns a streaming response of VM state changes. Better UX for interactive UIs than polling.

**CLI companion tool**
A thin `vmctl` CLI built with Click that wraps this API, targeting operators who prefer terminal workflows.

---

## Reliability & Operations

**Database-backed job queue**
Use Celery + Redis (or pg-queue) to handle long-running operations (bulk provision, scheduled cleanup) outside the request lifecycle. Enables background processing with retry logic.

**Graceful shutdown**
Handle SIGTERM by completing in-flight requests before closing the OpenStack connection pool — important for zero-downtime rolling deployments in Kubernetes.

**Rate limiting**
Per-caller rate limiting using `slowapi` (Redis-backed token bucket). Prevents a single project from starving the OpenStack control plane.

**Chaos engineering tests**
Inject failures at the repository boundary (SDK timeout, 503 from Nova) and assert that the service returns the correct error codes and does not leak connections.

---

## Infrastructure as Code

**Terraform module**
Provide a Terraform module that boots a preconfigured set of VMs using this API — demonstrating IaC integration and dogfooding the provisioning flow.

**Helm chart**
Package the service as a Kubernetes Helm chart with configurable replica count, resource limits, HPA, and a bundled Prometheus ServiceMonitor.
