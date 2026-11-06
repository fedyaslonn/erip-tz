from uuid import UUID

import pytest


@pytest.mark.parametrize(
    "source,target,amount,expected,rate",
    [
        ("usd", "byn", "10.00", "30.00", "3.000000000000"),
        ("BYN", "USD", "30.00", "10.00", "0.333333333333"),
        ("USD", "EUR", "10.00", "7.50", "0.750000000000"),
        ("RUB", "BYN", "1.00", "0.04", "0.035000000000"),
    ],
)
def test_quote(client, source, target, amount, expected, rate):
    response = client.post(
        "/api/exchange/quote",
        json={
            "source_amount": amount,
            "source_currency": source,
            "target_currency": target,
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert UUID(body["deal_id"])
    assert body["target_amount"] == expected
    assert body["exchange_rate"] == rate


@pytest.mark.parametrize(
    "amount,source,target",
    [
        ("0", "USD", "BYN"),
        ("1.001", "USD", "BYN"),
        ("10", "USD", "usd"),
    ],
)
def test_invalid_quote(client, amount, source, target):
    response = client.post(
        "/api/exchange/quote",
        json={
            "source_amount": amount,
            "source_currency": source,
            "target_currency": target,
        },
    )
    assert response.status_code == 422
    assert response.json()["detail"]


@pytest.mark.parametrize("currency", ["XXX", "123"])
def test_unknown_currency(client, currency):
    response = client.post(
        "/api/exchange/quote",
        json={
            "source_amount": "10",
            "source_currency": currency,
            "target_currency": "BYN",
        },
    )
    assert response.status_code == 404
    assert response.json() == {
        "detail": f"Exchange rate for {currency} is not available."
    }


@pytest.mark.parametrize("result", ["COMPLETED", "REJECTED"])
def test_process_deal(client, deals, result):
    response = client.post(
        "/api/exchange/confirm", json={"deal_id": str(deals[0].id), "result": result}
    )
    assert response.status_code == 200
    assert response.json()["deal_id"] == str(deals[0].id)
    assert response.json()["status"] == result

    response = client.post(
        "/api/exchange/confirm", json={"deal_id": str(deals[0].id), "result": result}
    )
    assert response.status_code == 409
    assert response.json() == {
        "detail": f"Transaction {deals[0].id} is already processed with status {result}."
    }


def test_quote_without_rates(client, uow):
    uow.rates.get_latest_date.return_value = None
    response = client.post(
        "/api/exchange/quote",
        json={
            "source_amount": "10",
            "source_currency": "USD",
            "target_currency": "BYN",
        },
    )
    assert response.status_code == 503
    assert response.json() == {"detail": "No exchange rates available"}


def test_unknown_deal(client):
    deal_id = str(UUID(int=99))
    response = client.post(
        "/api/exchange/confirm", json={"deal_id": deal_id, "result": "COMPLETED"}
    )
    assert response.status_code == 404
    assert response.json() == {"detail": f"Transaction {deal_id} not found."}


def test_pending_deals(client, deals):
    response = client.get("/api/exchange/pending")
    assert response.status_code == 200
    assert response.json() == [
        {
            "id": str(deals[0].id),
            "source_amount": "100.00",
            "target_amount": "300.00",
            "source_currency": "USD",
            "target_currency": "BYN",
            "exchange_rate": "3.000000000000",
        }
    ]
