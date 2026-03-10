import json
import pytest
from unittest.mock import patch, MagicMock
from click.testing import CliRunner
from cli.main import cli


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def mock_server():
    return {
        "id": 1,
        "hostname": "web-server-01",
        "ip_address": "192.168.1.100",
        "datacenter": "us-east-1",
        "state": "active",
        "created_at": "2024-01-01T00:00:00",
        "updated_at": "2024-01-01T00:00:00"
    }


class TestListCommand:

    @patch("cli.main.requests.request")
    def test_list_servers_empty(self, mock_request, runner):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = []
        mock_request.return_value = mock_response

        result = runner.invoke(cli, ["list"])

        assert result.exit_code == 0
        assert "No servers found" in result.output

    @patch("cli.main.requests.request")
    def test_list_servers_with_data(self, mock_request, runner, mock_server):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [mock_server]
        mock_request.return_value = mock_response

        result = runner.invoke(cli, ["list"])

        assert result.exit_code == 0
        assert mock_server["hostname"] in result.output

    @patch("cli.main.requests.request")
    def test_list_servers_json_output(self, mock_request, runner, mock_server):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [mock_server]
        mock_request.return_value = mock_response

        result = runner.invoke(cli, ["list", "--json-output"])

        assert result.exit_code == 0
        output = json.loads(result.output)
        assert len(output) == 1
        assert output[0]["hostname"] == mock_server["hostname"]

    @patch("cli.main.requests.request")
    def test_list_servers_with_pagination(self, mock_request, runner, mock_server):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [mock_server]
        mock_request.return_value = mock_response

        result = runner.invoke(cli, ["list", "--skip", "10", "--limit", "50"])

        assert result.exit_code == 0
        call_kwargs = mock_request.call_args[1]
        assert call_kwargs["params"]["skip"] == 10
        assert call_kwargs["params"]["limit"] == 50


class TestGetCommand:

    @patch("cli.main.requests.request")
    def test_get_server_success(self, mock_request, runner, mock_server):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_server
        mock_request.return_value = mock_response

        result = runner.invoke(cli, ["get", "1"])

        assert result.exit_code == 0
        assert mock_server["hostname"] in result.output

    @patch("cli.main.requests.request")
    def test_get_server_not_found(self, mock_request, runner):
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.json.return_value = {"detail": "Server not found"}
        mock_request.return_value = mock_response

        result = runner.invoke(cli, ["get", "999"])

        assert result.exit_code == 1
        assert "Server not found" in result.output

    @patch("cli.main.requests.request")
    def test_get_server_json_output(self, mock_request, runner, mock_server):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_server
        mock_request.return_value = mock_response

        result = runner.invoke(cli, ["get", "1", "--json-output"])

        assert result.exit_code == 0
        output = json.loads(result.output)
        assert output["hostname"] == mock_server["hostname"]


class TestCreateCommand:

    @patch("cli.main.requests.request")
    def test_create_server_success(self, mock_request, runner, mock_server):
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = mock_server
        mock_request.return_value = mock_response

        result = runner.invoke(cli, [
            "create",
            "--hostname", "web-server-01",
            "--ip-address", "192.168.1.100",
            "--datacenter", "us-east-1",
            "--state", "active"
        ])

        assert result.exit_code == 0
        assert "created successfully" in result.output

    @patch("cli.main.requests.request")
    def test_create_server_with_short_options(self, mock_request, runner, mock_server):
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = mock_server
        mock_request.return_value = mock_response

        result = runner.invoke(cli, [
            "create",
            "-n", "web-server-01",
            "-i", "192.168.1.100",
            "-d", "us-east-1",
            "-s", "active"
        ])

        assert result.exit_code == 0
        assert "created successfully" in result.output

    @patch("cli.main.requests.request")
    def test_create_server_duplicate(self, mock_request, runner):
        mock_response = MagicMock()
        mock_response.status_code = 409
        mock_response.json.return_value = {"detail": "hostname already exists"}
        mock_request.return_value = mock_response

        result = runner.invoke(cli, [
            "create",
            "--hostname", "web-server-01",
            "--ip-address", "192.168.1.100",
            "--datacenter", "us-east-1",
            "--state", "active"
        ])

        assert result.exit_code == 1
        assert "already exists" in result.output

    def test_create_server_missing_required(self, runner):
        result = runner.invoke(cli, ["create", "--hostname", "test"])

        assert result.exit_code != 0


