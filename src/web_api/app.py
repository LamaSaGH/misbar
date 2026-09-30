from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated, Any

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel, Field

from check_functions.registry import list_check_function_definitions
from services.generic_check_service import run_generic_monitoring_check
from services.scheduler import create_scheduler, is_scheduler_enabled
from storage.check_runs import list_check_runs
from storage.indexes import ensure_database_indexes
from storage.mongodb import ping_database
from storage.monitoring_checks import (
    create_monitoring_check,
    delete_monitoring_check as delete_monitoring_check_record,
    get_monitoring_check,
    list_monitoring_checks,
    set_monitoring_check_status,
    update_monitoring_check,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    ensure_database_indexes()

    scheduler = None

    if is_scheduler_enabled():
        scheduler = create_scheduler()
        scheduler.start()

    app.state.scheduler = scheduler

    try:
        yield
    finally:
        if scheduler is not None and scheduler.running:
            scheduler.shutdown(wait=False)


app = FastAPI(
    title="Misbar Platform Monitoring API",
    description=(
        "Create, save, run, edit, and schedule reusable "
        "monitoring checks for digital platforms."
    ),
    version="0.4.0",
    lifespan=lifespan,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DASHBOARD_FILE = PROJECT_ROOT / "index.html"


class MonitoringCheckRequest(BaseModel):
    name: str = Field(min_length=1)
    group: str = Field(min_length=1)
    request_url: str = Field(min_length=1)
    request_method: str = "GET"
    request_headers: dict[str, str] = Field(default_factory=dict)
    query_parameters: dict[str, Any] = Field(default_factory=dict)
    request_body: Any = None
    timeout_seconds: int = Field(default=15, ge=1, le=120)
    function_name: str | None = None
    function_parameters: dict[str, Any] = Field(default_factory=dict)
    validations: list[dict[str, Any]] = Field(default_factory=list)
    validation_logic: str = "all"
    tags: list[str] = Field(default_factory=list)
    schedule_enabled: bool = False
    frequency: str | None = None
    run_time: str | None = Field(
        default=None,
        pattern=r"^(?:[01]\d|2[0-3]):[0-5]\d$",
    )
    timezone_name: str = "Asia/Riyadh"


# Backward-compatible name used by existing tests and imports.
MonitoringCheckCreateRequest = MonitoringCheckRequest


class MonitoringCheckStatusRequest(BaseModel):
    status: str


def _check_arguments(
    request: MonitoringCheckRequest,
) -> dict[str, Any]:
    return {
        "name": request.name,
        "group": request.group,
        "request_url": request.request_url,
        "request_method": request.request_method,
        "request_headers": request.request_headers,
        "query_parameters": request.query_parameters,
        "request_body": request.request_body,
        "timeout_seconds": request.timeout_seconds,
        "function_name": request.function_name,
        "function_parameters": request.function_parameters,
        "validations": request.validations,
        "validation_logic": request.validation_logic,
        "tags": request.tags,
        "schedule_enabled": request.schedule_enabled,
        "frequency": request.frequency,
        "run_time": request.run_time,
        "timezone_name": request.timezone_name,
    }


@app.get("/", include_in_schema=False)
def dashboard():
    return FileResponse(DASHBOARD_FILE)


@app.get("/api/health")
def application_health():
    return {
        "status": "passed",
        "database_connected": ping_database(),
    }


@app.get("/api/check-functions")
def get_available_check_functions():
    functions = list_check_function_definitions()

    return {
        "functions": functions,
        "count": len(functions),
    }


@app.get("/api/check-runs")
def get_recent_check_runs(
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
):
    return list_check_runs(
        limit=limit,
        check_type="generic_api",
    )


@app.get("/api/monitoring-checks")
def get_monitoring_checks(
    limit: Annotated[int, Query(ge=1, le=200)] = 100,
    group: str | None = None,
    status: str | None = None,
    tag: str | None = None,
):
    try:
        return list_monitoring_checks(
            limit=limit,
            group=group,
            status=status,
            tag=tag,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error


@app.get("/api/monitoring-checks/{check_id}")
def get_monitoring_check_by_id(check_id: str):
    check = get_monitoring_check(check_id)

    if check is None:
        raise HTTPException(
            status_code=404,
            detail="Monitoring check not found.",
        )

    return check


@app.post("/api/monitoring-checks", status_code=201)
def create_generic_monitoring_check(
    request: MonitoringCheckRequest,
):
    try:
        check_id = create_monitoring_check(
            **_check_arguments(request),
        )
    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error

    check = get_monitoring_check(check_id)

    if check is None:
        raise HTTPException(
            status_code=500,
            detail=(
                "The monitoring check was created but could not "
                "be retrieved."
            ),
        )

    return check


@app.put("/api/monitoring-checks/{check_id}")
def edit_monitoring_check(
    check_id: str,
    request: MonitoringCheckRequest,
):
    try:
        updated = update_monitoring_check(
            check_id=check_id,
            **_check_arguments(request),
        )
    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error

    if not updated:
        raise HTTPException(
            status_code=404,
            detail="Monitoring check not found.",
        )

    check = get_monitoring_check(check_id)

    if check is None:
        raise HTTPException(
            status_code=404,
            detail="Monitoring check not found.",
        )

    return check


@app.patch("/api/monitoring-checks/{check_id}/status")
def update_monitoring_check_status(
    check_id: str,
    request: MonitoringCheckStatusRequest,
):
    try:
        updated = set_monitoring_check_status(
            check_id=check_id,
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
            detail="Monitoring check not found.",
        )

    check = get_monitoring_check(check_id)

    if check is None:
        raise HTTPException(
            status_code=404,
            detail="Monitoring check not found.",
        )

    return check


@app.post("/api/monitoring-checks/{check_id}/run")
def run_monitoring_check_now(check_id: str):
    try:
        return run_generic_monitoring_check(
            check_id,
            source="dashboard",
        )
    except ValueError as error:
        message = str(error)

        status_code = (
            404
            if message == "Monitoring check not found."
            else 400
        )

        raise HTTPException(
            status_code=status_code,
            detail=message,
        ) from error
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail="Monitoring check execution failed.",
        ) from error


@app.delete(
    "/api/monitoring-checks/{check_id}",
    status_code=204,
)
def delete_monitoring_check(check_id: str):
    deleted = delete_monitoring_check_record(check_id)

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Monitoring check not found.",
        )

    return Response(status_code=204)