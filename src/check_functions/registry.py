from collections.abc import Callable
from typing import Any

import requests

from check_functions.common import (
    expected_status_code,
    json_field_equals,
    json_field_exists,
    json_list_not_empty,
    response_contains_text,
    response_header_exists,
    status_code_200,
)


CheckFunction = Callable[..., dict[str, Any]]


CHECK_FUNCTIONS: dict[str, CheckFunction] = {
    "status_code_200": status_code_200,
    "expected_status_code": expected_status_code,
    "response_contains_text": (
        response_contains_text
    ),
    "json_field_exists": json_field_exists,
    "json_field_equals": json_field_equals,
    "json_list_not_empty": json_list_not_empty,
    "response_header_exists": (
        response_header_exists
    ),
}


CHECK_FUNCTION_METADATA: dict[
    str,
    dict[str, Any],
] = {
    "status_code_200": {
        "name": "status_code_200",
        "display_name": "حالة الاستجابة 200",
        "description": (
            "يتحقق من أن رمز استجابة HTTP يساوي 200."
        ),
        "response_type": "any",
        "parameters": [],
    },
    "expected_status_code": {
        "name": "expected_status_code",
        "display_name": "رمز استجابة محدد",
        "description": (
            "يتحقق من أن رمز HTTP يطابق القيمة المحددة."
        ),
        "response_type": "any",
        "parameters": [
            {
                "name": "expected_status_code",
                "type": "integer",
                "required": True,
                "description": (
                    "رمز HTTP المتوقع."
                ),
                "example": 200,
            }
        ],
    },
    "response_contains_text": {
        "name": "response_contains_text",
        "display_name": "وجود نص في الاستجابة",
        "description": (
            "يتحقق من وجود نص محدد داخل محتوى الاستجابة."
        ),
        "response_type": "text",
        "parameters": [
            {
                "name": "expected_text",
                "type": "string",
                "required": True,
                "description": "النص المطلوب.",
                "example": "success",
            },
            {
                "name": "case_sensitive",
                "type": "boolean",
                "required": False,
                "default": True,
                "description": (
                    "هل يؤخذ اختلاف حالة الأحرف في الحسبان؟"
                ),
                "example": False,
            },
        ],
    },
    "json_field_exists": {
        "name": "json_field_exists",
        "display_name": "وجود حقل JSON",
        "description": (
            "يتحقق من وجود مسار داخل استجابة JSON."
        ),
        "response_type": "json",
        "parameters": [
            {
                "name": "json_path",
                "type": "string",
                "required": True,
                "description": (
                    "مسار الحقل باستخدام النقاط."
                ),
                "example": "data.user.id",
            }
        ],
    },
    "json_field_equals": {
        "name": "json_field_equals",
        "display_name": "مطابقة قيمة JSON",
        "description": (
            "يتحقق من أن قيمة مسار JSON تطابق "
            "القيمة المتوقعة."
        ),
        "response_type": "json",
        "parameters": [
            {
                "name": "json_path",
                "type": "string",
                "required": True,
                "description": (
                    "مسار القيمة باستخدام النقاط."
                ),
                "example": "data.status",
            },
            {
                "name": "expected_value",
                "type": "any",
                "required": True,
                "description": "القيمة المتوقعة.",
                "example": "active",
            },
        ],
    },
    "json_list_not_empty": {
        "name": "json_list_not_empty",
        "display_name": "قائمة JSON غير فارغة",
        "description": (
            "يتحقق من أن المسار موجود ويحتوي "
            "على قائمة غير فارغة."
        ),
        "response_type": "json",
        "parameters": [
            {
                "name": "json_path",
                "type": "string",
                "required": True,
                "description": "مسار القائمة.",
                "example": "data.entries",
            }
        ],
    },
    "response_header_exists": {
        "name": "response_header_exists",
        "display_name": "وجود Response Header",
        "description": (
            "يتحقق من وجود Header محدد في الاستجابة."
        ),
        "response_type": "headers",
        "parameters": [
            {
                "name": "header_name",
                "type": "string",
                "required": True,
                "description": "اسم الـHeader المطلوب.",
                "example": "content-type",
            }
        ],
    },
}


def get_check_function(
    function_name: str,
) -> CheckFunction:
    normalized_name = function_name.strip()

    if not normalized_name:
        raise ValueError(
            "function_name must not be empty."
        )

    function = CHECK_FUNCTIONS.get(
        normalized_name
    )

    if function is None:
        available_functions = ", ".join(
            sorted(CHECK_FUNCTIONS)
        )

        raise ValueError(
            f"Unsupported function: "
            f"{normalized_name}. "
            f"Available functions: "
            f"{available_functions}."
        )

    return function


def run_registered_function(
    *,
    function_name: str,
    response: requests.Response,
    parameters: dict[str, Any] | None = None,
) -> dict[str, Any]:
    function = get_check_function(
        function_name
    )

    return function(
        response=response,
        parameters=parameters,
    )


def list_check_functions() -> list[str]:
    return sorted(CHECK_FUNCTIONS)


def list_check_function_definitions(
) -> list[dict[str, Any]]:
    definitions = []

    for function_name in sorted(
        CHECK_FUNCTIONS
    ):
        metadata = CHECK_FUNCTION_METADATA.get(
            function_name,
            {
                "name": function_name,
                "display_name": function_name,
                "description": None,
                "response_type": "any",
                "parameters": [],
            },
        )

        definitions.append(
            {
                **metadata,
                "registered": True,
            }
        )

    return definitions