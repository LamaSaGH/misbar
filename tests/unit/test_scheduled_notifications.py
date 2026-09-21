import notifications.teams as teams


def test_successful_scheduled_check_does_not_notify(
    monkeypatch,
):
    def unexpected_notification(**kwargs):
        raise AssertionError(
            "A successful check must not notify Teams."
        )

    monkeypatch.setattr(
        teams,
        "send_teams_notification",
        unexpected_notification,
    )

    result = teams.notify_scheduled_check_result(
        schedule_name="Daily uptime check",
        check_type="website_uptime",
        status="passed",
        result={"status": "passed"},
    )

    assert result == {
        "sent": False,
        "reason": "no_alert_needed",
    }


def test_failed_scheduled_check_notifies_teams(
    monkeypatch,
):
    captured = {}

    monkeypatch.setattr(
        teams,
        "is_teams_configured",
        lambda: True,
    )

    def fake_send_teams_notification(**kwargs):
        captured.update(kwargs)
        return {
            "sent": True,
            "status_code": 200,
        }

    monkeypatch.setattr(
        teams,
        "send_teams_notification",
        fake_send_teams_notification,
    )

    result = teams.notify_scheduled_check_result(
        schedule_name="Daily uptime check",
        check_type="website_uptime",
        status="failed",
        result={
            "error_message": "Server unavailable",
        },
    )

    assert result["sent"] is True
    assert captured["severity"] == "critical"
    assert captured["details"]["status"] == "failed"


def test_dictionary_changes_create_warning(
    monkeypatch,
):
    captured = {}

    monkeypatch.setattr(
        teams,
        "is_teams_configured",
        lambda: True,
    )

    def fake_send_teams_notification(**kwargs):
        captured.update(kwargs)
        return {
            "sent": True,
            "status_code": 200,
        }

    monkeypatch.setattr(
        teams,
        "send_teams_notification",
        fake_send_teams_notification,
    )

    result = teams.notify_scheduled_check_result(
        schedule_name="Dictionary scan",
        check_type="dictionary_scan",
        status="passed",
        result={
            "changes_detected": True,
            "added_count": 2,
            "removed_count": 1,
        },
    )

    assert result["sent"] is True
    assert captured["severity"] == "warning"