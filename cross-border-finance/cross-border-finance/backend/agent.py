"""
The agent itself.

Same agentic-loop pattern as the finance base project: hand Claude a set of
tools, let it decide what to call (rates, provider comparisons, compliance
checks, executing a transfer), feed results back, repeat until it has a
final answer.
"""

import os
from anthropic import Anthropic
from tools import TOOL_SCHEMAS, execute_tool

MODEL = os.environ.get("CLAUDE_MODEL", "claude-sonnet-5")
MAX_AGENT_STEPS = 6

SYSTEM_PROMPT = """You are an assistant embedded in a cross-border money transfer app.
You can call tools to look up live-ish exchange rates, compare remittance providers,
run compliance checks, execute a transfer, and view transfer history.

Rules:
- Always look up real rates/provider data via tools before quoting numbers. Never guess.
- Before executing a transfer with create_transfer, first call check_compliance. If it
  returns any high-severity flags, explain them to the user and ask for confirmation
  before proceeding -- do not silently execute a flagged transfer.
- When recommending a provider, briefly explain the tradeoff (cheapest vs fastest vs
  most reliable) rather than only stating the cheapest.
- Be concise and use concrete numbers from the tools.
- This is a demo app with mock data, not real financial infrastructure -- if asked,
  be upfront about that.
"""


class CrossBorderAgent:
    def __init__(self, api_key: str | None = None):
        self.client = Anthropic(api_key=api_key) if api_key else Anthropic()

    def chat(self, user_message: str, history: list[dict] | None = None) -> dict:
        messages = list(history or [])
        messages.append({"role": "user", "content": user_message})

        tool_calls_made = []

        for _ in range(MAX_AGENT_STEPS):
            response = self.client.messages.create(
                model=MODEL,
                max_tokens=1024,
                system=SYSTEM_PROMPT,
                tools=TOOL_SCHEMAS,
                messages=messages,
            )

            if response.stop_reason != "tool_use":
                final_text = "".join(
                    block.text for block in response.content if block.type == "text"
                )
                messages.append({"role": "assistant", "content": response.content})
                return {
                    "reply": final_text,
                    "tool_calls": tool_calls_made,
                    "history": messages,
                }

            messages.append({"role": "assistant", "content": response.content})
            tool_results = []
            for block in response.content:
                if block.type != "tool_use":
                    continue
                try:
                    result = execute_tool(block.name, block.input)
                except Exception as e:
                    result = {"error": str(e)}
                tool_calls_made.append({"tool": block.name, "input": block.input, "result": result})
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": str(result),
                })
            messages.append({"role": "user", "content": tool_results})

        return {
            "reply": "I wasn't able to finish that request in the allotted steps -- could you rephrase or narrow it down?",
            "tool_calls": tool_calls_made,
            "history": messages,
        }
