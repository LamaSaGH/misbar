import pytest

import notifications.teams as teams


def test_missing_teams_webhook_is_reported(
    monkeypatch,
):
    monkeypatch.delenv(
        "TEAMS_WEBHOOK_URL",
        raising=False,
    )

    assert teams.is_teams_configured() is False

    with pytest.raises(
        RuntimeError,
        match="TEAMS_WEBHOOK_URL is not configured",
    ):
        teams.send_teams_notification(
            title="Test",
            message="Test message",
            severity="info",
        )


def test_teams_notification_sends_expected_payload(
    monkeypatch,
):
    captured_request = {}

    class FakeResponse:
        status_code = 202

        def raise_for_status(self):
            return None

    def fake_post(url, json, timeout):
        captured_request["url"] = url
        captured_request["json"] = json
        captured_request["timeout"] = timeout

        return FakeResponse()

    monkeypatch.setenv(
        "TEAMS_WEBHOOK_URL",
        "https://example.test/teams-webhook",
    )

    monkeypatch.setattr(
        teams.requests,
        "post",
        fake_post,
    )

    result = teams.send_teams_notification(
        title="Dictionary change detected",
        message="One word was added.",
        severity="warning",
        details={
            "lexicon_id": "lexicon-1",
            "added_count": 1,
            "removed_count": 0,
        },
    )

    assert result == {
        "sent": True,
        "status_code": 202,
    }

    assert (
        captured_request["url"]
        == "https://example.test/teams-webhook"
    )
    assert captured_request["timeout"] == 15

    assert captured_request["json"] == {
        "title": "Dictionary change detected",
        "message": "One word was added.",
        "severity": "warning",
        "details": {
            "lexicon_id": "lexicon-1",
            "added_count": 1,
            "removed_count": 0,
        },
    }
    
def test_unchanged_daily_scan_does_not_notify(
    monkeypatch,
):
    def unexpected_notification(**kwargs):
        raise AssertionError(
            "No notification should be sent."
        )

    monkeypatch.setattr(
        teams,
        "send_teams_notification",
        unexpected_notification,
    )

    summary = {
        "run_date": "2026-09-16",
        "scheduled_count": 1,
        "completed_count": 1,
        "failed_count": 0,
        "completed": [
            {
                "lexicon_id": "lexicon-1",
                "changes_detected": False,
            }
        ],
        "failed": [],
    }

    result = teams.notify_daily_scan_summary(summary)

    assert result == {
        "sent": False,
        "reason": "no_alert_needed",
    }


def test_dictionary_change_creates_warning_notification(
    monkeypatch,
):
    captured_notification = {}

    def fake_notification(**kwargs):
        captured_notification.update(kwargs)

        return {
            "sent": True,
            "status_code": 202,
        }

    monkeypatch.setattr(
        teams,
        "send_teams_notification",
        fake_notification,
    )

    summary = {
        "run_date": "2026-09-16",
        "scheduled_count": 1,
        "completed_count": 1,
        "failed_count": 0,
        "completed": [
            {
                "lexicon_id": "lexicon-1",
                "changes_detected": True,
                "added_count": 2,
                "removed_count": 1,
            }
        ],
        "failed": [],
    }

    result = teams.notify_daily_scan_summary(summary)

    assert result["sent"] is True
    assert captured_notification["severity"] == "warning"
    assert (
        captured_notification["details"]["changed_count"]
        == 1
    )
    assert (
        captured_notification["details"]["changed_scans"][0][
            "lexicon_id"
        ]
        == "lexicon-1"
    )