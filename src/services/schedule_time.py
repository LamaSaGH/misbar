from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo


def calculate_next_run_at(
    *,
    frequency: str,
    run_time: str,
    timezone_name: str,
    from_time: datetime | None = None,
) -> datetime:
    if frequency not in {"daily", "weekly", "monthly"}:
        raise ValueError(f"Unsupported frequency: {frequency}")

    try:
        hour, minute = map(int, run_time.split(":"))
    except ValueError as error:
        raise ValueError(
            "run_time must use HH:MM format."
        ) from error

    if not 0 <= hour <= 23 or not 0 <= minute <= 59:
        raise ValueError("run_time must contain a valid time.")

    schedule_timezone = ZoneInfo(timezone_name)

    current_utc = from_time or datetime.now(timezone.utc)

    if current_utc.tzinfo is None:
        current_utc = current_utc.replace(
            tzinfo=timezone.utc
        )

    current_local = current_utc.astimezone(
        schedule_timezone
    )

    next_local = current_local.replace(
        hour=hour,
        minute=minute,
        second=0,
        microsecond=0,
    )

    if next_local <= current_local:
        if frequency == "daily":
            next_local += timedelta(days=1)

        elif frequency == "weekly":
            next_local += timedelta(weeks=1)

        elif frequency == "monthly":
            month = next_local.month + 1
            year = next_local.year

            if month == 13:
                month = 1
                year += 1

            next_local = next_local.replace(
                year=year,
                month=month,
                day=1,
            )

    return next_local.astimezone(timezone.utc)