#!/usr/bin/env python3
import os
import sys
import json
import logging
import click
import requests

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

API_URL = os.getenv("API_URL", "http://localhost:8000")
DEFAULT_TIMEOUT = int(os.getenv("CLI_TIMEOUT", "30"))


def format_server(server: dict) -> str:
    return (
        f"ID: {server['id']}\n"
        f"  Hostname:   {server['hostname']}\n"
        f"  IP Address: {server['ip_address']}\n"
        f"  Datacenter: {server['datacenter']}\n"
        f"  State:      {server['state']}\n"
        f"  Created:    {server['created_at']}\n"
        f"  Updated:    {server['updated_at']}"
    )


def handle_error(response: requests.Response):
    try:
        detail = response.json().get("detail", response.text)
    except json.JSONDecodeError:
        detail = response.text
    click.echo(f"Error: {detail}", err=True)
    sys.exit(1)


def make_request(method: str, url: str, timeout: int, **kwargs) -> requests.Response:
    """Make HTTP request with proper timeout handling."""
    # Use tuple for (connect_timeout, read_timeout)
    timeout_tuple = (min(5, timeout), timeout)
    try:
        logger.debug("Making %s request to %s", method.upper(), url)
        return requests.request(method, url, timeout=timeout_tuple, **kwargs)
    except requests.exceptions.ConnectTimeout:
        click.echo("Error: Connection timed out", err=True)
        sys.exit(1)
    except requests.exceptions.ReadTimeout:
        click.echo("Error: Request timed out waiting for response", err=True)
        sys.exit(1)
    except requests.exceptions.ConnectionError:
        click.echo("Error: Could not connect to API", err=True)
        sys.exit(1)


@click.group()
@click.option("--api-url", envvar="API_URL", default="http://localhost:8000", help="API base URL")
@click.option("--timeout", "-t", envvar="CLI_TIMEOUT", default=DEFAULT_TIMEOUT, type=int,
              help="Request timeout in seconds")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
@click.pass_context
def cli(ctx, api_url, timeout, verbose):
    ctx.ensure_object(dict)
    ctx.obj["api_url"] = api_url
    ctx.obj["timeout"] = timeout
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)


@cli.command("list")
@click.option("--json-output", "-j", is_flag=True, help="Output as JSON")
@click.option("--skip", default=0, type=int, help="Number of records to skip")
@click.option("--limit", default=100, type=int, help="Maximum number of records to return")
@click.pass_context
def list_servers(ctx, json_output, skip, limit):
    api_url = ctx.obj["api_url"]
    timeout = ctx.obj["timeout"]

    params = {"skip": skip, "limit": limit}
    response = make_request("get", f"{api_url}/servers", timeout, params=params)

    if response.status_code != 200:
        handle_error(response)

    servers = response.json()

    if json_output:
        click.echo(json.dumps(servers, indent=2))
    elif not servers:
        click.echo("No servers found.")
    else:
        for server in servers:
            click.echo(format_server(server))
            click.echo()


@cli.command("get")
@click.argument("server_id", type=int)
@click.option("--json-output", "-j", is_flag=True, help="Output as JSON")
@click.pass_context
def get_server(ctx, server_id, json_output):
    api_url = ctx.obj["api_url"]
    timeout = ctx.obj["timeout"]

    response = make_request("get", f"{api_url}/servers/{server_id}", timeout)

    if response.status_code != 200:
        handle_error(response)

    server = response.json()

    if json_output:
        click.echo(json.dumps(server, indent=2))
    else:
        click.echo(format_server(server))


@cli.command("create")
@click.option("--hostname", "-n", required=True, help="Server hostname")
@click.option("--ip-address", "-i", required=True, help="Server IP address")
@click.option("--datacenter", "-d", required=True, help="Data center location")
@click.option("--state", "-s", type=click.Choice(["active", "offline", "retired"]),
              default="active", help="Server state")
