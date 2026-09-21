import pytest
from requests.exceptions import Timeout
import platforms.sewar.verifier as verifier


def make_api_entry():
    return {
        "lemma": "سلام",
        "lexiconName": "معجم الرياض",
        "senses": [
            {
                "definition": "التحية"
            }
        ],
    }


@pytest.mark.parametrize(
    (
        "expected_visible",
        "actual_visible",
        "expected_passed",
    ),
    [
        (True, True, True),
        (True, False, False),
        (False, False, True),
        (False, True, False),
    ],
)
def test_verify_word_visibility(
    monkeypatch,
    expected_visible,
    actual_visible,
    expected_passed,
):
    api_entries = [make_api_entry()] if actual_visible else []

    monkeypatch.setattr(
        verifier,
        "search_word",
        lambda word: {
            "entries": api_entries,
        },
    )

    result = verifier.verify_word_visibility(
        word="سلام",
        expected_visible=expected_visible,
    )

    assert result["actual_visible"] is actual_visible
    assert result["passed"] is expected_passed

    expected_status = (
        "passed"
        if expected_passed
        else "failed"
    )

    assert result["status"] == expected_status


def test_visibility_can_be_limited_to_a_dictionary(monkeypatch):
    monkeypatch.setattr(
        verifier,
        "search_word",
        lambda word: {
            "entries": [make_api_entry()],
        },
    )

    visible_in_riyadh = verifier.verify_word_visibility(
        word="سلام",
        expected_visible=True,
        expected_dictionary="معجم الرياض",
    )

    hidden_in_another_dictionary = verifier.verify_word_visibility(
        word="سلام",
        expected_visible=False,
        expected_dictionary="معجم آخر",
    )

    assert visible_in_riyadh["scope"] == "dictionary"
    assert visible_in_riyadh["actual_visible"] is True
    assert visible_in_riyadh["passed"] is True

    assert hidden_in_another_dictionary["actual_visible"] is False
    assert hidden_in_another_dictionary["passed"] is True

    assert hidden_in_another_dictionary["found_in_dictionaries"] == [
        "معجم الرياض"
    ]

def test_api_failure_is_error_not_hidden(monkeypatch):
    def raise_timeout(word):
        raise Timeout("Sewar request timed out")

    monkeypatch.setattr(
        verifier,
        "search_word",
        raise_timeout,
    )

    result = verifier.verify_word_visibility(
        word="example_word",
        expected_visible=False,
    )

    assert result["status"] == "error"
    assert result["actual_visible"] is None
    assert result["passed"] is None
    assert result["error_type"] == "Timeout"