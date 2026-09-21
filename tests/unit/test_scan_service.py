import pytest

import services.scan_service as scan_service


def test_first_scan_creates_baseline_without_changes(
    monkeypatch,
):
    pages = [
        {
            "words": [
                {
                    "lexical_entry_id": "entry-1",
                    "word": "سلام",
                    "language_code": "ar",
                    "belongs_to": "lemma",
                },
                {
                    "lexical_entry_id": "entry-2",
                    "word": "كتاب",
                    "language_code": "ar",
                    "belongs_to": "lemma",
                },
            ]
        }
    ]

    saved_entries = []
    saved_changes = {}
    finished_scan = {}

    monkeypatch.setattr(
        scan_service,
        "get_latest_completed_scan",
        lambda lexicon_id: None,
    )

    monkeypatch.setattr(
        scan_service,
        "get_active_entry_ids",
        lambda lexicon_id: set(),
    )

    monkeypatch.setattr(
        scan_service,
        "start_scan_run",
        lambda **kwargs: "scan-run-1",
    )

    monkeypatch.setattr(
        scan_service,
        "iter_lexicon_word_pages",
        lambda **kwargs: iter(pages),
    )

    def fake_upsert(**kwargs):
        saved_entries.extend(kwargs["entries"])
        return len(kwargs["entries"])

    monkeypatch.setattr(
        scan_service,
        "upsert_lexicon_entries",
        fake_upsert,
    )

    monkeypatch.setattr(
        scan_service,
        "get_lexicon_entries_by_ids",
        lambda **kwargs: [],
    )

    monkeypatch.setattr(
        scan_service,
        "deactivate_missing_entries",
        lambda **kwargs: 0,
    )

    def fake_save_changes(**kwargs):
        saved_changes.update(kwargs)
        return 0

    monkeypatch.setattr(
        scan_service,
        "save_scan_changes",
        fake_save_changes,
    )

    def fake_finish(**kwargs):
        finished_scan.update(kwargs)

    monkeypatch.setattr(
        scan_service,
        "finish_scan_run",
        fake_finish,
    )

    result = scan_service.run_lexicon_scan(
        lexicon_id="test-lexicon",
        lexicon_name="Test Lexicon",
        source="verification",
    )

    assert result["status"] == "completed"
    assert result["is_baseline"] is True
    assert result["total_entries"] == 2
    assert result["added_count"] == 0
    assert result["removed_count"] == 0
    assert result["saved_change_count"] == 0
    assert result["added_entries"] == []
    assert result["removed_entries"] == []
    assert result["changes_detected"] is False

    assert len(saved_entries) == 2

    assert saved_changes["scan_run_id"] == (
        "scan-run-1"
    )
    assert saved_changes["lexicon_id"] == (
        "test-lexicon"
    )
    assert saved_changes["added_entries"] == []
    assert saved_changes["removed_entries"] == []

    assert finished_scan["status"] == "completed"
    assert finished_scan["is_baseline"] is True
    assert finished_scan["total_entries"] == 2


