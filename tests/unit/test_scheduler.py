import pytest

from services.scheduler import (
    SCHEDULE_POLL_JOB_ID,
    create_scheduler,
    is_scheduler_enabled,
)


def test_scheduler_is_disabled_by_default(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.delenv(
        "MISBAR_SCHEDULER_ENABLED",
        raising=False,
    )

    assert is_scheduler_enabled() is False


@pytest.mark.parametrize(
    "value",
    [
        "1",
        "true",
        "TRUE",
        "yes",
        "YES",
        "on",
        "ON",
        " true ",
    ],
)
def test_scheduler_accepts_true_environment_values(
    monkeypatch: pytest.MonkeyPatch,
    value: str,
):
    monkeypatch.setenv(
        "MISBAR_SCHEDULER_ENABLED",
        value,
    )

    assert is_scheduler_enabled() is True


@pytest.mark.parametrize(
    "value",
    [
        "0",
        "false",
        "no",
        "off",
        "",
        "invalid",
    ],
)
def test_scheduler_rejects_other_environment_values(
    monkeypatch: pytest.MonkeyPatch,
    value: str,
):
    monkeypatch.setenv(
        "MISBAR_SCHEDULER_ENABLED",
        value,
    )

    assert is_scheduler_enabled() is False


def test_scheduler_registers_polling_job():
    scheduler = create_scheduler()

    job = scheduler.get_job(SCHEDULE_POLL_JOB_ID)

    assert job is not None
    assert job.id == SCHEDULE_POLL_JOB_ID
    assert job.trigger.interval.total_seconds() == 60
    assert job.max_instances == 1
    assert job.coalesce is True