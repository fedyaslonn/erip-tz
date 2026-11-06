from decimal import Decimal

import pytest

pytestmark = pytest.mark.anyio


async def test_stats(db_client):
    response = await db_client.get(
        "/api/exchange/stats",
        params={"date_from": "2026-01-02", "date_to": "2026-01-02"},
    )
    assert response.status_code == 200
    actual = {
        row["currency"]: (
            Decimal(row["total_received"]),
            Decimal(row["total_spent"]),
            row["deals_count"],
        )
        for row in response.json()
    }
    assert actual == {
        "USD": (Decimal("10"), Decimal("5"), 2),
        "BYN": (Decimal("15"), Decimal("30"), 2),
    }


async def test_stats_currency_filter(db_client):
    response = await db_client.get(
        "/api/exchange/stats",
        params={
            "date_from": "2026-01-02",
            "date_to": "2026-01-02",
            "currency": "usd",
        },
    )
    assert response.status_code == 200
    assert response.json() == [
        {
            "currency": "USD",
            "total_received": "10.00",
            "total_spent": "5.00",
            "deals_count": 2,
        }
    ]


async def test_stats_empty_period(db_client):
    response = await db_client.get(
        "/api/exchange/stats",
        params={"date_from": "2025-01-01", "date_to": "2025-01-02"},
    )
    assert response.status_code == 200
    assert response.json() == []


def test_invalid_stats_period(client):
    response = client.get(
        "/api/exchange/stats",
        params={"date_from": "2026-01-03", "date_to": "2026-01-02"},
    )
    assert response.status_code == 422
    assert response.json()["detail"]
