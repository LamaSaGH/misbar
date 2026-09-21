from datetime import datetime, timezone
from typing import Any, Iterable

from pymongo import UpdateOne

from storage.mongodb import get_database


def save_scan_changes(
    *,
    scan_run_id: str,
    lexicon_id: str,
    added_entries: Iterable[dict[str, Any]],
    removed_entries: Iterable[dict[str, Any]],
) -> int:
    detected_at = datetime.now(timezone.utc)
    operations = []

    for change_type, entries in (
        ("added", added_entries),
        ("removed", removed_entries),
    ):
        for entry in entries:
            lexical_entry_id = entry[
                "lexical_entry_id"
            ]

            operations.append(
                UpdateOne(
                    {
                        "scan_run_id": scan_run_id,
                        "lexical_entry_id": (
                            lexical_entry_id
                        ),
                        "change_type": change_type,
                    },
                    {
                        "$set": {
                            "platform": "sewar",
                            "lexicon_id": lexicon_id,
                            "word": entry["word"],
                            "language_code": entry.get(
                                "language_code"
                            ),
                            "belongs_to": entry.get(
                                "belongs_to"
                            ),
                        },
                        "$setOnInsert": {
                            "detected_at": detected_at,
                        },
                    },
                    upsert=True,
                )
            )

    if not operations:
        return 0

    database = get_database()

    for start in range(0, len(operations), 1_000):
        batch = operations[start : start + 1_000]

        database["scan_changes"].bulk_write(
            batch,
            ordered=False,
        )

    return len(operations)


def list_scan_changes(
    *,
    scan_run_id: str,
    change_type: str | None = None,
    limit: int = 200,
) -> list[dict[str, Any]]:
    if limit < 1 or limit > 1_000:
        raise ValueError(
            "limit must be between 1 and 1000."
        )

    if change_type not in {
        None,
        "added",
        "removed",
        "updated",
    }:
        raise ValueError(
            "Unsupported change type."
        )

    query: dict[str, Any] = {
        "scan_run_id": scan_run_id,
    }

    if change_type is not None:
        query["change_type"] = change_type

    database = get_database()

    cursor = (
        database["scan_changes"]
        .find(query)
        .sort("detected_at", 1)
        .limit(limit)
    )

    documents = []

    for document in cursor:
        document["_id"] = str(document["_id"])
        documents.append(document)

    return documents