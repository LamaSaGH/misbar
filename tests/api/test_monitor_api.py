from fastapi.testclient import TestClient

import web_api.app as api_module


client = TestClient(api_module.app)


def test_application_health_reports_database_connection(
    monkeypatch,
):
    monkeypatch.setattr(
        api_module,
        "ping_database",
        lambda: True,
    )

    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "passed",
        "database_connected": True,
    }


def test_dashboard_word_visibility_check_uses_service(
    monkeypatch,
):
    captured_request = {}

    def fake_visibility_check(**kwargs):
        captured_request.update(kwargs)

        return {
            "run_id": "dashboard-run-id",
            "status": "passed",
        }

    monkeypatch.setattr(
        api_module,
        "run_word_visibility_check",
        fake_visibility_check,
    )

    response = client.post(
        "/api/checks/word-visibility",
        json={
            "word": "سلام",
            "expected_visible": True,
            "expected_dictionary": "معجم الرياض",
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "run_id": "dashboard-run-id",
        "status": "passed",
    }

    assert captured_request == {
        "word": "سلام",
        "expected_visible": True,
        "expected_dictionary": "معجم الرياض",
        "source": "dashboard",
    }


def test_dashboard_rejects_empty_word():
    response = client.post(
        "/api/checks/word-visibility",
        json={
            "word": "",
            "expected_visible": True,
        },
    )

    assert response.status_code == 422