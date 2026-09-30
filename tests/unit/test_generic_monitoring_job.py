from datetime import datetime, timezone

import jobs.generic_monitoring_job as monitoring_job


def build_scheduled_check(
    check_id: str = "check-123",
) -> dict:
    return {
        "_id": check_id,
        "name": "Platform health check",
        "status": "active",
        "schedule": {
            "enabled": True,
            "frequency": "daily",
            "run_time": "10:00",
            "timezone": "Asia/Riyadh",
        },
    }


def test_uninitialized_schedule_gets_next_run(
    monkeypatch,
):
    check = build_scheduled_check()
    saved_next_runs = []

    monkeypatch.setattr(
        monitoring_job,
        "list_uninitialized_scheduled_checks",
        lambda: [check],
    )

    def fake_initialize(
        *,
        check_id,
        next_run_at,
    ):
        saved_next_runs.append(
            {
                "check_id": check_id,
                "next_run_at": next_run_at,
            }
        )
        return True

    monkeypatch.setattr(
        monitoring_job,
        "initialize_monitoring_check_next_run",
        fake_initialize,
    )

    current_time = datetime(
        2026,
        9,
        27,
        7,
        0,
        tzinfo=timezone.utc,
    )

    initialized_count = (
        monitoring_job.initialize_next_run_times(
            current_time=current_time,
        )
    )

    assert initialized_count == 1
    assert len(saved_next_runs) == 1
    assert (
        saved_next_runs[0]["check_id"]
        == "check-123"
    )

    next_run_at = saved_next_runs[0][
        "next_run_at"
    ]

    assert isinstance(next_run_at, datetime)
    assert next_run_at.tzinfo == timezone.utc


def test_due_check_runs_and_next_time_is_saved(
    monkeypatch,
):
    check = build_scheduled_check()
    saved_next_runs = []

    monkeypatch.setattr(
        monitoring_job,
        "list_uninitialized_scheduled_checks",
        lambda: [],
    )

    monkeypatch.setattr(
        monitoring_job,
        "list_due_monitoring_checks",
        lambda current_time: [check],
    )

    monkeypatch.setattr(
        monitoring_job,
        "claim_due_monitoring_check",
        lambda **kwargs: True,
    )

    monkeypatch.setattr(
        monitoring_job,
        "run_generic_monitoring_check",
        lambda check_id, source: {
            "run_id": "run-123",
            "monitoring_check_id": check_id,
            "status": "passed",
        },
    )

    def fake_complete(
        *,
        check_id,
        next_run_at,
    ):
        saved_next_runs.append(
            {
                "check_id": check_id,
                "next_run_at": next_run_at,
            }
        )
        return True

    monkeypatch.setattr(
        monitoring_job,
        "complete_monitoring_check_schedule",
        fake_complete,
    )

    result = (
        monitoring_job.run_due_monitoring_checks()
    )

    assert result["initialized_count"] == 0
    assert result["due_count"] == 1
    assert result["claimed_count"] == 1
    assert result["passed_count"] == 1
    assert result["failed_count"] == 0
    assert result["error_count"] == 0
    assert result["skipped_count"] == 0

    assert len(saved_next_runs) == 1
    assert (
        saved_next_runs[0]["check_id"]
        == "check-123"
    )
    assert (
        saved_next_runs[0]["next_run_at"].tzinfo
        == timezone.utc
    )


def test_failed_validation_is_counted(
    monkeypatch,
):
    check = build_scheduled_check()

    monkeypatch.setattr(
        monitoring_job,
        "list_uninitialized_scheduled_checks",
        lambda: [],
    )

    monkeypatch.setattr(
        monitoring_job,
        "list_due_monitoring_checks",
        lambda current_time: [check],
    )

    monkeypatch.setattr(
        monitoring_job,
        "claim_due_monitoring_check",
        lambda **kwargs: True,
    )

    monkeypatch.setattr(
        monitoring_job,
        "run_generic_monitoring_check",
        lambda check_id, source: {
            "run_id": "run-failed",
            "monitoring_check_id": check_id,
            "status": "failed",
        },
    )

    monkeypatch.setattr(
        monitoring_job,
        "complete_monitoring_check_schedule",
        lambda **kwargs: True,
    )

    result = (
        monitoring_job.run_due_monitoring_checks()
    )

    assert result["due_count"] == 1
    assert result["passed_count"] == 0
    assert result["failed_count"] == 1
    assert result["error_count"] == 0


def test_execution_error_does_not_stop_other_checks(
    monkeypatch,
):
    first_check = build_scheduled_check(
        "check-error"
    )
    second_check = build_scheduled_check(
        "check-passed"
    )

    completed_schedules = []

    monkeypatch.setattr(
        monitoring_job,
        "list_uninitialized_scheduled_checks",
        lambda: [],
    )

    monkeypatch.setattr(
        monitoring_job,
        "list_due_monitoring_checks",
        lambda current_time: [
            first_check,
            second_check,
        ],
    )

    monkeypatch.setattr(
        monitoring_job,
        "claim_due_monitoring_check",
        lambda **kwargs: True,
    )

    def fake_run(
        check_id,
        source,
    ):
        if check_id == "check-error":
            raise TimeoutError(
                "External API timed out."
            )

        return {
            "run_id": "run-passed",
            "monitoring_check_id": check_id,
            "status": "passed",
        }

    monkeypatch.setattr(
        monitoring_job,
        "run_generic_monitoring_check",
        fake_run,
    )

    def fake_complete(
        *,
        check_id,
        next_run_at,
    ):
        completed_schedules.append(check_id)
        return True

    monkeypatch.setattr(
        monitoring_job,
        "complete_monitoring_check_schedule",
        fake_complete,
    )

    result = (
        monitoring_job.run_due_monitoring_checks()
    )

    assert result["due_count"] == 2
    assert result["claimed_count"] == 2
    assert result["passed_count"] == 1
    assert result["error_count"] == 1

    assert completed_schedules == [
        "check-error",
        "check-passed",
    ]


def test_unclaimed_check_is_skipped(
    monkeypatch,
):
    check = build_scheduled_check()

    monkeypatch.setattr(
        monitoring_job,
        "list_uninitialized_scheduled_checks",
        lambda: [],
    )

    monkeypatch.setattr(
        monitoring_job,
        "list_due_monitoring_checks",
        lambda current_time: [check],
    )

    monkeypatch.setattr(
        monitoring_job,
        "claim_due_monitoring_check",
        lambda **kwargs: False,
    )

    def unexpected_run(*args, **kwargs):
        raise AssertionError(
            "An unclaimed check must not run."
        )

    monkeypatch.setattr(
        monitoring_job,
        "run_generic_monitoring_check",
        unexpected_run,
    )

    result = (
        monitoring_job.run_due_monitoring_checks()
    )

    assert result["due_count"] == 1
    assert result["claimed_count"] == 0
    assert result["skipped_count"] == 1
    assert result["passed_count"] == 0
    assert result["error_count"] == 0