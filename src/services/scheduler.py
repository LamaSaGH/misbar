from datetime import datetime, timezone
import os
from apscheduler.schedulers.background import BackgroundScheduler

from jobs.generic_monitoring_job import run_due_monitoring_checks


SCHEDULE_POLL_JOB_ID = "misbar-due-monitoring-checks"

SCHEDULER_ENABLED_ENV = "MISBAR_SCHEDULER_ENABLED"
TRUE_VALUES = {"1", "true", "yes", "on"}


def is_scheduler_enabled() -> bool:
    value = os.getenv(SCHEDULER_ENABLED_ENV, "false")
    return value.strip().lower() in TRUE_VALUES

def create_scheduler() -> BackgroundScheduler:
    scheduler = BackgroundScheduler(timezone="UTC")

    scheduler.add_job(
        run_due_monitoring_checks,
        trigger="interval",
        seconds=60,
        id=SCHEDULE_POLL_JOB_ID,
        replace_existing=True,
        max_instances=1,
        coalesce=True,
        next_run_time=datetime.now(timezone.utc),
    )

    return scheduler