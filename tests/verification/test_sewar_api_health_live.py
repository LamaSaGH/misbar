from platforms.sewar.health import check_search_api_health


def test_sewar_search_api_is_healthy():
    result = check_search_api_health()

    assert result["check_type"] == "search_api_health"
    assert result["platform"] == "sewar"
    assert result["status"] == "passed"
    assert result["is_healthy"] is True
    assert result["schema_valid"] is True
    assert result["entries_count"] > 0
    assert result["response_time_ms"] >= 0