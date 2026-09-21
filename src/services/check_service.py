from typing import Any

from platforms.sewar.verifier import verify_word_visibility
from storage.check_runs import save_check_run

from platforms.sewar.health import (
    check_search_api_health,
    check_website_uptime,
)
def run_word_visibility_check(
    *,
    word: str,
    expected_visible: bool,
    expected_dictionary: str | None = None,
    source: str = "manual",
) -> dict[str, Any]:
    verification = verify_word_visibility(
        word=word,
        expected_visible=expected_visible,
        expected_dictionary=expected_dictionary,
    )

    if verification.get("status") == "error":
        status = "error"
    elif verification.get("passed") is True:
        status = "passed"
    else:
        status = "failed"

    request = {
        "word": word,
        "expected_visible": expected_visible,
        "expected_dictionary": expected_dictionary,
    }

    run_id = save_check_run(
        check_type="word_visibility",
        status=status,
        source=source,
        request=request,
        result=verification,
    )

    return {
        "run_id": run_id,
        "status": status,
        "verification": verification,
    }
    
def run_website_uptime_check(
    *,
    source: str = "manual",
) -> dict[str, Any]:
    check_result = check_website_uptime()
    status = check_result.get("status", "error")

    run_id = save_check_run(
        check_type="website_uptime",
        status=status,
        source=source,
        request={},
        result=check_result,
    )

    return {
        "run_id": run_id,
        "status": status,
        "check": check_result,
    }


def run_search_api_health_check(
    *,
    probe_word: str = "سلام",
    source: str = "manual",
) -> dict[str, Any]:
    check_result = check_search_api_health(
        probe_word=probe_word
    )
    status = check_result.get("status", "error")

    run_id = save_check_run(
        check_type="search_api_health",
        status=status,
        source=source,
        request={
            "probe_word": probe_word,
        },
        result=check_result,
    )

    return {
        "run_id": run_id,
        "status": status,
        "check": check_result,
    }