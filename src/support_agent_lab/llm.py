"""First Claude connection: one message, without tools or an agent loop yet."""

import argparse
import os

from anthropic import Anthropic


def ask_claude(prompt: str, model: str) -> str:
    """Send one message; the SDK reads ANTHROPIC_API_KEY from the environment."""
    with Anthropic(timeout=30.0, max_retries=0) as client:
        response = client.messages.create(
            model=model,
            max_tokens=256,
            messages=[{"role": "user", "content": prompt}],
        )
    return "\n".join(block.text for block in response.content if block.type == "text")


def main() -> None:
    parser = argparse.ArgumentParser(description="Send one message to Claude (uses API credits).")
    parser.add_argument("prompt", help="Message to send to Claude")
    parser.add_argument("--model", default="claude-haiku-5-5", help="Claude API model ID")
    args = parser.parse_args()
    if not os.environ.get("ANTHROPIC_API_KEY"):
        parser.error("Export ANTHROPIC_API_KEY in this terminal before running this command.")
    print(ask_claude(args.prompt, args.model))


if __name__ == "__main__":
    main()
