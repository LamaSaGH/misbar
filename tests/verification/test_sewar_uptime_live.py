from platforms.sewar.health import check_website_uptime


def test_sewar_website_is_reachable():
    result = check_website_uptime()

    assert result["check_type"] == "website_uptime"
    assert result["platform"] == "sewar"
    assert result["is_up"] is True
    assert result["status"] == "passed"
    assert 200 <= result["http_status"] < 400
    assert result["response_time_ms"] >= 0