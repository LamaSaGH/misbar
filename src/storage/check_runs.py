from datetime import datetime, timezone
from typing import Any

from bson import ObjectId

from storage.mongodb import get_database


def save_check_run(
    *,
    check_type: str,
    status: str,
    source: str,
    request: dict[str, Any],
    result: dict[str, Any],
) -> str:
    document = {
        "platform": "sewar",
        "check_type": check_type,
        "status": status,
        "source": source,
        "request": request,
        "result": result,
        "created_at": datetime.now(timezone.utc),
    }

    database = get_database()
    inserted = database["check_runs"].insert_one(document)

    return str(inserted.inserted_id)


def get_check_run(run_id: str) -> dict[str, Any] | None:
    database = get_database()

    document = database["check_runs"].find_one(
        {"_id": ObjectId(run_id)}
    )

    if document is None:
        return None

    document["_id"] = str(document["_id"])
    return document

def list_check_runs(
    *,
    limit: int = 50,
    check_type: str | None = None,
) -> list[dict[str, Any]]:
    if limit < 1 or limit > 200:
        raise ValueError("limit must be between 1 and 200.")

    query = {}

    if check_type is not None:
        query["check_type"] = check_type

    database = get_database()
    cursor = (
        database["check_runs"]
        .find(query)
        .sort("created_at", -1)
        .limit(limit)
    )

    documents = []

    for document in cursor:
        document["_id"] = str(document["_id"])
        documents.append(document)

    return documents