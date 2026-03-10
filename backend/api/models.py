from datetime import datetime
from enum import Enum
from pydantic import BaseModel, field_validator
from api.validators import validate_ip_address, validate_hostname


class ServerState(str, Enum):
    active = "active"
    offline = "offline"
    retired = "retired"


class ServerBase(BaseModel):
    """Base model with shared validation logic."""
    hostname: str
    ip_address: str
    datacenter: str
    state: ServerState

    @field_validator("hostname")
    @classmethod
    def hostname_must_be_valid(cls, v: str) -> str:
        if not validate_hostname(v):
            raise ValueError("Invalid hostname format")
        return v

    @field_validator("ip_address")
    @classmethod
    def ip_must_be_valid(cls, v: str) -> str:
        if not validate_ip_address(v):
            raise ValueError("Invalid IP address format")
        return v


class ServerCreate(ServerBase):
    """Request model for creating a server."""
    pass


class ServerUpdate(ServerBase):
    """Request model for full server update (PUT)."""
    pass


class ServerPatch(BaseModel):
    """Request model for partial server update (PATCH)."""
    hostname: str | None = None
    ip_address: str | None = None
    datacenter: str | None = None
    state: ServerState | None = None

    @field_validator("hostname")
    @classmethod
    def hostname_must_be_valid(cls, v: str | None) -> str | None:
        if v is not None and not validate_hostname(v):
            raise ValueError("Invalid hostname format")
        return v

    @field_validator("ip_address")
    @classmethod
    def ip_must_be_valid(cls, v: str | None) -> str | None:
        if v is not None and not validate_ip_address(v):
            raise ValueError("Invalid IP address format")
        return v


class ServerResponse(BaseModel):
    """Response model for server data."""
    model_config = {"from_attributes": True}

    id: int
    hostname: str
    ip_address: str
    datacenter: str
    state: ServerState
    created_at: datetime
    updated_at: datetime
