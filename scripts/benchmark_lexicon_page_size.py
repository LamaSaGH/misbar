from time import perf_counter

from platforms.sewar.api_client import get_lexicon_word_page


LEXICON_ID = "Riyadh"
PAGE_SIZES = (30, 100, 300, 500)


for page_size in PAGE_SIZES:
    started_at = perf_counter()

    try:
        result = get_lexicon_word_page(
            lexicon_id=LEXICON_ID,
            first=0,
            rows=page_size,
        )

        elapsed = perf_counter() - started_at

        print(
            f"Requested: {page_size:>3} | "
            f"Returned: {result['returned_count']:>3} | "
            f"Time: {elapsed:.2f}s"
        )

    except Exception as error:
        elapsed = perf_counter() - started_at

        print(
            f"Requested: {page_size:>3} | "
            f"FAILED after {elapsed:.2f}s | "
            f"{type(error).__name__}: {error}"
        )