from typing import Any

from notifications.teams import (
    notify_scheduled_check_result,
)
from services.check_service import (
    run_search_api_health_check,
    run_website_uptime_check,
    run_word_visibility_check,
)
from services.scan_service import run_lexicon_scan
from storage.scheduled_checks import (
    get_scheduled_check,
    record_scheduled_check_run,
)


def _send_schedule_notification(
    *,
    schedule_name: str,
    check_type: str,
    status: str,
    result: dict[str, Any],
) -> dict[str, Any]:
    try:
        return notify_scheduled_check_result(
            schedule_name=schedule_name,
            check_type=check_type,
            status=status,
            result=result,
        )
    except Exception as error:
        return {
            "sent": False,
            "reason": "notification_error",
            "error": f"{type(error).__name__}: {error}",
        }


def run_scheduled_check(
    schedule_id: str,
) -> dict[str, Any]:
    schedule = get_scheduled_check(schedule_id)

    if schedule is None:
        raise ValueError("Scheduled check not found.")

    check_type = schedule["check_type"]
    parameters = schedule.get("parameters") or {}

    try:
        if check_type == "website_uptime":
            result = run_website_uptime_check(
                source="scheduled"
            )

        elif check_type == "search_api_health":
            result = run_search_api_health_check(
                probe_word=parameters.get(
                    "probe_word",
                    "سلام",
                ),
                source="scheduled",
            )

        elif check_type == "word_visibility":
            word = parameters.get("word")

            if not word:
                raise ValueError(
                    "word_visibility requires a word parameter."
                )

            result = run_word_visibility_check(
                word=word,
                expected_visible=parameters.get(
                    "expected_visible",
                    True,
                ),
                expected_dictionary=parameters.get(
                    "expected_dictionary"
                ),
                source="scheduled",
            )

        elif check_type == "dictionary_scan":
            lexicon_id = parameters.get("lexicon_id")
            lexicon_name = parameters.get("lexicon_name")

            if not lexicon_id or not lexicon_name:
                raise ValueError(
                    "dictionary_scan requires lexicon_id "
                    "and lexicon_name parameters."
                )

            result = run_lexicon_scan(
                lexicon_id=lexicon_id,
                lexicon_name=lexicon_name,
                source="scheduled",
            )

        else:
            raise ValueError(
                f"Unsupported scheduled check type: {check_type}"
            )

        result_status = result.get("status", "error")

        if result_status == "completed":
            result_status = "passed"

        run_id = (
            result.get("run_id")
            or result.get("scan_run_id")
        )

        record_scheduled_check_run(
            schedule_id=schedule_id,
            run_status=result_status,
            run_id=run_id,
        )

        notification = _send_schedule_notification(
            schedule_name=schedule["name"],
            check_type=check_type,
            status=result_status,
            result=result,
        )

        return {
            "schedule_id": schedule_id,
            "schedule_name": schedule["name"],
            "check_type": check_type,
            "status": result_status,
            "result": result,
            "notification": notification,
        }

    except Exception as error:
        record_scheduled_check_run(
            schedule_id=schedule_id,
            run_status="failed",
        )

        _send_schedule_notification(
            schedule_name=schedule["name"],
            check_type=check_type,
            status="failed",
            result={
                "error_type": type(error).__name__,
                "error_message": str(error),
            },
        )

        raise