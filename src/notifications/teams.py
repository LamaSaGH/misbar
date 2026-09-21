import os
from typing import Any

import requests
from dotenv import load_dotenv


load_dotenv()


def is_teams_configured() -> bool:
    return bool(os.getenv("TEAMS_WEBHOOK_URL"))


def send_teams_notification(
    *,
    title: str,
    message: str,
    severity: str,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if severity not in {
        "info",
        "warning",
        "critical",
    }:
        raise ValueError(
            "severity must be info, warning, or critical."
        )

    webhook_url = os.getenv("TEAMS_WEBHOOK_URL")

    if not webhook_url:
        raise RuntimeError(
            "TEAMS_WEBHOOK_URL is not configured."
        )

    payload = {
        "title": title,
        "message": message,
        "severity": severity,
        "details": details or {},
    }

    response = requests.post(
        webhook_url,
        json=payload,
        timeout=15,
    )

    response.raise_for_status()

    return {
        "sent": True,
        "status_code": response.status_code,
    }
    
def notify_daily_scan_summary(
    summary: dict[str, Any],
) -> dict[str, Any]:
    changed_scans = [
        scan
        for scan in summary["completed"]
        if scan.get("changes_detected") is True
    ]

    failed_count = summary["failed_count"]
    changed_count = len(changed_scans)

    if failed_count == 0 and changed_count == 0:
        return {
            "sent": False,
            "reason": "no_alert_needed",
        }

    if failed_count > 0:
        title = "Sewar dictionary scan failure"
        severity = "critical"
        message = (
            f"{failed_count} dictionary scan(s) failed. "
            f"{changed_count} dictionary change(s) "
            "were also detected."
        )
    else:
        title = "Sewar dictionary changes detected"
        severity = "warning"
        message = (
            f"Changes were detected in "
            f"{changed_count} dictionary scan(s)."
        )

    return send_teams_notification(
        title=title,
        message=message,
        severity=severity,
        details={
            "run_date": summary["run_date"],
            "scheduled_count": summary[
                "scheduled_count"
            ],
            "completed_count": summary[
                "completed_count"
            ],
            "failed_count": failed_count,
            "changed_count": changed_count,
            "failed_scans": summary["failed"],
            "changed_scans": changed_scans,
        },
    )
    
def notify_scheduled_check_result(
    *,
    schedule_name: str,
    check_type: str,
    status: str,
    result: dict[str, Any],
) -> dict[str, Any]:
    changes_detected = (
        check_type == "dictionary_scan"
        and result.get("changes_detected") is True
    )

    failed = status in {
        "failed",
        "error",
    }

    if not failed and not changes_detected:
        return {
            "sent": False,
            "reason": "no_alert_needed",
        }

    if not is_teams_configured():
        return {
            "sent": False,
            "reason": "teams_not_configured",
        }

    if failed:
        title = "Sewar scheduled check failed"
        severity = "critical"
        message = (
            f'The scheduled check "{schedule_name}" '
            f"finished with status: {status}."
        )
    else:
        title = "Sewar dictionary changes detected"
        severity = "warning"
        message = (
            f'The scheduled scan "{schedule_name}" '
            "detected dictionary changes."
        )

    return send_teams_notification(
        title=title,
        message=message,
        severity=severity,
        details={
            "schedule_name": schedule_name,
            "check_type": check_type,
            "status": status,
            "result": result,
        },
    )