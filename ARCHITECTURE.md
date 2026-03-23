# Architecture & Design

## Overview

This service exposes a clean REST API surface over OpenStack's Nova (compute) and Cinder (block storage) APIs. The architecture deliberately separates HTTP concerns, business logic, and infrastructure I/O into distinct layers — making each independently testable and replaceable.

```
HTTP Request
     │
     ▼
┌─────────────────────┐
│  FastAPI Routers    │  ← Input validation, HTTP status mapping, OpenAPI docs
└──────────┬──────────┘
           │  Pydantic models (request/response)
           ▼
┌─────────────────────┐
│   Service Layer     │  ← Business logic, orchestration, domain model
└──────────┬──────────┘
           │  Repository interface
           ▼
┌─────────────────────┐
│ Repository Layer    │  ← All openstacksdk calls live here
└──────────┬──────────┘
           │
           ▼
    OpenStack APIs
    (Nova / Cinder)
```

---

## Key Design Decisions

### 1. Repository Pattern

All OpenStack SDK calls are encapsulated in `VMRepository` and `VolumeRepository`. Nothing above those classes imports `openstack`. This provides three concrete benefits:

- **Testability**: Unit tests swap the repository for a `MagicMock(spec=VMRepository)` and never touch the network.
- **Replaceability**: Migrating from openstacksdk to boto3 (for AWS) or a different cloud SDK means only updating the repository classes.
- **Error isolation**: All SDK exceptions are caught in the repository and re-raised as domain exceptions (`NotFoundError`, `ConflictError`, etc.) at a single chokepoint.

### 2. Dependency Injection via FastAPI

Services are injected into route handlers using FastAPI's `Depends()`. This gives two advantages:

- Tests override dependencies at the app level (`app.dependency_overrides`) rather than monkey-patching imports.
- The OpenStack connection is built once (via `@lru_cache`) and shared across requests without global state.

### 3. Pydantic v2 for Schema Validation

Request and response models are defined as strict Pydantic v2 schemas. This provides:

- Automatic 422 Unprocessable Entity responses with detailed field-level errors for bad client input.
- Auto-generated OpenAPI documentation visible in `/docs`.
- Clean separation between what the API *accepts* (request schema) and what it *returns* (response schema).

### 4. Thin Service Layer

Services do not perform any I/O — they only orchestrate repository calls and transform raw OpenStack objects into typed response models. This keeps business rules easy to reason about and test without mocking network I/O.

### 5. Error Hierarchy

```
PlatformError (500)
├── NotFoundError (404)
├── ConflictError (409)
├── ValidationError (422)
├── QuotaExceededError (429)
└── OpenStackError (502)
```

A single `platform_error_handler` converts any domain error to a consistent JSON envelope:

```json
{
  "error": "NOT_FOUND",
  "message": "Server vm-abc not found",
  "detail": "..."
}
```

This consistency makes client error handling predictable.

### 6. Structured JSON Logging

Every request is logged as a JSON line:

```json
{"time":"2024-01-01T12:00:00Z","level":"INFO","name":"api.access","msg":"method":"POST","path":"/api/v1/vms","status":202,"duration_ms":143.7}
```

This format is directly ingestible by ELK, Loki, CloudWatch, or Datadog without parsing configuration.

### 7. Async-Ready Architecture

All route handlers are declared `async`. The FastAPI/uvicorn runtime handles request concurrency via asyncio. The current openstacksdk calls are synchronous (blocking), but the architecture is ready for a full async migration — wrapping blocking calls in `asyncio.to_thread()` or switching to an async-native HTTP client for OpenStack APIs.

---

## Trade-offs and Acknowledged Limitations

**Authentication** — The current implementation uses OpenStack's own Keystone token system. The API itself has no authentication layer (no API keys, JWT, etc.). For production deployment behind a corporate network this is acceptable; for a public endpoint an API gateway (Kong, AWS API Gateway) or bearer token middleware should be added.

**Synchronous SDK** — `openstacksdk` is synchronous. Under high concurrency, blocking calls will occupy worker threads. This is mitigated by running multiple uvicorn workers and is suitable for the timebox scope. A production hardening would wrap SDK calls with `asyncio.to_thread`.

**No Database** — VM and volume state is always fetched live from OpenStack. There is no local cache or event-driven state sync. This means the API is always consistent but each request hits the OpenStack APIs. For high-read scenarios a Redis cache layer would reduce latency significantly.

**Wait/Poll Semantics** — VM and volume operations are submitted asynchronously (HTTP 202 Accepted). The caller must poll `GET /api/v1/vms/{id}` to observe status transitions. A webhook or SSE notification system would be a valuable addition (see ROADMAP).

---

## Testing Strategy

| Layer | Type | Approach |
|-------|------|----------|
| Repository | Unit | Would require mock of openstacksdk Connection — deferred to integration suite |
| Service | Unit | `MagicMock(spec=Repo)` — full coverage, fast, no network |
| Endpoints | Integration | FastAPI `TestClient` + `dependency_overrides` — tests routing, validation, error mapping |
| E2E | Manual / CI | Against a real OpenStack devstack instance in CI |

The `tests/unit` suite covers all service-layer business logic branches. The `tests/integration` suite covers every endpoint — request validation, happy paths, and all error codes.

---

## Security Considerations

- Non-root Docker user (`appuser`) prevents privilege escalation inside the container.
- OpenStack passwords and tokens are loaded from environment variables only, never hard-coded.
- The `.gitignore` excludes `.env` files to prevent accidental credential leaks.
- CORS is currently open (`allow_origins=["*"]`) — production would restrict this to known frontend origins.
