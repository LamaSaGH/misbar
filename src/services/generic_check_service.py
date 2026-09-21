from time import perf_counter
from typing import Any

import requests

from check_functions.registry import (
    run_registered_function,
)
from storage.check_runs import save_generic_check_run
from storage.monitoring_checks import (
    get_monitoring_check,
    record_monitoring_check_run,
)


MAX_RESPONSE_PREVIEW_LENGTH = 10_000


def _build_response_snapshot(
    response: requests.Response,
    response_time_ms: int,
) -> dict[str, Any]:
    content_type = response.headers.get(
        "content-type",
        ""
    )

    response_snapshot: dict[str, Any] = {
        "status_code": response.status_code,
        "response_time_ms": response_time_ms,
        "content_type": content_type,
        "headers": {
            "content-type": content_type,
        },
    }

    try:
        response_snapshot["json"] = response.json()
    except ValueError:
        response_snapshot["text_preview"] = (
            response.text[
                :MAX_RESPONSE_PREVIEW_LENGTH
            ]
        )

    return response_snapshot


def run_generic_monitoring_check(
    check_id: str,
    *,
    source: str = "manual",
) -> dict[str, Any]:
    check = get_monitoring_check(check_id)

    if check is None:
        raise ValueError(
            "Monitoring check not found."
        )

    if check.get("status") != "active":
        raise ValueError(
            "Monitoring check is not active."
        )

    request_configuration = check["request"]
    function_name = check["function_name"]

    request_snapshot = {
        "method": request_configuration["method"],
        "url": request_configuration["url"],
        "headers": request_configuration.get(
            "headers",
            {},
        ),
        "query_parameters": request_configuration.get(
            "query_parameters",
            {},
        ),
        "body": request_configuration.get("body"),
        "timeout_seconds": request_configuration.get(
            "timeout_seconds",
            15,
        ),
    }

    started_at = perf_counter()

    try:
        request_arguments: dict[str, Any] = {
            "method": request_snapshot["method"],
            "url": request_snapshot["url"],
            "headers": request_snapshot["headers"],
            "params": request_snapshot[
                "query_parameters"
            ],
            "timeout": request_snapshot[
                "timeout_seconds"
            ],
        }

        if request_snapshot["body"] is not None:
            request_arguments["json"] = (
                request_snapshot["body"]
            )

        response = requests.request(
            **request_arguments
        )

        response_time_ms = round(
            (perf_counter() - started_at) * 1000
        )

        validation = run_registered_function(
            function_name=function_name,
            response=response,
            parameters=check.get(
                "function_parameters",
                {},
            ),
        )

        status = (
            "passed"
            if validation.get("passed") is True
            else "failed"
        )

        result = {
            "response": _build_response_snapshot(
                response,
                response_time_ms,
            ),
            "validation": validation,
        }

    except requests.RequestException as error:
        response_time_ms = round(
            (perf_counter() - started_at) * 1000
        )

        status = "error"

        result = {
            "response": None,
            "validation": {
                "passed": False,
                "function_name": function_name,
                "message": (
                    f"{type(error).__name__}: "
                    f"{error}"
                ),
            },
            "response_time_ms": response_time_ms,
        }

    run_id = save_generic_check_run(
        monitoring_check_id=check_id,
        check_name=check["name"],
        group=check["group"],
        tags=check.get("tags") or [],
        status=status,
        source=source,
        function_name=function_name,
        request=request_snapshot,
        result=result,
    )

    record_monitoring_check_run(
        check_id=check_id,
        run_status=status,
        run_id=run_id,
    )

    return {
        "run_id": run_id,
        "monitoring_check_id": check_id,
        "name": check["name"],
        "group": check["group"],
        "status": status,
        "function_name": function_name,
        "result": result,
    }