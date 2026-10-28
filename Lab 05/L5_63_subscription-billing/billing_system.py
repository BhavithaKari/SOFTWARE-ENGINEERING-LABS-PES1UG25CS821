
"""Subscription billing system.

Handles trials, plan subscriptions, coupons, billing dates, upgrade
proration, payment retries, refunds, card encryption, signed XML
webhooks and HTML invoices.
"""

import calendar
import hashlib
import hmac
import html
import os
import secrets
from datetime import date

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from defusedxml import ElementTree

PLANS = {"basic": 199, "pro": 499, "team": 999}
GST = 0.18
TRIAL_DAYS = 14
MAX_ATTEMPTS = 3
BILLING_PERIOD_DAYS = 30
ACTIVE_STATUSES = ("trial", "active")

# Load secrets from the environment.
# Demo fallback values are generated when variables are not configured.
WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET") or secrets.token_hex(32)

if "CARD_KEY_HEX" in os.environ:
    CARD_KEY = bytes.fromhex(os.environ["CARD_KEY_HEX"])
    if len(CARD_KEY) != 32:
        raise ValueError("CARD_KEY_HEX must contain a 32-byte AES-256 key")
else:
    CARD_KEY = AESGCM.generate_key(bit_length=256)

subscriptions = {}

coupons = {
    "WELCOME10": {
        "percent": 10,
        "expires": date(2026, 12, 31),
    },
    "FRIENDS150": {
        "percent": 150,
        "expires": date(2027, 1, 31),
    },
}


def subscribe(user, plan, start):
    """Start a trial subscription for a user on a valid plan."""
    if plan not in PLANS:
        raise ValueError(f"Unknown plan: {plan}")

    subscriptions[user] = {
        "plan": plan,
        "start": start,
        "status": "trial",
        "invoices": [],
    }
    return subscriptions[user]


def is_trial_over(user, today):
    """Return True once the trial period has fully elapsed."""
    return (today - subscriptions[user]["start"]).days >= TRIAL_DAYS


def apply_coupon(amount, code, today=None):
    """Apply a valid coupon through its expiry day."""
    today = today or date.today()
    coupon = coupons.get(code)

    if coupon is None or today > coupon["expires"]:
        return amount

    percent = coupon["percent"]

    # Reject invalid percentages instead of treating them as 100% off.
    if not isinstance(percent, (int, float)) or not 0 <= percent <= 100:
        return amount

    return round(amount * (1 - percent / 100), 2)


def invoice_amount(user, code=None, today=None):
    """Return the GST-inclusive invoice total after applying a coupon."""
    plan_price = PLANS[subscriptions[user]["plan"]]
    with_tax = round(plan_price * (1 + GST), 2)
    return apply_coupon(with_tax, code, today)


