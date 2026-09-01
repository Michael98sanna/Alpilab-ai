"""Orchestrate iPhone panic log check and analyze flows."""

from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .analyzer import IPhonePanicAnalyzer
from .collector import PanicLogCollector
from .device_probe import iOSDeviceProbe
from .models import AnalysisFindings, to_dict
from .parser import IPhonePanicParser

logger = logging.getLogger(__name__)


class IPhonePanicService:
    """Main orchestrator for panic log operations."""

    def __init__(self, cache_dir: Path | None = None) -> None:
        self.cache_dir = cache_dir or Path.home() / ".alpilab" / "iphone_panic"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.probe = iOSDeviceProbe()
        self.collector = PanicLogCollector()
        self.parser = IPhonePanicParser()
        self.analyzer = IPhonePanicAnalyzer()

    async def check(self) -> dict[str, Any]:
        """Verify device connection and locate latest panic log."""
        try:
            device_info = await self.probe.probe_device()
            if not device_info:
                return {
                    "status": "no_device",
                    "device_id": None,
                    "error_message": "No iOS device found",
                }

            panic_file = await self.collector.collect_latest(device_info["device_id"])
            if not panic_file:
                return {
                    "status": "no_panic",
                    "device_id": device_info["device_id"],
                    "device_name": device_info["device_name"],
                    "ios_version": device_info["ios_version"],
                    "model": device_info["model"],
                    "error_message": "No panic log found",
                }

            content = panic_file.read_text(encoding="utf-8")
            file_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
            cached = self._cache_read(file_hash) is not None

            return {
                "status": "success",
                "device_id": device_info["device_id"],
                "device_name": device_info["device_name"],
                "ios_version": device_info["ios_version"],
                "model": device_info["model"],
                "panic_log_filename": panic_file.name,
                "panic_timestamp": datetime.fromtimestamp(
                    panic_file.stat().st_mtime,
                    tz=timezone.utc,
                ).isoformat(),
                "file_hash": file_hash,
                "cached": cached,
            }
        except Exception as exc:
            logger.error("Error in check: %s", exc)
            return {
                "status": "error",
                "error_message": str(exc),
            }

    async def analyze(self, force_reanalyze: bool = False) -> dict[str, Any]:
        """Check, parse, analyze, and cache panic log results."""
        try:
            check_result = await self.check()
            if check_result["status"] != "success":
                return {
                    "status": check_result["status"],
                    "error_message": check_result.get("error_message"),
                    "device_id": check_result.get("device_id"),
                    "device_name": check_result.get("device_name"),
                    "ios_version": check_result.get("ios_version"),
                }

            file_hash = str(check_result["file_hash"])
            device_id = str(check_result["device_id"])

            if not force_reanalyze:
                cached = self._cache_read(file_hash)
                if cached:
                    return {**cached, "cached": True}

            panic_file = await self.collector.collect_latest(device_id)
            if not panic_file:
                return {
                    "status": "error",
                    "error_message": "Failed to collect panic log",
                }

            doc = await self.parser.parse_file(str(panic_file))
            if not doc:
                return {
                    "status": "error",
                    "error_message": "Failed to parse panic log",
                }

            findings: AnalysisFindings = self.analyzer.analyze(doc)
            result = {
                "status": "success",
                "device_id": check_result["device_id"],
                "device_name": check_result["device_name"],
                "ios_version": check_result["ios_version"],
                "model": check_result["model"],
                "panic_log_filename": check_result["panic_log_filename"],
                "file_hash": file_hash,
                "panic_type": findings.panic_type,
                "panic_string": findings.panic_signature,
                "component": findings.dominant_component,
                "severity": findings.estimated_severity,
                "confidence": findings.estimated_confidence,
                "raw_findings": [
                    to_dict(match)
                    for match in findings.rule_matches
                    if match.matched
                ],
                "recommendations": self._get_recommendations(findings),
                "analysis_timestamp": datetime.now(timezone.utc).isoformat(),
                "cached": False,
            }
            self._cache_write(file_hash, result)
            return result
        except Exception as exc:
            logger.error("Error in analyze: %s", exc)
            return {
                "status": "error",
                "error_message": str(exc),
            }

    def _cache_read(self, file_hash: str) -> dict[str, Any] | None:
        cache_file = self.cache_dir / f"{file_hash}.json"
        if not cache_file.is_file():
            return None
        try:
            with open(cache_file, encoding="utf-8") as handle:
                return json.load(handle)
        except Exception:
            return None

    def _cache_write(self, file_hash: str, result: dict[str, Any]) -> None:
        cache_file = self.cache_dir / f"{file_hash}.json"
        try:
            with open(cache_file, "w", encoding="utf-8") as handle:
                json.dump(result, handle, indent=2)
        except Exception as exc:
            logger.error("Cache write error: %s", exc)

    def _get_recommendations(self, findings: AnalysisFindings) -> list[str]:
        recommendations: list[str] = []
        for match in findings.rule_matches:
            if not match.matched:
                continue
            rule = self.analyzer.rules.get(match.rule_id) or {}
            recommendations.extend(rule.get("recommendations") or [])
        deduped: list[str] = []
        for item in recommendations:
            if item not in deduped:
                deduped.append(item)
        return deduped[:5]
