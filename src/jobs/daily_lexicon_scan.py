import json
from notifications.teams import (
    is_teams_configured,
    notify_daily_scan_summary,
)
from services.daily_scan_service import (
    run_daily_lexicon_scans,
)
from storage.indexes import ensure_database_indexes


def main() -> int:
    ensure_database_indexes()

    summary = run_daily_lexicon_scans()
    notification_failed = False

    if is_teams_configured():
        try:
            notification = notify_daily_scan_summary(
                summary
            )
        except Exception as error:
            notification_failed = True
            notification = {
                "sent": False,
                "reason": "notification_error",
                "error": (
                    f"{type(error).__name__}: {error}"
                ),
            }
    else:
        notification = {
            "sent": False,
            "reason": "teams_not_configured",
        }

    summary["notification"] = notification

    print(
        json.dumps(
            summary,
            ensure_ascii=False,
            indent=2,
            default=str,
        )
    )

    if (
        summary["failed_count"] > 0
        or notification_failed
    ):
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())