@click.option("--json-output", "-j", is_flag=True, help="Output as JSON")
@click.pass_context
def create_server(ctx, hostname, ip_address, datacenter, state, json_output):
    api_url = ctx.obj["api_url"]
    timeout = ctx.obj["timeout"]
    payload = {
        "hostname": hostname,
        "ip_address": ip_address,
        "datacenter": datacenter,
        "state": state,
    }

    logger.info("Creating server: %s", hostname)
    response = make_request("post", f"{api_url}/servers", timeout, json=payload)

    if response.status_code != 201:
        handle_error(response)

    server = response.json()
    logger.info("Server created with ID: %d", server["id"])

    if json_output:
        click.echo(json.dumps(server, indent=2))
    else:
        click.echo("Server created successfully:")
        click.echo(format_server(server))


@cli.command("update")
@click.argument("server_id", type=int)
@click.option("--hostname", "-n", required=True, help="Server hostname")
@click.option("--ip-address", "-i", required=True, help="Server IP address")
@click.option("--datacenter", "-d", required=True, help="Data center location")
@click.option("--state", "-s", type=click.Choice(["active", "offline", "retired"]),
              required=True, help="Server state")
@click.option("--json-output", "-j", is_flag=True, help="Output as JSON")
@click.pass_context
def update_server(ctx, server_id, hostname, ip_address, datacenter, state, json_output):
    api_url = ctx.obj["api_url"]
    timeout = ctx.obj["timeout"]
    payload = {
        "hostname": hostname,
        "ip_address": ip_address,
        "datacenter": datacenter,
        "state": state,
    }

    logger.info("Updating server %d", server_id)
    response = make_request("put", f"{api_url}/servers/{server_id}", timeout, json=payload)

    if response.status_code != 200:
        handle_error(response)

    server = response.json()
    logger.info("Server %d updated successfully", server_id)

    if json_output:
        click.echo(json.dumps(server, indent=2))
    else:
        click.echo("Server updated successfully:")
        click.echo(format_server(server))


@cli.command("patch")
@click.argument("server_id", type=int)
@click.option("--hostname", "-n", help="Server hostname")
@click.option("--ip-address", "-i", help="Server IP address")
@click.option("--datacenter", "-d", help="Data center location")
@click.option("--state", "-s", type=click.Choice(["active", "offline", "retired"]),
              help="Server state")
@click.option("--json-output", "-j", is_flag=True, help="Output as JSON")
@click.pass_context
def patch_server(ctx, server_id, hostname, ip_address, datacenter, state, json_output):
    api_url = ctx.obj["api_url"]
    timeout = ctx.obj["timeout"]

    payload = {}
    if hostname is not None:
        payload["hostname"] = hostname
    if ip_address is not None:
        payload["ip_address"] = ip_address
    if datacenter is not None:
        payload["datacenter"] = datacenter
    if state is not None:
        payload["state"] = state

    if not payload:
        click.echo("Error: At least one field must be specified for update", err=True)
        sys.exit(1)

    logger.info("Patching server %d with fields: %s", server_id, list(payload.keys()))
    response = make_request("patch", f"{api_url}/servers/{server_id}", timeout, json=payload)

    if response.status_code != 200:
        handle_error(response)

    server = response.json()
    logger.info("Server %d patched successfully", server_id)

    if json_output:
        click.echo(json.dumps(server, indent=2))
    else:
        click.echo("Server updated successfully:")
        click.echo(format_server(server))


@cli.command("delete")
@click.argument("server_id", type=int)
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation")
@click.pass_context
def delete_server(ctx, server_id, yes):
    api_url = ctx.obj["api_url"]
    timeout = ctx.obj["timeout"]

    if not yes:
        click.confirm(f"Are you sure you want to delete server {server_id}?", abort=True)

    logger.info("Deleting server %d", server_id)
    response = make_request("delete", f"{api_url}/servers/{server_id}", timeout)

    if response.status_code != 204:
        handle_error(response)

    logger.info("Server %d deleted successfully", server_id)
    click.echo(f"Server {server_id} deleted successfully.")


def main():
    cli(obj={})


if __name__ == "__main__":
    main()
