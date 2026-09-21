from bson import ObjectId

from storage.mongodb import get_database
from storage.scheduled_checks import (
    create_scheduled_check,
    get_scheduled_check,
    list_scheduled_checks,
    set_scheduled_check_status,
)


def test_scheduled_check_can_be_created_and_paused():
    schedule_id = None

    try:
        schedule_id = create_scheduled_check(
            name="Sewar uptime test",
            check_type="website_uptime",
            frequency="daily",
            run_time="09:00",
        )

        created = get_scheduled_check(schedule_id)

        assert created is not None
        assert created["name"] == "Sewar uptime test"
        assert created["check_type"] == "website_uptime"
        assert created["frequency"] == "daily"
        assert created["status"] == "active"

        updated = set_scheduled_check_status(
            schedule_id=schedule_id,
            status="paused",
        )

        assert updated is True

        paused_schedules = list_scheduled_checks(
            status="paused",
        )

        assert any(
            schedule["_id"] == schedule_id
            for schedule in paused_schedules
        )

    finally:
        if schedule_id is not None:
            database = get_database()
            database["scheduled_checks"].delete_one(
                {"_id": ObjectId(schedule_id)}
            )