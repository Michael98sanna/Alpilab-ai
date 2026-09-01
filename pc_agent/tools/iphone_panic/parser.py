"""Parse Apple .ips panic log files into structured documents."""

from __future__ import annotations

import hashlib
import json
import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .models import PanicLogDocument, PanicLogMetadata, PanicLogPayload

logger = logging.getLogger(__name__)


class IPhonePanicParser:
    """Parse .ips format (Apple crash log)."""

    async def parse_file(self, file_path: str) -> PanicLogDocument | None:
        """
        Read .ips file and return PanicLogDocument.

        Format:
        - Line 1: JSON metadata
        - Line 2+: JSON payload
        """
        try:
            file_path_obj = Path(file_path)
            if not file_path_obj.is_file():
                logger.error("File not found: %s", file_path)
                return None

            lines = file_path_obj.read_text(encoding="utf-8").splitlines()
            if len(lines) < 2:
                logger.error("Invalid .ips format: %s (< 2 lines)", file_path)
                return None

            try:
                metadata_dict = json.loads(lines[0])
            except json.JSONDecodeError as exc:
                logger.error("Invalid metadata JSON: %s", exc)
                return None

            payload_text = "\n".join(lines[1:])
            try:
                payload_dict = json.loads(payload_text)
            except json.JSONDecodeError as exc:
                logger.error("Invalid payload JSON: %s", exc)
                return None

            metadata = PanicLogMetadata(
                bug_type=str(metadata_dict.get("bug_type", "unknown")),
                timestamp=str(metadata_dict.get("timestamp", "")),
                os_version=str(metadata_dict.get("os_version", "")),
                incident_id=str(metadata_dict.get("incident_id", "")),
                model_code=str(metadata_dict.get("model_code", "")),
                build_version=str(metadata_dict.get("build_version", "")),
                process_name=metadata_dict.get("process_name"),
                bundle_id=metadata_dict.get("bundle_id"),
                app_version=metadata_dict.get("app_version"),
            )

            panic_string = str(payload_dict.get("panicString", ""))
            payload = PanicLogPayload(
                panic_string=panic_string,
                process_by_pid=payload_dict.get("processByPid") or {},
                binary_images=payload_dict.get("binaryImages") or [],
                memory_status=payload_dict.get("memoryStatus"),
                raw_content=json.dumps(payload_dict),
            )

            file_hash = self._compute_hash(payload_text)
            doc = PanicLogDocument(
                metadata=metadata,
                payload=payload,
                file_hash=file_hash,
                parsed_at=datetime.now(timezone.utc),
            )
            logger.info(
                "Parsed .ips: %s (%s)",
                metadata.model_code or "unknown-model",
                metadata.bug_type,
            )
            return doc
        except Exception as exc:
            logger.error("Error parsing .ips file: %s", exc)
            return None

    def _compute_hash(self, content: str) -> str:
        """SHA-256 of payload JSON text."""
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def _extract_panic_signature(self, panic_string: str) -> str | None:
        """Extract short signature from panic_string."""
        patterns = [
            r"(SMC PANIC[^\n]*)",
            r"(NAND[^\n]*)",
            r"(ANS[^\n]*)",
            r"(kernel panic[^\n]*)",
        ]
        for pattern in patterns:
            match = re.search(pattern, panic_string, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return None

    def _extract_error_code(self, panic_string: str) -> str | None:
        """Extract hex code (e.g. 0x800)."""
        match = re.search(r"(0x[a-fA-F0-9]+)", panic_string)
        return match.group(1) if match else None

    def metadata_fields(self, metadata_dict: dict[str, Any]) -> dict[str, Any]:
        """Helper for tests — expose normalized metadata keys."""
        return {
            "bug_type": metadata_dict.get("bug_type"),
            "model_code": metadata_dict.get("model_code"),
        }
