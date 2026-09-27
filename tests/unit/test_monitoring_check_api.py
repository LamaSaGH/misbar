from fastapi.testclient import TestClient

import web_api.app as api_module


client = TestClient(api_module.app)


def build_monitoring_check():
    return {
        "_id": "check-123",
        "name": "Example uptime check",
        "group": "example",
        "status": "active",
        "request": {
            "url": "https://example.com",
            "method": "GET",
            "headers": {},
            "query_parameters": {},
            "body": None,
            "timeout_seconds": 15,
        },
        "function_name": "status_code_200",
        "function_parameters": {},
        "tags": [
            "availability",
        ],
        "schedule": {
            "enabled": False,
            "frequency": None,
            "run_time": None,
            "timezone": "Asia/Riyadh",
        },
    }


def test_list_monitoring_checks(
    monkeypatch,
):
    monkeypatch.setattr(
        api_module,
        "list_monitoring_checks",
        lambda **kwargs: [
            build_monitoring_check()
        ],
    )

    response = client.get(
        "/api/monitoring-checks",
        params={
            "group": "example",
            "status": "active",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["_id"] == "check-123"
    assert data[0]["group"] == "example"


def test_get_monitoring_check_by_id(
    monkeypatch,
):
    monkeypatch.setattr(
        api_module,
        "get_monitoring_check",
        lambda check_id: (
            build_monitoring_check()
        ),
    )

    response = client.get(
        "/api/monitoring-checks/check-123"
    )

    assert response.status_code == 200
    assert response.json()["name"] == (
        "Example uptime check"
    )


def test_missing_monitoring_check_returns_404(
    monkeypatch,
):
    monkeypatch.setattr(
        api_module,
        "get_monitoring_check",
        lambda check_id: None,
    )

    response = client.get(
        "/api/monitoring-checks/missing"
    )

    assert response.status_code == 404
    assert response.json()["detail"] == (
        "Monitoring check not found."
    )


def test_create_monitoring_check(
    monkeypatch,
):
    received_arguments = {}

    def fake_create(**kwargs):
        received_arguments.update(kwargs)
        return "check-123"

    monkeypatch.setattr(
        api_module,
        "create_monitoring_check",
        fake_create,
    )

    monkeypatch.setattr(
        api_module,
        "get_monitoring_check",
        lambda check_id: (
            build_monitoring_check()
        ),
    )

    response = client.post(
        "/api/monitoring-checks",
        json={
            "name": "Example uptime check",
            "group": "example",
            "request_url": (
                "https://example.com"
            ),
            "request_method": "GET",
            "function_name": (
                "status_code_200"
            ),
            "tags": [
                "availability",
            ],
            "schedule_enabled": False,
        },
    )

    assert response.status_code == 201
    assert response.json()["_id"] == (
        "check-123"
    )

    assert received_arguments["name"] == (
        "Example uptime check"
    )
    assert received_arguments[
        "request_url"
    ] == "https://example.com"

    assert received_arguments[
        "function_name"
    ] == "status_code_200"


def test_update_monitoring_check_status(
    monkeypatch,
):
    updated_arguments = {}

    def fake_update(**kwargs):
        updated_arguments.update(kwargs)
        return True

    paused_check = build_monitoring_check()
    paused_check["status"] = "paused"

    monkeypatch.setattr(
        api_module,
        "set_monitoring_check_status",
        fake_update,
    )

    monkeypatch.setattr(
        api_module,
        "get_monitoring_check",
        lambda check_id: paused_check,
    )

    response = client.patch(
        (
            "/api/monitoring-checks/"
            "check-123/status"
        ),
        json={
            "status": "paused",
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == (
        "paused"
    )

    assert updated_arguments == {
        "check_id": "check-123",
        "status": "paused",
    }


def test_run_monitoring_check_now(
    monkeypatch,
):
    def fake_run(
        check_id,
        *,
        source,
    ):
        return {
            "run_id": "run-123",
            "monitoring_check_id": check_id,
            "name": "Example uptime check",
            "group": "example",
            "status": "passed",
            "function_name": (
                "status_code_200"
            ),
            "result": {
                "validation": {
                    "passed": True,
                }
            },
        }

    monkeypatch.setattr(
        api_module,
        "run_generic_monitoring_check",
        fake_run,
    )

    response = client.post(
        (
            "/api/monitoring-checks/"
            "check-123/run"
        )
    )

    assert response.status_code == 200

    data = response.json()

    assert data["run_id"] == "run-123"
    assert data["status"] == "passed"
    assert data["monitoring_check_id"] == (
        "check-123"
    )