def next_billing_date(current):
    """Return the same day next month, clamped to that month's length."""
    year = current.year + current.month // 12
    month = current.month % 12 + 1
    day = min(current.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def prorate_upgrade(user, new_plan, today, period_end):
    """Switch plans and calculate the prorated upgrade charge."""
    if new_plan not in PLANS:
        raise ValueError(f"Unknown plan: {new_plan}")

    old_price = PLANS[subscriptions[user]["plan"]]
    new_price = PLANS[new_plan]

    days_left = max((period_end - today).days, 0)
    period_days = calendar.monthrange(
        period_end.year, period_end.month
    )[1]

    subscriptions[user]["plan"] = new_plan

    return round(
        (new_price - old_price) * days_left / period_days,
        2,
    )


def retry_payment(charge):
    """Attempt payment up to MAX_ATTEMPTS times."""
    attempts = 0

    while attempts < MAX_ATTEMPTS:
        attempts += 1
        if charge():
            break

    return attempts


def cancel_refund(user, days_used):
    """Refund the unused part of the 30-day billing period."""
    price = PLANS[subscriptions[user]["plan"]]
    days_used = min(max(days_used, 0), BILLING_PERIOD_DAYS)
    unused_days = BILLING_PERIOD_DAYS - days_used

    return round(price * unused_days / BILLING_PERIOD_DAYS, 2)


def coupon_code():
    """Generate an unpredictable promotional coupon code."""
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    code = "".join(
        secrets.choice(alphabet) for _ in range(6)
    )
    return f"SAVE-{code}"


def active_users():
    """Return users whose subscriptions are trial or active."""
    return {
        user
        for user, subscription in subscriptions.items()
        if subscription["status"] in ACTIVE_STATUSES
    }


def encrypt_card(card_number):
    """Encrypt a card number with AES-GCM and a fresh random nonce."""
    nonce = os.urandom(12)
    ciphertext = AESGCM(CARD_KEY).encrypt(
        nonce,
        card_number.encode("utf-8"),
        None,
    )
    return (nonce + ciphertext).hex()


def decrypt_card(token):
    """Decrypt a card token created by encrypt_card."""
    raw = bytes.fromhex(token)

    if len(raw) < 12 + 16:
        raise ValueError("Invalid encrypted card token")

    plaintext = AESGCM(CARD_KEY).decrypt(
        raw[:12],
        raw[12:],
        None,
    )
    return plaintext.decode("utf-8")


def verify_webhook(body, signature):
    """Verify an HMAC-SHA256 signature using constant-time comparison."""
    expected = hmac.new(
        WEBHOOK_SECRET.encode("utf-8"),
        body,
        hashlib.sha256,
    ).hexdigest()

    return hmac.compare_digest(expected, signature)


def parse_webhook(xml_bytes):
    """Parse webhook XML safely, blocking unsafe XML entities."""
    root = ElementTree.fromstring(xml_bytes)

    return {
        "event": root.findtext("event"),
        "user": root.findtext("user"),
    }


def render_invoice(user, amount):
    """Render an HTML invoice with an escaped username."""
    if amount < 0:
        raise ValueError("Invoice amount cannot be negative")

    safe_user = html.escape(user)
    return (
        f"<h1>Invoice for {safe_user}</h1>"
        f"<p>Total: Rs.{amount:.2f}</p>"
    )


def main():
    """Run a demonstration of the subscription billing system."""
    subscribe("asha", "pro", date(2026, 9, 1))
    subscribe(
        "<b onmouseover=alert(1)>ravi</b>",
        "basic",
        date(2026, 9, 20),
    )

    print(
        "Trial (14 days from 09-01) over on 09-15?",
        is_trial_over("asha", date(2026, 9, 15)),
    )

    print(
        "Pro invoice with WELCOME10:",
        invoice_amount("asha", "WELCOME10", date(2026, 10, 1)),
    )

    print(
        "Pro invoice with FRIENDS150:",
        invoice_amount("asha", "FRIENDS150", date(2026, 10, 1)),
    )

    print(
        "Coupon on its expiry day:",
        invoice_amount("asha", "WELCOME10", date(2026, 12, 31)),
    )

    print(
        "Next billing after 2026-10-15:",
        next_billing_date(date(2026, 10, 15)),
    )

    print(
        "Next billing after 2026-12-31:",
        next_billing_date(date(2026, 12, 31)),
    )

    print(
        "Upgrade pro->team with 10 days left in Feb:",
        prorate_upgrade(
            "asha",
            "team",
            date(2027, 2, 18),
            date(2027, 2, 28),
        ),
    )

    print(
        "Payment attempts (max 3, always failing):",
        retry_payment(lambda: False),
    )

    print(
        "Refund after using 25 of 30 days:",
        cancel_refund("asha", 25),
    )

    token = encrypt_card("4111111111111111")

    print(
        "Same card, same ciphertext?",
        token == encrypt_card("4111111111111111"),
    )

    print(
        "Card round-trips?",
        decrypt_card(token) == "4111111111111111",
    )

    signature = hmac.new(
        WEBHOOK_SECRET.encode("utf-8"),
        b"<x/>",
        hashlib.sha256,
    ).hexdigest()

    print(
        "Webhook verified:",
        verify_webhook(b"<x/>", signature),
    )

    print(
        "Webhook:",
        parse_webhook(
            b"<hook><event>paid</event><user>asha</user></hook>"
        ),
    )

    print(
        "Invoice HTML:",
        render_invoice(
            "<b onmouseover=alert(1)>ravi</b>",
            199,
        ),
    )

    print("Coupon:", coupon_code())


if __name__ == "__main__":
    main()
