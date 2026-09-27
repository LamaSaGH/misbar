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
    "expected_status_code": (
        expected_status_code
    ),
}


CHECK_FUNCTION_METADATA: dict[
    str,
    dict[str, Any],
] = {
    "status_code_200": {
        "name": "status_code_200",
        "display_name": "Status code is 200",
        "description": (
            "Passes when the HTTP response "
            "status code is 200."
        ),
        "parameters": [],
    },
    "expected_status_code": {
        "name": "expected_status_code",
        "display_name": "Expected status code",
        "description": (
            "Passes when the HTTP response "
            "status code matches the configured "
            "status code."
        ),
        "parameters": [
            {
                "name": "expected_status_code",
                "type": "integer",
                "required": True,
                "description": (
                    "The expected HTTP status code."
                ),
                "example": 200,
            }
        ],
    },
}


def get_check_function(
    function_name: str,
) -> CheckFunction:
    normalized_name = function_name.strip()

    if not normalized_name:
        raise ValueError(
            "function_name must not be empty."
        )

    function = CHECK_FUNCTIONS.get(
        normalized_name
    )

    if function is None:
        available_functions = ", ".join(
            sorted(CHECK_FUNCTIONS)
        )

        raise ValueError(
            f"Unsupported function: "
            f"{normalized_name}. "
            f"Available functions: "
            f"{available_functions}."
        )

    return function


def run_registered_function(
    *,
    function_name: str,
    response: requests.Response,
    parameters: dict[str, Any] | None = None,
) -> dict[str, Any]:
    function = get_check_function(
        function_name
    )

    return function(
        response=response,
        parameters=parameters,
    )


def list_check_functions() -> list[str]:
    return sorted(CHECK_FUNCTIONS)


def list_check_function_definitions(
) -> list[dict[str, Any]]:
    definitions = []

    for function_name in sorted(
        CHECK_FUNCTIONS
    ):
        metadata = CHECK_FUNCTION_METADATA.get(
            function_name,
            {
                "name": function_name,
                "display_name": function_name,
                "description": None,
                "parameters": [],
            },
        )

        definitions.append(
            {
                **metadata,
                "registered": True,
            }
        )

    return definitions