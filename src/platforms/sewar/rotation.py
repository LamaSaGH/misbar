from datetime import date

WORKDAYS = (
    "sunday",
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
)


def get_eligible_lexicons(lexicons):
    eligible = [
        lexicon
        for lexicon in lexicons
        if lexicon.get("status") == "APPROVED"
        and not lexicon.get("is_soon", False)
        and lexicon.get("is_searchable") is not False
    ]

    return sorted(
        eligible,
        key=lambda lexicon: lexicon["lexicon_id"],
    )


def build_workweek_plan(lexicons):
    eligible = get_eligible_lexicons(lexicons)

    base_size, remainder = divmod(
        len(eligible),
        len(WORKDAYS),
    )

    plan = {}
    start = 0

    for index, day in enumerate(WORKDAYS):
        day_size = base_size

        if index < remainder:
            day_size += 1

        plan[day] = eligible[start : start + day_size]
        start += day_size

    return plan

PYTHON_WEEKDAY_TO_WORKDAY = {
    6: "sunday",
    0: "monday",
    1: "tuesday",
    2: "wednesday",
    3: "thursday",
}


def get_lexicons_for_date(lexicons, run_date):
    weekday = run_date.weekday()

    workday = PYTHON_WEEKDAY_TO_WORKDAY.get(weekday)

    # Friday and Saturday are not working days.
    if workday is None:
        return []

    plan = build_workweek_plan(lexicons)

    return plan[workday]