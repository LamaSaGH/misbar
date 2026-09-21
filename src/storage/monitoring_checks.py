import re
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlparse

from bson import ObjectId

from check_functions.registry import get_check_function
from storage.mongodb import get_database


ALLOWED_METHODS = {
    "GET",
    "POST",
    "PUT",
    "PATCH",
    "DELETE",
    "HEAD",
}

ALLOWED_FREQUENCIES = {
    "daily",
    "weekly",
    "monthly",
}

ALLOWED_STATUSES = {
    "active",
    "paused",
    "archived",
}

RUN_TIME_PATTERN = re.compile(
    r"^(?:[01]\d|2[0-3]):[0-5]\d$"
)


def _validate_request_url(request_url: str) -> str:
    normalized_url = request_url.strip()
    parsed_url = urlparse(normalized_url)

    if (
        parsed_url.scheme not in {"http", "https"}
        or not parsed_url.netloc
    ):
        raise ValueError(
            "request_url must be a valid HTTP or HTTPS URL."
        )

    return normalized_url


def _normalize_tags(
    tags: list[str] | None,
) -> list[str]:
    normalized_tags = {
        tag.strip().lower()
        for tag in (tags or [])
        if tag.strip()
    }

    return sorted(normalized_tags)


def create_monitoring_check(
    *,
    name: str,
    group: str,
    request_url: str,
    request_method: str,
    function_name: str,
    tags: list[str] | None = None,
    request_headers: dict[str, str] | None = None,
    query_parameters: dict[str, Any] | None = None,
    request_body: Any = None,
    timeout_seconds: int = 15,
    function_parameters: dict[str, Any] | None = None,
    schedule_enabled: bool = False,
    frequency: str | None = None,
    run_time: str | None = None,
    timezone_name: str = "Asia/Riyadh",
) -> str:
    normalized_name = name.strip()
    normalized_group = group.strip()
    normalized_method = request_method.strip().upper()

    if not normalized_name:
        raise ValueError("name must not be empty.")

    if not normalized_group:
        raise ValueError("group must not be empty.")

    if normalized_method not in ALLOWED_METHODS:
        raise ValueError(
            f"Unsupported request method: "
            f"{normalized_method}"
        )

    normalized_url = _validate_request_url(request_url)

    if timeout_seconds < 1 or timeout_seconds > 120:
        raise ValueError(
            "timeout_seconds must be between 1 and 120."
        )

    get_check_function(function_name)

    if schedule_enabled:
        if frequency not in ALLOWED_FREQUENCIES:
            raise ValueError(
                "Scheduled checks require a supported "
                "frequency."
            )

        if (
            run_time is None
            or RUN_TIME_PATTERN.fullmatch(run_time) is None
        ):
            raise ValueError(
                "Scheduled checks require run_time in "
                "HH:MM format."
            )
    else:
        frequency = None
        run_time = None

    now = datetime.now(timezone.utc)

    document = {
        "name": normalized_name,
        "group": normalized_group,
        "tags": _normalize_tags(tags),
        "test_type": "api",
        "request": {
            "method": normalized_method,
            "url": normalized_url,
            "headers": request_headers or {},
            "query_parameters": query_parameters or {},
            "body": request_body,
            "timeout_seconds": timeout_seconds,
        },
        "function_name": function_name.strip(),
        "function_parameters": function_parameters or {},
        "schedule": {
            "enabled": schedule_enabled,
            "frequency": frequency,
            "run_time": run_time,
            "timezone": timezone_name,
        },
        "status": "active",
        "last_run_at": None,
        "last_run_status": None,
        "last_run_id": None,
        "next_run_at": None,
        "created_at": now,
        "updated_at": now,
    }

    database = get_database()

    inserted = database[
        "monitoring_checks"
    ].insert_one(document)

    return str(inserted.inserted_id)


def get_monitoring_check(
    check_id: str,
) -> dict[str, Any] | None:
    if not ObjectId.is_valid(check_id):
        return None

    database = get_database()

    document = database[
        "monitoring_checks"
    ].find_one(
        {
            "_id": ObjectId(check_id),
        }
    )

    if document is None:
        return None

    document["_id"] = str(document["_id"])
    return document


def list_monitoring_checks(
    *,
    limit: int = 100,
    group: str | None = None,
    status: str | None = None,
    tag: str | None = None,
) -> list[dict[str, Any]]:
    if limit < 1 or limit > 200:
        raise ValueError(
            "limit must be between 1 and 200."
        )

    if (
        status is not None
        and status not in ALLOWED_STATUSES
    ):
        raise ValueError(
            f"Unsupported monitoring status: {status}"
        )

    query: dict[str, Any] = {}

    if group is not None:
        query["group"] = group

    if status is not None:
        query["status"] = status

    if tag is not None:
        query["tags"] = tag.strip().lower()

    database = get_database()

    cursor = (
        database["monitoring_checks"]
        .find(query)
        .sort("created_at", -1)
        .limit(limit)
    )

    documents = []

    for document in cursor:
        document["_id"] = str(document["_id"])
        documents.append(document)

    return documents


def set_monitoring_check_status(
    *,
    check_id: str,
    status: str,
) -> bool:
    if status not in ALLOWED_STATUSES:
        raise ValueError(
            "status must be active, paused, or archived."
        )

    if not ObjectId.is_valid(check_id):
        return False

    database = get_database()

    result = database[
        "monitoring_checks"
    ].update_one(
        {
            "_id": ObjectId(check_id),
        },
        {
            "$set": {
                "status": status,
                "updated_at": datetime.now(timezone.utc),
            }
        },
    )

    return result.matched_count == 1


def record_monitoring_check_run(
    *,
    check_id: str,
    run_status: str,
    run_id: str | None,
) -> bool:
    if not ObjectId.is_valid(check_id):
        return False

    now = datetime.now(timezone.utc)
    database = get_database()

    result = database[
        "monitoring_checks"
    ].update_one(
        {
            "_id": ObjectId(check_id),
        },
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