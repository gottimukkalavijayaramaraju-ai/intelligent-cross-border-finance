# Intelligent Cross-Border Finance — Base Project

A minimal but complete starting point for an agentic cross-border payments app.

- **Backend:** FastAPI + an agentic loop built on Claude's tool-use API.
  The agent looks up exchange rates, compares remittance providers, runs
  AML-style compliance checks, and can execute a transfer — all by calling
  real tools against the app's data rather than guessing numbers.
- **Autonomous compliance monitor:** a rule-based engine (`compliance.py`)
  flags large transfers, first-time large transfers to a new recipient, and
  possible "structuring" (several smaller transfers that add up to more than
  a reporting threshold). This is a simplified educational demo, not real
  compliance software.
- **Data:** mock FX rates (`data/exchange_rates.json`) and mock remittance
  providers with fee structures (`data/providers.json`) — swap for a live FX
  API and real provider integrations later.
- **Frontend:** a single-page dashboard (currency converter, provider
  comparison table, transfer history) with a chat panel wired to the agent.

## Project structure

```
cross-border-finance/
├── backend/
│   ├── main.py           FastAPI app & routes
│   ├── agent.py          The agentic loop (Claude + tools)
│   ├── tools.py          Tool schemas + implementations the agent can call
│   ├── compliance.py     Rule-based autonomous compliance monitor
│   ├── data_store.py     In-memory data layer (rates, providers, transfers)
│   ├── requirements.txt
│   └── .env.example
├── data/
│   ├── exchange_rates.json
│   └── providers.json
└── frontend/
    └── index.html        Dashboard + chat UI (no build step, plain JS)
```

## Setup

1. **Install dependencies**

   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate      # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Add your API key**

   ```bash
   cp .env.example .env
   # then edit .env and paste your key:
   # ANTHROPIC_API_KEY=sk-ant-...
   ```

   Get a key from the [Claude Console](https://console.anthropic.com/).
   The dashboard (rates, provider comparison, converting, transfer history)
   works without a key — only the chat panel needs one.

3. **Run the server**

   ```bash
   python main.py
   ```

   Then open **http://localhost:8000** in your browser.

## How the agent works

`agent.py` runs a standard agentic loop:

1. The user's message is sent to Claude with a list of tool schemas
   (`tools.py`): `get_exchange_rate`, `convert_currency`, `compare_providers`,
   `check_compliance`, `create_transfer`, `get_transfer_history`.
2. Claude decides which tools it needs and calls them (possibly several in
   sequence — e.g. compare providers, then run a compliance check, then
   execute the transfer).
3. The backend runs each tool against `data_store.py` / `compliance.py` and
   returns the results to Claude.
4. This repeats (up to `MAX_AGENT_STEPS`) until Claude has a final, grounded
   answer. The system prompt requires it to run a compliance check before
   executing any transfer, and to surface high-severity flags to the user
   instead of silently proceeding.

Try asking things like:

- "What's the exchange rate from USD to PHP right now?"
- "Cheapest way to send $500 to my sister in the Philippines?"
- "Check compliance for a $12,000 transfer to Alex."
- "Send $200 to Maria using the cheapest provider."
- "Show my recent transfers."

## Extending this base project

- **Live FX rates:** replace `data_store.py`'s static JSON load with a call
  to a real FX API — nothing in `tools.py` or `agent.py` needs to change.
- **Real providers:** swap the mock provider list for real integrations
  (Wise, Remitly, etc. APIs) behind the same `compare_providers` interface.
- **Real compliance/KYC:** replace `compliance.py`'s heuristics with an
  actual sanctions-list screening and identity-verification provider.
- **Persistent storage:** move `data_store.py`'s in-memory transfer list to
  a real database.
- **More tools:** add a function + schema entry in `tools.py` and the agent
  gains the capability automatically.
