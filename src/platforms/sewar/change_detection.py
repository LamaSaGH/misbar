def word_record_key(record):
    return (
        record["word"].strip(),
        record["lexical_entry_id"],
        record.get("language_code"),
        record.get("belongs_to"),
    )


def compare_word_snapshots(previous_words, current_words):
    previous_records = {
        word_record_key(record): record
        for record in previous_words
    }

    current_records = {
        word_record_key(record): record
        for record in current_words
    }

    added = [
        record
        for key, record in current_records.items()
        if key not in previous_records
    ]

    removed = [
        record
        for key, record in previous_records.items()
        if key not in current_records
    ]

    return {
        "has_changes": bool(added or removed),
        "added_count": len(added),
        "removed_count": len(removed),
        "added": added,
        "removed": removed,
    }
    
def evaluate_word_snapshot(previous_words, current_words):
    if previous_words is None:
        return {
            "status": "baseline",
            "should_notify": False,
            "has_changes": False,
            "current_count": len(current_words),
            "added_count": 0,
            "removed_count": 0,
            "added": [],
            "removed": [],
        }

    comparison = compare_word_snapshots(
        previous_words=previous_words,
        current_words=current_words,
    )

    return {
        **comparison,
        "status": (
            "changed"
            if comparison["has_changes"]
            else "unchanged"
        ),
        "should_notify": comparison["has_changes"],
        "current_count": len(current_words),
    }