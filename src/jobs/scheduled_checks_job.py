import sys
from datetime import datetime, timezone

from services.schedule_service import run_scheduled_check
from services.schedule_time import calculate_next_run_at
from storage.scheduled_checks import (
    claim_due_scheduled_check,
    list_due_scheduled_checks,
    list_scheduled_checks,
    set_scheduled_check_next_run,
)


def initialize_next_run_times(
    current_time: datetime,
) -> int:
    initialized_count = 0

    schedules = list_scheduled_checks(status="active")

    for schedule in schedules:
        if schedule.get("next_run_at") is not None:
            continue

        next_run_at = calculate_next_run_at(
            frequency=schedule["frequency"],
            run_time=schedule["run_time"],
            timezone_name=schedule.get(
                "timezone",
                "Asia/Riyadh",
            ),
            from_time=current_time,
        )

        set_scheduled_check_next_run(
            schedule_id=schedule["_id"],
            next_run_at=next_run_at,
        )

        initialized_count += 1

    return initialized_count


def run_due_scheduled_checks() -> dict:
    current_time = datetime.now(timezone.utc)

    initialized_count = initialize_next_run_times(
        current_time
    )

    due_schedules = list_due_scheduled_checks(
        current_time=current_time
    )

    completed_count = 0
    failed_count = 0
    skipped_locked_count = 0

    for schedule in due_schedules:
        claimed = claim_due_scheduled_check(
            schedule_id=schedule["_id"],
            current_time=current_time,
        )

        if not claimed:
            skipped_locked_count += 1
            continue

        try:
            run_scheduled_check(schedule["_id"])
            completed_count += 1

        except Exception as error:
            failed_count += 1
            print(
                f"Schedule {schedule['_id']} failed: "
                f"{type(error).__name__}: {error}"
            )

        finally:
            next_run_at = calculate_next_run_at(
                frequency=schedule["frequency"],
                run_time=schedule["run_time"],
                timezone_name=schedule.get(
                    "timezone",
                    "Asia/Riyadh",
                ),
                from_time=current_time,
            )

            set_scheduled_check_next_run(
                schedule_id=schedule["_id"],
                next_run_at=next_run_at,
            )

    return {
        "initialized_count": initialized_count,
        "due_count": len(due_schedules),
        "completed_count": completed_count,
        "failed_count": failed_count,
        "skipped_locked_count": skipped_locked_count,
    }


def main() -> int:
    result = run_due_scheduled_checks()
    print(result)

    return 1 if result["failed_count"] > 0 else 0


if __name__ == "__main__":
    sys.exit(main())