import subprocess
import time
import pytest
import requests

pytestmark = pytest.mark.integration

API_URL = "http://localhost:8000"
COMPOSE_FILE = "docker-compose.yml"


@pytest.fixture(scope="module")
def docker_compose():
    subprocess.run(
        ["docker", "compose", "-f", COMPOSE_FILE, "up", "-d", "--build", "--wait"],
        check=True,
        capture_output=True
    )

    for _ in range(30):
        try:
            response = requests.get(f"{API_URL}/health", timeout=2)
            if response.status_code == 200:
                break
        except requests.exceptions.ConnectionError:
            pass
        time.sleep(1)
    else:
        pytest.fail("API did not become healthy in time")

    yield

    subprocess.run(
        ["docker", "compose", "-f", COMPOSE_FILE, "down", "-v"],
        check=True,
        capture_output=True
    )


@pytest.fixture(autouse=True)
def clean_servers(docker_compose):
    response = requests.get(f"{API_URL}/servers")
    for server in response.json():
        requests.delete(f"{API_URL}/servers/{server['id']}")
    yield


class TestIntegrationCRUD:

    def test_health_check(self, docker_compose):
        response = requests.get(f"{API_URL}/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["database"] == "connected"

    def test_create_and_get_server(self, docker_compose):
        payload = {
            "hostname": "integration-test-01",
            "ip_address": "10.0.0.1",
            "datacenter": "us-east-1",
            "state": "active"
        }

        create_response = requests.post(f"{API_URL}/servers", json=payload)
        assert create_response.status_code == 201
        server = create_response.json()
        assert server["hostname"] == payload["hostname"]
        server_id = server["id"]

        get_response = requests.get(f"{API_URL}/servers/{server_id}")
        assert get_response.status_code == 200
        assert get_response.json()["hostname"] == payload["hostname"]

    def test_list_servers(self, docker_compose):
        servers = [
            {"hostname": "server-1", "ip_address": "10.0.0.1", "datacenter": "dc1", "state": "active"},
            {"hostname": "server-2", "ip_address": "10.0.0.2", "datacenter": "dc2", "state": "offline"},
        ]
        for s in servers:
            requests.post(f"{API_URL}/servers", json=s)

        response = requests.get(f"{API_URL}/servers")

        assert response.status_code == 200
        assert len(response.json()) == 2

    def test_update_server(self, docker_compose):
        payload = {
            "hostname": "update-test",
            "ip_address": "10.0.0.1",
            "datacenter": "us-east-1",
            "state": "active"
        }
        create_response = requests.post(f"{API_URL}/servers", json=payload)
        server_id = create_response.json()["id"]

        updated = {
            "hostname": "update-test-modified",
            "ip_address": "10.0.0.2",
            "datacenter": "us-west-1",
            "state": "offline"
        }
        update_response = requests.put(f"{API_URL}/servers/{server_id}", json=updated)

        assert update_response.status_code == 200
        data = update_response.json()
        assert data["hostname"] == "update-test-modified"
        assert data["state"] == "offline"

    def test_delete_server(self, docker_compose):
        payload = {
            "hostname": "delete-test",
            "ip_address": "10.0.0.1",
            "datacenter": "us-east-1",
            "state": "active"
        }
        create_response = requests.post(f"{API_URL}/servers", json=payload)
        server_id = create_response.json()["id"]

        delete_response = requests.delete(f"{API_URL}/servers/{server_id}")
        assert delete_response.status_code == 204

        get_response = requests.get(f"{API_URL}/servers/{server_id}")
        assert get_response.status_code == 404

    def test_duplicate_hostname_rejected(self, docker_compose):
        payload = {
            "hostname": "duplicate-test",
            "ip_address": "10.0.0.1",
            "datacenter": "us-east-1",
            "state": "active"
        }
        requests.post(f"{API_URL}/servers", json=payload)

        payload["ip_address"] = "10.0.0.2"
        response = requests.post(f"{API_URL}/servers", json=payload)

        assert response.status_code == 409

    def test_invalid_ip_rejected(self, docker_compose):
        payload = {
            "hostname": "invalid-ip-test",
            "ip_address": "not-an-ip",
            "datacenter": "us-east-1",
            "state": "active"
        }

        response = requests.post(f"{API_URL}/servers", json=payload)

        assert response.status_code == 422

    def test_invalid_state_rejected(self, docker_compose):
        payload = {
            "hostname": "invalid-state-test",
            "ip_address": "10.0.0.1",
            "datacenter": "us-east-1",
            "state": "invalid"
        }

        response = requests.post(f"{API_URL}/servers", json=payload)

        assert response.status_code == 422

    def test_ipv6_support(self, docker_compose):
        payload = {
            "hostname": "ipv6-test",
            "ip_address": "2001:db8::1",
            "datacenter": "us-east-1",
            "state": "active"
        }

        response = requests.post(f"{API_URL}/servers", json=payload)

        assert response.status_code == 201
        assert response.json()["ip_address"] == "2001:db8::1"


class TestIntegrationCLI:

    def test_cli_list_empty(self, docker_compose):
        result = subprocess.run(
            ["python", "-m", "cli.main", "list"],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        assert "No servers found" in result.stdout

    def test_cli_create_and_list(self, docker_compose):
        create_result = subprocess.run(
            ["python", "-m", "cli.main", "create",
             "-n", "cli-test-server",
             "-i", "192.168.1.1",
             "-d", "us-east-1",
             "-s", "active"],
            capture_output=True,
            text=True
        )

        assert create_result.returncode == 0
        assert "created successfully" in create_result.stdout

        list_result = subprocess.run(
            ["python", "-m", "cli.main", "list"],
            capture_output=True,
            text=True
        )

        assert list_result.returncode == 0
        assert "cli-test-server" in list_result.stdout

    def test_cli_get_server(self, docker_compose):
        requests.post(f"{API_URL}/servers", json={
            "hostname": "cli-get-test",
            "ip_address": "10.0.0.1",
            "datacenter": "dc1",
            "state": "active"
        })

        list_response = requests.get(f"{API_URL}/servers")
        server_id = list_response.json()[0]["id"]

        result = subprocess.run(
            ["python", "-m", "cli.main", "get", str(server_id)],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        assert "cli-get-test" in result.stdout

    def test_cli_delete_server(self, docker_compose):
        response = requests.post(f"{API_URL}/servers", json={
            "hostname": "cli-delete-test",
            "ip_address": "10.0.0.1",
            "datacenter": "dc1",
            "state": "active"
        })
        server_id = response.json()["id"]

        result = subprocess.run(
            ["python", "-m", "cli.main", "delete", str(server_id), "-y"],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        assert "deleted successfully" in result.stdout

    def test_cli_json_output(self, docker_compose):
        requests.post(f"{API_URL}/servers", json={
            "hostname": "cli-json-test",
            "ip_address": "10.0.0.1",
            "datacenter": "dc1",
            "state": "active"
        })

        result = subprocess.run(
            ["python", "-m", "cli.main", "list", "-j"],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        import json
        data = json.loads(result.stdout)
        assert isinstance(data, list)
        assert data[0]["hostname"] == "cli-json-test"
