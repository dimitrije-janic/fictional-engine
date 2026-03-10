# Server Inventory Management API

A CRUD application for tracking servers across multiple data centers.

## Quick Start

### Using Docker Compose (Recommended)

```bash
# Start the entire stack (API + PostgreSQL)
docker-compose up -d

# View logs
docker-compose logs -f api

# Stop the stack
docker-compose down
```

The API will be available at `http://localhost:8000`.

### Running Locally

1. **Start PostgreSQL**
   ```bash
   docker-compose up -d db
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set environment variables**
   ```bash
   export DATABASE_URL=postgresql://postgres:postgres@localhost:5432/inventory
   ```

4. **Start the API**
   ```bash
   uvicorn api.main:app --reload
   ```

### Running Tests

```bash
# Unit tests (requires test database)
docker compose --profile test up -d db-test
export TEST_DATABASE_URL=postgresql://postgres:postgres@localhost:5433/inventory_test
pytest -v tests/test_*.py

# Integration tests (spins up full Docker Compose stack automatically)
pytest -v tests/integration/

# All tests
pytest -v
```

---

## API Specification

Base URL: `http://localhost:8000`

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /servers | Create a new server |
| GET | /servers | List all servers |
| GET | /servers/{id} | Get a server by ID |
| PUT | /servers/{id} | Update a server |
| DELETE | /servers/{id} | Delete a server |
| GET | /health | Health check |

---

### POST /servers

Create a new server.

**Request Body:**
```json
{
  "hostname": "web-server-01",
  "ip_address": "192.168.1.100",
  "datacenter": "us-east-1",
  "state": "active"
}
```

**Validation Rules:**
- `hostname`: Required, must be unique, 1-255 alphanumeric characters with hyphens and dots
- `ip_address`: Required, must be valid IPv4 or IPv6 address
- `datacenter`: Required, string
- `state`: Required, one of: `active`, `offline`, `retired`

**Response (201 Created):**
```json
{
  "id": 1,
  "hostname": "web-server-01",
  "ip_address": "192.168.1.100",
  "datacenter": "us-east-1",
  "state": "active",
  "created_at": "2024-01-15T10:30:00.000000",
  "updated_at": "2024-01-15T10:30:00.000000"
}
```

**Error Responses:**
- `409 Conflict`: Hostname already exists
- `422 Unprocessable Entity`: Validation error

---

### GET /servers

List all servers.

**Response (200 OK):**
```json
[
  {
    "id": 1,
    "hostname": "web-server-01",
    "ip_address": "192.168.1.100",
    "datacenter": "us-east-1",
    "state": "active",
    "created_at": "2024-01-15T10:30:00.000000",
    "updated_at": "2024-01-15T10:30:00.000000"
  }
]
```

---

### GET /servers/{id}

Get a server by ID.

**Response (200 OK):**
```json
{
  "id": 1,
  "hostname": "web-server-01",
  "ip_address": "192.168.1.100",
  "datacenter": "us-east-1",
  "state": "active",
  "created_at": "2024-01-15T10:30:00.000000",
  "updated_at": "2024-01-15T10:30:00.000000"
}
```

**Error Responses:**
- `404 Not Found`: Server not found

---

### PUT /servers/{id}

Update an existing server.

**Request Body:**
```json
{
  "hostname": "web-server-01-updated",
  "ip_address": "10.0.0.1",
  "datacenter": "us-west-2",
  "state": "offline"
}
```

**Response (200 OK):**
```json
{
  "id": 1,
  "hostname": "web-server-01-updated",
  "ip_address": "10.0.0.1",
  "datacenter": "us-west-2",
  "state": "offline",
  "created_at": "2024-01-15T10:30:00.000000",
  "updated_at": "2024-01-15T11:00:00.000000"
}
```

**Error Responses:**
- `404 Not Found`: Server not found
- `409 Conflict`: Hostname already exists (on another server)
- `422 Unprocessable Entity`: Validation error

---

### DELETE /servers/{id}

Delete a server.

**Response (204 No Content):** Empty body

**Error Responses:**
- `404 Not Found`: Server not found

---

### GET /health

Health check endpoint.

**Response (200 OK):**
```json
{
  "status": "healthy"
}
```

---

## CLI Specification

The CLI interacts with the API to manage servers.

### Installation

```bash
pip install -r requirements.txt
```

### Configuration

Set the API URL via environment variable:
```bash
export API_URL=http://localhost:8000
```

Or use the `--api-url` flag:
```bash
python -m cli.main --api-url http://localhost:8000 list
```

### Commands

#### List Servers

```bash
# List all servers
python -m cli.main list

# Output as JSON
python -m cli.main list --json-output
python -m cli.main list -j
```

**Example Output:**
```
ID: 1
  Hostname:   web-server-01
  IP Address: 192.168.1.100
  Datacenter: us-east-1
  State:      active
  Created:    2024-01-15T10:30:00.000000
  Updated:    2024-01-15T10:30:00.000000
```

#### Get Server

```bash
# Get server by ID
python -m cli.main get 1

# Output as JSON
python -m cli.main get 1 --json-output
```

#### Create Server

```bash
# Create a new server
python -m cli.main create \
  --hostname web-server-02 \
  --ip-address 192.168.1.101 \
  --datacenter us-east-1 \
  --state active

# Short form
python -m cli.main create \
  -h web-server-02 \
  -i 192.168.1.101 \
  -d us-east-1 \
  -s active
```

**Options:**
| Flag | Short | Required | Description |
|------|-------|----------|-------------|
| --hostname | -h | Yes | Server hostname |
| --ip-address | -i | Yes | IP address (IPv4 or IPv6) |
| --datacenter | -d | Yes | Data center location |
| --state | -s | No | Server state (default: active) |
| --json-output | -j | No | Output as JSON |

#### Update Server

```bash
# Update an existing server
python -m cli.main update 1 \
  --hostname web-server-01-updated \
  --ip-address 10.0.0.1 \
  --datacenter us-west-2 \
  --state offline
```

**Options:** Same as create command (all required for update)

#### Delete Server

```bash
# Delete with confirmation prompt
python -m cli.main delete 1

# Skip confirmation
python -m cli.main delete 1 --yes
python -m cli.main delete 1 -y
```

### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Error (API error, connection error, etc.) |

---

## Data Model

### Server

| Field | Type | Description |
|-------|------|-------------|
| id | integer | Auto-generated unique identifier |
| hostname | string | Unique server hostname (1-255 chars) |
| ip_address | string | Valid IPv4 or IPv6 address |
| datacenter | string | Data center location |
| state | enum | One of: active, offline, retired |
| created_at | datetime | Record creation timestamp |
| updated_at | datetime | Last update timestamp |

---

## OpenAPI Documentation

When the API is running, interactive documentation is available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
