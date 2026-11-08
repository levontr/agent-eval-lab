"""A tiny fake store for our customer-support agent."""

from support_agent_lab.policy import get_refund_policy
from copy import deepcopy


INITIAL_ORDERS = {
    "ORD-001": {
        "item": "Wireless headphones",
        "price_usd": 80,
        "delivery_days_late": 3,
        "refunded": False,
    },
    "ORD-002": {
        "item": "USB-C cable",
        "price_usd": 15,
        "delivery_days_late": 0,
        "refunded": False,
    },
    "ORD-003": {
        "item": "Keyboard",
        "price_usd": 60,
        "delivery_days_late": 5,
        "refunded": True,
    },
}

ORDERS = deepcopy(INITIAL_ORDERS)


def reset_store() -> None:
    """Restore the fictional starting data before an evaluation scenario."""
    global ORDERS
    ORDERS = deepcopy(INITIAL_ORDERS)


def get_order(order_id: str) -> dict:
    """Look up an order by its ID, or return an error if it doesn't exist."""
    order = ORDERS.get(order_id)
    if order is None:
        return {"error": "Order not found", "order_id": order_id}

    return {"order_id": order_id, **order}


def issue_refund(order_id: str) -> dict:
    """Simulate a full refund for an eligible order; never move real money.

    Changes live in memory and reset when the Python process restarts.
    """
    order = ORDERS.get(order_id)
    if order is None:
        return {"error": "Order not found", "order_id": order_id}

    policy = get_refund_policy()
    if order["refunded"]:
        return {"error": "Order already refunded", "order_id": order_id}

    if order["delivery_days_late"] < policy["minimum_days_late"]:
        return {"error": "Delivery does not qualify for a refund", "order_id": order_id}

    order["refunded"] = True
    return {
        "order_id": order_id,
        "status": "refunded",
        "amount_usd": order["price_usd"],
        "policy_id": policy["policy_id"],
    }
