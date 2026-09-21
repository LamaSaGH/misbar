from datetime import date
from platforms.sewar.rotation import (
    WORKDAYS,
    build_workweek_plan,
    get_eligible_lexicons,
    get_lexicons_for_date,
)


def make_lexicon(
    number,
    status="APPROVED",
    is_soon=False,
    is_searchable=None,
):
    return {
        "lexicon_id": f"lexicon-{number:02}",
        "name": f"Dictionary {number}",
        "status": status,
        "is_soon": is_soon,
        "is_searchable": is_searchable,
    }


def test_38_lexicons_are_distributed_over_five_workdays():
    lexicons = [
        make_lexicon(number)
        for number in range(1, 39)
    ]

    plan = build_workweek_plan(lexicons)

    assert list(plan.keys()) == list(WORKDAYS)

    assert [
        len(plan[day])
        for day in WORKDAYS
    ] == [8, 8, 8, 7, 7]

    all_ids = [
        lexicon["lexicon_id"]
        for day in WORKDAYS
        for lexicon in plan[day]
    ]

    assert len(all_ids) == 38
    assert len(all_ids) == len(set(all_ids))


def test_ineligible_lexicons_are_excluded():
    lexicons = [
        make_lexicon(1),
        make_lexicon(2, status="DRAFT"),
        make_lexicon(3, is_soon=True),
        make_lexicon(4, is_searchable=False),
    ]

    eligible = get_eligible_lexicons(lexicons)

    assert [
        item["lexicon_id"]
        for item in eligible
    ] == ["lexicon-01"]
    
def test_correct_batch_is_selected_for_each_workday():
    lexicons = [
        make_lexicon(number)
        for number in range(1, 39)
    ]

    expected_sizes = {
        date(2026, 9, 20): 8,  # Sunday
        date(2026, 9, 21): 8,  # Monday
        date(2026, 9, 22): 8,  # Tuesday
        date(2026, 9, 23): 7,  # Wednesday
        date(2026, 9, 24): 7,  # Thursday
    }

    for run_date, expected_size in expected_sizes.items():
        selected = get_lexicons_for_date(
            lexicons,
            run_date,
        )

        assert len(selected) == expected_size


def test_weekend_returns_no_lexicons():
    lexicons = [
        make_lexicon(number)
        for number in range(1, 39)
    ]

    friday = date(2026, 9, 25)
    saturday = date(2026, 9, 26)

    assert get_lexicons_for_date(lexicons, friday) == []
    assert get_lexicons_for_date(lexicons, saturday) == []