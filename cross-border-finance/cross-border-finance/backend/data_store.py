"""
In-memory data layer for the cross-border finance demo.

Rates and providers are loaded from static JSON (swap for a live FX API /
real provider integrations later). Transfer history is kept in memory only.
"""

import json
import uuid
from pathlib import Path
from datetime import datetime, timedelta

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


class Store:
    def __init__(self):
        with open(DATA_DIR / "exchange_rates.json") as f:
            fx = json.load(f)
        self.base_currency = fx["base"]
        self.rates_updated = fx["updated"]
        self.rates = fx["rates"]

        with open(DATA_DIR / "providers.json") as f:
            self.providers = json.load(f)

        self.transfers = []  # in-memory transfer history

    # ---------- FX ----------
    def get_rate(self, from_currency: str, to_currency: str) -> float:
        from_currency, to_currency = from_currency.upper(), to_currency.upper()
        if from_currency not in self.rates or to_currency not in self.rates:
            raise ValueError(f"Unsupported currency: {from_currency} or {to_currency}")
        # rates table is USD-based: X per 1 USD
        usd_amount = 1 / self.rates[from_currency]
        return round(usd_amount * self.rates[to_currency], 6)

    def convert(self, amount: float, from_currency: str, to_currency: str) -> dict:
        rate = self.get_rate(from_currency, to_currency)
        return {
            "amount": amount,
            "from_currency": from_currency.upper(),
            "to_currency": to_currency.upper(),
            "rate": rate,
            "converted_amount": round(amount * rate, 2),
        }

    # ---------- providers ----------
    def compare_providers(self, amount: float, from_currency: str, to_currency: str) -> list:
        base_rate = self.get_rate(from_currency, to_currency)
        usd_to_from_rate = self.get_rate("USD", from_currency)
        amount_in_usd = amount / usd_to_from_rate
        results = []
        for p in self.providers:
            effective_rate = base_rate * (1 - p["fx_markup_pct"] / 100)
            fee_in_from_currency = p["flat_fee_usd"] * usd_to_from_rate
            net_send_amount = max(amount - fee_in_from_currency, 0)
            received = round(net_send_amount * effective_rate, 2)
            total_cost_usd = round(p["flat_fee_usd"] + amount_in_usd * (p["fx_markup_pct"] / 100), 2)
            results.append({
                "provider": p["name"],
                "id": p["id"],
                "method": p["method"],
                "delivery": p["delivery"],
                "flat_fee_usd": p["flat_fee_usd"],
                "fx_markup_pct": p["fx_markup_pct"],
                "effective_rate": round(effective_rate, 6),
                "recipient_receives": max(received, 0),
                "estimated_total_cost_usd": total_cost_usd,
            })
        results.sort(key=lambda r: r["estimated_total_cost_usd"])
        return results

    # ---------- transfers ----------
    def create_transfer(self, recipient: str, amount: float, from_currency: str, to_currency: str, provider_id: str):
        provider = next((p for p in self.providers if p["id"] == provider_id), None)
        if not provider:
            raise ValueError(f"Unknown provider: {provider_id}")
        conv = self.convert(amount, from_currency, to_currency)
        transfer = {
            "id": str(uuid.uuid4())[:8],
            "timestamp": datetime.utcnow().isoformat(),
            "recipient": recipient,
            "amount": amount,
            "from_currency": from_currency.upper(),
            "to_currency": to_currency.upper(),
            "provider": provider["name"],
            "provider_id": provider_id,
            "recipient_receives": conv["converted_amount"],
            "status": "completed",
        }
        self.transfers.append(transfer)
        return transfer

    def get_transfers(self, limit: int = 20):
        return list(reversed(self.transfers))[:limit]

    def transfers_for_recipient(self, recipient: str):
        return [t for t in self.transfers if t["recipient"].lower() == recipient.lower()]

    def recent_transfers(self, minutes: int = 60):
        cutoff = datetime.utcnow() - timedelta(minutes=minutes)
        return [t for t in self.transfers if datetime.fromisoformat(t["timestamp"]) >= cutoff]


store = Store()
