from platforms.sewar.change_detection import (
    compare_word_snapshots,
    evaluate_word_snapshot,
)

def test_compare_word_snapshots_detects_added_and_removed_words():
    previous_words = [
        {
            "word": "سلام",
            "lexical_entry_id": "entry-1",
            "language_code": "ar",
            "belongs_to": "lemma",
        },
        {
            "word": "قديم",
            "lexical_entry_id": "entry-2",
            "language_code": "ar",
            "belongs_to": "lemma",
        },
    ]

    current_words = [
        {
            "word": "سلام",
            "lexical_entry_id": "entry-1",
            "language_code": "ar",
            "belongs_to": "lemma",
        },
        {
            "word": "جديد",
            "lexical_entry_id": "entry-3",
            "language_code": "ar",
            "belongs_to": "lemma",
        },
    ]

    result = compare_word_snapshots(
        previous_words=previous_words,
        current_words=current_words,
    )

    assert result["has_changes"] is True
    assert result["added_count"] == 1
    assert result["removed_count"] == 1
    assert result["added"][0]["word"] == "جديد"
    assert result["removed"][0]["word"] == "قديم"
    
def test_first_scan_creates_baseline_without_notification():
    current_words = [
        {
            "word": "سلام",
            "lexical_entry_id": "entry-1",
            "language_code": "ar",
            "belongs_to": "lemma",
        }
    ]

    result = evaluate_word_snapshot(
        previous_words=None,
        current_words=current_words,
    )

    assert result["status"] == "baseline"
    assert result["should_notify"] is False
    assert result["current_count"] == 1
    assert result["added_count"] == 0


def test_unchanged_snapshot_does_not_create_notification():
    words = [
        {
            "word": "سلام",
            "lexical_entry_id": "entry-1",
            "language_code": "ar",
            "belongs_to": "lemma",
        }
    ]

    result = evaluate_word_snapshot(
        previous_words=words,
        current_words=words,
    )

    assert result["status"] == "unchanged"
    assert result["should_notify"] is False
    assert result["has_changes"] is False


def test_changed_snapshot_requires_notification():
    previous_words = [
        {
            "word": "قديم",
            "lexical_entry_id": "entry-1",
            "language_code": "ar",
            "belongs_to": "lemma",
        }
    ]

    current_words = [
        {
            "word": "جديد",
            "lexical_entry_id": "entry-2",
            "language_code": "ar",
            "belongs_to": "lemma",
        }
    ]

    result = evaluate_word_snapshot(
        previous_words=previous_words,
        current_words=current_words,
    )

    assert result["status"] == "changed"
    assert result["should_notify"] is True
    assert result["added_count"] == 1
    assert result["removed_count"] == 1