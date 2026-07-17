"""
Tools the cross-border finance agent is allowed to call.
"""

from data_store import store
from compliance import check_transfer

TOOL_SCHEMAS = [
    {
        "name": "get_exchange_rate",
        "description": "Get the current exchange rate between two currencies.",
        "input_schema": {
            "type": "object",
            "properties": {
                "from_currency": {"type": "string", "description": "3-letter currency code, e.g. USD"},
                "to_currency": {"type": "string", "description": "3-letter currency code, e.g. INR"},
            },
            "required": ["from_currency", "to_currency"],
        },
    },
    {
        "name": "convert_currency",
        "description": "Convert an amount from one currency to another at the current rate.",
        "input_schema": {
            "type": "object",
            "properties": {
                "amount": {"type": "number"},
                "from_currency": {"type": "string"},
                "to_currency": {"type": "string"},
            },
            "required": ["amount", "from_currency", "to_currency"],
        },
    },
    {
        "name": "compare_providers",
        "description": "Compare remittance providers for a transfer: fees, FX markup, delivery time, and how much the recipient will receive. Returns cheapest first.",
        "input_schema": {
            "type": "object",
            "properties": {
                "amount": {"type": "number"},
                "from_currency": {"type": "string"},
                "to_currency": {"type": "string"},
            },
            "required": ["amount", "from_currency", "to_currency"],
        },
    },
    {
        "name": "check_compliance",
        "description": "Run AML/compliance checks on a proposed transfer before sending (large-amount, new-recipient, and structuring heuristics).",
        "input_schema": {
            "type": "object",
            "properties": {
                "recipient": {"type": "string"},
                "amount": {"type": "number"},
                "from_currency": {"type": "string"},
            },
            "required": ["recipient", "amount", "from_currency"],
        },
    },
    {
        "name": "create_transfer",
        "description": "Execute a cross-border transfer using a specific provider (call compare_providers first to get a valid provider id).",
        "input_schema": {
            "type": "object",
            "properties": {
                "recipient": {"type": "string"},
                "amount": {"type": "number"},
                "from_currency": {"type": "string"},
                "to_currency": {"type": "string"},
                "provider_id": {"type": "string", "description": "id field from compare_providers results, e.g. 'quickremit'"},
            },
            "required": ["recipient", "amount", "from_currency", "to_currency", "provider_id"],
        },
    },
    {
        "name": "get_transfer_history",
        "description": "Get recent past transfers.",
        "input_schema": {
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "default": 20},
            },
        },
    },
]


def execute_tool(name: str, tool_input: dict):
    if name == "get_exchange_rate":
        rate = store.get_rate(tool_input["from_currency"], tool_input["to_currency"])
        return {"from_currency": tool_input["from_currency"].upper(), "to_currency": tool_input["to_currency"].upper(), "rate": rate}

    if name == "convert_currency":
        return store.convert(tool_input["amount"], tool_input["from_currency"], tool_input["to_currency"])

    if name == "compare_providers":
        return store.compare_providers(tool_input["amount"], tool_input["from_currency"], tool_input["to_currency"])

    if name == "check_compliance":
        flags = check_transfer(tool_input["recipient"], tool_input["amount"], tool_input["from_currency"])
        return {"flags": flags, "clear": len(flags) == 0}

    if name == "create_transfer":
        return store.create_transfer(
            recipient=tool_input["recipient"],
            amount=tool_input["amount"],
            from_currency=tool_input["from_currency"],
            to_currency=tool_input["to_currency"],
            provider_id=tool_input["provider_id"],
        )

    if name == "get_transfer_history":
        return store.get_transfers(tool_input.get("limit", 20))

    raise ValueError(f"Unknown tool: {name}")
