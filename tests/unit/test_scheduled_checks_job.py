from datetime import datetime, timezone

import jobs.scheduled_checks_job as scheduled_job


def test_due_schedule_runs_and_next_time_is_saved(
    monkeypatch,
):
    schedule = {
        "_id": "schedule-123",
        "name": "Daily uptime check",
        "frequency": "daily",
        "run_time": "10:00",
        "timezone": "Asia/Riyadh",
    }

    executed_schedule_ids = []
    saved_next_runs = []

    monkeypatch.setattr(
        scheduled_job,
        "list_scheduled_checks",
        lambda status: [],
    )

    monkeypatch.setattr(
        scheduled_job,
        "list_due_scheduled_checks",
        lambda current_time: [schedule],
    )

    monkeypatch.setattr(
        scheduled_job,
        "claim_due_scheduled_check",
        lambda schedule_id, current_time: True,
    )

    monkeypatch.setattr(
        scheduled_job,
        "run_scheduled_check",
        lambda schedule_id: executed_schedule_ids.append(
            schedule_id
        ),
    )

    def save_next_run(
        *,
        schedule_id,
        next_run_at,
    ):
        saved_next_runs.append(
            {
                "schedule_id": schedule_id,
                "next_run_at": next_run_at,
            }
        )
        return True

    monkeypatch.setattr(
        scheduled_job,
        "set_scheduled_check_next_run",
        save_next_run,
    )

    result = scheduled_job.run_due_scheduled_checks()

    assert executed_schedule_ids == ["schedule-123"]
    assert result["due_count"] == 1
    assert result["completed_count"] == 1
    assert result["failed_count"] == 0
    assert result["skipped_locked_count"] == 0

    assert len(saved_next_runs) == 1
    assert saved_next_runs[0]["schedule_id"] == (
        "schedule-123"
    )

    next_run_at = saved_next_runs[0]["next_run_at"]

    assert isinstance(next_run_at, datetime)
    assert next_run_at.tzinfo == timezone.utc


def test_locked_schedule_is_not_executed(
    monkeypatch,
):
    schedule = {
        "_id": "schedule-locked",
        "name": "Locked uptime check",
        "frequency": "daily",
        "run_time": "10:00",
        "timezone": "Asia/Riyadh",
    }

    monkeypatch.setattr(
        scheduled_job,
        "list_scheduled_checks",
        lambda status: [],
    )

    monkeypatch.setattr(
        scheduled_job,
        "list_due_scheduled_checks",
        lambda current_time: [schedule],
    )

    monkeypatch.setattr(
        scheduled_job,
        "claim_due_scheduled_check",
        lambda schedule_id, current_time: False,
    )

    def unexpected_execution(schedule_id):
        raise AssertionError(
            "A locked schedule must not execute."
        )

    monkeypatch.setattr(
        scheduled_job,
        "run_scheduled_check",
        unexpected_execution,
    )

    result = scheduled_job.run_due_scheduled_checks()

    assert result["due_count"] == 1
    assert result["completed_count"] == 0
    assert result["failed_count"] == 0
    assert result["skipped_locked_count"] == 1