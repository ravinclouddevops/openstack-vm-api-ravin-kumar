# OpenStack VM API

A production-ready REST API service for managing OpenStack virtual machine lifecycle operations — built with **FastAPI**, **openstacksdk**, and **Pydantic v2**.

## Quick Start

```bash
# 1. Clone and enter the project
git clone <repo-url> && cd openstack-vm-api

# 2. Create a virtual environment
python3 -m venv venv && source venv/bin/activate

# 3. Install dependencies
pip install -r requirements-dev.txt

# 4. Configure OpenStack credentials (choose one option)

# Option A — clouds.yaml (recommended)
# Place your clouds.yaml at ~/.config/openstack/clouds.yaml and set:
export OS_CLOUD=mycloud

# Option B — explicit environment variables
cp .env.example .env
# Edit .env with your Keystone URL, username, password, project

# 5. Run the API
uvicorn app.main:app --reload --port 8080
```

The interactive API docs are available at:
- Swagger UI: http://localhost:8080/docs
- ReDoc: http://localhost:8080/redoc

---

## API Endpoints

### Virtual Machines

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/v1/vms` | List all VMs (optional `?status=ACTIVE` filter) |
| `POST` | `/api/v1/vms` | Create (boot) a new VM |
| `GET` | `/api/v1/vms/{vm_id}` | Get full VM details |
| `DELETE` | `/api/v1/vms/{vm_id}` | Terminate a VM |
| `POST` | `/api/v1/vms/{vm_id}/start` | Power on a VM |
| `POST` | `/api/v1/vms/{vm_id}/stop` | Power off a VM |
| `POST` | `/api/v1/vms/{vm_id}/reboot` | Reboot (SOFT or HARD) |
| `PATCH` | `/api/v1/vms/{vm_id}/metadata` | Update metadata key/value pairs |
| `GET` | `/api/v1/vms/{vm_id}/console` | Get VNC console URL |

### Volumes

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/v1/volumes` | List all volumes |
| `POST` | `/api/v1/volumes` | Create a volume (optionally from snapshot) |
| `GET` | `/api/v1/volumes/{volume_id}` | Get volume details |
| `DELETE` | `/api/v1/volumes/{volume_id}` | Delete a volume |
| `POST` | `/api/v1/volumes/{volume_id}/attach` | Attach volume to a VM |
| `POST` | `/api/v1/volumes/{volume_id}/detach` | Detach volume from a VM |
| `POST` | `/api/v1/volumes/{volume_id}/snapshots` | Create a snapshot |
| `GET` | `/api/v1/volumes/{volume_id}/snapshots` | List snapshots for a volume |

### Health

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Liveness probe (always 200 if running) |
| `GET` | `/ready` | Readiness probe |

---

## Example Requests

### Boot a VM

```bash
curl -s -X POST http://localhost:8080/api/v1/vms \
  -H "Content-Type: application/json" \
  -d '{
    "name": "web-server-01",
    "flavor_id": "m1.small",
    "image_id": "ubuntu-22.04-amd64",
    "networks": [{"network_id": "private-net"}],
    "key_name": "my-keypair",
    "security_groups": ["default", "web"],
    "metadata": {"environment": "production", "team": "platform"}
  }' | jq .
```

### Stop a VM

```bash
curl -s -X POST http://localhost:8080/api/v1/vms/VM_ID/stop | jq .status
```

### Create and attach a data volume

```bash
# Create 100 GiB volume
VOL=$(curl -s -X POST http://localhost:8080/api/v1/volumes \
  -H "Content-Type: application/json" \
  -d '{"name": "data-vol", "size_gb": 100}' | jq -r .id)

# Attach to VM
curl -s -X POST http://localhost:8080/api/v1/volumes/$VOL/attach \
  -H "Content-Type: application/json" \
  -d '{"vm_id": "VM_ID", "mount_point": "/dev/vdb"}' | jq .status
```

---

## Running Tests

```bash
# All tests
pytest

# With coverage report
pytest --cov=app --cov-report=term-missing --cov-report=html

# Unit tests only (no network required)
pytest tests/unit -v

# Integration / endpoint tests
pytest tests/integration -v
```

The test suite enforces **≥ 80% code coverage** via `.coveragerc`.

---

## Docker

```bash
# Build and run
docker-compose up --build

# Or build manually
docker build -t openstack-vm-api .
docker run -p 8080:8080 \
  -e OS_CLOUD=mycloud \
  -v ~/.config/openstack:/root/.config/openstack:ro \
  openstack-vm-api
```

---

## Configuration Reference

| Variable | Default | Description |
|----------|---------|-------------|
| `OS_CLOUD` | _(empty)_ | Named cloud from `clouds.yaml` |
| `OS_AUTH_URL` | _(empty)_ | Keystone v3 endpoint |
| `OS_USERNAME` | _(empty)_ | OpenStack username |
| `OS_PASSWORD` | _(empty)_ | OpenStack password |
| `OS_PROJECT_NAME` | _(empty)_ | Project / tenant |
| `OS_USER_DOMAIN_NAME` | `Default` | User domain |
| `OS_PROJECT_DOMAIN_NAME` | `Default` | Project domain |
| `OS_REGION_NAME` | `RegionOne` | Region |
| `LOG_LEVEL` | `INFO` | Logging level |
| `DEBUG` | `false` | Enable debug mode |

---

## Project Structure

```
openstack-vm-api/
├── app/
│   ├── main.py              # FastAPI app factory
│   ├── config.py            # Environment-based settings
│   ├── dependencies.py      # Dependency injection providers
│   ├── exceptions.py        # Domain exceptions + HTTP handlers
│   ├── logging_config.py    # Structured JSON logging
│   ├── models/
│   │   ├── vm.py            # VM request/response schemas
│   │   ├── volume.py        # Volume request/response schemas
│   │   └── common.py        # Shared envelope types
│   ├── repositories/
│   │   ├── openstack_client.py   # Connection factory + error mapping
│   │   ├── vm_repository.py      # Nova SDK operations
│   │   └── volume_repository.py  # Cinder SDK operations
│   ├── services/
│   │   ├── vm_service.py         # VM business logic
│   │   └── volume_service.py     # Volume business logic
│   └── routers/
│       ├── vms.py                # VM endpoints
│       ├── volumes.py            # Volume endpoints
│       └── health.py             # Health/readiness endpoints
├── tests/
│   ├── conftest.py           # Shared fixtures
│   ├── unit/                 # Service-layer tests (all mocked)
│   └── integration/          # Endpoint tests (TestClient + mocks)
├── .gitlab-ci.yml
├── Dockerfile
├── docker-compose.yml
└── ARCHITECTURE.md
```

---

## Design Choices

See [ARCHITECTURE.md](ARCHITECTURE.md) for a detailed discussion of design decisions, trade-offs, and the engineering principles behind the implementation.

## Roadmap

See [ROADMAP.md](ROADMAP.md) for planned enhancements beyond the timebox.
