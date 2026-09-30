from typing import Any

import requests


def _validation_result(
    *,
    passed: bool,
    function_name: str,
    expected: dict[str, Any],
    actual: dict[str, Any],
    success_message: str,
    failure_message: str,
) -> dict[str, Any]:
    return {
        "passed": passed,
        "function_name": function_name,
        "expected": expected,
        "actual": actual,
        "message": (
            success_message
            if passed
            else failure_message
        ),
    }


def _get_required_string(
    parameters: dict[str, Any],
    parameter_name: str,
) -> str:
    value = parameters.get(parameter_name)

    if not isinstance(value, str) or not value.strip():
        raise ValueError(
            f"{parameter_name} must be a non-empty string."
        )

    return value.strip()


def _get_response_json(
    response: requests.Response,
) -> Any:
    try:
        return response.json()
    except ValueError as error:
        raise ValueError(
            "The response body is not valid JSON."
        ) from error


def _resolve_json_path(
    data: Any,
    json_path: str,
) -> tuple[bool, Any]:
    """
    Resolve paths such as:
    status
    data.user.name
    entries.0.definition
    """
    normalized_path = json_path.strip()

    if not normalized_path:
        raise ValueError(
            "json_path must not be empty."
        )

    current_value = data

    for path_part in normalized_path.split("."):
        if isinstance(current_value, dict):
            if path_part not in current_value:
                return False, None

            current_value = current_value[path_part]
            continue

        if isinstance(current_value, list):
            try:
                list_index = int(path_part)
            except ValueError:
                return False, None

            if (
                list_index < 0
                or list_index >= len(current_value)
            ):
                return False, None

            current_value = current_value[list_index]
            continue

        return False, None

    return True, current_value


def status_code_200(
    *,
    response: requests.Response,
    parameters: dict[str, Any] | None = None,
) -> dict[str, Any]:
    actual_status_code = response.status_code
    passed = actual_status_code == 200

    return _validation_result(
        passed=passed,
        function_name="status_code_200",
        expected={
            "status_code": 200,
        },
        actual={
            "status_code": actual_status_code,
        },
        success_message=(
            "The response status code is 200."
        ),
        failure_message=(
            "Expected status code 200, "
            f"but received {actual_status_code}."
        ),
    )


def expected_status_code(
    *,
    response: requests.Response,
    parameters: dict[str, Any] | None = None,
) -> dict[str, Any]:
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

    return _validation_result(
        passed=passed,
        function_name="expected_status_code",
        expected={
            "status_code": expected,
        },
        actual={
            "status_code": actual,
        },
        success_message=(
            f"The response status code is {expected}."
        ),
        failure_message=(
            f"Expected status code {expected}, "
            f"but received {actual}."
        ),
    )


def response_contains_text(
    *,
    response: requests.Response,
    parameters: dict[str, Any] | None = None,
) -> dict[str, Any]:
    configured_parameters = parameters or {}

    expected_text = _get_required_string(
        configured_parameters,
        "expected_text",
    )

    case_sensitive = configured_parameters.get(
        "case_sensitive",
        True,
    )

    if not isinstance(case_sensitive, bool):
        raise ValueError(
            "case_sensitive must be a boolean."
        )

    response_text = response.text

    if case_sensitive:
        passed = expected_text in response_text
    else:
        passed = (
            expected_text.casefold()
            in response_text.casefold()
        )

    return _validation_result(
        passed=passed,
        function_name="response_contains_text",
        expected={
            "text": expected_text,
            "case_sensitive": case_sensitive,
        },
        actual={
            "text_found": passed,
        },
        success_message=(
            "The expected text exists in the response."
        ),
        failure_message=(
            "The expected text was not found "
            "in the response."
        ),
    )


def json_field_exists(
    *,
    response: requests.Response,
    parameters: dict[str, Any] | None = None,
) -> dict[str, Any]:
    configured_parameters = parameters or {}

    json_path = _get_required_string(
        configured_parameters,
        "json_path",
    )

    response_json = _get_response_json(response)

    exists, actual_value = _resolve_json_path(
        response_json,
        json_path,
    )

    return _validation_result(
        passed=exists,
        function_name="json_field_exists",
        expected={
            "json_path": json_path,
            "exists": True,
        },
        actual={
            "exists": exists,
            "value": actual_value,
        },
        success_message=(
            f"JSON field '{json_path}' exists."
        ),
        failure_message=(
            f"JSON field '{json_path}' does not exist."
        ),
    )


def json_field_equals(
    *,
    response: requests.Response,
    parameters: dict[str, Any] | None = None,
) -> dict[str, Any]:
    configured_parameters = parameters or {}

    json_path = _get_required_string(
        configured_parameters,
        "json_path",
    )

    if "expected_value" not in configured_parameters:
        raise ValueError(
            "expected_value is required."
        )

    expected_value = configured_parameters[
        "expected_value"
    ]

    response_json = _get_response_json(response)

    exists, actual_value = _resolve_json_path(
        response_json,
        json_path,
    )

    passed = (
        exists
        and actual_value == expected_value
    )

    return _validation_result(
        passed=passed,
        function_name="json_field_equals",
        expected={
            "json_path": json_path,
            "value": expected_value,
        },
        actual={
            "exists": exists,
            "value": actual_value,
        },
        success_message=(
            f"JSON field '{json_path}' matches "
            "the expected value."
        ),
        failure_message=(
            f"JSON field '{json_path}' does not match "
            "the expected value."
        ),
    )


def json_list_not_empty(
    *,
    response: requests.Response,
    parameters: dict[str, Any] | None = None,
) -> dict[str, Any]:
    configured_parameters = parameters or {}

    json_path = _get_required_string(
        configured_parameters,
        "json_path",
    )

    response_json = _get_response_json(response)

    exists, actual_value = _resolve_json_path(
        response_json,
        json_path,
    )

    is_list = isinstance(actual_value, list)

    passed = (
        exists
        and is_list
        and len(actual_value) > 0
    )

    list_length = (
        len(actual_value)
        if is_list
        else None
    )

    return _validation_result(
        passed=passed,
        function_name="json_list_not_empty",
        expected={
            "json_path": json_path,
            "minimum_length": 1,
        },
        actual={
            "exists": exists,
            "is_list": is_list,
            "length": list_length,
        },
        success_message=(
            f"JSON list '{json_path}' is not empty."
        ),
        failure_message=(
            f"JSON path '{json_path}' is missing, "
            "is not a list, or is empty."
        ),
    )


def response_header_exists(
    *,
    response: requests.Response,
    parameters: dict[str, Any] | None = None,
) -> dict[str, Any]:
    configured_parameters = parameters or {}

    header_name = _get_required_string(
        configured_parameters,
        "header_name",
    )

    exists = header_name in response.headers
    actual_value = response.headers.get(header_name)

    return _validation_result(
        passed=exists,
        function_name="response_header_exists",
        expected={
            "header_name": header_name,
            "exists": True,
        },
        actual={
            "exists": exists,
            "value": actual_value,
        },
        success_message=(
            f"Response header '{header_name}' exists."
        ),
        failure_message=(
            f"Response header '{header_name}' "
            "does not exist."
        ),
    )