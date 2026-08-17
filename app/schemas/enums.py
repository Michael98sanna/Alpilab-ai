"""Shared enums used across repair data schemas."""

from enum import Enum


class RepairSessionStatus(str, Enum):
    """Lifecycle status of a repair session."""

    OPEN = "open"
    IN_PROGRESS = "in_progress"
    WAITING_PARTS = "waiting_parts"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class DiagnosticTestStatus(str, Enum):
    """Execution status of a diagnostic test."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    INVALID = "invalid"


class SessionMode(str, Enum):
    """Repair session interaction mode."""

    GUIDED = "guided"
    FREE = "free"


class SessionFlowState(str, Enum):
    """Guided diagnostic flow control state."""

    ACTIVE = "active"
    PAUSED = "paused"
    STOPPED = "stopped"
    RESUMED = "resumed"


class EvidenceKind(str, Enum):
    """Kind of diagnostic evidence."""

    OBSERVATION = "observation"
    MEASUREMENT = "measurement"
    HYPOTHESIS = "hypothesis"
    DIAGNOSIS = "diagnosis"


class ClientPlatform(str, Enum):
    """Client device platform."""

    WINDOWS = "windows"
    ANDROID = "android"
    IOS = "ios"
    WEB = "web"
    UNKNOWN = "unknown"


class MessageChannel(str, Enum):
    """Origin channel of a conversation message."""

    TEXT = "text"
    VOICE = "voice"
    SYSTEM = "system"
    COMMAND = "command"


class IntentType(str, Enum):
    """Parsed user intent categories."""

    CONVERSATION = "conversation"
    OPEN_TOOL = "open_tool"
    OPEN_APPLICATION = "open_application"
    CLOSE_TOOL = "close_tool"
    CAPTURE_IMAGE = "capture_image"
    SAVE_MEASUREMENT = "save_measurement"
    SHOW_SCHEMA = "show_schema"
    CONTINUE_DIAGNOSIS = "continue_diagnosis"
    STOP = "stop"
    PAUSE = "pause"
    RESUME = "resume"
    RESET_DIAGNOSTIC_FLOW = "reset_diagnostic_flow"
    UNKNOWN = "unknown"


class ActionRiskLevel(str, Enum):
    """Risk classification for actions."""

    READ_ONLY = "read_only"
    SAFE = "safe"
    CONFIRM_REQUIRED = "confirm_required"
    DANGEROUS = "dangerous"


class ToolStatus(str, Enum):
    """Lifecycle status of a bench tool."""

    UNKNOWN = "unknown"
    AVAILABLE = "available"
    OPEN = "open"
    BUSY = "busy"
    ERROR = "error"
    DISCONNECTED = "disconnected"


class ToolType(str, Enum):
    """Categories of tools integrated via Hub or software bridges."""

    MICROSCOPE = "microscope"
    THERMAL_CAMERA = "thermal_camera"
    MULTIMETER = "multimeter"
    POWER_SUPPLY = "power_supply"
    SOFTWARE_3UTOOLS = "3utools"
    SOFTWARE_BORNEO = "borneo"
    SOFTWARE_ZXW = "zxw"
    ALPILAB_CHECK = "alpilab_check"
    GENERIC = "generic"


class DiagnosisConfidence(str, Enum):
    """Confidence level for a diagnosis."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CONFIRMED = "confirmed"


class RepairResultStatus(str, Enum):
    """Outcome of a repair attempt."""

    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"
    NOT_ATTEMPTED = "not_attempted"


class ImageAttachmentKind(str, Enum):
    """Category of an attached image."""

    BEFORE = "before"
    AFTER = "after"
    MICROSCOPE = "microscope"
    THERMAL = "thermal"
    BOARDVIEW = "boardview"
    OTHER = "other"
