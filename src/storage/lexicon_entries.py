from datetime import datetime, timezone
from typing import Any, Iterable

from pymongo import UpdateOne

from storage.mongodb import get_database


def get_active_entry_ids(
    lexicon_id: str,
) -> set[str]:
    database = get_database()

    cursor = database["lexicon_entries"].find(
        {
            "lexicon_id": lexicon_id,
            "is_active": True,
        },
        {
            "_id": 0,
            "lexical_entry_id": 1,
        },
    )

    return {
        document["lexical_entry_id"]
        for document in cursor
    }


def get_lexicon_entries_by_ids(
    *,
    lexicon_id: str,
    lexical_entry_ids: Iterable[str],
) -> list[dict[str, Any]]:
    entry_ids = list(set(lexical_entry_ids))

    if not entry_ids:
        return []

    database = get_database()

    cursor = database["lexicon_entries"].find(
        {
            "lexicon_id": lexicon_id,
            "lexical_entry_id": {
                "$in": entry_ids,
            },
        },
        {
            "_id": 0,
            "lexical_entry_id": 1,
            "word": 1,
            "language_code": 1,
            "belongs_to": 1,
            "is_active": 1,
        },
    )

    return list(cursor)

def upsert_lexicon_entries(
    *,
    lexicon_id: str,
    entries: Iterable[dict[str, Any]],
    scan_run_id: str,
) -> int:
    now = datetime.now(timezone.utc)

    unique_entries = {
        entry["lexical_entry_id"]: entry
        for entry in entries
    }

    operations = []

    for lexical_entry_id, entry in unique_entries.items():
        operations.append(
            UpdateOne(
                {
                    "lexicon_id": lexicon_id,
                    "lexical_entry_id": lexical_entry_id,
                },
                {
                    "$set": {
                        "word": entry["word"],
                        "language_code": entry.get(
                            "language_code"
                        ),
                        "belongs_to": entry.get("belongs_to"),
                        "is_active": True,
                        "last_seen_at": now,
                        "last_seen_scan_id": scan_run_id,
                    },
                    "$setOnInsert": {
                        "first_seen_at": now,
                    },
                    "$unset": {
                        "removed_at": "",
                    },
                },
                upsert=True,
            )
        )

    if not operations:
        return 0

    database = get_database()
    database["lexicon_entries"].bulk_write(
        operations,
        ordered=False,
    )

    return len(unique_entries)


def deactivate_missing_entries(
    *,
    lexicon_id: str,
    scan_run_id: str,
) -> int:
    now = datetime.now(timezone.utc)
    database = get_database()

    result = database["lexicon_entries"].update_many(
        {
            "lexicon_id": lexicon_id,
            "is_active": True,
            "last_seen_scan_id": {
                "$ne": scan_run_id,
            },
        },
        {
            "$set": {
                "is_active": False,
                "removed_at": now,
            }
        },
    )

    return result.modified_count