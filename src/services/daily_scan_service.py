from datetime import date, datetime
from typing import Any
from zoneinfo import ZoneInfo

from platforms.sewar.api_client import get_public_lexicons
from platforms.sewar.rotation import get_lexicons_for_date
from services.scan_service import run_lexicon_scan


RIYADH_TIMEZONE = ZoneInfo("Asia/Riyadh")


def get_riyadh_date() -> date:
    return datetime.now(RIYADH_TIMEZONE).date()


def run_daily_lexicon_scans(
    *,
    run_date: date | None = None,
) -> dict[str, Any]:
    target_date = run_date or get_riyadh_date()

    lexicons = get_public_lexicons()
    selected_lexicons = get_lexicons_for_date(
        lexicons,
        target_date,
    )

    completed = []
    failed = []

    for lexicon in selected_lexicons:
        try:
            result = run_lexicon_scan(
                lexicon_id=lexicon["lexicon_id"],
                lexicon_name=lexicon["name"],
                source="scheduled",
            )

            completed.append(result)

        except Exception as error:
            failed.append(
                {
                    "lexicon_id": lexicon["lexicon_id"],
                    "lexicon_name": lexicon["name"],
                    "error": (
                        f"{type(error).__name__}: {error}"
                    ),
                }
            )

    return {
        "run_date": target_date.isoformat(),
        "scheduled_count": len(selected_lexicons),
        "completed_count": len(completed),
        "failed_count": len(failed),
        "completed": completed,
        "failed": failed,
    }