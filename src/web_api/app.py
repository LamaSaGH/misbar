from pathlib import Path
from typing import Annotated, Any

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from services.check_service import (
    run_search_api_health_check,
    run_website_uptime_check,
    run_word_visibility_check,
)
from services.schedule_service import (
    run_scheduled_check,
)
from storage.check_runs import list_check_runs
from storage.mongodb import ping_database
from storage.scan_changes import list_scan_changes
from storage.scan_runs import (
    get_scan_run,
    list_scan_runs,
)
from storage.scheduled_checks import (
    create_scheduled_check,
    get_scheduled_check,
    list_scheduled_checks,
    set_scheduled_check_status,
)


app = FastAPI(
    title="Sewar Monitor API",
    version="0.1.0",
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DASHBOARD_FILE = PROJECT_ROOT / "index.html"


class WordVisibilityRequest(BaseModel):
    word: str = Field(min_length=1)
    expected_visible: bool
    expected_dictionary: str | None = None


class SearchApiHealthRequest(BaseModel):
    probe_word: str = Field(
        default="سلام",
        min_length=1,
    )


class ScheduledCheckCreateRequest(BaseModel):
    name: str = Field(min_length=1)
    check_type: str
    frequency: str
    run_time: str = Field(
        pattern=r"^(?:[01]\d|2[0-3]):[0-5]\d$"
    )
    parameters: dict[str, Any] = Field(
        default_factory=dict
    )
    timezone_name: str = "Asia/Riyadh"


class ScheduledCheckStatusRequest(BaseModel):
    status: str


@app.get("/", include_in_schema=False)
def dashboard():
    return FileResponse(DASHBOARD_FILE)


@app.get("/api/health")
def application_health():
    return {
        "status": "passed",
        "database_connected": ping_database(),
    }


@app.get("/api/checks")
def recent_checks(
    limit: Annotated[
        int,
        Query(ge=1, le=200),
    ] = 20,
    check_type: str | None = None,
):
    return list_check_runs(
        limit=limit,
        check_type=check_type,
    )


@app.get("/api/scans")
def recent_scans(
    limit: Annotated[
        int,
        Query(ge=1, le=200),
    ] = 50,
    lexicon_id: str | None = None,
    status: str | None = None,
):
    try:
        return list_scan_runs(
            limit=limit,
            lexicon_id=lexicon_id,
            status=status,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error


@app.get(
    "/api/scans/{scan_run_id}/changes"
)
def scan_run_changes(
    scan_run_id: str,
    limit: Annotated[
        int,
        Query(ge=1, le=1_000),
    ] = 200,
    change_type: str | None = None,
):
    scan = get_scan_run(scan_run_id)

    if scan is None:
        raise HTTPException(
            status_code=404,
            detail="Scan run not found.",
        )

    try:
        changes = list_scan_changes(
            scan_run_id=scan_run_id,
            change_type=change_type,
            limit=limit,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error

    return {
        "scan": scan,
        "changes": changes,
        "returned_count": len(changes),
    }


@app.post("/api/checks/word-visibility")
def word_visibility_check(
    request: WordVisibilityRequest,
):
    return run_word_visibility_check(
        word=request.word,
        expected_visible=request.expected_visible,
        expected_dictionary=(
            request.expected_dictionary
        ),
        source="dashboard",
    )


@app.post("/api/checks/website-uptime")
def website_uptime_check():
    return run_website_uptime_check(
        source="dashboard"
    )


@app.post("/api/checks/search-api-health")
def search_api_health_check(
    request: SearchApiHealthRequest,
):
    return run_search_api_health_check(
        probe_word=request.probe_word,
        source="dashboard",
    )


@app.get("/api/schedules")
def recent_schedules(
    status: str | None = None,
):
    return list_scheduled_checks(
        status=status
    )


@app.post("/api/schedules", status_code=201)
def create_schedule(
    request: ScheduledCheckCreateRequest,
):
    try:
        schedule_id = create_scheduled_check(
            name=request.name,
            check_type=request.check_type,
            frequency=request.frequency,
            run_time=request.run_time,
            parameters=request.parameters,
            timezone_name=request.timezone_name,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error

    schedule = get_scheduled_check(
        schedule_id
    )

    if schedule is None:
        raise HTTPException(
            status_code=500,
            detail=(
                "The schedule was created but "
                "could not be retrieved."
            ),
        )

    return schedule


@app.patch(
    "/api/schedules/{schedule_id}/status"
)
def update_schedule_status(
    schedule_id: str,
    request: ScheduledCheckStatusRequest,
):
    try:
        updated = set_scheduled_check_status(
            schedule_id=schedule_id,
            status=request.status,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error

    if not updated:
        raise HTTPException(
            status_code=404,
            detail="Scheduled check not found.",
        )

    schedule = get_scheduled_check(
        schedule_id
    )

    if schedule is None:
        raise HTTPException(
            status_code=404,
            detail="Scheduled check not found.",
        )

    return schedule


@app.post(
    "/api/schedules/{schedule_id}/run"
)
def run_schedule_now(
    schedule_id: str,
):
    try:
        return run_scheduled_check(
            schedule_id
        )

    except ValueError as error:
        status_code = (
            404
            if str(error)
            == "Scheduled check not found."
            else 400
        )

        raise HTTPException(
            status_code=status_code,
            detail=str(error),
        ) from error

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=(
                "Scheduled check execution "
                "failed."
            ),
        ) from error