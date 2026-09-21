from requests.exceptions import Timeout

import platforms.sewar.health as health


class FakeResponse:
    def __init__(self, status_code):
        self.status_code = status_code


def test_uptime_reports_failed_for_server_error(monkeypatch):
    monkeypatch.setattr(
        health.requests,
        "get",
        lambda *args, **kwargs: FakeResponse(503),
    )

    result = health.check_website_uptime()

    assert result["status"] == "failed"
    assert result["is_up"] is False
    assert result["http_status"] == 503
    assert result["error_type"] is None


def test_uptime_reports_error_for_timeout(monkeypatch):
    def raise_timeout(*args, **kwargs):
        raise Timeout("Sewar timed out")

    monkeypatch.setattr(
        health.requests,
        "get",
        raise_timeout,
    )

    result = health.check_website_uptime()

    assert result["status"] == "error"
    assert result["is_up"] is False
    assert result["http_status"] is None
    assert result["error_type"] == "Timeout"