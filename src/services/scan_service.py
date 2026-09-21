from typing import Any

from platforms.sewar.api_client import (
    iter_lexicon_word_pages,
)
from storage.lexicon_entries import (
    deactivate_missing_entries,
    get_active_entry_ids,
    get_lexicon_entries_by_ids,
    upsert_lexicon_entries,
)
from storage.scan_changes import save_scan_changes
from storage.scan_runs import (
    finish_scan_run,
    get_latest_completed_scan,
    start_scan_run,
)


def run_lexicon_scan(
    *,
    lexicon_id: str,
    lexicon_name: str,
    source: str = "scheduled",
    rows: int = 500,
    language_code: str = "ar",
) -> dict[str, Any]:
    previous_scan = get_latest_completed_scan(
        lexicon_id
    )

    previous_entry_ids = get_active_entry_ids(
        lexicon_id
    )

    is_baseline = previous_scan is None

    scan_run_id = start_scan_run(
        lexicon_id=lexicon_id,
        lexicon_name=lexicon_name,
        source=source,
    )

    unique_entries: dict[str, dict[str, Any]] = {}

    try:
        for page in iter_lexicon_word_pages(
            lexicon_id=lexicon_id,
            rows=rows,
            language_code=language_code,
        ):
            for entry in page["words"]:
                unique_entries[
                    entry["lexical_entry_id"]
                ] = entry

        current_entry_ids = set(unique_entries)

        if is_baseline:
            added_entry_ids: set[str] = set()
            removed_entry_ids: set[str] = set()
        else:
            added_entry_ids = (
                current_entry_ids
                - previous_entry_ids
            )

            removed_entry_ids = (
                previous_entry_ids
                - current_entry_ids
            )

        added_entries = [
            {
                "lexical_entry_id": entry_id,
                "word": unique_entries[
                    entry_id
                ]["word"],
                "language_code": unique_entries[
                    entry_id
                ].get("language_code"),
                "belongs_to": unique_entries[
                    entry_id
                ].get("belongs_to"),
                "is_active": True,
            }
            for entry_id in sorted(
                added_entry_ids
            )
        ]

        removed_entries = get_lexicon_entries_by_ids(
            lexicon_id=lexicon_id,
            lexical_entry_ids=removed_entry_ids,
        )

        for entry in removed_entries:
            entry["is_active"] = False

        removed_entries.sort(
            key=lambda entry: entry[
                "lexical_entry_id"
            ]
        )

        added_count = len(added_entries)

        entries = list(unique_entries.values())

        for start in range(
            0,
            len(entries),
            1_000,
        ):
            batch = entries[
                start : start + 1_000
            ]

            upsert_lexicon_entries(
                lexicon_id=lexicon_id,
                entries=batch,
                scan_run_id=scan_run_id,
            )

        removed_count = deactivate_missing_entries(
            lexicon_id=lexicon_id,
            scan_run_id=scan_run_id,
        )

        saved_change_count = save_scan_changes(
            scan_run_id=scan_run_id,
            lexicon_id=lexicon_id,
            added_entries=added_entries,
            removed_entries=removed_entries,
        )

        finish_scan_run(
            scan_run_id=scan_run_id,
            status="completed",
            total_entries=len(
                current_entry_ids
            ),
            added_count=added_count,
            removed_count=removed_count,
            is_baseline=is_baseline,
        )

        return {
            "scan_run_id": scan_run_id,
            "lexicon_id": lexicon_id,
            "lexicon_name": lexicon_name,
            "status": "completed",
            "is_baseline": is_baseline,
            "total_entries": len(
                current_entry_ids
            ),
            "added_count": added_count,
            "removed_count": removed_count,
            "saved_change_count": (
                saved_change_count
            ),
            "added_entries": added_entries,
            "removed_entries": removed_entries,
            "changes_detected": (
                not is_baseline
                and (
                    added_count > 0
                    or removed_count > 0
                )
            ),
        }

    except Exception as error:
        finish_scan_run(
            scan_run_id=scan_run_id,
            status="failed",
            total_entries=len(
                unique_entries
            ),
            added_count=0,
            removed_count=0,
            is_baseline=is_baseline,
            error=(
                f"{type(error).__name__}: "
                f"{error}"
            ),
        )

        raise