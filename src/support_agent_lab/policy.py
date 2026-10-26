"""The fictional store's refund policy, exposed as a read-only tool."""


def get_refund_policy() -> dict:
    """Return the rules for refunding a late delivery."""
    return {
        "policy_id": "late-delivery-v1",
        "minimum_days_late": 2,
        "refund_amount": "full_order_price",
        "allow_repeat_refund": False,
        "rules": [
            "The order must exist.",
            "Delivery must be at least 2 days late (including exactly 2 days).",
            "An order that has already been refunded cannot be refunded again.",
            "An eligible order receives a refund of its full price.",
        ],
    }
