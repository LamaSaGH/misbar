from fastapi.testclient import TestClient

from check_functions.registry import (
    list_check_function_definitions,
)
from web_api.app import app


client = TestClient(app)


def test_function_catalog_contains_all_functions():
    definitions = (
        list_check_function_definitions()
    )

    function_names = {
        definition["name"]
        for definition in definitions
    }

    assert function_names == {
        "expected_status_code",
        "json_field_equals",
        "json_field_exists",
        "json_list_not_empty",
        "response_contains_text",
        "response_header_exists",
        "status_code_200",
    }


def test_each_function_has_catalog_metadata():
    definitions = (
        list_check_function_definitions()
    )

    for definition in definitions:
        assert definition["name"]
        assert definition["display_name"]
        assert definition["description"]
        assert definition["response_type"]
        assert isinstance(
            definition["parameters"],
            list,
        )
        assert definition["registered"] is True


def test_check_functions_api_returns_catalog():
    response = client.get(
        "/api/check-functions"
    )

    assert response.status_code == 200

    body = response.json()

    assert body["count"] == 7
    assert len(body["functions"]) == 7


def test_json_field_equals_metadata():
    definitions = (
        list_check_function_definitions()
    )

    definition = next(
        item
        for item in definitions
        if item["name"] == "json_field_equals"
    )

    parameter_names = {
        parameter["name"]
        for parameter in definition["parameters"]
    }

    assert parameter_names == {
        "json_path",
        "expected_value",
    }