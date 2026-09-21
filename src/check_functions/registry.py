from collections.abc import Callable
from typing import Any

import requests

from check_functions.common import (
    expected_status_code,
    status_code_200,
)


CheckFunction = Callable[..., dict[str, Any]]


CHECK_FUNCTIONS: dict[str, CheckFunction] = {
    "status_code_200": status_code_200,
    "expected_status_code": expected_status_code,
}


def get_check_function(
    function_name: str,
) -> CheckFunction:
    normalized_name = function_name.strip()

    if not normalized_name:
        raise ValueError(
            "function_name must not be empty."
        )

    function = CHECK_FUNCTIONS.get(normalized_name)

    if function is None:
        available_functions = ", ".join(
            sorted(CHECK_FUNCTIONS)
        )

        raise ValueError(
            f"Unsupported function: {normalized_name}. "
            f"Available functions: {available_functions}."
        )

    return function


def run_registered_function(
    *,
    function_name: str,
    response: requests.Response,
    parameters: dict[str, Any] | None = None,
) -> dict[str, Any]:
    function = get_check_function(function_name)

    return function(
        response=response,
        parameters=parameters,
    )


def list_check_functions() -> list[str]:
    return sorted(CHECK_FUNCTIONS)