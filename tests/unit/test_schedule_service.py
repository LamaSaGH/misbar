import services.schedule_service as schedule_service


def test_scheduled_uptime_check_runs_and_is_recorded(
    monkeypatch,
):
    recorded = {}

    monkeypatch.setattr(
        schedule_service,
        "get_scheduled_check",
        lambda schedule_id: {
            "_id": schedule_id,
            "name": "Daily uptime check",
            "check_type": "website_uptime",
            "parameters": {},
            "status": "active",
        },
    )

    monkeypatch.setattr(
        schedule_service,
        "run_website_uptime_check",
        lambda source: {
            "run_id": "check-run-123",
            "status": "passed",
        },
    )

    def fake_record_scheduled_check_run(
        *,
        schedule_id,
        run_status,
        run_id=None,
    ):
        recorded["schedule_id"] = schedule_id
        recorded["run_status"] = run_status
        recorded["run_id"] = run_id
        return True

    monkeypatch.setattr(
        schedule_service,
        "record_scheduled_check_run",
        fake_record_scheduled_check_run,
    )

    result = schedule_service.run_scheduled_check(
        "schedule-123"
    )

    assert result["status"] == "passed"
    assert result["check_type"] == "website_uptime"

    assert recorded == {
        "schedule_id": "schedule-123",
        "run_status": "passed",
        "run_id": "check-run-123",
    }