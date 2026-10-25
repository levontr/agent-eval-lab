"""A tiny fake store for our customer-support agent."""


ORDERS = {
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


def get_order(order_id: str) -> dict:
    """Look up an order by its ID, or return an error if it doesn't exist."""
    order = ORDERS.get(order_id)
    if order is None:
        return {"error": "Order not found", "order_id": order_id}

    return {"order_id": order_id, **order}

