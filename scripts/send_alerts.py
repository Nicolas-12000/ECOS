#!/usr/bin/env python3
"""Generate alert reports and optionally send email notifications.

Requires predictions output (CSV/JSON). Email is optional via SMTP settings.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from email.message import EmailMessage
import smtplib

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = REPO_ROOT / "data/processed/predictions_demo.csv"
DEFAULT_REPORT = REPO_ROOT / "data/processed/alerts_report.md"


def load_predictions(path: Path) -> pd.DataFrame:
    if path.suffix.lower() == ".json":
        data = json.loads(path.read_text(encoding="utf-8"))
        return pd.DataFrame(data)
    return pd.read_csv(path)


def build_report(df: pd.DataFrame) -> str:
    if df.empty:
        return "# Alertas ECOS\n\nSin alertas activas en el periodo.\n"

    lines = [
        "# Alertas ECOS",
        "",
        f"Alertas activas: {len(df)}",
        "",
        "| Departamento | Municipio | Enfermedad | Semana | Casos previstos | Brote |",
        "|---|---|---|---|---|---|",
    ]

    for _, row in df.iterrows():
        lines.append(
            "| {departamento_code} | {municipio_code} | {disease} | {epi_year}-W{epi_week} | {predicted_cases:.2f} | {outbreak_flag} |".format(
                departamento_code=row.get("departamento_code", ""),
                municipio_code=row.get("municipio_code", ""),
                disease=row.get("disease", ""),
                epi_year=row.get("epi_year", ""),
                epi_week=row.get("epi_week", ""),
                predicted_cases=float(row.get("predicted_cases", 0.0)),
                outbreak_flag=str(row.get("outbreak_flag", False)).lower(),
            )
        )

    return "\n".join(lines) + "\n"


def send_email(subject: str, body: str, recipients: list[str]) -> None:
    host = os.getenv("SMTP_HOST", "")
    port = int(os.getenv("SMTP_PORT", "587"))
    user = os.getenv("SMTP_USER", "")
    password = os.getenv("SMTP_PASSWORD", "")
    sender = os.getenv("SMTP_SENDER", user)

    if not host or not sender or not recipients:
        print("[skip] email not configured")
        return

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = ", ".join(recipients)
    msg.set_content(body)

    with smtplib.SMTP(host, port) as smtp:
        smtp.starttls()
        if user and password:
            smtp.login(user, password)
        smtp.send_message(msg)


def main() -> int:
    parser = argparse.ArgumentParser(description="Send ECOS alerts")
    parser.add_argument("--input", default=str(DEFAULT_INPUT))
    parser.add_argument("--report", default=str(DEFAULT_REPORT))
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"[error] predictions not found: {input_path}")
        return 1

    df = load_predictions(input_path)
    if "outbreak_flag" not in df.columns:
        print("[error] outbreak_flag column missing in predictions")
        return 1

    alerts = df[df["outbreak_flag"] == True].copy()
    report = build_report(alerts)

    report_path = Path(args.report)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report, encoding="utf-8")
    print(f"[ok] report -> {report_path}")

    if args.dry_run:
        print("[skip] dry run, no email sent")
        return 0

    recipients = [item.strip() for item in os.getenv("ALERT_EMAILS", "").split(",") if item.strip()]
    send_email("ECOS alertas activas", report, recipients)
    print("[ok] email sent" if recipients else "[skip] no recipients configured")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
