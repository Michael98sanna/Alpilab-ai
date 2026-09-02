#!/usr/bin/env python3
"""CLI read-only analysis for ALPILAB Brain classification and similarity tuning."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.ai.brain_tuning_analysis import (  # noqa: E402
    format_report,
    format_report_markdown,
    run_analysis,
)
from app.models.database import SessionLocal  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Analisi taratura ALPILAB Brain (sola lettura, nessuna chiamata LLM)."
    )
    parser.add_argument(
        "--days",
        type=int,
        default=30,
        help="Finestra temporale in giorni (default: 30)",
    )
    parser.add_argument(
        "--export",
        metavar="FILE",
        help="Esporta il report in Markdown (es. report.md)",
    )
    parser.add_argument(
        "--section",
        choices=["classification", "similarity", "summary", "all"],
        default="all",
        help="Sezione da includere (default: all)",
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disattiva colori ANSI nel terminale",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    db = SessionLocal()
    try:
        report = run_analysis(
            db,
            days=max(1, args.days),
            section=args.section,
            use_color=not args.no_color,
        )
        text = (
            format_report_markdown(report)
            if args.export
            else format_report(report, use_color=not args.no_color)
        )
        if args.export:
            export_path = Path(args.export)
            export_path.write_text(text, encoding="utf-8")
            print(f"Report scritto in {export_path.resolve()}")
        else:
            print(text)
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
