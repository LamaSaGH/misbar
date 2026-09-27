from pymongo import ASCENDING, DESCENDING

from storage.mongodb import get_database


def ensure_database_indexes() -> None:
    database = get_database()

    database["check_runs"].create_index(
        [
            ("created_at", DESCENDING),
        ]
    )

    database["check_runs"].create_index(
        [
            ("check_type", ASCENDING),
            ("created_at", DESCENDING),
        ]
    )

    database["check_runs"].create_index(
        [
            ("monitoring_check_id", ASCENDING),
            ("created_at", DESCENDING),
        ]
    )

    database["check_runs"].create_index(
        [
            ("group", ASCENDING),
            ("created_at", DESCENDING),
        ]
    )

    database["check_runs"].create_index(
        [
            ("status", ASCENDING),
            ("created_at", DESCENDING),
        ]
    )

    database["monitoring_checks"].create_index(
        [
            ("status", ASCENDING),
            ("created_at", DESCENDING),
        ]
    )

    database["monitoring_checks"].create_index(
        [
            ("group", ASCENDING),
            ("status", ASCENDING),
        ]
    )

    database["monitoring_checks"].create_index(
        [
            ("tags", ASCENDING),
        ]
    )

    database["monitoring_checks"].create_index(
        [
            ("status", ASCENDING),
            ("schedule.enabled", ASCENDING),
            ("next_run_at", ASCENDING),
        ]
    )