from requests.exceptions import Timeout

import platforms.sewar.health as health


def test_api_health_fails_when_schema_is_missing(monkeypatch):
    monkeypatch.setattr(
        health,
        "search_word",
        lambda word: {
            "unexpected_field": [],
        },
    )

    result = health.check_search_api_health()

    assert result["status"] == "failed"
    assert result["is_healthy"] is False
    assert result["schema_valid"] is False
    assert result["entries_count"] == 0


def test_api_health_fails_when_known_word_has_no_results(
    monkeypatch,
):
    monkeypatch.setattr(
        health,
        "search_word",
        lambda word: {
            "entries": [],
        },
    )

    result = health.check_search_api_health()

    assert result["status"] == "failed"
    assert result["is_healthy"] is False
    assert result["schema_valid"] is True
    assert result["entries_count"] == 0


def test_api_health_reports_error_for_timeout(monkeypatch):
    def raise_timeout(word):
        raise Timeout("Search API timed out")

    monkeypatch.setattr(
        health,
        "search_word",
        raise_timeout,
    )

    result = health.check_search_api_health()

    assert result["status"] == "error"
    assert result["is_healthy"] is False
    assert result["schema_valid"] is False
    assert result["error_type"] == "Timeout"