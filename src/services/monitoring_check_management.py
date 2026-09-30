from storage.check_runs import (
    monitoring_check_has_runs,
)
from storage.monitoring_checks import (
    delete_archived_monitoring_check,
    get_monitoring_check,
)


class MonitoringCheckNotFoundError(
    ValueError
):
    pass


class MonitoringCheckDeletionConflictError(
    ValueError
):
    pass


def delete_unused_monitoring_check(
    check_id: str,
) -> None:
    check = get_monitoring_check(check_id)

    if check is None:
        raise MonitoringCheckNotFoundError(
            "Monitoring check not found."
        )

    if check["status"] != "archived":
        raise MonitoringCheckDeletionConflictError(
            "The monitoring check must be archived "
            "before it can be deleted."
        )

    if monitoring_check_has_runs(check_id):
        raise MonitoringCheckDeletionConflictError(
            "The monitoring check cannot be deleted "
            "because it has saved run history. "
            "Keep it archived instead."
        )

    deleted = delete_archived_monitoring_check(
        check_id
    )

    if not deleted:
        raise MonitoringCheckDeletionConflictError(
            "The monitoring check could not be deleted. "
            "It may have been executed or modified."
        )