from platforms.sewar.api_client import search_word
from requests.exceptions import RequestException
def verify_word_exists(word: str) -> dict:
    cleaned_word = word.strip()
    data = search_word(cleaned_word)
    entries = data.get("entries", [])

    exact_matches = [
        entry
        for entry in entries
        if entry.get("nonDiacriticsLemma") == cleaned_word
    ]

    dictionaries = sorted({
        entry.get("lexiconName")
        for entry in exact_matches
        if entry.get("lexiconName")
    })

    return {
        "word": cleaned_word,
        "found": bool(exact_matches),
        "matching_entries_count": len(exact_matches),
        "dictionaries": dictionaries,
        "entries": exact_matches,
    }


def get_dictionary_definitions(word: str, dictionary: str) -> dict:
    result = verify_word_exists(word)

    matching_entries = [
        entry
        for entry in result["entries"]
        if entry.get("lexiconName") == dictionary
    ]

    definitions = []

    for entry in matching_entries:
        for sense in entry.get("senses") or []:
            definition = sense.get("definition")

            if isinstance(definition, str) and definition.strip():
                definitions.append(definition.strip())

    return {
        "word": result["word"],
        "dictionary": dictionary,
        "found_in_dictionary": bool(matching_entries),
        "matching_entries_count": len(matching_entries),
        "definitions": definitions,
    }
    
def verify_word_visibility(
    word,
    expected_visible,
    expected_dictionary=None,
):
    if not isinstance(expected_visible, bool):
        raise ValueError("expected_visible must be True or False")

    scope = (
        "dictionary"
        if expected_dictionary
        else "global")
    try:
        search_result = search_word(word)
    except RequestException as error:
        return {
            "check_type": "word_visibility",
            "word": word,
            "scope": scope,
            "expected_dictionary": expected_dictionary,
            "expected_visible": expected_visible,
            "actual_visible": None,
            "passed": None,
            "status": "error",
            "found_in_dictionaries": [],
            "matching_entries_count": 0,
            "error_type": type(error).__name__,
            "error_message": str(error), }
        
    all_entries = search_result.get("entries") or []

    if expected_dictionary:
        expected_dictionary_clean = expected_dictionary.strip()

        matching_entries = [
            entry
            for entry in all_entries
            if (entry.get("lexiconName") or "").strip()
            == expected_dictionary_clean
        ]

        scope = "dictionary"
    else:
        matching_entries = all_entries
        scope = "global"

    actual_visible = len(matching_entries) > 0
    passed = actual_visible == expected_visible

    found_in_dictionaries = sorted({
        entry["lexiconName"].strip()
        for entry in all_entries
        if entry.get("lexiconName")
    })

    return {
        "check_type": "word_visibility",
        "word": word,
        "scope": scope,
        "expected_dictionary": expected_dictionary,
        "expected_visible": expected_visible,
        "actual_visible": actual_visible,
        "passed": passed,
        "status": "passed" if passed else "failed",
        "found_in_dictionaries": found_in_dictionaries,
        "matching_entries_count": len(matching_entries),
    }