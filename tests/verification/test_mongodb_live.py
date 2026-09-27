from bson import ObjectId

from storage.check_runs import (
    get_check_run,
    list_check_runs,
    save_generic_check_run,
)
from storage.mongodb import (
    get_database,
    ping_database,
)


def test_mongodb_is_reachable():
    assert ping_database() is True


def test_expected_mongodb_database_is_selected():
    database = get_database()

    # This is the existing database name.
    # We can migrate it to misbar_monitor separately.
    assert database.name == "sewar_monitor"


def test_generic_check_run_can_be_saved_and_retrieved():
    run_id = save_generic_check_run(
        monitoring_check_id=(
            "verification-monitoring-check"
        ),
        check_name="Verification API check",
        group="Verification Platform",
        tags=[
            "verification",
            "api",
        ],
        status="passed",
        source="verification",
        function_name="rule_engine",
        request={
            "method": "GET",
            "url": "https://example.com/api/health",
            "headers": {},
            "query_parameters": {},
            "body": None,
            "timeout_seconds": 15,
        },
        result={
            "response": {
                "status_code": 200,
                "response_time_ms": 125,
                "content_type": "application/json",
            },
            "validation": {
                "passed": True,
                "logic": "all",
                "results": [
                    {
                        "source": "status_code",
                        "operator": "equals",
                        "expected": 200,
                        "actual": 200,
                        "passed": True,
                    }
                ],
            },
        },
    )

    try:
        stored_run = get_check_run(run_id)

        assert stored_run is not None
        assert stored_run["_id"] == run_id
        assert stored_run["platform"] == (
            "Verification Platform"
        )
        assert stored_run["group"] == (
            "Verification Platform"
        )
        assert stored_run["check_type"] == (
            "generic_api"
        )
        assert stored_run["status"] == "passed"
        assert stored_run["source"] == (
            "verification"
        )
        assert stored_run["function_name"] == (
            "rule_engine"
        )

        assert (
            stored_run["request"]["method"]
            == "GET"
        )

        assert (
            stored_run["result"]["response"][
                "status_code"
            ]
            == 200
        )

        assert stored_run["created_at"] is not None

    finally:
        database = get_database()

        database["check_runs"].delete_one(
            {
                "_id": ObjectId(run_id),
            }
        )


def test_recent_generic_runs_are_returned_newest_first():
    first_id = save_generic_check_run(
        monitoring_check_id="verification-check-1",
        check_name="First verification check",
        group="Verification Platform",
        tags=["verification"],
        status="passed",
        source="verification",
        function_name="rule_engine",
        request={
            "method": "GET",
            "url": "https://example.com/first",
        },
        result={
            "order": 1,
        },
    )

    second_id = save_generic_check_run(
        monitoring_check_id="verification-check-2",
        check_name="Second verification check",
        group="Verification Platform",
        tags=["verification"],
        status="failed",
        source="verification",
        function_name="rule_engine",
        request={
            "method": "GET",
            "url": "https://example.com/second",
        },
        result={
            "order": 2,
        },
    )

    try:
        history = list_check_runs(
            limit=2,
            check_type="generic_api",
        )

        assert len(history) == 2

        assert history[0]["_id"] == second_id
        assert history[0]["result"]["order"] == 2

        assert history[1]["_id"] == first_id
        assert history[1]["result"]["order"] == 1

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