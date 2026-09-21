
from platforms.sewar.api_client import (
    get_lexicon_word_page,
    iter_lexicon_word_pages,
)


def test_get_lexicon_word_page_returns_words():
    result = get_lexicon_word_page(
        lexicon_id="Riyadh",
        first=0,
        rows=5,
    )

    assert result["lexicon_id"] == "Riyadh"
    assert result["lexicon_name"]
    assert result["total_words_count"] > 0
    assert result["total_entries_count"] > 0

    assert 0 < result["returned_count"] <= 5
    assert len(result["words"]) == result["returned_count"]

    for item in result["words"]:
        assert item["word"]
        assert item["lexical_entry_id"]
        assert item["language_code"] == "ar"
        
def test_lexicon_word_pages_do_not_repeat_entries():
    first_page = get_lexicon_word_page(
        lexicon_id="Riyadh",
        first=0,
        rows=5,
    )

    second_page = get_lexicon_word_page(
        lexicon_id="Riyadh",
        first=5,
        rows=5,
    )

    first_page_records = {
        (
            item["word"],
            item["lexical_entry_id"],
            item["belongs_to"],
        )
        for item in first_page["words"]
    }

    second_page_records = {
        (
            item["word"],
            item["lexical_entry_id"],
            item["belongs_to"],
        )
        for item in second_page["words"]
    }

    assert first_page["returned_count"] == 5
    assert second_page["returned_count"] == 5
    assert first_page_records.isdisjoint(second_page_records)
    
def test_iter_lexicon_word_pages_moves_to_next_offset():
    pages = list(
        iter_lexicon_word_pages(
            lexicon_id="Riyadh",
            rows=5,
            max_pages=2,
        )
    )

    assert len(pages) == 2
    assert pages[0]["first"] == 0
    assert pages[1]["first"] == 5
    assert pages[0]["returned_count"] == 5
    assert pages[1]["returned_count"] == 5