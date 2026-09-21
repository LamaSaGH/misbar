from fastapi.testclient import TestClient

import web_api.app as web_app


client = TestClient(web_app.app)


def test_recent_scans_returns_scan_runs(
    monkeypatch,
):
    scans = [
        {
            "_id": "scan-123",
            "lexicon_id": "lexicon-123",
            "lexicon_name": "Test Dictionary",
            "status": "completed",
            "total_entries": 205,
            "added_count": 1,
            "removed_count": 0,
            "is_baseline": False,
        }
    ]

    monkeypatch.setattr(
        web_app,
        "list_scan_runs",
        lambda **kwargs: scans,
    )

    response = client.get(
        "/api/scans",
        params={
            "limit": 50,
            "status": "completed",
        },
    )

    assert response.status_code == 200
    assert response.json() == scans


def test_scan_changes_returns_exact_words(
    monkeypatch,
):
    scan = {
        "_id": "6aaac1a34da00a37c321f1d3",
        "lexicon_id": "lexicon-123",
        "lexicon_name": "Test Dictionary",
        "status": "completed",
        "added_count": 1,
        "removed_count": 1,
        "is_baseline": False,
    }

    changes = [
        {
            "scan_run_id": scan["_id"],
            "change_type": "added",
            "lexical_entry_id": "entry-2",
            "word": "كتاب",
        },
        {
            "scan_run_id": scan["_id"],
            "change_type": "removed",
            "lexical_entry_id": "entry-3",
            "word": "قلم",
        },
    ]

    monkeypatch.setattr(
        web_app,
        "get_scan_run",
        lambda scan_run_id: scan,
    )

    monkeypatch.setattr(
        web_app,
        "list_scan_changes",
        lambda **kwargs: changes,
    )

    response = client.get(
        f"/api/scans/{scan['_id']}/changes"
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["scan"] == scan
    assert payload["changes"] == changes
    assert payload["returned_count"] == 2

    assert payload["changes"][0]["word"] == "كتاب"
    assert payload["changes"][1]["word"] == "قلم"


def test_unknown_scan_returns_404(
    monkeypatch,
):
    monkeypatch.setattr(
        web_app,
        "get_scan_run",
        lambda scan_run_id: None,
    )

    response = client.get(
        "/api/scans/not-a-valid-scan/changes"
    )

    assert response.status_code == 404
    assert response.json()["detail"] == (
        "Scan run not found."
    )
    