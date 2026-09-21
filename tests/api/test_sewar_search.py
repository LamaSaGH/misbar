from platforms.sewar.api_client import search_word
from uuid import uuid4
import pytest
def test_search_returns_known_word():
    data = search_word("سلام")
    entries = data.get("entries", [])

    assert entries, "Sewar returned no entries for the known word سلام."

    assert any(
        entry.get("nonDiacriticsLemma") == "سلام"
        for entry in entries
    ), "The exact word سلام was not found in the returned entries."

def test_search_response_has_required_structure():
    response = search_word("سلام")

    assert isinstance(response, dict)

    entries = response.get("entries")

    assert isinstance(entries, list)
    assert len(entries) > 0

    assert all(
        isinstance(entry, dict)
        for entry in entries
    )

    assert any(
        isinstance(entry.get("lexiconName"), str)
        and entry["lexiconName"].strip()
        for entry in entries
    )

    assert any(
        isinstance(entry.get("senses"), list)
        for entry in entries
    )

def test_search_returns_no_entries_for_unknown_word():
    unknown_word = f"sewarmonitor{uuid4().hex}"

    response = search_word(unknown_word)
    entries = response.get("entries")

    assert isinstance(entries, list)
    assert entries == []

@pytest.mark.parametrize(
    "query",
    [
        "  سلام  ",
        "سَلَام",
    ],
)
def test_search_handles_common_input_variations(query):
    response = search_word(query)
    entries = response.get("entries")

    assert isinstance(entries, list)
    assert len(entries) > 0


def test_search_rejects_empty_input():
    with pytest.raises(
        ValueError,
        match="cannot be empty",
    ):
        search_word("   ")