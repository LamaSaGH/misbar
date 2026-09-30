from datetime import datetime, timezone
from typing import Any

from bson import ObjectId

from storage.mongodb import get_database


def save_generic_check_run(
    *,
    monitoring_check_id: str,
    check_name: str,
    group: str,
    tags: list[str],
    status: str,
    source: str,
    function_name: str,
    request: dict[str, Any],
    result: dict[str, Any],
) -> str:
    if status not in {
        "passed",
        "failed",
        "error",
    }:
        raise ValueError(
            "status must be passed, failed, or error."
        )

    document = {
        "platform": group,
        "check_type": "generic_api",
        "monitoring_check_id": (
            monitoring_check_id
        ),
        "check_name": check_name,
        "group": group,
        "tags": tags,
        "status": status,
        "source": source,
        "function_name": function_name,
        "request": request,
        "result": result,
        "created_at": datetime.now(
            timezone.utc
        ),
    }

    database = get_database()

    inserted = database[
        "check_runs"
    ].insert_one(document)

    return str(inserted.inserted_id)


def monitoring_check_has_runs(
    monitoring_check_id: str,
) -> bool:
    """
    Return True when a monitoring check has at least
    one stored execution result.
    """
    database = get_database()

    document = database[
        "check_runs"
    ].find_one(
        {
            "monitoring_check_id": (
                monitoring_check_id
            ),
        },
        {
            "_id": 1,
        },
    )

    return document is not None


def get_check_run(
    run_id: str,
) -> dict[str, Any] | None:
    if not ObjectId.is_valid(run_id):
        return None

    database = get_database()

    document = database[
        "check_runs"
    ].find_one(
        {
            "_id": ObjectId(run_id),
        }
    )

    if document is None:
        return None

    document["_id"] = str(
        document["_id"]
    )

    return document


def list_check_runs(
    *,
    limit: int = 50,
    check_type: str | None = None,
) -> list[dict[str, Any]]:
    if limit < 1 or limit > 200:
        raise ValueError(
            "limit must be between 1 and 200."
        )

    query: dict[str, Any] = {}

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
        document["_id"] = str(
            document["_id"]
        )

        documents.append(document)

    return documents