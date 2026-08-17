"""Minimal repair-session API — in-memory foundation only."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.models.device import Device
from app.models.repair import RepairSession
from app.services.repair_service import RepairService

router = APIRouter()

# Process-local store for early scaffolding. Replace with DI + DB later.
_repair_service = RepairService()


class CreateDeviceBody(BaseModel):
    brand: str
    model: str
    identifier: str | None = None
    color: str | None = None
    storage_gb: int | None = None
    os_version: str | None = None
    notes: str | None = None


class OpenSessionBody(BaseModel):
    device_id: str
    technician: str | None = None


@router.post("/devices", response_model=Device)
def create_device(body: CreateDeviceBody) -> Device:
    device = Device(**body.model_dump())
    return _repair_service.create_device(device)


@router.get("/devices/{device_id}", response_model=Device)
def get_device(device_id: str) -> Device:
    device = _repair_service.get_device(device_id)
    if device is None:
        raise HTTPException(status_code=404, detail="Device non trovato")
    return device


@router.post("/sessions", response_model=RepairSession)
def open_session(body: OpenSessionBody) -> RepairSession:
    try:
        return _repair_service.open_session(body.device_id, technician=body.technician)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/sessions/{session_id}", response_model=RepairSession)
def get_session(session_id: str) -> RepairSession:
    session = _repair_service.get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Sessione non trovata")
    return session


@router.get("/sessions", response_model=list[RepairSession])
def list_sessions() -> list[RepairSession]:
    return _repair_service.list_sessions()
