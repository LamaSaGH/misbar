from typing import Any

from mcp.server import MCPServer

from platforms.sewar.api_client import search_word
from services.check_service import (
    run_search_api_health_check,
    run_website_uptime_check,
    run_word_visibility_check,
)
from services.scan_service import run_lexicon_scan
from services.schedule_service import run_scheduled_check
from storage.check_runs import list_check_runs
from storage.scheduled_checks import (
    create_scheduled_check,
    get_scheduled_check,
    list_scheduled_checks,
    set_scheduled_check_status,
)


mcp = MCPServer("Sewar Monitor")


@mcp.tool()
def verify_word_visibility(
    word: str,
    expected_visible: bool,
    expected_dictionary: str | None = None,
) -> dict[str, Any]:
    """Verify whether a word has the expected public visibility."""
    return run_word_visibility_check(
        word=word,
        expected_visible=expected_visible,
        expected_dictionary=expected_dictionary,
        source="mcp",
    )


@mcp.tool()
def lookup_word_details(
    word: str,
    max_entries: int = 10,
) -> dict[str, Any]:
    """
    Return definitions, roots, examples, translations, and
    dictionary information for a word from Sewar's live API.
    """
    normalized_word = word.strip()

    if not normalized_word:
        raise ValueError("word must not be empty.")

    if max_entries < 1 or max_entries > 50:
        raise ValueError(
            "max_entries must be between 1 and 50."
        )

    response = search_word(normalized_word)
    entries = response.get("entries") or []

    results = []

    for entry in entries[:max_entries]:
        senses = []

        for sense in entry.get("senses") or []:
            synset = sense.get("synset") or {}

            senses.append(
                {
                    "definition": sense.get("definition"),
                    "contexts": sense.get("contexts") or [],
                    "examples": sense.get("examples") or [],
                    "translations": (
                        sense.get("translations") or []
                    ),
                    "relations": sense.get("relations") or [],
                    "domains": sense.get("domains") or [],
                    "synset": {
                        "name": synset.get("name"),
                        "description": synset.get(
                            "description"
                        ),
                        "code": synset.get("code"),
                    },
                }
            )

        results.append(
            {
                "lexical_entry_id": entry.get(
                    "lexicalEntryId"
                ),
                "lexicon_id": entry.get("lexiconId"),
                "lexicon_name": entry.get("lexiconName"),
                "lemma": entry.get("lemma"),
                "non_diacritics_lemma": entry.get(
                    "nonDiacriticsLemma"
                ),
                "lemma_type": entry.get("lemmaType"),
                "root": entry.get("root"),
                "part_of_speech": entry.get("pos"),
                "pattern": entry.get("pattern"),
                "senses": senses,
                "word_forms": entry.get("wordForms") or [],
                "entry_relations": (
                    entry.get("entryRelations") or []
                ),
            }
        )

    return {
        "word": normalized_word,
        "matching_entries_count": len(entries),
        "returned_count": len(results),
        "entries": results,
    }


@mcp.tool()
def check_website_uptime() -> dict[str, Any]:
    """Check whether the public Sewar website is reachable."""
    return run_website_uptime_check(source="mcp")


@mcp.tool()
def check_search_api_health(
    probe_word: str = "سلام",
) -> dict[str, Any]:
    """Check Sewar's public search API and response structure."""
    return run_search_api_health_check(
        probe_word=probe_word,
        source="mcp",
    )


@mcp.tool()
def get_recent_checks(
    limit: int = 20,
    check_type: str | None = None,
) -> list[dict[str, Any]]:
    """Return recent monitoring results from MongoDB."""
    return list_check_runs(
        limit=limit,
        check_type=check_type,
    )


@mcp.tool()
def scan_dictionary(
    lexicon_id: str,
    lexicon_name: str,
) -> dict[str, Any]:
    """Scan one Sewar dictionary and detect entry changes."""
    return run_lexicon_scan(
        lexicon_id=lexicon_id,
        lexicon_name=lexicon_name,
        source="mcp",
    )


@mcp.tool()
def create_monitoring_schedule(
    name: str,
    check_type: str,
    frequency: str,
    run_time: str,
    parameters: dict[str, Any] | None = None,
    timezone_name: str = "Asia/Riyadh",
) -> dict[str, Any]:
    """
    Create a recurring Sewar monitoring schedule.

    Supported check types:
    website_uptime, search_api_health,
    word_visibility, dictionary_scan.

    Supported frequencies:
    daily, weekly, monthly.

    run_time must use the 24-hour HH:MM format.
    """
    schedule_id = create_scheduled_check(
        name=name,
        check_type=check_type,
        frequency=frequency,
        run_time=run_time,
        parameters=parameters,
        timezone_name=timezone_name,
    )

    schedule = get_scheduled_check(schedule_id)

    if schedule is None:
        raise RuntimeError(
            "The schedule was created but could not be retrieved."
        )

    return schedule


@mcp.tool()
def get_monitoring_schedules(
    status: str | None = None,
) -> list[dict[str, Any]]:
    """List active, paused, or all monitoring schedules."""
    return list_scheduled_checks(status=status)


@mcp.tool()
def pause_monitoring_schedule(
    schedule_id: str,
) -> dict[str, Any]:
    """Pause an existing monitoring schedule."""
    updated = set_scheduled_check_status(
        schedule_id=schedule_id,
        status="paused",
    )

    if not updated:
        raise ValueError("Scheduled check not found.")

    schedule = get_scheduled_check(schedule_id)

    if schedule is None:
        raise ValueError("Scheduled check not found.")

    return schedule


@mcp.tool()
def resume_monitoring_schedule(
    schedule_id: str,
) -> dict[str, Any]:
    """Resume a paused monitoring schedule."""
    updated = set_scheduled_check_status(
        schedule_id=schedule_id,
        status="active",
    )

    if not updated:
        raise ValueError("Scheduled check not found.")

    schedule = get_scheduled_check(schedule_id)

    if schedule is None:
        raise ValueError("Scheduled check not found.")

    return schedule


@mcp.tool()
def run_monitoring_schedule_now(
    schedule_id: str,
) -> dict[str, Any]:
    """Run an existing monitoring schedule immediately."""
    return run_scheduled_check(schedule_id)