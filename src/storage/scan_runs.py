from datetime import datetime, timezone
from typing import Any

from bson import ObjectId

from storage.mongodb import get_database


def start_scan_run(
    *,
    lexicon_id: str,
    lexicon_name: str,
    source: str = "scheduled",
) -> str:
    document = {
        "platform": "sewar",
        "lexicon_id": lexicon_id,
        "lexicon_name": lexicon_name,
        "source": source,
        "status": "running",
        "total_entries": 0,
        "added_count": 0,
        "removed_count": 0,
        "started_at": datetime.now(timezone.utc),
        "completed_at": None,
        "error": None,
        "is_baseline": None,
    }

    database = get_database()
    inserted = database["scan_runs"].insert_one(document)

    return str(inserted.inserted_id)


def finish_scan_run(
    *,
    scan_run_id: str,
    status: str,
    total_entries: int,
    added_count: int,
    removed_count: int,
    is_baseline: bool = False,
    error: str | None = None,
) -> None:
    if status not in {"completed", "failed"}:
        raise ValueError(
            "status must be 'completed' or 'failed'."
        )

    database = get_database()
    update_result = database["scan_runs"].update_one(
        {"_id": ObjectId(scan_run_id)},
        {
            "$set": {
                "status": status,
                "total_entries": total_entries,
                "added_count": added_count,
                "removed_count": removed_count,
                "is_baseline": is_baseline,
                "completed_at": datetime.now(timezone.utc),
                "error": error,
            }
        },
    )

    if update_result.matched_count == 0:
        raise ValueError("Scan run was not found.")


def get_scan_run(
    scan_run_id: str,
) -> dict[str, Any] | None:
    if not ObjectId.is_valid(scan_run_id):
        return None

    database = get_database()

    document = database["scan_runs"].find_one(
        {"_id": ObjectId(scan_run_id)}
    )

    if document is None:
        return None

    document["_id"] = str(document["_id"])
    return document


def get_latest_completed_scan(
    lexicon_id: str,
) -> dict[str, Any] | None:
    database = get_database()

    document = database["scan_runs"].find_one(
        {
            "lexicon_id": lexicon_id,
            "status": "completed",
        },
        sort=[
            ("completed_at", -1),
        ],
    )

    if document is None:
        return None

    document["_id"] = str(document["_id"])
    return document



def list_scan_runs(
    *,
    limit: int = 50,
    lexicon_id: str | None = None,
    status: str | None = None,
) -> list[dict[str, Any]]:
    if limit < 1 or limit > 200:
        raise ValueError(
            "limit must be between 1 and 200."
        )

    if status not in {
        None,
        "running",
        "completed",
        "failed",
    }:
        raise ValueError(
            "Unsupported scan status."
        )

    query: dict[str, Any] = {}

    if lexicon_id is not None:
        query["lexicon_id"] = lexicon_id

    if status is not None:
        query["status"] = status

    database = get_database()

    cursor = (
        database["scan_runs"]
        .find(query)
        .sort("started_at", -1)
        .limit(limit)
    )

    documents = []

    for document in cursor:
        document["_id"] = str(document["_id"])
        documents.append(document)

    return documents