def test_later_scan_detects_and_saves_changed_words(
    monkeypatch,
):
    pages = [
        {
            "words": [
                {
                    "lexical_entry_id": "entry-1",
                    "word": "سلام",
                    "language_code": "ar",
                    "belongs_to": "lemma",
                },
                {
                    "lexical_entry_id": "entry-3",
                    "word": "قلم",
                    "language_code": "ar",
                    "belongs_to": "lemma",
                },
            ]
        }
    ]

    saved_changes = {}
    finished_scan = {}

    monkeypatch.setattr(
        scan_service,
        "get_latest_completed_scan",
        lambda lexicon_id: {
            "_id": "previous-scan",
            "status": "completed",
        },
    )

    monkeypatch.setattr(
        scan_service,
        "get_active_entry_ids",
        lambda lexicon_id: {
            "entry-1",
            "entry-2",
        },
    )

    monkeypatch.setattr(
        scan_service,
        "start_scan_run",
        lambda **kwargs: "scan-run-2",
    )

    monkeypatch.setattr(
        scan_service,
        "iter_lexicon_word_pages",
        lambda **kwargs: iter(pages),
    )

    monkeypatch.setattr(
        scan_service,
        "get_lexicon_entries_by_ids",
        lambda **kwargs: [
            {
                "lexical_entry_id": "entry-2",
                "word": "كتاب",
                "language_code": "ar",
                "belongs_to": "lemma",
                "is_active": True,
            }
        ],
    )

    monkeypatch.setattr(
        scan_service,
        "upsert_lexicon_entries",
        lambda **kwargs: len(kwargs["entries"]),
    )

    monkeypatch.setattr(
        scan_service,
        "deactivate_missing_entries",
        lambda **kwargs: 1,
    )

    def fake_save_changes(**kwargs):
        saved_changes.update(kwargs)

        return (
            len(kwargs["added_entries"])
            + len(kwargs["removed_entries"])
        )

    monkeypatch.setattr(
        scan_service,
        "save_scan_changes",
        fake_save_changes,
    )

    def fake_finish(**kwargs):
        finished_scan.update(kwargs)

    monkeypatch.setattr(
        scan_service,
        "finish_scan_run",
        fake_finish,
    )

    result = scan_service.run_lexicon_scan(
        lexicon_id="test-lexicon",
        lexicon_name="Test Lexicon",
    )

    assert result["is_baseline"] is False
    assert result["total_entries"] == 2
    assert result["added_count"] == 1
    assert result["removed_count"] == 1
    assert result["saved_change_count"] == 2
    assert result["changes_detected"] is True

    assert result["added_entries"] == [
        {
            "lexical_entry_id": "entry-3",
            "word": "قلم",
            "language_code": "ar",
            "belongs_to": "lemma",
            "is_active": True,
        }
    ]

    assert result["removed_entries"] == [
        {
            "lexical_entry_id": "entry-2",
            "word": "كتاب",
            "language_code": "ar",
            "belongs_to": "lemma",
            "is_active": False,
        }
    ]

    assert saved_changes["scan_run_id"] == (
        "scan-run-2"
    )
    assert saved_changes["lexicon_id"] == (
        "test-lexicon"
    )
    assert saved_changes["added_entries"] == (
        result["added_entries"]
    )
    assert saved_changes["removed_entries"] == (
        result["removed_entries"]
    )

    assert finished_scan["status"] == "completed"
    assert finished_scan["added_count"] == 1
    assert finished_scan["removed_count"] == 1
    assert finished_scan["is_baseline"] is False


def test_failed_api_scan_does_not_update_entries(
    monkeypatch,
):
    finished_scan = {}

    monkeypatch.setattr(
        scan_service,
        "get_latest_completed_scan",
        lambda lexicon_id: {
            "_id": "previous-scan",
            "status": "completed",
        },
    )

    monkeypatch.setattr(
        scan_service,
        "get_active_entry_ids",
        lambda lexicon_id: {"entry-1"},
    )

    monkeypatch.setattr(
        scan_service,
        "start_scan_run",
        lambda **kwargs: "failed-scan",
    )

    def failing_pages(**kwargs):
        yield {
            "words": [
                {
                    "lexical_entry_id": "entry-1",
                    "word": "سلام",
                    "language_code": "ar",
                    "belongs_to": "lemma",
                }
            ]
        }

        raise TimeoutError("Sewar API timed out")

    monkeypatch.setattr(
        scan_service,
        "iter_lexicon_word_pages",
        failing_pages,
    )

    def unexpected_upsert(**kwargs):
        raise AssertionError(
            "Entries must not be updated "
            "after a partial scan."
        )

    monkeypatch.setattr(
        scan_service,
        "upsert_lexicon_entries",
        unexpected_upsert,
    )

    def unexpected_save_changes(**kwargs):
        raise AssertionError(
            "Changes must not be saved "
            "after a partial scan."
        )

    monkeypatch.setattr(
        scan_service,
        "save_scan_changes",
        unexpected_save_changes,
    )

    def fake_finish(**kwargs):
        finished_scan.update(kwargs)

    monkeypatch.setattr(
        scan_service,
        "finish_scan_run",
        fake_finish,
    )

    with pytest.raises(
        TimeoutError,
        match="Sewar API timed out",
    ):
        scan_service.run_lexicon_scan(
            lexicon_id="test-lexicon",
            lexicon_name="Test Lexicon",
        )

    assert finished_scan["status"] == "failed"
    assert finished_scan["removed_count"] == 0
    assert (
        finished_scan["error"]
        == "TimeoutError: Sewar API timed out"
    )