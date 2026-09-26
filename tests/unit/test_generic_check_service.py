import requests

import services.generic_check_service as generic_service


def build_active_check():
    return {
        "_id": "check-123",
        "name": "Example website uptime",
        "group": "example",
        "status": "active",
        "request": {
            "method": "GET",
            "url": "https://example.com",
            "headers": {},
            "query_parameters": {},
            "body": None,
            "timeout_seconds": 15,
        },
        "function_name": "status_code_200",
        "function_parameters": {},
        "tags": [
            "availability",
            "critical",
        ],
    }


class FakeResponse:
    status_code = 200

    headers = {
        "content-type": "application/json",
    }

    text = '{"status": "ok"}'

    def json(self):
        return {
            "status": "ok",
        }


def test_generic_check_passes_and_is_recorded(
    monkeypatch,
):
    saved_runs = []
    recorded_runs = []

    monkeypatch.setattr(
        generic_service,
        "get_monitoring_check",
        lambda check_id: build_active_check(),
    )

    monkeypatch.setattr(
        generic_service.requests,
        "request",
        lambda **kwargs: FakeResponse(),
    )

    monkeypatch.setattr(
        generic_service,
        "run_registered_function",
        lambda **kwargs: {
            "passed": True,
            "function_name": (
                kwargs["function_name"]
            ),
            "message": "The check passed.",
        },
    )

    def fake_save_run(**kwargs):
        saved_runs.append(kwargs)
        return "run-123"

    monkeypatch.setattr(
        generic_service,
        "save_generic_check_run",
        fake_save_run,
    )

    def fake_record_run(**kwargs):
        recorded_runs.append(kwargs)
        return True

    monkeypatch.setattr(
        generic_service,
        "record_monitoring_check_run",
        fake_record_run,
    )

    result = (
        generic_service
        .run_generic_monitoring_check(
            "check-123",
            source="verification",
        )
    )

    assert result["status"] == "passed"
    assert result["run_id"] == "run-123"
    assert result["monitoring_check_id"] == (
        "check-123"
    )
    assert result["function_name"] == (
        "status_code_200"
    )

    assert len(saved_runs) == 1
    assert saved_runs[0]["status"] == "passed"
    assert saved_runs[0]["source"] == (
        "verification"
    )

    assert len(recorded_runs) == 1
    assert recorded_runs[0] == {
        "check_id": "check-123",
        "run_status": "passed",
        "run_id": "run-123",
    }


def test_generic_check_records_failed_validation(
    monkeypatch,
):
    monkeypatch.setattr(
        generic_service,
        "get_monitoring_check",
        lambda check_id: build_active_check(),
    )

    class FailedResponse(FakeResponse):
        status_code = 500

    monkeypatch.setattr(
        generic_service.requests,
        "request",
        lambda **kwargs: FailedResponse(),
    )

    monkeypatch.setattr(
        generic_service,
        "run_registered_function",
        lambda **kwargs: {
            "passed": False,
            "function_name": (
                kwargs["function_name"]
            ),
            "message": (
                "Expected status code 200, "
                "but received 500."
            ),
        },
    )

    monkeypatch.setattr(
        generic_service,
        "save_generic_check_run",
        lambda **kwargs: "failed-run",
    )

    monkeypatch.setattr(
        generic_service,
        "record_monitoring_check_run",
        lambda **kwargs: True,
    )

    result = (
        generic_service
        .run_generic_monitoring_check(
            "check-123"
        )
    )

    assert result["status"] == "failed"
    assert (
        result["result"]["response"]["status_code"]
        == 500
    )
    assert (
        result["result"]["validation"]["passed"]
        is False
    )


def test_request_error_is_saved(
    monkeypatch,
):
    saved_run = {}

    monkeypatch.setattr(
        generic_service,
        "get_monitoring_check",
        lambda check_id: build_active_check(),
    )

    def raise_timeout(**kwargs):
        raise requests.Timeout(
            "The request timed out."
        )

    monkeypatch.setattr(
        generic_service.requests,
        "request",
        raise_timeout,
    )

    def fake_save_run(**kwargs):
        saved_run.update(kwargs)
        return "error-run"

    monkeypatch.setattr(
        generic_service,
        "save_generic_check_run",
        fake_save_run,
    )

    monkeypatch.setattr(
        generic_service,
        "record_monitoring_check_run",
        lambda **kwargs: True,
    )

    result = (
        generic_service
        .run_generic_monitoring_check(
            "check-123"
        )
    )

    assert result["status"] == "error"
    assert result["run_id"] == "error-run"
    assert saved_run["status"] == "error"

    assert (
        "Timeout"
        in result["result"][
            "validation"
        ]["message"]
    )


def test_paused_check_cannot_run(
    monkeypatch,
):
    paused_check = build_active_check()
    paused_check["status"] = "paused"

    monkeypatch.setattr(
        generic_service,
        "get_monitoring_check",
        lambda check_id: paused_check,
    )

    try:
        generic_service.run_generic_monitoring_check(
            "check-123"
        )
    except ValueError as error:
        assert str(error) == (
            "Monitoring check is not active."
        )
    else:
        raise AssertionError(
            "A paused check must not be executed."
        )