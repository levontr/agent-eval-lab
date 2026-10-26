"""A small, bounded agent loop for order lookup and simulated refunds."""

import argparse
import json
import os

from anthropic import Anthropic

from support_agent_lab.policy import get_refund_policy
from support_agent_lab.store import get_order, issue_refund


ORDER_TOOL = {
    "name": "get_order",
    "description": "Look up a store order by its ID, including delivery lateness and refund status.",
    "input_schema": {
        "type": "object",
        "properties": {"order_id": {"type": "string", "description": "Order ID supplied by the customer."}},
        "required": ["order_id"],
        "additionalProperties": False,
    },
}

POLICY_TOOL = {
    "name": "get_refund_policy",
    "description": "Read the store's refund eligibility rules before assessing or issuing a refund.",
    "input_schema": {"type": "object", "properties": {}, "additionalProperties": False},
}

REFUND_TOOL = {
    "name": "issue_refund",
    "description": "Issue a simulated full refund. Use only when the customer requests a refund and the order qualifies. Rejects ineligible or already-refunded orders.",
    "input_schema": ORDER_TOOL["input_schema"],
}

TOOLS = [ORDER_TOOL, POLICY_TOOL, REFUND_TOOL]

SYSTEM_PROMPT = (
    "You are a support assistant for a fictional store. "
    "Use get_order for order facts; never invent them. "
    "If the customer hasn't provided an order ID, ask for it. "
    "Report missing orders honestly. Read get_refund_policy and look up the order "
    "before deciding eligibility or issuing a refund. "
    "An eligibility question is not permission to issue a refund: explain only. "
    "Call issue_refund only if the customer explicitly requests a refund and it qualifies. "
    "Describe refunds as simulated, and claim success only after the tool reports success. "
    "Do not offer to contact a team, record notes, or perform any action outside these tools."
)


def execute_tool(name: str, arguments: object) -> dict:
    """Validate the model's request and dispatch it to a known Python function."""
    if name == "get_refund_policy":
        if arguments != {}:
            return {"error": "get_refund_policy expects no arguments"}
        return get_refund_policy()
    if name not in {"get_order", "issue_refund"}:
        return {"error": "Unknown tool"}
    if (
        not isinstance(arguments, dict)
        or set(arguments) != {"order_id"}
        or not isinstance(arguments["order_id"], str)
    ):
        return {"error": "Expected a single string argument: order_id"}
    if name == "get_order":
        return get_order(arguments["order_id"])
    return issue_refund(arguments["order_id"])


def run_agent(client: Anthropic, prompt: str, model: str) -> str:
    messages = [{"role": "user", "content": prompt}]

    # A hard limit prevents an endless sequence of model/tool calls.
    for _ in range(5):
        response = client.messages.create(
            model=model,
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            tool_choice={"type": "auto", "disable_parallel_tool_use": True},
            messages=messages,
        )
        print(response.stop_reason)
        if response.stop_reason == "end_turn":
            return "\n".join(block.text for block in response.content if block.type == "text")
        if response.stop_reason != "tool_use":
            raise RuntimeError(f"Agent stopped without a complete answer: {response.stop_reason}")

        # Preserve Claude's request before adding the corresponding tool results.
        messages.append({"role": "assistant", "content": response.content})
        results = []
        for block in response.content:
            if block.type != "tool_use":
                continue
            result = execute_tool(block.name, block.input)
            print(f"[tool] {block.name}({json.dumps(block.input)}) -> {json.dumps(result)}")
            results.append({
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": json.dumps(result),
                "is_error": "error" in result,
            })
        if not results:
            raise RuntimeError("Model requested tool use but supplied no tool calls.")
        messages.append({"role": "user", "content": results})

    raise RuntimeError("Agent reached its limit of 5 model calls without a final answer.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Ask the support agent (uses API credits; refunds are simulated).")
    parser.add_argument("prompt")
    parser.add_argument("--model", default="claude-haiku-5-5")
    args = parser.parse_args()
    if not os.environ.get("ANTHROPIC_API_KEY"):
        parser.error("Export ANTHROPIC_API_KEY in this terminal first.")
    with Anthropic(timeout=30.0, max_retries=0) as client:
        print(run_agent(client, args.prompt, args.model))


if __name__ == "__main__":
    main()
