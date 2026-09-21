from platforms.sewar.api_client import get_public_lexicons

def test_get_public_lexicons_returns_valid_data():
    lexicons = get_public_lexicons()

    assert len(lexicons) > 0

    lexicon_ids = []

    for lexicon in lexicons:
        assert lexicon["lexicon_id"]
        assert lexicon["name"]

        lexicon_ids.append(lexicon["lexicon_id"])

    # Every dictionary should have a unique identifier.
    assert len(lexicon_ids) == len(set(lexicon_ids))