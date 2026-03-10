import pytest
from concurrent.futures import ThreadPoolExecutor, as_completed


class TestCreateServer:

    def test_create_server_success(self, client, sample_server):
        response = client.post("/servers", json=sample_server)

        assert response.status_code == 201
        data = response.json()
        assert data["hostname"] == sample_server["hostname"]
        assert data["ip_address"] == sample_server["ip_address"]
        assert data["datacenter"] == sample_server["datacenter"]
        assert data["state"] == sample_server["state"]
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data

    def test_create_server_duplicate_hostname(self, client, sample_server):
        client.post("/servers", json=sample_server)
        response = client.post("/servers", json=sample_server)

        assert response.status_code == 409
        assert "already exists" in response.json()["detail"]

    def test_create_server_invalid_ip(self, client, sample_server):
        sample_server["ip_address"] = "invalid-ip"
        response = client.post("/servers", json=sample_server)

        assert response.status_code == 422

    def test_create_server_invalid_state(self, client, sample_server):
        sample_server["state"] = "invalid-state"
        response = client.post("/servers", json=sample_server)

        assert response.status_code == 422

    def test_create_server_ipv6(self, client, sample_server):
        sample_server["ip_address"] = "2001:0db8:85a3:0000:0000:8a2e:0370:7334"
        response = client.post("/servers", json=sample_server)

        assert response.status_code == 201
        assert response.json()["ip_address"] == sample_server["ip_address"]

    def test_create_server_missing_fields(self, client):
        response = client.post("/servers", json={"hostname": "test"})

        assert response.status_code == 422


