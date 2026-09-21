from platforms.sewar.verifier import verify_word_visibility


def test_known_word_is_publicly_visible():
    result = verify_word_visibility(
        word="سلام",
        expected_visible=True,
    )

    assert result["scope"] == "global"
    assert result["expected_visible"] is True
    assert result["actual_visible"] is True
    assert result["passed"] is True
    assert result["status"] == "passed"
    assert result["found_in_dictionaries"]