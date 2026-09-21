from platforms.sewar.verifier import (
    get_dictionary_definitions,
    verify_word_exists,
)

def test_known_word_exists_in_expected_dictionary():
    result = verify_word_exists("سلام")

    assert result["found"] is True
    assert result["matching_entries_count"] > 0

    assert (
        "معجم الرياض للغة العربية المعاصرة"
        in result["dictionaries"]
    )
    
def test_known_word_contains_expected_meaning():
    result = get_dictionary_definitions(
        word="سلام",
        dictionary="معجم الرياض للغة العربية المعاصرة",
    )

    assert result["found_in_dictionary"] is True
    assert result["definitions"], "No definitions were returned."

    assert any(
        "أمن" in definition
        for definition in result["definitions"]
    ), "None of the definitions contained the expected meaning: أمن."