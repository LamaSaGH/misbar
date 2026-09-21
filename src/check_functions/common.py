from typing import Any

import requests


def status_code_200(
    *,
    response: requests.Response,
    parameters: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Pass when the HTTP response status code is 200.
    """
    actual_status_code = response.status_code
    passed = actual_status_code == 200

    return {
        "passed": passed,
        "function_name": "status_code_200",
        "expected": {
            "status_code": 200,
        },
        "actual": {
            "status_code": actual_status_code,
        },
        "message": (
            "The response status code is 200."
            if passed
            else (
                "Expected status code 200, "
                f"but received {actual_status_code}."
            )
        ),
    }


def expected_status_code(
    *,
    response: requests.Response,
    parameters: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Pass when the response status code matches a configured value.
    """
    configured_parameters = parameters or {}

    expected = configured_parameters.get(
        "expected_status_code"
    )

    if not isinstance(expected, int):
        raise ValueError(
            "expected_status_code must be an integer."
        )

    actual = response.status_code
    passed = actual == expected

    return {
        "passed": passed,
        "function_name": "expected_status_code",
        "expected": {
            "status_code": expected,
        },
        "actual": {
            "status_code": actual,
        },
        "message": (
            f"The response status code is {expected}."
            if passed
            else (
                f"Expected status code {expected}, "
                f"but received {actual}."
            )
        ),
    }