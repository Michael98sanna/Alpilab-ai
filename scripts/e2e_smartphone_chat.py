#!/usr/bin/env python3
"""Quick E2E: smartphone WS → NL command → PC Agent → assistant reply."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys

import websockets


async def run(host: str, port: int, session: str, message: str) -> int:
    base = f"ws://{host}:{port}"
    url = (
        f"{base}/ws/sessions/{session}"
        "?device_id=phone-home-01&device_type=phone&device_name=iPhone"
    )
    print(f"[1] Connect {url}")
    async with websockets.connect(url) as ws:
        snap = json.loads(await ws.recv())
        print(f"[2] Snapshot OK (session={session})")
        await ws.send(
            json.dumps({"type": "chat_message", "content": message, "role": "user"})
        )
        print(f"[3] Sent: {message!r}")

        statuses: list[str] = []
        assistant: str | None = None
        tools: list[str] = []

        for _ in range(25):
            try:
                raw = await asyncio.wait_for(ws.recv(), timeout=20.0)
            except asyncio.TimeoutError:
                break
            msg = json.loads(raw)
            if msg.get("type") != "event":
                continue
            ev = msg["event"]
            et = ev.get("event_type")
            pl = ev.get("payload") or {}
            if et == "ASSISTANT_STATUS" and pl.get("status"):
                statuses.append(pl["status"])
                print(f"    status: {pl['status']}")
            if et == "CHAT_MESSAGE" and pl.get("role") == "assistant":
                assistant = pl.get("content")
                print(f"    reply: {assistant}")
            if et and et.startswith("TOOL_"):
                tools.append(et)
                print(f"    event: {et}")
            if assistant and statuses and statuses[-1] in {"IDLE", "SPEAKING"}:
                break

        print("\n=== SUMMARY ===")
        print(f"Statuses: {statuses}")
        print(f"Tool events: {tools}")
        print(f"Assistant: {assistant}")

        ok = (
            "THINKING" in statuses
            and "WORKING" in statuses
            and assistant is not None
            and ("aperto" in assistant.lower() or "verrebbe avviato" in assistant.lower())
        )
        return 0 if ok else 1


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--host", default="192.168.1.107")
    p.add_argument("--port", type=int, default=8000)
    p.add_argument("--session", default="repair-001")
    p.add_argument("--message", default="Aprimi 3uTools")
    args = p.parse_args()
    raise SystemExit(asyncio.run(run(args.host, args.port, args.session, args.message)))


if __name__ == "__main__":
    main()
