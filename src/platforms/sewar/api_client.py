from urllib.parse import quote

import requests

BASE_URL = "https://siwar.ksaa.gov.sa"


def search_word(word: str) -> dict:
    cleaned_word = word.strip()

    if not cleaned_word:
        raise ValueError("The search word cannot be empty.")

    encoded_word = quote(cleaned_word, safe="")
    url = f"{BASE_URL}/api/search/alt/global-public/{encoded_word}"

    response = requests.get(
        url,
        headers={"Accept": "application/json"},
        timeout=30,
    )

    response.raise_for_status()
    return response.json()



def get_public_lexicons():
    url = "https://siwar.ksaa.gov.sa/api/lexicons/findAll/public"

    response = requests.get(
        url,
        headers={
            "Accept": "application/json",
            "Cache-Control": "no-cache",
        },
        timeout=30,
    )

    response.raise_for_status()
    data = response.json()

    if not isinstance(data, list):
        raise ValueError(
            f"Expected a list of lexicons, received {type(data).__name__}"
        )

    lexicons = []

    for item in data:
        lexicon_id = item.get("_id")
        name = item.get("name")

        # Ignore incomplete records that cannot be used later.
        if not lexicon_id or not name:
            continue

        public_profile = item.get("publicProfile") or {}

        lexicons.append(
            {
                "lexicon_id": lexicon_id,
                "name": name.strip(),
                "status": item.get("status"),
                "is_soon": item.get("isSoon", False),
                "is_searchable": public_profile.get("isSearchable"),
            }
        )

    return lexicons

def get_lexicon_word_page(
    lexicon_id,
    first=0,
    rows=30,
    language_code="ar",
):
    if first < 0:
        raise ValueError("first cannot be negative")

    if rows <= 0:
        raise ValueError("rows must be greater than zero")

    encoded_lexicon_id = quote(lexicon_id, safe="")

    url = (
        "https://siwar.ksaa.gov.sa/"
        "api/screens/public/get-lexicon-search-screen-data/"
        f"{encoded_lexicon_id}?languageCode="
    )

    payload = {
        "preferences": {
            "first": first,
            "rows": rows,
            "filters": {
                "languageCode": [
                    {
                        "value": language_code,
                        "matchMode": "equals",
                        "operator": "and",
                    }
                ]
            },
            "multisortmeta": [],
        }
    }

    response = requests.post(
        url,
        json=payload,
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Origin": "https://siwar.ksaa.gov.sa",
            "Referer": "https://siwar.ksaa.gov.sa/",
        },
        timeout=30,
    )

    response.raise_for_status()
    data = response.json()

    lexicon = data.get("lexicon") or {}
    paginated = data.get("paginated") or {}
    raw_words = paginated.get("words") or []

    words = []

    for item in raw_words:
        word = item.get("word")
        lexical_entry_id = item.get("lexicalEntryId")

        if not word or not lexical_entry_id:
            continue

        words.append(
            {
                "word": word.strip(),
                "lexical_entry_id": lexical_entry_id,
                "language_code": item.get("languageCode"),
                "belongs_to": item.get("belongsTo"),
            }
        )

    return {
        "lexicon_id": lexicon.get("_id", lexicon_id),
        "lexicon_name": lexicon.get("name"),
        "total_entries_count": lexicon.get("totalEntriesCount"),
        "total_words_count": paginated.get("totalCount", 0),
        "first": first,
        "rows_requested": rows,
        "returned_count": len(words),
        "words": words,
    }
    
def iter_lexicon_word_pages(
    lexicon_id,
    rows=500,
    language_code="ar",
    max_pages=None,
):
    if rows <= 0:
        raise ValueError("rows must be greater than zero")

    if max_pages is not None and max_pages <= 0:
        raise ValueError("max_pages must be greater than zero")

    first = 0
    pages_fetched = 0

    while True:
        if max_pages is not None and pages_fetched >= max_pages:
            break

        page = get_lexicon_word_page(
            lexicon_id=lexicon_id,
            first=first,
            rows=rows,
            language_code=language_code,
        )

        yield page
        pages_fetched += 1

        if page["returned_count"] == 0:
            break

        first += rows
        total_words_count = page["total_words_count"]

        if first >= total_words_count:
            break