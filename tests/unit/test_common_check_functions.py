import json

import pytest
import requests

from check_functions.common import (
    expected_status_code,
    json_field_equals,
    json_field_exists,
    json_list_not_empty,
    response_contains_text,
    response_header_exists,
    status_code_200,
)


def build_response(
    *,
    status_code: int = 200,
    json_body=None,
    text_body: str | None = None,
    headers: dict[str, str] | None = None,
) -> requests.Response:
    response = requests.Response()
    response.status_code = status_code
    response.headers.update(headers or {})

    if json_body is not None:
        response._content = json.dumps(
            json_body
        ).encode("utf-8")
        response.headers[
            "content-type"
        ] = "application/json"
    else:
        response._content = (
            text_body or ""
        ).encode("utf-8")

    response.encoding = "utf-8"
    return response


def test_status_code_200_passes():
    result = status_code_200(
        response=build_response(
            status_code=200
        )
    )

    assert result["passed"] is True


def test_expected_status_code_can_use_201():
    result = expected_status_code(
        response=build_response(
            status_code=201
        ),
        parameters={
            "expected_status_code": 201,
        },
    )

    assert result["passed"] is True


def test_response_contains_text_can_ignore_case():
    result = response_contains_text(
        response=build_response(
            text_body="Service is HEALTHY"
        ),
        parameters={
            "expected_text": "healthy",
            "case_sensitive": False,
        },
    )

    assert result["passed"] is True


def test_json_field_exists_supports_nested_paths():
    result = json_field_exists(
        response=build_response(
            json_body={
                "data": {
                    "user": {
                        "id": 15,
                    }
                }
            }
        ),
        parameters={
            "json_path": "data.user.id",
        },
    )

    assert result["passed"] is True
    assert result["actual"]["value"] == 15


def test_json_field_equals_supports_list_indexes():
    result = json_field_equals(
        response=build_response(
            json_body={
                "entries": [
                    {
                        "status": "active",
                    }
                ]
            }
        ),
        parameters={
            "json_path": "entries.0.status",
            "expected_value": "active",
        },
    )

    assert result["passed"] is True


def test_json_field_equals_fails_for_wrong_value():
    result = json_field_equals(
        response=build_response(
            json_body={
                "status": "failed",
            }
        ),
        parameters={
            "json_path": "status",
            "expected_value": "passed",
        },
    )

    assert result["passed"] is False


def test_json_list_not_empty_passes():
    result = json_list_not_empty(
        response=build_response(
            json_body={
                "data": {
                    "entries": [
                        {
                            "id": 1,
                        }
                    ]
                }
            }
        ),
        parameters={
            "json_path": "data.entries",
        },
    )

    assert result["passed"] is True
    assert result["actual"]["length"] == 1


def test_empty_json_list_fails():
    result = json_list_not_empty(
        response=build_response(
            json_body={
                "entries": [],
            }
        ),
        parameters={
            "json_path": "entries",
        },
    )

    assert result["passed"] is False


def test_response_header_exists_is_case_insensitive():
    result = response_header_exists(
        response=build_response(
            headers={
                "Content-Type": "application/json",
            }
        ),
        parameters={
            "header_name": "content-type",
        },
    )

    assert result["passed"] is True


def test_json_function_rejects_non_json_response():
    with pytest.raises(
        ValueError,
        match="not valid JSON",
    ):
        json_field_exists(
            response=build_response(
                text_body="<html></html>"
            ),
            parameters={
                "json_path": "data",
            },
        )