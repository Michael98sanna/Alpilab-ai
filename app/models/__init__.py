"""Domain models shared as a contract between Alpilab AI, Alpilab Check, and Alpilab Hub."""

from .common import SourceSystem, utcnow
from .device import Device, DeviceIdentifierType
from .repair import (
    CustomerIssue,
    Diagnosis,
    DiagnosticStatus,
    DiagnosticTest,
    ImageAnnotation,
    ImageAttachment,
    ImageKind,
    Measurement,
    MeasurementKind,
    Note,
    RepairAction,
    RepairActionStatus,
    RepairResult,
    RepairSession,
    RepairSessionStatus,
)

__all__ = [
    "SourceSystem",
    "utcnow",
    "Device",
    "DeviceIdentifierType",
    "CustomerIssue",
    "Diagnosis",
    "DiagnosticStatus",
    "DiagnosticTest",
    "ImageAnnotation",
    "ImageAttachment",
    "ImageKind",
    "Measurement",
    "MeasurementKind",
    "Note",
    "RepairAction",
    "RepairActionStatus",
    "RepairResult",
    "RepairSession",
    "RepairSessionStatus",
]
