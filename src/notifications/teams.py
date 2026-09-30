import os
from typing import Any

import requests
from dotenv import load_dotenv


load_dotenv()


FAILED_STATUSES = {
    "failed",
    "error",
}


def is_teams_configured() -> bool:
    return bool(
        os.getenv("TEAMS_WEBHOOK_URL")
    )


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
            "severity must be info, warning, "
            "or critical."
        )

    webhook_url = os.getenv(
        "TEAMS_WEBHOOK_URL"
    )

    if not webhook_url:
        raise RuntimeError(
            "TEAMS_WEBHOOK_URL is not "
            "configured."
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


def notify_monitoring_check_result(
    *,
    check_name: str,
    platform: str,
    status: str,
    result: dict[str, Any],
    run_id: str | None = None,
) -> dict[str, Any]:
    """
    Send a Teams notification when a generic
    monitoring check fails or encounters an error.
    """
    if status not in FAILED_STATUSES:
        return {
            "sent": False,
            "reason": "no_alert_needed",
        }

    if not is_teams_configured():
        return {
            "sent": False,
            "reason": "teams_not_configured",
        }

    if status == "error":
        title = "Misbar monitoring connection error"
        severity = "critical"
        message = (
            f'The check "{check_name}" for '
            f'"{platform}" could not complete '
            "because of a connection or request "
            "error."
        )

    else:
        title = "Misbar monitoring check failed"
        severity = "warning"
        message = (
            f'The check "{check_name}" for '
            f'"{platform}" completed, but one or '
            "more validation conditions failed."
        )

    return send_teams_notification(
        title=title,
        message=message,
        severity=severity,
        details={
            "check_name": check_name,
            "platform": platform,
            "status": status,
            "run_id": run_id,
            "result": result,
        },
    )