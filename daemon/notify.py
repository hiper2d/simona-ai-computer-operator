"""
Simona long-loop notifier — Telegram only.

Shares marlow's bot + chat (credentials come from TELEGRAM_BOT_TOKEN
and TELEGRAM_CHAT_ID env vars, which tick.sh sources from marlow's
.env). All notifications are tagged "[Simona]" so they're visually
distinct from Marlow's messages in the same chat.

Usage:
    python daemon/notify.py "<message>"
"""

from __future__ import annotations

import argparse
import os
import sys

import requests

TELEGRAM_API = "https://api.telegram.org/bot{token}/sendMessage"
TELEGRAM_TIMEOUT = 15


def send_telegram(message: str) -> tuple[bool, str]:
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        return False, "missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID"
    text = f"[Simona] {message}"
    try:
        resp = requests.post(
            TELEGRAM_API.format(token=token),
            json={"chat_id": chat_id, "text": text},
            timeout=TELEGRAM_TIMEOUT,
        )
        if resp.status_code != 200:
            return False, f"telegram returned {resp.status_code}: {resp.text[:200]}"
        return True, "sent"
    except requests.RequestException as e:
        return False, f"telegram request failed: {e}"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("message")
    args = parser.parse_args()
    ok, detail = send_telegram(args.message)
    print(detail)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
