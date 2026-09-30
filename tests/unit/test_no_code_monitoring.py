import json

import requests

import services.generic_check_service as check_service


def build_response() -> requests.Response:
    response = requests.Response()
    response.status_code = 200
    response._content = json.dumps(
        {
            "data": {
                "status": "active",
            }
        }
    ).encode("utf-8")
    response.headers[
        "content-type"
    ] = "application/json"
    response.encoding = "utf-8"

    return response


def test_no_code_rules_execute_and_are_saved(
    monkeypatch,
):
    check = {
        "_id": "check-123",
        "name": "Platform health",
        "group": "مركز ذكاء العربية",
        "tags": [
            "api",
        ],
        "status": "active",
        "validation_mode": "rules",
        "validation_logic": "all",
        "validations": [
            {
                "source": "status_code",
                "operator": "equals",
                "expected": 200,
            },
            {
                "source": "json",
                "path": "data.status",
                "operator": "equals",
                "expected": "active",
            },
        ],
        "request": {
            "method": "GET",
            "url": (
                "https://example.com/api/health"
            ),
            "headers": {},
            "query_parameters": {},
            "body": None,
            "timeout_seconds": 15,
        },
    }

    saved_runs = []
    recorded_runs = []

    monkeypatch.setattr(
        check_service,
        "get_monitoring_check",
        lambda check_id: check,
    )

    monkeypatch.setattr(
        check_service.requests,
        "request",
        lambda **kwargs: build_response(),
    )

    def fake_save_run(**kwargs):
        saved_runs.append(kwargs)
        return "run-123"

    monkeypatch.setattr(
        check_service,
        "save_generic_check_run",
        fake_save_run,
    )

    def fake_record_run(**kwargs):
        recorded_runs.append(kwargs)
        return True

    monkeypatch.setattr(
        check_service,
        "record_monitoring_check_run",
        fake_record_run,
    )

    result = (
        check_service.run_generic_monitoring_check(
            "check-123",
            source="dashboard",
        )
    )

    assert result["status"] == "passed"
    assert result["validation_mode"] == "rules"
    assert result["function_name"] == "rule_engine"

    validation = result["result"][
        "validation"
    ]

    assert validation["passed"] is True
    assert validation["total_count"] == 2
    assert validation["passed_count"] == 2
    assert validation["failed_count"] == 0

    assert len(saved_runs) == 1
    assert (
        saved_runs[0]["function_name"]
        == "rule_engine"
    )
    assert saved_runs[0]["status"] == "passed"

    assert recorded_runs == [
        {
            "check_id": "check-123",
            "run_status": "passed",
            "run_id": "run-123",
        }
    ]