class TestUpdateCommand:

    @patch("cli.main.requests.request")
    def test_update_server_success(self, mock_request, runner, mock_server):
        mock_server["state"] = "offline"
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_server
        mock_request.return_value = mock_response

        result = runner.invoke(cli, [
            "update", "1",
            "--hostname", "web-server-01",
            "--ip-address", "192.168.1.100",
            "--datacenter", "us-east-1",
            "--state", "offline"
        ])

        assert result.exit_code == 0
        assert "updated successfully" in result.output

    @patch("cli.main.requests.request")
    def test_update_server_not_found(self, mock_request, runner):
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.json.return_value = {"detail": "Server not found"}
        mock_request.return_value = mock_response

        result = runner.invoke(cli, [
            "update", "999",
            "--hostname", "test",
            "--ip-address", "192.168.1.1",
            "--datacenter", "us-east-1",
            "--state", "active"
        ])

        assert result.exit_code == 1


class TestPatchCommand:

    @patch("cli.main.requests.request")
    def test_patch_server_single_field(self, mock_request, runner, mock_server):
        mock_server["state"] = "offline"
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_server
        mock_request.return_value = mock_response

        result = runner.invoke(cli, [
            "patch", "1",
            "--state", "offline"
        ])

        assert result.exit_code == 0
        assert "updated successfully" in result.output
        call_kwargs = mock_request.call_args[1]
        assert call_kwargs["json"] == {"state": "offline"}

    @patch("cli.main.requests.request")
    def test_patch_server_multiple_fields(self, mock_request, runner, mock_server):
        mock_server["state"] = "retired"
        mock_server["datacenter"] = "eu-west-1"
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_server
        mock_request.return_value = mock_response

        result = runner.invoke(cli, [
            "patch", "1",
            "--state", "retired",
            "--datacenter", "eu-west-1"
        ])

        assert result.exit_code == 0
        call_kwargs = mock_request.call_args[1]
        assert call_kwargs["json"] == {"state": "retired", "datacenter": "eu-west-1"}

    def test_patch_server_no_fields(self, runner):
        result = runner.invoke(cli, ["patch", "1"])

        assert result.exit_code == 1
        assert "At least one field" in result.output

    @patch("cli.main.requests.request")
    def test_patch_server_not_found(self, mock_request, runner):
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.json.return_value = {"detail": "Server not found"}
        mock_request.return_value = mock_response

        result = runner.invoke(cli, [
            "patch", "999",
            "--state", "offline"
        ])

        assert result.exit_code == 1


class TestDeleteCommand:

    @patch("cli.main.requests.request")
    def test_delete_server_success(self, mock_request, runner):
        mock_response = MagicMock()
        mock_response.status_code = 204
        mock_request.return_value = mock_response

        result = runner.invoke(cli, ["delete", "1", "--yes"])

        assert result.exit_code == 0
        assert "deleted successfully" in result.output

    @patch("cli.main.requests.request")
    def test_delete_server_not_found(self, mock_request, runner):
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.json.return_value = {"detail": "Server not found"}
        mock_request.return_value = mock_response

        result = runner.invoke(cli, ["delete", "999", "--yes"])

        assert result.exit_code == 1

    def test_delete_server_confirmation_abort(self, runner):
        result = runner.invoke(cli, ["delete", "1"], input="n\n")

        assert result.exit_code != 0


class TestConnectionError:

    @patch("cli.main.requests.request")
    def test_connection_error(self, mock_request, runner):
        import requests
        mock_request.side_effect = requests.exceptions.ConnectionError()

        result = runner.invoke(cli, ["list"])

        assert result.exit_code == 1
        assert "Could not connect" in result.output

    @patch("cli.main.requests.request")
    def test_connect_timeout(self, mock_request, runner):
        import requests
        mock_request.side_effect = requests.exceptions.ConnectTimeout()

        result = runner.invoke(cli, ["list"])

        assert result.exit_code == 1
        assert "Connection timed out" in result.output

    @patch("cli.main.requests.request")
    def test_read_timeout(self, mock_request, runner):
        import requests
        mock_request.side_effect = requests.exceptions.ReadTimeout()

        result = runner.invoke(cli, ["list"])

        assert result.exit_code == 1
        assert "Request timed out" in result.output


class TestApiUrlOption:

    @patch("cli.main.requests.request")
    def test_custom_api_url(self, mock_request, runner):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = []
        mock_request.return_value = mock_response

        result = runner.invoke(cli, ["--api-url", "http://custom:9000", "list"])

        assert result.exit_code == 0
        mock_request.assert_called_once()
        call_args = mock_request.call_args
        assert "http://custom:9000" in call_args[0][1]


class TestTimeoutOption:

    @patch("cli.main.requests.request")
    def test_custom_timeout(self, mock_request, runner):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = []
        mock_request.return_value = mock_response

        result = runner.invoke(cli, ["--timeout", "60", "list"])

        assert result.exit_code == 0
        call_kwargs = mock_request.call_args[1]
        assert call_kwargs["timeout"] == (5, 60)


class TestVerboseOption:

    @patch("cli.main.requests.request")
    def test_verbose_output(self, mock_request, runner):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = []
        mock_request.return_value = mock_response

        result = runner.invoke(cli, ["--verbose", "list"])

        assert result.exit_code == 0
