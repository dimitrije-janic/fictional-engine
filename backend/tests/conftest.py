import os

# Set test database URL BEFORE any other imports
# This must happen at module load time, before api modules are imported
os.environ["DATABASE_URL"] = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5433/inventory_test"
)

import pytest
from fastapi.testclient import TestClient

from api.main import app
from api.database import get_db, init_db, init_pool, close_pool


@pytest.fixture(scope="session")
def setup_database():
    """Initialize database and connection pool for the test session."""
    init_pool()
    init_db()
    yield
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("DROP TABLE IF EXISTS servers CASCADE")
    close_pool()


@pytest.fixture
def clean_database(setup_database):
    """Clean database between tests."""
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("TRUNCATE TABLE servers RESTART IDENTITY CASCADE")
    yield


@pytest.fixture
def client(clean_database):
    """Create a test client."""
    return TestClient(app)


@pytest.fixture
def sample_server():
    """Sample server data for testing."""
    return {
        "hostname": "web-server-01",
        "ip_address": "192.168.1.100",
        "datacenter": "us-east-1",
        "state": "active"
    }


@pytest.fixture
def created_server(client, sample_server):
    """Create a server and return its data."""
    response = client.post("/servers", json=sample_server)
    return response.json()
