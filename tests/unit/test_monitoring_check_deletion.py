import pytest

import services.monitoring_check_management as management


def test_archived_unused_check_can_be_deleted(
    monkeypatch,
):
    deleted_check_ids = []

    monkeypatch.setattr(
        management,
        "get_monitoring_check",
        lambda check_id: {
            "_id": check_id,
            "status": "archived",
        },
    )

    monkeypatch.setattr(
        management,
        "monitoring_check_has_runs",
        lambda check_id: False,
    )

    def fake_delete(check_id):
        deleted_check_ids.append(check_id)
        return True

    monkeypatch.setattr(
        management,
        "delete_archived_monitoring_check",
        fake_delete,
    )

    management.delete_unused_monitoring_check(
        "check-123"
    )

    assert deleted_check_ids == [
        "check-123",
    ]


def test_active_check_cannot_be_deleted(
    monkeypatch,
):
    monkeypatch.setattr(
        management,
        "get_monitoring_check",
        lambda check_id: {
            "_id": check_id,
            "status": "active",
        },
    )

    with pytest.raises(
        management.MonitoringCheckDeletionConflictError,
        match="must be archived",
    ):
        management.delete_unused_monitoring_check(
            "check-123"
        )


def test_check_with_history_cannot_be_deleted(
    monkeypatch,
):
    monkeypatch.setattr(
        management,
        "get_monitoring_check",
        lambda check_id: {
            "_id": check_id,
            "status": "archived",
        },
    )

    monkeypatch.setattr(
        management,
        "monitoring_check_has_runs",
        lambda check_id: True,
    )

    with pytest.raises(
        management.MonitoringCheckDeletionConflictError,
        match="saved run history",
    ):
        management.delete_unused_monitoring_check(
            "check-123"
        )


def test_missing_check_returns_not_found(
    monkeypatch,
):
    monkeypatch.setattr(
        management,
        "get_monitoring_check",
        lambda check_id: None,
    )

    with pytest.raises(
        management.MonitoringCheckNotFoundError,
        match="not found",
    ):
        management.delete_unused_monitoring_check(
            "missing-check"
        )