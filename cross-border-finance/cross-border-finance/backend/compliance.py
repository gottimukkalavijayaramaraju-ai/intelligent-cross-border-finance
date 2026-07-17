"""
Lightweight autonomous compliance monitor.

Runs independently of the chat agent -- inspects a proposed or completed
transfer and raises flags using simple, well-known AML heuristics:
  - large single transfers (reporting-threshold style check)
  - possible structuring (several smaller transfers to the same recipient
    that add up to more than the threshold in a short window)
  - first-time large transfer to a new recipient

This is a simplified educational demo, not real compliance software, and
does not make any judgment based on country or nationality.
"""

from data_store import store

LARGE_TRANSFER_THRESHOLD_USD = 10000
NEW_RECIPIENT_REVIEW_THRESHOLD_USD = 3000
STRUCTURING_WINDOW_MINUTES = 60


def _to_usd(amount: float, currency: str) -> float:
    rate = store.get_rate(currency, "USD")
    return amount * rate


def check_transfer(recipient: str, amount: float, from_currency: str) -> list:
    flags = []
    amount_usd = _to_usd(amount, from_currency)

    if amount_usd >= LARGE_TRANSFER_THRESHOLD_USD:
        flags.append({
            "severity": "high",
            "rule": "large_transfer",
            "message": f"Transfer of ~${amount_usd:,.2f} exceeds the ${LARGE_TRANSFER_THRESHOLD_USD:,} reporting threshold and needs enhanced verification.",
        })

    prior = store.transfers_for_recipient(recipient)
    if not prior and amount_usd >= NEW_RECIPIENT_REVIEW_THRESHOLD_USD:
        flags.append({
            "severity": "medium",
            "rule": "new_recipient",
            "message": f"This is a first-time transfer to '{recipient}' of ~${amount_usd:,.2f}. Recommend identity verification before sending.",
        })

    recent = store.recent_transfers(minutes=STRUCTURING_WINDOW_MINUTES)
    recent_to_recipient = [t for t in recent if t["recipient"].lower() == recipient.lower()]
    running_total_usd = sum(_to_usd(t["amount"], t["from_currency"]) for t in recent_to_recipient) + amount_usd
    if recent_to_recipient and running_total_usd >= LARGE_TRANSFER_THRESHOLD_USD and amount_usd < LARGE_TRANSFER_THRESHOLD_USD:
        flags.append({
            "severity": "high",
            "rule": "possible_structuring",
            "message": f"Multiple transfers to '{recipient}' in the last {STRUCTURING_WINDOW_MINUTES} minutes total ~${running_total_usd:,.2f}, "
                       f"which is at or above the reporting threshold even though each is individually smaller. Flagged for review.",
        })

    return flags
