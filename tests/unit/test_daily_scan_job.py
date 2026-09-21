import json

import pytest

import jobs.daily_lexicon_scan as daily_job


@pytest.mark.parametrize(
    ("failed_count", "expected_exit_code"),
    [
        (0, 0),
        (2, 1),
    ],
)
def test_daily_scan_job_returns_correct_exit_code(
    monkeypatch,
    capsys,
    failed_count,
    expected_exit_code,
):
    indexes_created = {"value": False}

    def fake_ensure_indexes():
        indexes_created["value"] = True

    summary = {
        "run_date": "2026-09-16",
        "scheduled_count": 8,
        "completed_count": 8 - failed_count,
        "failed_count": failed_count,
        "completed": [],
        "failed": [],
    }

    monkeypatch.setattr(
        daily_job,
        "ensure_database_indexes",
        fake_ensure_indexes,
    )

    monkeypatch.setattr(
        daily_job,
        "run_daily_lexicon_scans",
        lambda: summary,
    )

    exit_code = daily_job.main()

    printed_output = capsys.readouterr().out
    printed_summary = json.loads(printed_output)

    assert indexes_created["value"] is True
    assert printed_summary == summary
    assert exit_code == expected_exit_code