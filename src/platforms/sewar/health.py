from time import perf_counter
from platforms.sewar.api_client import search_word
import requests
from requests.exceptions import RequestException


SEWAR_HOME_URL = "https://siwar.ksaa.gov.sa/home"


def check_website_uptime(timeout=15):
    started_at = perf_counter()

    try:
        response = requests.get(
            SEWAR_HOME_URL,
            headers={
                "Accept": "text/html",
            },
            timeout=timeout,
        )

        duration_ms = round(
            (perf_counter() - started_at) * 1000,
            2,
        )

        is_up = 200 <= response.status_code < 400

        return {
            "check_type": "website_uptime",
            "platform": "sewar",
            "url": SEWAR_HOME_URL,
            "status": "passed" if is_up else "failed",
            "is_up": is_up,
            "http_status": response.status_code,
            "response_time_ms": duration_ms,
            "error_type": None,
            "error_message": None,
        }

    except RequestException as error:
        duration_ms = round(
            (perf_counter() - started_at) * 1000,
            2,
        )

        return {
            "check_type": "website_uptime",
            "platform": "sewar",
            "url": SEWAR_HOME_URL,
            "status": "error",
            "is_up": False,
            "http_status": None,
            "response_time_ms": duration_ms,
            "error_type": type(error).__name__,
            "error_message": str(error),
        }
        
def check_search_api_health(probe_word="سلام"):
    started_at = perf_counter()

    try:
        response = search_word(probe_word)

        duration_ms = round(
            (perf_counter() - started_at) * 1000,
            2,
        )

        entries = response.get("entries")
        schema_valid = isinstance(entries, list)

        entries_count = (
            len(entries)
            if schema_valid
            else 0
        )

        is_healthy = (
            schema_valid
            and entries_count > 0
        )

        return {
            "check_type": "search_api_health",
            "platform": "sewar",
            "status": (
                "passed"
                if is_healthy
                else "failed"
            ),
            "is_healthy": is_healthy,
            "probe_word": probe_word,
            "schema_valid": schema_valid,
            "entries_count": entries_count,
            "response_time_ms": duration_ms,
            "error_type": None,
            "error_message": None,
        }

    except RequestException as error:
        duration_ms = round(
            (perf_counter() - started_at) * 1000,
            2,
        )

        return {
            "check_type": "search_api_health",
            "platform": "sewar",
            "status": "error",
            "is_healthy": False,
            "probe_word": probe_word,
            "schema_valid": False,
            "entries_count": 0,
            "response_time_ms": duration_ms,
            "error_type": type(error).__name__,
            "error_message": str(error),
        }