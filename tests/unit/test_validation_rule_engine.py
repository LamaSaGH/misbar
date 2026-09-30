import json

import pytest
import requests

from validation.rule_engine import (
    evaluate_validation_rules,
    validate_validation_rules,
)


def build_response(
    *,
    status_code: int = 200,
    json_body=None,
    text_body: str = "",
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
            text_body.encode("utf-8")
        )

    response.encoding = "utf-8"
    return response


def test_status_code_rule_passes():
    result = evaluate_validation_rules(
        response=build_response(
            status_code=200
        ),
        response_time_ms=120,
        validations=[
            {
                "source": "status_code",
                "operator": "equals",
                "expected": 200,
            }
        ],
    )

    assert result["passed"] is True
    assert result["passed_count"] == 1


def test_response_time_rule_passes():
    result = evaluate_validation_rules(
        response=build_response(),
        response_time_ms=500,
        validations=[
            {
                "source": "response_time_ms",
                "operator": "less_than",
                "expected": 1000,
            }
        ],
    )

    assert result["passed"] is True


def test_nested_json_rule_passes():
    result = evaluate_validation_rules(
        response=build_response(
            json_body={
                "data": {
                    "status": "active",
                }
            }
        ),
        response_time_ms=100,
        validations=[
            {
                "source": "json",
                "path": "data.status",
                "operator": "equals",
                "expected": "active",
            }
        ],
    )

    assert result["passed"] is True


def test_json_list_not_empty_passes():
    result = evaluate_validation_rules(
        response=build_response(
            json_body={
                "entries": [
                    {
                        "id": 1,
                    }
                ]
            }
        ),
        response_time_ms=100,
        validations=[
            {
                "source": "json",
                "path": "entries",
                "operator": "is_not_empty",
            }
        ],
    )

    assert result["passed"] is True


def test_text_contains_can_ignore_case():
    result = evaluate_validation_rules(
        response=build_response(
            text_body="Service is HEALTHY"
        ),
        response_time_ms=100,
        validations=[
            {
                "source": "text",
                "operator": "contains",
                "expected": "healthy",
                "case_sensitive": False,
            }
        ],
    )

    assert result["passed"] is True


def test_header_exists_passes():
    result = evaluate_validation_rules(
        response=build_response(
            headers={
                "Content-Type": "application/json",
            }
        ),
        response_time_ms=100,
        validations=[
            {
                "source": "header",
                "name": "content-type",
                "operator": "exists",
            }
        ],
    )

    assert result["passed"] is True


def test_all_logic_fails_when_one_rule_fails():
    result = evaluate_validation_rules(
        response=build_response(
            status_code=200
        ),
        response_time_ms=2000,
        validations=[
            {
                "source": "status_code",
                "operator": "equals",
                "expected": 200,
            },
            {
                "source": "response_time_ms",
                "operator": "less_than",
                "expected": 1000,
            },
        ],
        validation_logic="all",
    )

    assert result["passed"] is False
    assert result["passed_count"] == 1
    assert result["failed_count"] == 1


def test_any_logic_passes_when_one_rule_passes():
    result = evaluate_validation_rules(
        response=build_response(
            status_code=500
        ),
        response_time_ms=200,
        validations=[
            {
                "source": "status_code",
                "operator": "equals",
                "expected": 200,
            },
            {
                "source": "response_time_ms",
                "operator": "less_than",
                "expected": 1000,
            },
        ],
        validation_logic="any",
    )

    assert result["passed"] is True


def test_empty_rules_are_rejected():
    with pytest.raises(
        ValueError,
        match="At least one",
    ):
        validate_validation_rules(
            validations=[],
            validation_logic="all",
        )


def test_invalid_operator_is_rejected():
    with pytest.raises(
        ValueError,
        match="not supported",
    ):
        validate_validation_rules(
            validations=[
                {
                    "source": "status_code",
                    "operator": "contains",
                    "expected": 200,
                }
            ],
            validation_logic="all",
        )