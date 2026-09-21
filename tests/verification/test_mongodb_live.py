from storage.mongodb import get_database, ping_database
from bson import ObjectId
from storage.check_runs import (
    get_check_run,
    list_check_runs,
    save_check_run,
)
from storage.scan_runs import (
    finish_scan_run,
    get_scan_run,
    start_scan_run,
)
from storage.lexicon_entries import (
    deactivate_missing_entries,
    get_active_entry_ids,
    upsert_lexicon_entries,
)
def test_mongodb_is_reachable():
    assert ping_database() is True


def test_expected_mongodb_database_is_selected():
    database = get_database()

    assert database.name == "sewar_monitor"
    
    
def test_check_run_can_be_saved_and_retrieved():
    run_id = save_check_run(
        check_type="database_test",
        status="passed",
        source="verification",
        request={"word": "سلام"},
        result={"actual_visible": True},
    )

    try:
        stored_run = get_check_run(run_id)

        assert stored_run is not None
        assert stored_run["_id"] == run_id
        assert stored_run["platform"] == "sewar"
        assert stored_run["check_type"] == "database_test"
        assert stored_run["status"] == "passed"
        assert stored_run["source"] == "verification"
        assert stored_run["request"]["word"] == "سلام"
        assert stored_run["result"]["actual_visible"] is True
        assert stored_run["created_at"] is not None
    finally:
        database = get_database()
        database["check_runs"].delete_one(
            {"_id": ObjectId(run_id)}
        )
        
def test_recent_check_runs_are_returned_newest_first():
    first_id = save_check_run(
        check_type="history_test",
        status="passed",
        source="verification",
        request={"order": 1},
        result={"message": "first"},
    )

    second_id = save_check_run(
        check_type="history_test",
        status="failed",
        source="verification",
        request={"order": 2},
        result={"message": "second"},
    )

    try:
        history = list_check_runs(
            limit=2,
            check_type="history_test",
        )

        assert len(history) == 2
        assert history[0]["_id"] == second_id
        assert history[0]["request"]["order"] == 2
        assert history[1]["_id"] == first_id
        assert history[1]["request"]["order"] == 1
    finally:
        database = get_database()
        database["check_runs"].delete_many(
            {
                "_id": {
                    "$in": [
                        ObjectId(first_id),
                        ObjectId(second_id),
                    ]
                }
            }
        )
        
def test_scan_run_moves_from_running_to_completed():
    scan_run_id = start_scan_run(
        lexicon_id="test-lexicon",
        lexicon_name="Test Lexicon",
        source="verification",
    )

    try:
        running_scan = get_scan_run(scan_run_id)

        assert running_scan is not None
        assert running_scan["status"] == "running"
        assert running_scan["completed_at"] is None

        finish_scan_run(
            scan_run_id=scan_run_id,
            status="completed",
            total_entries=100,
            added_count=3,
            removed_count=1,
        )

        completed_scan = get_scan_run(scan_run_id)

        assert completed_scan is not None
        assert completed_scan["status"] == "completed"
        assert completed_scan["total_entries"] == 100
        assert completed_scan["added_count"] == 3
        assert completed_scan["removed_count"] == 1
        assert completed_scan["completed_at"] is not None
        assert completed_scan["error"] is None
    finally:
        database = get_database()
        database["scan_runs"].delete_one(
            {"_id": ObjectId(scan_run_id)}
        )
        
def test_lexicon_entries_track_added_and_removed_words():
    lexicon_id = "verification-test-lexicon"
    database = get_database()

    database["lexicon_entries"].delete_many(
        {"lexicon_id": lexicon_id}
    )

    try:
        first_entries = [
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

        first_count = upsert_lexicon_entries(
            lexicon_id=lexicon_id,
            entries=first_entries,
            scan_run_id="scan-1",
        )

        assert first_count == 2
        assert get_active_entry_ids(lexicon_id) == {
            "entry-1",
            "entry-2",
        }

        second_entries = [
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

        second_count = upsert_lexicon_entries(
            lexicon_id=lexicon_id,
            entries=second_entries,
            scan_run_id="scan-2",
        )

        removed_count = deactivate_missing_entries(
            lexicon_id=lexicon_id,
            scan_run_id="scan-2",
        )

        assert second_count == 2
        assert removed_count == 1
        assert get_active_entry_ids(lexicon_id) == {
            "entry-1",
            "entry-3",
        }

        removed_entry = database[
            "lexicon_entries"
        ].find_one(
            {
                "lexicon_id": lexicon_id,
                "lexical_entry_id": "entry-2",
            }
        )

        assert removed_entry["is_active"] is False
        assert removed_entry["removed_at"] is not None
    finally:
        database["lexicon_entries"].delete_many(
            {"lexicon_id": lexicon_id}
        )