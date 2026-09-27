import re
from datetime import datetime, timedelta, timezone
from typing import Any
from urllib.parse import urlparse

from bson import ObjectId
from validation.rule_engine import (
    validate_validation_rules,
)
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


def _validate_request_url(
    request_url: str,
) -> str:
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


def _serialize_document(
    document: dict[str, Any],
) -> dict[str, Any]:
    document["_id"] = str(document["_id"])
    return document


def create_monitoring_check(
    *,
    name: str,
    group: str,
    request_url: str,
    request_method: str,
    function_name: str | None = None,
    tags: list[str] | None = None,
    request_headers: dict[str, str] | None = None,
    query_parameters: dict[str, Any] | None = None,
    request_body: Any = None,
    timeout_seconds: int = 15,
    function_parameters: dict[str, Any] | None = None,
    validations: list[dict[str, Any]] | None = None,
    validation_logic: str = "all",
    schedule_enabled: bool = False,
    frequency: str | None = None,
    run_time: str | None = None,
    timezone_name: str = "Asia/Riyadh",
) -> str:
    normalized_name = name.strip()
    normalized_group = group.strip()
    normalized_method = request_method.strip().upper()
    normalized_timezone_name = timezone_name.strip()

    if not normalized_name:
        raise ValueError(
            "name must not be empty."
        )

    if not normalized_group:
        raise ValueError(
            "group must not be empty."
        )

    if normalized_method not in ALLOWED_METHODS:
        raise ValueError(
            f"Unsupported request method: "
            f"{normalized_method}"
        )

    normalized_url = _validate_request_url(
        request_url
    )

    if timeout_seconds < 1 or timeout_seconds > 120:
        raise ValueError(
            "timeout_seconds must be between 1 and 120."
        )

    configured_validations = validations or []

    if configured_validations:
        validation_mode = "rules"

        validate_validation_rules(
            validations=configured_validations,
            validation_logic=validation_logic,
        )

        normalized_function_name = None
        normalized_function_parameters = {}

    else:
        validation_mode = "function"

        if (
            function_name is None
            or not function_name.strip()
        ):
            raise ValueError(
                "A function name or validation rules "
                "are required."
            )

        normalized_function_name = (
            function_name.strip()
        )

        get_check_function(
            normalized_function_name
        )

        normalized_function_parameters = (
            function_parameters or {}
        )

    if schedule_enabled:
        if frequency not in ALLOWED_FREQUENCIES:
            raise ValueError(
                "Scheduled checks require a supported "
                "frequency."
            )

        if (
            run_time is None
            or RUN_TIME_PATTERN.fullmatch(
                run_time
            ) is None
        ):
            raise ValueError(
                "Scheduled checks require run_time in "
                "HH:MM format."
            )

        if not normalized_timezone_name:
            raise ValueError(
                "timezone_name must not be empty."
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
            "query_parameters": (
                query_parameters or {}
            ),
            "body": request_body,
            "timeout_seconds": timeout_seconds,
        },
        "validation_mode": validation_mode,
        "validations": configured_validations,
        "validation_logic": validation_logic,
        "function_name": normalized_function_name,
        "function_parameters": (
            normalized_function_parameters
        ),
        "schedule": {
            "enabled": schedule_enabled,
            "frequency": frequency,
            "run_time": run_time,
            "timezone": normalized_timezone_name,
        },
        "status": "active",
        "last_run_at": None,
        "last_run_status": None,
        "last_run_id": None,
        "next_run_at": None,
        "execution_claimed_until": None,
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

    return _serialize_document(document)


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

    return [
        _serialize_document(document)
        for document in cursor
    ]


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

    now = datetime.now(timezone.utc)

    fields_to_set: dict[str, Any] = {
        "status": status,
        "updated_at": now,
    }

    if status in {"paused", "archived"}:
        fields_to_set["next_run_at"] = None
        fields_to_set[
            "execution_claimed_until"
        ] = None

    database = get_database()

    result = database[
        "monitoring_checks"
    ].update_one(
        {
            "_id": ObjectId(check_id),
        },
        {
            "$set": fields_to_set,
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


def list_uninitialized_scheduled_checks(
    *,
    limit: int = 200,
) -> list[dict[str, Any]]:
    """
    Return active scheduled checks that do not yet have
    a next execution time.
    """
    if limit < 1 or limit > 1_000:
        raise ValueError(
            "limit must be between 1 and 1000."
        )

    database = get_database()

    cursor = (
        database["monitoring_checks"]
        .find(
            {
                "status": "active",
                "schedule.enabled": True,
                "next_run_at": None,
            }
        )
        .sort("created_at", 1)
        .limit(limit)
    )

    return [
        _serialize_document(document)
        for document in cursor
    ]


def initialize_monitoring_check_next_run(
    *,
    check_id: str,
    next_run_at: datetime,
) -> bool:
    """
    Save the first next_run_at value only when it has not
    already been initialized by another scheduler process.
    """
    if not ObjectId.is_valid(check_id):
        return False

    if next_run_at.tzinfo is None:
        raise ValueError(
            "next_run_at must be timezone-aware."
        )

    now = datetime.now(timezone.utc)
    database = get_database()

    result = database[
        "monitoring_checks"
    ].update_one(
        {
            "_id": ObjectId(check_id),
            "status": "active",
            "schedule.enabled": True,
            "next_run_at": None,
        },
        {
            "$set": {
                "next_run_at": next_run_at,
                "updated_at": now,
            }
        },
    )

    return result.modified_count == 1


def list_due_monitoring_checks(
    *,
    current_time: datetime,
    limit: int = 100,
) -> list[dict[str, Any]]:
    """
    Return scheduled checks whose next_run_at time has
    arrived.
    """
    if current_time.tzinfo is None:
        raise ValueError(
            "current_time must be timezone-aware."
        )

    if limit < 1 or limit > 1_000:
        raise ValueError(
            "limit must be between 1 and 1000."
        )

    database = get_database()

    cursor = (
        database["monitoring_checks"]
        .find(
            {
                "status": "active",
                "schedule.enabled": True,
                "next_run_at": {
                    "$ne": None,
                    "$lte": current_time,
                },
            }
        )
        .sort("next_run_at", 1)
        .limit(limit)
    )

    return [
        _serialize_document(document)
        for document in cursor
    ]


def claim_due_monitoring_check(
    *,
    check_id: str,
    current_time: datetime,
    claim_minutes: int = 10,
) -> bool:
    """
    Atomically claim a due check so two scheduler processes
    cannot run the same check simultaneously.
    """
    if not ObjectId.is_valid(check_id):
        return False

    if current_time.tzinfo is None:
        raise ValueError(
            "current_time must be timezone-aware."
        )

    if claim_minutes < 1 or claim_minutes > 60:
        raise ValueError(
            "claim_minutes must be between 1 and 60."
        )

    claimed_until = (
        current_time
        + timedelta(minutes=claim_minutes)
    )

    database = get_database()

    result = database[
        "monitoring_checks"
    ].update_one(
        {
            "_id": ObjectId(check_id),
            "status": "active",
            "schedule.enabled": True,
            "next_run_at": {
                "$ne": None,
                "$lte": current_time,
            },
            "$or": [
                {
                    "execution_claimed_until": None,
                },
                {
                    "execution_claimed_until": {
                        "$lte": current_time,
                    }
                },
                {
                    "execution_claimed_until": {
                        "$exists": False,
                    }
                },
            ],
        },
        {
            "$set": {
                "execution_claimed_until": (
                    claimed_until
                ),
                "updated_at": datetime.now(
                    timezone.utc
                ),
            }
        },
    )

    return result.modified_count == 1


def complete_monitoring_check_schedule(
    *,
    check_id: str,
    next_run_at: datetime,
) -> bool:
    """
    Store the following run time and release the scheduler
    claim after an execution attempt.
    """
    if not ObjectId.is_valid(check_id):
        return False

    if next_run_at.tzinfo is None:
        raise ValueError(
            "next_run_at must be timezone-aware."
        )

    database = get_database()

    result = database[
        "monitoring_checks"
    ].update_one(
        {
            "_id": ObjectId(check_id),
        },
        {
            "$set": {
                "next_run_at": next_run_at,
                "execution_claimed_until": None,
                "updated_at": datetime.now(
                    timezone.utc
                ),
            }
        },
    )

    return result.matched_count == 1

def delete_archived_monitoring_check(
    check_id: str,
) -> bool:
    """
    Delete an archived check that has never been run.

    The status and last-run conditions prevent active or
    previously executed checks from being deleted.
    """
    if not ObjectId.is_valid(check_id):
        return False

    database = get_database()

    result = database[
        "monitoring_checks"
    ].delete_one(
        {
            "_id": ObjectId(check_id),
            "status": "archived",
            "last_run_at": None,
            "last_run_id": None,
        }
    )

    return result.deleted_count == 1