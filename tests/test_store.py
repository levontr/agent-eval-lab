"""Verify store behavior without an LLM or external services."""

from copy import deepcopy

import pytest

from support_agent_lab import store


@pytest.fixture(autouse=True)
def fresh_store(monkeypatch):
    """Give each test its own orders; restore the original afterward."""
    monkeypatch.setattr(store, "ORDERS", deepcopy(store.ORDERS))


def test_lookup_returns_order_facts():
    order = store.get_order("ORD-001")

    assert order["order_id"] == "ORD-001"
    assert order["price_usd"] == 80
    assert order["refunded"] is False


def test_lookup_does_not_allow_changing_the_stored_order():
    order = store.get_order("ORD-001")
    order["refunded"] = True

    assert store.get_order("ORD-001")["refunded"] is False


def test_lookup_reports_missing_order():
    assert store.get_order("UNKNOWN") == {
        "error": "Order not found",
        "order_id": "UNKNOWN",
    }


def test_refund_returns_full_price_and_updates_only_target_order():
    other_orders = deepcopy({key: value for key, value in store.ORDERS.items() if key != "ORD-001"})

    result = store.issue_refund("ORD-001")

    assert result == {
        "order_id": "ORD-001",
        "status": "refunded",
        "amount_usd": 80,
        "policy_id": "late-delivery-v1",
    }
    assert store.get_order("ORD-001")["refunded"] is True
    for order_id, order in other_orders.items():
        assert store.ORDERS[order_id] == order


@pytest.mark.parametrize(
    ("order_id", "expected_error"),
    [
        ("UNKNOWN", "Order not found"),
        ("ORD-002", "Delivery does not qualify for a refund"),
        ("ORD-003", "Order already refunded"),
    ],
)
def test_rejected_refund_leaves_store_unchanged(order_id, expected_error):
    before = deepcopy(store.ORDERS)

    result = store.issue_refund(order_id)

    assert result == {"error": expected_error, "order_id": order_id}
    assert store.ORDERS == before


def test_second_refund_is_rejected():
    store.issue_refund("ORD-001")
    after_first_refund = deepcopy(store.ORDERS)

    result = store.issue_refund("ORD-001")

    assert result["error"] == "Order already refunded"
    assert store.ORDERS == after_first_refund


@pytest.mark.parametrize(("days_late", "eligible"), [(1, False), (2, True)])
def test_refund_policy_boundary(days_late, eligible):
    store.ORDERS["ORD-001"]["delivery_days_late"] = days_late

    result = store.issue_refund("ORD-001")

    assert (result.get("status") == "refunded") is eligible
    assert store.get_order("ORD-001")["refunded"] is eligible
