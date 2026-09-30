from unittest.mock import Mock

from fastapi.testclient import TestClient

import web_api.app as app_module


def test_lifespan_keeps_scheduler_disabled(
    monkeypatch,
):
    ensure_indexes = Mock()

    monkeypatch.setattr(
        app_module,
        "ensure_database_indexes",
        ensure_indexes,
    )
    monkeypatch.setattr(
        app_module,
        "is_scheduler_enabled",
        lambda: False,
    )

    with TestClient(app_module.app):
        assert app_module.app.state.scheduler is None

    ensure_indexes.assert_called_once_with()


def test_lifespan_starts_and_stops_scheduler(
    monkeypatch,
):
    ensure_indexes = Mock()
    scheduler = Mock()
    scheduler.running = True

    monkeypatch.setattr(
        app_module,
        "ensure_database_indexes",
        ensure_indexes,
    )
    monkeypatch.setattr(
        app_module,
        "is_scheduler_enabled",
        lambda: True,
    )
    monkeypatch.setattr(
        app_module,
        "create_scheduler",
        lambda: scheduler,
    )

    with TestClient(app_module.app):
        scheduler.start.assert_called_once_with()
        assert app_module.app.state.scheduler is scheduler

    scheduler.shutdown.assert_called_once_with(
        wait=False,
    )
    ensure_indexes.assert_called_once_with()