import logging
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query, Request, status
from psycopg2.errors import UniqueViolation
from pythonjsonlogger.json import JsonFormatter

from api.models import ServerCreate, ServerUpdate, ServerPatch, ServerResponse
from api.database import (
    init_db,
    init_pool,
    close_pool,
    create_server,
    get_all_servers,
    get_server_by_id,
    update_server,
    patch_server,
    delete_server,
    get_db,
)

handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(JsonFormatter(
    fmt="%(asctime)s %(name)s %(levelname)s %(message)s",
    rename_fields={"asctime": "timestamp", "name": "logger", "levelname": "level"},
))
logging.basicConfig(level=logging.INFO, handlers=[handler])
logging.getLogger("uvicorn").setLevel(logging.WARNING)
logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Server Inventory API")
    init_pool()
    init_db()
    logger.info("Application startup complete")
    yield
    logger.info("Shutting down application")
    close_pool()
    logger.info("Application shutdown complete")


app = FastAPI(
    title="Server Inventory API",
    description="CRUD API for managing server inventory across data centers",
    version="1.0.0",
    lifespan=lifespan,
)


@app.post("/servers", response_model=ServerResponse, status_code=status.HTTP_201_CREATED)
def create_server_endpoint(server: ServerCreate):
    logger.info("Creating server: hostname=%s, datacenter=%s", server.hostname, server.datacenter)
    try:
        result = create_server(
            hostname=server.hostname,
            ip_address=server.ip_address,
            datacenter=server.datacenter,
            state=server.state.value,
        )
        logger.info("Server created: id=%d, hostname=%s", result["id"], result["hostname"])
        return ServerResponse(**result)
    except UniqueViolation:
        logger.warning("Duplicate hostname rejected: %s", server.hostname)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Server with hostname '{server.hostname}' already exists"
        )


@app.get("/servers", response_model=list[ServerResponse])
def list_servers_endpoint(
    skip: int = Query(default=0, ge=0, description="Number of records to skip"),
    limit: int = Query(default=100, ge=1, le=1000, description="Maximum number of records to return")
):
    logger.debug("Listing servers: skip=%d, limit=%d", skip, limit)
    servers = get_all_servers(skip=skip, limit=limit)
    logger.debug("Retrieved %d servers", len(servers))
    return [ServerResponse(**s) for s in servers]


@app.get("/servers/{server_id}", response_model=ServerResponse)
def get_server_endpoint(server_id: int):
    logger.debug("Getting server: id=%d", server_id)
    server = get_server_by_id(server_id)
    if not server:
        logger.warning("Server not found: id=%d", server_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Server with id {server_id} not found"
        )
    return ServerResponse(**server)


@app.put("/servers/{server_id}", response_model=ServerResponse)
def update_server_endpoint(server_id: int, server: ServerUpdate):
    logger.info("Updating server: id=%d, hostname=%s", server_id, server.hostname)
    try:
        result = update_server(
            server_id=server_id,
            hostname=server.hostname,
            ip_address=server.ip_address,
            datacenter=server.datacenter,
            state=server.state.value,
        )
        if not result:
            logger.warning("Server not found for update: id=%d", server_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Server with id {server_id} not found"
            )
        logger.info("Server updated: id=%d", server_id)
        return ServerResponse(**result)
    except UniqueViolation:
        logger.warning("Duplicate hostname rejected on update: %s", server.hostname)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Server with hostname '{server.hostname}' already exists"
        )


@app.patch("/servers/{server_id}", response_model=ServerResponse)
def patch_server_endpoint(server_id: int, server: ServerPatch):
    update_data = {k: v.value if hasattr(v, 'value') else v for k, v in server.model_dump(exclude_unset=True).items()}
    logger.info("Patching server: id=%d, fields=%s", server_id, list(update_data.keys()))

    if not update_data:
        existing = get_server_by_id(server_id)
        if not existing:
            logger.warning("Server not found for patch: id=%d", server_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Server with id {server_id} not found"
            )
        return ServerResponse(**existing)

    try:
        result = patch_server(server_id=server_id, **update_data)
        if not result:
            logger.warning("Server not found for patch: id=%d", server_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Server with id {server_id} not found"
            )
        logger.info("Server patched: id=%d", server_id)
        return ServerResponse(**result)
    except UniqueViolation:
        logger.warning("Duplicate hostname rejected on patch: %s", server.hostname)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Server with hostname '{server.hostname}' already exists"
        )


@app.delete("/servers/{server_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_server_endpoint(server_id: int):
    logger.info("Deleting server: id=%d", server_id)
    if not delete_server(server_id):
        logger.warning("Server not found for delete: id=%d", server_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Server with id {server_id} not found"
        )
    logger.info("Server deleted: id=%d", server_id)
    return None


@app.get("/health")
def health_check():
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        logger.error("Health check failed: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database unavailable"
        )
