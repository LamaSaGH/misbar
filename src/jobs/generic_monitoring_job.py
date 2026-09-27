import sys
from datetime import datetime, timezone
from typing import Any

from services.generic_check_service import (
    run_generic_monitoring_check,
)
from services.schedule_time import (
    calculate_next_run_at,
)
from storage.monitoring_checks import (
    claim_due_monitoring_check,
    complete_monitoring_check_schedule,
    initialize_monitoring_check_next_run,
    list_due_monitoring_checks,
    list_uninitialized_scheduled_checks,
)


def initialize_next_run_times(
    *,
    current_time: datetime,
) -> int:
    """
    Assign next_run_at to active scheduled checks that do
    not yet have an execution time.
    """
    initialized_count = 0

    checks = list_uninitialized_scheduled_checks()

    for check in checks:
        schedule = check["schedule"]

        next_run_at = calculate_next_run_at(
            frequency=schedule["frequency"],
            run_time=schedule["run_time"],
            timezone_name=schedule.get(
                "timezone",
                "Asia/Riyadh",
            ),
            from_time=current_time,
        )

        initialized = (
            initialize_monitoring_check_next_run(
                check_id=check["_id"],
                next_run_at=next_run_at,
            )
        )

        if initialized:
            initialized_count += 1

    return initialized_count


def run_due_monitoring_checks() -> dict[str, Any]:
    """
    Initialize new schedules, execute all due checks, and
    calculate their following execution times.
    """
    current_time = datetime.now(timezone.utc)

    initialized_count = initialize_next_run_times(
        current_time=current_time,
    )

    due_checks = list_due_monitoring_checks(
        current_time=current_time,
    )

    claimed_count = 0
    passed_count = 0
    failed_count = 0
    error_count = 0
    skipped_count = 0

    executions = []

    for check in due_checks:
        check_id = check["_id"]

        claimed = claim_due_monitoring_check(
            check_id=check_id,
            current_time=current_time,
        )

        if not claimed:
            skipped_count += 1
            continue

        claimed_count += 1

        try:
            execution = run_generic_monitoring_check(
                check_id,
                source="scheduled",
            )

            execution_status = execution["status"]

            if execution_status == "passed":
                passed_count += 1
            else:
                failed_count += 1

            executions.append(
                {
                    "monitoring_check_id": check_id,
                    "name": check["name"],
                    "status": execution_status,
                    "run_id": execution.get("run_id"),
                }
            )

        except Exception as error:
            error_count += 1

            executions.append(
                {
                    "monitoring_check_id": check_id,
                    "name": check["name"],
                    "status": "error",
                    "run_id": None,
                    "error": (
                        f"{type(error).__name__}: "
                        f"{error}"
                    ),
                }
            )

            print(
                f"Monitoring check {check_id} failed: "
                f"{type(error).__name__}: {error}"
            )

        finally:
            schedule = check["schedule"]

            next_run_at = calculate_next_run_at(
                frequency=schedule["frequency"],
                run_time=schedule["run_time"],
                timezone_name=schedule.get(
                    "timezone",
                    "Asia/Riyadh",
                ),
                from_time=current_time,
            )

            complete_monitoring_check_schedule(
                check_id=check_id,
                next_run_at=next_run_at,
            )

    return {
        "initialized_count": initialized_count,
        "due_count": len(due_checks),
        "claimed_count": claimed_count,
        "passed_count": passed_count,
        "failed_count": failed_count,
        "error_count": error_count,
        "skipped_count": skipped_count,
        "executions": executions,
    }


def main() -> int:
    result = run_due_monitoring_checks()
    print(result)

    return 1 if result["error_count"] > 0 else 0


if __name__ == "__main__":
    sys.exit(main())