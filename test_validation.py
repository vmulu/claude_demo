import pytest

import app as app_module
from app import create_app
from splitter import validate_expense

VALID = {"amount_cents": 900, "paid_by": "ana", "participants": ["ana", "ben", "cal"]}


@pytest.fixture
def client():
    app_module._expenses.clear()
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()


def without(field):
    return {k: v for k, v in VALID.items() if k != field}


def test_valid_expense_has_no_errors():
    assert validate_expense(VALID) == []


@pytest.mark.parametrize("field", ["amount_cents", "paid_by", "participants"])
def test_missing_field_is_reported(field):
    assert validate_expense(without(field)) == [f"{field} is required"]


def test_every_missing_field_is_reported_at_once():
    assert len(validate_expense({})) == 3


@pytest.mark.parametrize(
    "overrides",
    [
        {"amount_cents": 9.0},
        {"amount_cents": "900"},
        {"amount_cents": True},
        {"amount_cents": 0},
        {"amount_cents": -100},
        {"paid_by": ""},
        {"paid_by": "   "},
        {"paid_by": 7},
        {"participants": []},
        {"participants": "ana"},
        {"participants": ["ana", ""]},
        {"participants": ["ana", 3]},
        {"participants": ["ana", "ana"]},
    ],
)
def test_bad_values_are_rejected(overrides):
    assert validate_expense({**VALID, **overrides})


def test_non_object_body_is_rejected():
    assert validate_expense([VALID]) == ["expense must be a JSON object"]


@pytest.mark.parametrize("field", ["amount_cents", "paid_by", "participants"])
def test_post_missing_field_returns_400(client, field):
    resp = client.post("/expenses", json=without(field))
    assert resp.status_code == 400
    assert f"{field} is required" in resp.get_json()["details"]


def test_post_without_json_returns_400(client):
    resp = client.post("/expenses", data="not json", content_type="text/plain")
    assert resp.status_code == 400


def test_post_json_array_returns_400(client):
    assert client.post("/expenses", json=[VALID]).status_code == 400


def test_rejected_expense_is_not_stored(client):
    client.post("/expenses", json={**VALID, "amount_cents": -1})
    assert client.get("/balances").get_json()["balances"] == {}


def test_valid_post_still_returns_201(client):
    assert client.post("/expenses", json=VALID).status_code == 201
