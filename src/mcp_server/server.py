from typing import Any

from mcp.server import MCPServer

from services.generic_check_service import (
    run_generic_monitoring_check,
)
from services.monitoring_check_management import (
    MonitoringCheckDeletionConflictError,
    MonitoringCheckNotFoundError,
    delete_unused_monitoring_check,
)
from storage.check_runs import list_check_runs
from storage.monitoring_checks import (
    create_monitoring_check,
    get_monitoring_check,
    list_monitoring_checks,
    set_monitoring_check_status,
)


mcp = MCPServer("Misbar Monitoring")


@mcp.tool()
def create_api_check(
    name: str,
    platform: str,
    request_url: str,
    request_method: str = "GET",
    validations: list[dict[str, Any]] | None = None,
    validation_logic: str = "all",
    tags: list[str] | None = None,
    request_headers: dict[str, str] | None = None,
    query_parameters: dict[str, Any] | None = None,
    request_body: Any = None,
    timeout_seconds: int = 15,
    schedule_enabled: bool = False,
    frequency: str | None = None,
    run_time: str | None = None,
    timezone_name: str = "Asia/Riyadh",
) -> dict[str, Any]:
    """
    Create and save a reusable API monitoring check.

    Validation rule examples:

    Status code equals 200:
    {
        "source": "status_code",
        "operator": "equals",
        "expected": 200
    }

    JSON field is not empty:
    {
        "source": "json",
        "path": "entries",
        "operator": "is_not_empty"
    }

    Response time is below 1000 milliseconds:
    {
        "source": "response_time_ms",
        "operator": "less_than",
        "expected": 1000
    }

    Supported validation_logic values:
    all, any.

    Supported schedule frequencies:
    daily, weekly, monthly.
    """
    configured_validations = validations or [
        {
            "source": "status_code",
            "operator": "equals",
            "expected": 200,
        }
    ]

    check_id = create_monitoring_check(
        name=name,
        group=platform,
        request_url=request_url,
        request_method=request_method,
        function_name=None,
        function_parameters={},
        validations=configured_validations,
        validation_logic=validation_logic,
        tags=tags,
        request_headers=request_headers,
        query_parameters=query_parameters,
        request_body=request_body,
        timeout_seconds=timeout_seconds,
        schedule_enabled=schedule_enabled,
        frequency=frequency,
        run_time=run_time,
        timezone_name=timezone_name,
    )

    check = get_monitoring_check(check_id)

    if check is None:
        raise RuntimeError(
            "The monitoring check was created but "
            "could not be retrieved."
        )

    return check


@mcp.tool()
def list_api_checks(
    platform: str | None = None,
    status: str | None = None,
    tag: str | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    """
    List saved monitoring checks.

    status may be:
    active, paused, or archived.
    """
    return list_monitoring_checks(
        limit=limit,
        group=platform,
        status=status,
        tag=tag,
    )


@mcp.tool()
def get_api_check(
    check_id: str,
) -> dict[str, Any]:
    """Return the complete configuration of one check."""
    check = get_monitoring_check(check_id)

    if check is None:
        raise ValueError(
            "Monitoring check not found."
        )

    return check


@mcp.tool()
def run_api_check(
    check_id: str,
) -> dict[str, Any]:
    """
    Run a saved active monitoring check immediately.

    The result includes the status, response metadata,
    response time, and validation results.
    """
    return run_generic_monitoring_check(
        check_id,
        source="mcp",
    )


@mcp.tool()
def get_recent_api_check_runs(
    limit: int = 20,
    platform: str | None = None,
    status: str | None = None,
) -> list[dict[str, Any]]:
    """
    Return recent generic API monitoring results.

    status may be:
    passed, failed, or error.
    """
    if limit < 1 or limit > 200:
        raise ValueError(
            "limit must be between 1 and 200."
        )

    if status not in {
        None,
        "passed",
        "failed",
        "error",
    }:
        raise ValueError(
            "status must be passed, failed, or error."
        )

    runs = list_check_runs(
        limit=200,
        check_type="generic_api",
    )

    filtered_runs = []

    for run in runs:
        run_platform = (
            run.get("group")
            or run.get("platform")
        )

        if (
            platform is not None
            and run_platform != platform
        ):
            continue

        if (
            status is not None
            and run.get("status") != status
        ):
            continue

        filtered_runs.append(run)

        if len(filtered_runs) >= limit:
            break

    return filtered_runs


@mcp.tool()
def pause_api_check(
    check_id: str,
) -> dict[str, Any]:
    """Pause a monitoring check."""
    return _change_check_status(
        check_id=check_id,
        status="paused",
    )


@mcp.tool()
def resume_api_check(
    check_id: str,
) -> dict[str, Any]:
    """Reactivate a paused or archived monitoring check."""
    return _change_check_status(
        check_id=check_id,
        status="active",
    )


@mcp.tool()
def archive_api_check(
    check_id: str,
) -> dict[str, Any]:
    """
    Archive a monitoring check while preserving its
    execution history.
    """
    return _change_check_status(
        check_id=check_id,
        status="archived",
    )


@mcp.tool()
def delete_api_check(
    check_id: str,
) -> dict[str, Any]:
    """
    Permanently delete an unused archived check.

    Checks with execution history cannot be permanently
    deleted because their monitoring records must remain
    available.
    """
    try:
        delete_unused_monitoring_check(check_id)

    except MonitoringCheckNotFoundError as error:
        raise ValueError(str(error)) from error

    except (
        MonitoringCheckDeletionConflictError
    ) as error:
        raise ValueError(str(error)) from error

    return {
        "deleted": True,
        "check_id": check_id,
    }


@mcp.tool()
def list_scheduled_api_checks(
    platform: str | None = None,
    status: str | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    """Return monitoring checks with scheduling enabled."""
    checks = list_monitoring_checks(
        limit=limit,
        group=platform,
        status=status,
    )

    return [
        check
        for check in checks
        if (
            check.get("schedule") or {}
        ).get("enabled") is True
    ]


def _change_check_status(
    *,
    check_id: str,
    status: str,
) -> dict[str, Any]:
    updated = set_monitoring_check_status(
        check_id=check_id,
        status=status,
    )

    if not updated:
        raise ValueError(
            "Monitoring check not found."
        )

    check = get_monitoring_check(check_id)

    if check is None:
        raise ValueError(
            "Monitoring check not found."
        )

    return check