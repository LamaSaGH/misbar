from datetime import datetime, timedelta, timezone
from typing import Any

from bson import ObjectId

from storage.mongodb import get_database


ALLOWED_FREQUENCIES = {
    "daily",
    "weekly",
    "monthly",
}

ALLOWED_CHECK_TYPES = {
    "website_uptime",
    "search_api_health",
    "word_visibility",
    "dictionary_scan",
}


def create_scheduled_check(
    *,
    name: str,
    check_type: str,
    frequency: str,
    run_time: str,
    parameters: dict[str, Any] | None = None,
    timezone_name: str = "Asia/Riyadh",
) -> str:
    if not name.strip():
        raise ValueError("name must not be empty.")

    if check_type not in ALLOWED_CHECK_TYPES:
        raise ValueError(f"Unsupported check type: {check_type}")

    if frequency not in ALLOWED_FREQUENCIES:
        raise ValueError(f"Unsupported frequency: {frequency}")

    now = datetime.now(timezone.utc)

    document = {
        "platform": "sewar",
        "name": name.strip(),
        "check_type": check_type,
        "frequency": frequency,
        "run_time": run_time,
        "timezone": timezone_name,
        "parameters": parameters or {},
        "status": "active",
        "last_run_at": None,
        "next_run_at": None,
        "created_at": now,
        "updated_at": now,
    }

    database = get_database()
    inserted = database["scheduled_checks"].insert_one(document)

    return str(inserted.inserted_id)


def get_scheduled_check(
    schedule_id: str,
) -> dict[str, Any] | None:
    if not ObjectId.is_valid(schedule_id):
        return None

    database = get_database()
    document = database["scheduled_checks"].find_one(
        {"_id": ObjectId(schedule_id)}
    )

    if document is None:
        return None

    document["_id"] = str(document["_id"])
    return document


def list_scheduled_checks(
    *,
    status: str | None = None,
) -> list[dict[str, Any]]:
    query = {}

    if status is not None:
        query["status"] = status

    database = get_database()
    cursor = database["scheduled_checks"].find(query).sort(
        "created_at",
        -1,
    )

    documents = []

    for document in cursor:
        document["_id"] = str(document["_id"])
        documents.append(document)

    return documents


def set_scheduled_check_status(
    *,
    schedule_id: str,
    status: str,
) -> bool:
    if status not in {"active", "paused"}:
        raise ValueError("status must be active or paused.")

    if not ObjectId.is_valid(schedule_id):
        return False

    database = get_database()
    result = database["scheduled_checks"].update_one(
        {"_id": ObjectId(schedule_id)},
        {
            "$set": {
                "status": status,
                "updated_at": datetime.now(timezone.utc),
            }
        },
    )

    return result.matched_count == 1

def record_scheduled_check_run(
    *,
    schedule_id: str,
    run_status: str,
    run_id: str | None = None,
) -> bool:
    if not ObjectId.is_valid(schedule_id):
        return False

    now = datetime.now(timezone.utc)

    result = get_database()["scheduled_checks"].update_one(
        {"_id": ObjectId(schedule_id)},
        {
            "$set": {
                "last_run_at": now,
                "last_run_status": run_status,
                "last_run_id": run_id,
                "updated_at": now,
            }
        },
    )

    return result.matched_count == 1

def set_scheduled_check_next_run(
    *,
    schedule_id: str,
    next_run_at: datetime,
) -> bool:
    if not ObjectId.is_valid(schedule_id):
        return False

    result = get_database()["scheduled_checks"].update_one(
        {"_id": ObjectId(schedule_id)},
        {
            "$set": {
                "next_run_at": next_run_at,
                "updated_at": datetime.now(timezone.utc),
            }
        },
    )

    return result.matched_count == 1


def list_due_scheduled_checks(
    *,
    current_time: datetime | None = None,
) -> list[dict[str, Any]]:
    now = current_time or datetime.now(timezone.utc)

    cursor = get_database()["scheduled_checks"].find(
        {
            "status": "active",
            "next_run_at": {
                "$ne": None,
                "$lte": now,
            },
        }
    ).sort("next_run_at", 1)

    documents = []

    for document in cursor:
        document["_id"] = str(document["_id"])
        documents.append(document)

    return documents

def claim_due_scheduled_check(
    *,
    schedule_id: str,
    current_time: datetime | None = None,
    lock_minutes: int = 15,
) -> bool:
    if not ObjectId.is_valid(schedule_id):
        return False

    now = current_time or datetime.now(timezone.utc)
    lock_until = now + timedelta(minutes=lock_minutes)

    result = get_database()["scheduled_checks"].update_one(
        {
            "_id": ObjectId(schedule_id),
            "status": "active",
            "next_run_at": {
                "$ne": None,
                "$lte": now,
            },
            "$or": [
                {"run_lock_until": {"$exists": False}},
                {"run_lock_until": None},
                {"run_lock_until": {"$lte": now}},
            ],
        },
        {
            "$set": {
                "run_lock_until": lock_until,
                "updated_at": now,
            }
        },
    )

    return result.modified_count == 1