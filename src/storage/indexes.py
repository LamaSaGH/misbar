from pymongo import ASCENDING, DESCENDING

from storage.mongodb import get_database


def ensure_database_indexes() -> None:
    database = get_database()

    database["check_runs"].create_index(
        [("created_at", DESCENDING)]
    )

    database["check_runs"].create_index(
        [
            ("check_type", ASCENDING),
            ("created_at", DESCENDING),
        ]
    )

    database["scan_runs"].create_index(
        [
            ("lexicon_id", ASCENDING),
            ("started_at", DESCENDING),
        ]
    )

    database["lexicon_entries"].create_index(
        [
            ("lexicon_id", ASCENDING),
            ("lexical_entry_id", ASCENDING),
        ],
        unique=True,
    )

    database["lexicon_entries"].create_index(
        [
            ("lexicon_id", ASCENDING),
            ("is_active", ASCENDING),
        ]
    )
    
    database["scheduled_checks"].create_index(
        [
            ("status", ASCENDING),
            ("next_run_at", ASCENDING),
        ]
    )

    database["scheduled_checks"].create_index(
        [
            ("platform", ASCENDING),
            ("check_type", ASCENDING),
        ]
    )