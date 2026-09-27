from fastapi.testclient import TestClient

from check_functions.registry import (
    list_check_function_definitions,
)
from web_api.app import app


client = TestClient(app)


def test_function_definitions_are_returned():
    definitions = (
        list_check_function_definitions()
    )

    names = {
        definition["name"]
        for definition in definitions
    }

    assert "status_code_200" in names

    assert (
        "expected_status_code"
        in names
    )

    for definition in definitions:
        assert (
            definition["registered"]
            is True
        )

        assert (
            "display_name"
            in definition
        )

        assert (
            "description"
            in definition
        )

        assert (
            "parameters"
            in definition
        )


def test_function_catalog_api():
    response = client.get(
        "/api/check-functions"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["count"] == 2

    assert len(
        data["functions"]
    ) == 2

    function_names = {
        function["name"]
        for function in data["functions"]
    }

    assert function_names == {
        "status_code_200",
        "expected_status_code",
    }


def test_status_code_200_has_no_parameters():
    definitions = (
        list_check_function_definitions()
    )

    function = next(
        definition
        for definition in definitions
        if definition["name"]
        == "status_code_200"
    )

    assert function["parameters"] == []


def test_expected_status_code_metadata():
    response = client.get(
        "/api/check-functions"
    )

    functions = response.json()[
        "functions"
    ]

    function = next(
        item
        for item in functions
        if item["name"]
        == "expected_status_code"
    )

    parameters = function["parameters"]

    assert len(parameters) == 1

    parameter = parameters[0]

    assert parameter["name"] == (
        "expected_status_code"
    )

    assert parameter["type"] == "integer"

    assert parameter["required"] is True

    assert parameter["example"] == 200