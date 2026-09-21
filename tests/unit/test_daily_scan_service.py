from datetime import date

import services.daily_scan_service as daily_scan_service


def test_daily_runner_continues_when_one_scan_fails(
    monkeypatch,
):
    lexicons = [
        {
            "lexicon_id": "lexicon-1",
            "name": "First Lexicon",
        },
        {
            "lexicon_id": "lexicon-2",
            "name": "Second Lexicon",
        },
    ]

    monkeypatch.setattr(
        daily_scan_service,
        "get_public_lexicons",
        lambda: lexicons,
    )

    monkeypatch.setattr(
        daily_scan_service,
        "get_lexicons_for_date",
        lambda all_lexicons, run_date: all_lexicons,
    )

    def fake_scan(**kwargs):
        if kwargs["lexicon_id"] == "lexicon-2":
            raise TimeoutError("Sewar timed out")

        return {
            "lexicon_id": kwargs["lexicon_id"],
            "status": "completed",
        }

    monkeypatch.setattr(
        daily_scan_service,
        "run_lexicon_scan",
        fake_scan,
    )

    result = daily_scan_service.run_daily_lexicon_scans(
        run_date=date(2026, 9, 16),
    )

    assert result["run_date"] == "2026-09-16"
    assert result["scheduled_count"] == 2
    assert result["completed_count"] == 1
    assert result["failed_count"] == 1

    assert result["completed"][0]["lexicon_id"] == "lexicon-1"

    assert result["failed"][0]["lexicon_id"] == "lexicon-2"
    assert (
        result["failed"][0]["error"]
        == "TimeoutError: Sewar timed out"
    )