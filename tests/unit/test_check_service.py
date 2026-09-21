import services.check_service as check_service


def test_word_visibility_check_is_saved(monkeypatch):
    verification_result = {
        "status": "completed",
        "passed": True,
        "actual_visible": True,
        "expected_visible": True,
    }

    saved_document = {}

    monkeypatch.setattr(
        check_service,
        "verify_word_visibility",
        lambda **kwargs: verification_result,
    )

    def fake_save_check_run(**kwargs):
        saved_document.update(kwargs)
        return "test-run-id"

    monkeypatch.setattr(
        check_service,
        "save_check_run",
        fake_save_check_run,
    )

    result = check_service.run_word_visibility_check(
        word="سلام",
        expected_visible=True,
        expected_dictionary="معجم الرياض",
        source="mcp",
    )

    assert result["run_id"] == "test-run-id"
    assert result["status"] == "passed"
    assert result["verification"] == verification_result

    assert saved_document["check_type"] == "word_visibility"
    assert saved_document["status"] == "passed"
    assert saved_document["source"] == "mcp"
    assert saved_document["request"]["word"] == "سلام"
    assert saved_document["request"]["expected_visible"] is True
    assert (
        saved_document["request"]["expected_dictionary"]
        == "معجم الرياض"
    )
    assert saved_document["result"] == verification_result
    
    
def test_website_uptime_check_is_saved(
    monkeypatch,
):
    check_result = {
        "status": "passed",
        "status_code": 200,
        "latency_ms": 150,
    }

    saved_document = {}

    monkeypatch.setattr(
        check_service,
        "check_website_uptime",
        lambda: check_result,
    )

    def fake_save(**kwargs):
        saved_document.update(kwargs)
        return "uptime-run-id"

    monkeypatch.setattr(
        check_service,
        "save_check_run",
        fake_save,
    )

    result = check_service.run_website_uptime_check(
        source="mcp"
    )

    assert result["run_id"] == "uptime-run-id"
    assert result["status"] == "passed"
    assert saved_document["check_type"] == "website_uptime"
    assert saved_document["source"] == "mcp"
    assert saved_document["result"] == check_result


def test_search_api_health_check_is_saved(
    monkeypatch,
):
    check_result = {
        "status": "passed",
        "probe_word": "سلام",
        "results_count": 15,
    }

    saved_document = {}

    monkeypatch.setattr(
        check_service,
        "check_search_api_health",
        lambda probe_word: check_result,
    )

    def fake_save(**kwargs):
        saved_document.update(kwargs)
        return "api-health-run-id"

    monkeypatch.setattr(
        check_service,
        "save_check_run",
        fake_save,
    )

    result = check_service.run_search_api_health_check(
        probe_word="سلام",
        source="mcp",
    )

    assert result["run_id"] == "api-health-run-id"
    assert result["status"] == "passed"
    assert (
        saved_document["check_type"]
        == "search_api_health"
    )
    assert saved_document["source"] == "mcp"
    assert saved_document["request"] == {
        "probe_word": "سلام"
    }
    assert saved_document["result"] == check_result