class TestListServers:

    def test_list_servers_empty(self, client):
        response = client.get("/servers")

        assert response.status_code == 200
        assert response.json() == []

    def test_list_servers_with_data(self, client, sample_server):
        client.post("/servers", json=sample_server)

        sample_server2 = sample_server.copy()
        sample_server2["hostname"] = "web-server-02"
        sample_server2["ip_address"] = "192.168.1.101"
        client.post("/servers", json=sample_server2)

        response = client.get("/servers")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    def test_list_servers_pagination(self, client, sample_server):
        # Create multiple servers
        for i in range(5):
            server = sample_server.copy()
            server["hostname"] = f"web-server-{i:02d}"
            server["ip_address"] = f"192.168.1.{100 + i}"
            client.post("/servers", json=server)

        # Test limit
        response = client.get("/servers?limit=2")
        assert response.status_code == 200
        assert len(response.json()) == 2

        # Test skip
        response = client.get("/servers?skip=3")
        assert response.status_code == 200
        assert len(response.json()) == 2

        # Test skip and limit
        response = client.get("/servers?skip=1&limit=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["hostname"] == "web-server-01"

    def test_list_servers_pagination_validation(self, client):
        # Test invalid skip
        response = client.get("/servers?skip=-1")
        assert response.status_code == 422

        # Test invalid limit
        response = client.get("/servers?limit=0")
        assert response.status_code == 422

        # Test limit exceeds max
        response = client.get("/servers?limit=1001")
        assert response.status_code == 422


class TestGetServer:

    def test_get_server_success(self, client, created_server):
        response = client.get(f"/servers/{created_server['id']}")

        assert response.status_code == 200
        assert response.json()["hostname"] == created_server["hostname"]

    def test_get_server_not_found(self, client):
        response = client.get("/servers/99999")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"]


class TestUpdateServer:

    def test_update_server_success(self, client, created_server):
        updated_data = {
            "hostname": "updated-hostname",
            "ip_address": "10.0.0.1",
            "datacenter": "us-west-2",
            "state": "offline"
        }
        response = client.put(f"/servers/{created_server['id']}", json=updated_data)

        assert response.status_code == 200
        data = response.json()
        assert data["hostname"] == "updated-hostname"
        assert data["ip_address"] == "10.0.0.1"
        assert data["datacenter"] == "us-west-2"
        assert data["state"] == "offline"

    def test_update_server_not_found(self, client, sample_server):
        response = client.put("/servers/99999", json=sample_server)

        assert response.status_code == 404

    def test_update_server_duplicate_hostname(self, client, sample_server):
        client.post("/servers", json=sample_server)

        sample_server2 = sample_server.copy()
        sample_server2["hostname"] = "web-server-02"
        sample_server2["ip_address"] = "192.168.1.101"
        response2 = client.post("/servers", json=sample_server2)
        server2_id = response2.json()["id"]

        sample_server2["hostname"] = sample_server["hostname"]
        response = client.put(f"/servers/{server2_id}", json=sample_server2)

        assert response.status_code == 409

    def test_update_server_same_hostname(self, client, created_server):
        updated_data = {
            "hostname": created_server["hostname"],
            "ip_address": "10.0.0.1",
            "datacenter": "us-west-2",
            "state": "offline"
        }
        response = client.put(f"/servers/{created_server['id']}", json=updated_data)

        assert response.status_code == 200


class TestPatchServer:

    def test_patch_server_single_field(self, client, created_server):
        response = client.patch(f"/servers/{created_server['id']}", json={"state": "offline"})

        assert response.status_code == 200
        data = response.json()
        assert data["state"] == "offline"
        assert data["hostname"] == created_server["hostname"]
        assert data["ip_address"] == created_server["ip_address"]

    def test_patch_server_multiple_fields(self, client, created_server):
        response = client.patch(
            f"/servers/{created_server['id']}",
            json={"state": "retired", "datacenter": "eu-west-1"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["state"] == "retired"
        assert data["datacenter"] == "eu-west-1"
        assert data["hostname"] == created_server["hostname"]

    def test_patch_server_not_found(self, client):
        response = client.patch("/servers/99999", json={"state": "offline"})

        assert response.status_code == 404

    def test_patch_server_duplicate_hostname(self, client, sample_server):
        client.post("/servers", json=sample_server)

        sample_server2 = sample_server.copy()
        sample_server2["hostname"] = "web-server-02"
        sample_server2["ip_address"] = "192.168.1.101"
        response2 = client.post("/servers", json=sample_server2)
        server2_id = response2.json()["id"]

        response = client.patch(
            f"/servers/{server2_id}",
            json={"hostname": sample_server["hostname"]}
        )

        assert response.status_code == 409

    def test_patch_server_empty_body(self, client, created_server):
        response = client.patch(f"/servers/{created_server['id']}", json={})

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == created_server["id"]

    def test_patch_server_invalid_field(self, client, created_server):
        response = client.patch(
            f"/servers/{created_server['id']}",
            json={"ip_address": "invalid-ip"}
        )

        assert response.status_code == 422


class TestDeleteServer:

    def test_delete_server_success(self, client, created_server):
        response = client.delete(f"/servers/{created_server['id']}")

        assert response.status_code == 204

        get_response = client.get(f"/servers/{created_server['id']}")
        assert get_response.status_code == 404

    def test_delete_server_not_found(self, client):
        response = client.delete("/servers/99999")

        assert response.status_code == 404


class TestValidation:

    def test_valid_states(self, client, sample_server):
        for state in ["active", "offline", "retired"]:
            sample_server["state"] = state
            sample_server["hostname"] = f"server-{state}"
            response = client.post("/servers", json=sample_server)
            assert response.status_code == 201

    def test_valid_ipv4_addresses(self, client, sample_server):
        valid_ips = ["0.0.0.0", "255.255.255.255", "192.168.1.1", "10.0.0.1"]
        for i, ip in enumerate(valid_ips):
            sample_server["ip_address"] = ip
            sample_server["hostname"] = f"server-ipv4-{i}"
            response = client.post("/servers", json=sample_server)
            assert response.status_code == 201

    def test_valid_ipv6_addresses(self, client, sample_server):
        valid_ips = [
            "::1",
            "fe80::1",
            "2001:db8::1",
            "2001:0db8:85a3:0000:0000:8a2e:0370:7334"
        ]
        for i, ip in enumerate(valid_ips):
            sample_server["ip_address"] = ip
            sample_server["hostname"] = f"server-ipv6-{i}"
            response = client.post("/servers", json=sample_server)
            assert response.status_code == 201

    def test_valid_hostnames(self, client, sample_server):
        valid_hostnames = [
            "a",
            "server1",
            "web-server",
            "app.example.com",
            "db-01.us-east-1.example.com",
        ]
        for i, hostname in enumerate(valid_hostnames):
            sample_server["hostname"] = hostname
            sample_server["ip_address"] = f"10.0.0.{i + 1}"
            response = client.post("/servers", json=sample_server)
            assert response.status_code == 201, f"Failed for hostname: {hostname}"

    def test_invalid_hostnames(self, client, sample_server):
        invalid_hostnames = [
            "-server",
            "server-",
            ".server",
            "server.",
            "server..name",
            "ser ver",
            "a" * 256,
        ]
        for hostname in invalid_hostnames:
            sample_server["hostname"] = hostname
            response = client.post("/servers", json=sample_server)
            assert response.status_code == 422, f"Should fail for hostname: {hostname}"


class TestHealthCheck:

    def test_health_check(self, client):
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["database"] == "connected"


class TestConcurrency:
    """Test concurrent access to prevent race conditions."""

    def test_concurrent_create_different_hostnames(self, client, sample_server):
        """Multiple threads creating servers with different hostnames should all succeed."""
        def create_server(index):
            server = sample_server.copy()
            server["hostname"] = f"concurrent-server-{index}"
            server["ip_address"] = f"10.0.0.{index}"
            return client.post("/servers", json=server)

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(create_server, i) for i in range(10)]
            results = [f.result() for f in as_completed(futures)]

        success_count = sum(1 for r in results if r.status_code == 201)
        assert success_count == 10

    def test_concurrent_create_same_hostname(self, client, sample_server):
        """Multiple threads creating servers with the same hostname - exactly one should succeed."""
        def create_server():
            server = sample_server.copy()
            server["hostname"] = "race-condition-test"
            return client.post("/servers", json=server)

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(create_server) for _ in range(5)]
            results = [f.result() for f in as_completed(futures)]

        success_count = sum(1 for r in results if r.status_code == 201)
        conflict_count = sum(1 for r in results if r.status_code == 409)

        assert success_count == 1
        assert conflict_count == 4

    def test_concurrent_reads(self, client, created_server):
        """Multiple concurrent reads should all succeed."""
        def read_server():
            return client.get(f"/servers/{created_server['id']}")

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(read_server) for _ in range(10)]
            results = [f.result() for f in as_completed(futures)]

        assert all(r.status_code == 200 for r in results)
        assert all(r.json()["id"] == created_server["id"] for r in results)
