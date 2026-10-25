"""Command-line entry point for trying our store tool."""

import argparse
import json

from support_agent_lab.store import get_order


def main() -> None:
    parser = argparse.ArgumentParser(description="Look up a fictional store order.")
    parser.add_argument("order_id", help="Order ID, for example ORD-001")
    args = parser.parse_args()
    print(json.dumps(get_order(args.order_id), indent=2))
