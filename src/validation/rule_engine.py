from typing import Any

import requests


ALLOWED_LOGIC = {
    "all",
    "any",
}

ALLOWED_SOURCES = {
    "status_code",
    "response_time_ms",
    "json",
    "text",
    "header",
}

SOURCE_OPERATORS = {
    "status_code": {
        "equals",
        "not_equals",
    },
    "response_time_ms": {
        "less_than",
        "less_than_or_equal",
        "greater_than",
        "greater_than_or_equal",
    },
    "json": {
        "equals",
        "not_equals",
        "contains",
        "exists",
        "not_exists",
        "is_empty",
        "is_not_empty",
    },
    "text": {
        "contains",
        "not_contains",
        "equals",
    },
    "header": {
        "exists",
        "not_exists",
        "equals",
        "contains",
    },
}


def _resolve_json_path(
    data: Any,
    path: str,
) -> tuple[bool, Any]:
    normalized_path = path.strip()

    if not normalized_path:
        raise ValueError(
            "JSON validation requires a path."
        )

    current_value = data

    for part in normalized_path.split("."):
        if isinstance(current_value, dict):
            if part not in current_value:
                return False, None

            current_value = current_value[part]
            continue

        if isinstance(current_value, list):
            try:
                index = int(part)
            except ValueError:
                return False, None

            if (
                index < 0
                or index >= len(current_value)
            ):
                return False, None

            current_value = current_value[index]
            continue

        return False, None

    return True, current_value


def _compare_values(
    *,
    actual: Any,
    operator: str,
    expected: Any = None,
    exists: bool = True,
) -> bool:
    if operator == "exists":
        return exists

    if operator == "not_exists":
        return not exists

    if not exists:
        return False

    if operator == "equals":
        return actual == expected

    if operator == "not_equals":
        return actual != expected

    if operator == "contains":
        try:
            return expected in actual
        except TypeError:
            return False

    if operator == "not_contains":
        try:
            return expected not in actual
        except TypeError:
            return False

    if operator == "is_empty":
        try:
            return len(actual) == 0
        except TypeError:
            return False

    if operator == "is_not_empty":
        try:
            return len(actual) > 0
        except TypeError:
            return False

    if operator == "less_than":
        try:
            return actual < expected
        except TypeError:
            return False

    if operator == "less_than_or_equal":
        try:
            return actual <= expected
        except TypeError:
            return False

    if operator == "greater_than":
        try:
            return actual > expected
        except TypeError:
            return False

    if operator == "greater_than_or_equal":
        try:
            return actual >= expected
        except TypeError:
            return False

    raise ValueError(
        f"Unsupported operator: {operator}"
    )


def validate_validation_rules(
    *,
    validations: list[dict[str, Any]],
    validation_logic: str,
) -> None:
    if validation_logic not in ALLOWED_LOGIC:
        raise ValueError(
            "validation_logic must be all or any."
        )

    if not isinstance(validations, list):
        raise ValueError(
            "validations must be a list."
        )

    if not validations:
        raise ValueError(
            "At least one validation rule is required."
        )

    if len(validations) > 20:
        raise ValueError(
            "A check cannot contain more than "
            "20 validation rules."
        )

    for index, rule in enumerate(validations):
        if not isinstance(rule, dict):
            raise ValueError(
                f"Validation rule {index + 1} "
                "must be an object."
            )

        source = rule.get("source")
        operator = rule.get("operator")

        if source not in ALLOWED_SOURCES:
            raise ValueError(
                f"Unsupported validation source: "
                f"{source}"
            )

        if operator not in SOURCE_OPERATORS[source]:
            raise ValueError(
                f"Operator '{operator}' is not "
                f"supported for source '{source}'."
            )

        if (
            source == "json"
            and not str(rule.get("path", "")).strip()
        ):
            raise ValueError(
                "JSON validation requires a path."
            )

        if (
            source == "header"
            and not str(rule.get("name", "")).strip()
        ):
            raise ValueError(
                "Header validation requires a name."
            )

        operators_without_expected = {
            "exists",
            "not_exists",
            "is_empty",
            "is_not_empty",
        }

        if (
            operator not in operators_without_expected
            and "expected" not in rule
        ):
            raise ValueError(
                f"Validation rule {index + 1} "
                "requires an expected value."
            )


def _evaluate_rule(
    *,
    response: requests.Response,
    response_time_ms: int,
    rule: dict[str, Any],
) -> dict[str, Any]:
    source = rule["source"]
    operator = rule["operator"]
    expected = rule.get("expected")

    path = None
    name = None
    exists = True

    if source == "status_code":
        actual = response.status_code

    elif source == "response_time_ms":
        actual = response_time_ms

    elif source == "text":
        actual = response.text

        if (
            rule.get("case_sensitive", True)
            is False
        ):
            actual = actual.casefold()

            if isinstance(expected, str):
                expected = expected.casefold()

    elif source == "header":
        name = str(rule["name"]).strip()
        exists = name in response.headers
        actual = response.headers.get(name)

        if (
            rule.get("case_sensitive", False)
            is False
            and isinstance(actual, str)
            and isinstance(expected, str)
        ):
            actual = actual.casefold()
            expected = expected.casefold()

    elif source == "json":
        path = str(rule["path"]).strip()

        try:
            response_json = response.json()
        except ValueError:
            exists = False
            actual = None
        else:
            exists, actual = _resolve_json_path(
                response_json,
                path,
            )

    else:
        raise ValueError(
            f"Unsupported validation source: "
            f"{source}"
        )

    passed = _compare_values(
        actual=actual,
        operator=operator,
        expected=expected,
        exists=exists,
    )

    return {
        "passed": passed,
        "source": source,
        "operator": operator,
        "path": path,
        "name": name,
        "expected": expected,
        "actual": actual,
        "exists": exists,
        "message": (
            "Validation rule passed."
            if passed
            else "Validation rule failed."
        ),
    }


def evaluate_validation_rules(
    *,
    response: requests.Response,
    response_time_ms: int,
    validations: list[dict[str, Any]],
    validation_logic: str = "all",
) -> dict[str, Any]:
    validate_validation_rules(
        validations=validations,
        validation_logic=validation_logic,
    )

    results = [
        _evaluate_rule(
            response=response,
            response_time_ms=response_time_ms,
            rule=rule,
        )
        for rule in validations
    ]

    if validation_logic == "all":
        passed = all(
            result["passed"]
            for result in results
        )
    else:
        passed = any(
            result["passed"]
            for result in results
        )

    passed_count = sum(
        result["passed"]
        for result in results
    )

    return {
        "passed": passed,
        "validation_type": "rules",
        "validation_logic": validation_logic,
        "total_count": len(results),
        "passed_count": passed_count,
        "failed_count": (
            len(results) - passed_count
        ),
        "results": results,
        "message": (
            "All required validation rules passed."
            if passed
            else "One or more validation rules failed."
        ),
    }