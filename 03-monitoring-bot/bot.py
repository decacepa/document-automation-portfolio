"""
Monitoring bot.

Watches a source on a schedule, keeps only what matches the criteria in
config.json, and never alerts twice for the same thing. The rules live outside
the code so a non-technical user can change what counts as a match without
touching Python.

The sample source in feed.py is a local stub. Swapping it for a real API or an
HTML page means replacing one function, not rewriting the bot.

Usage:
    python bot.py --once          # single pass, useful for testing
    python bot.py                 # loop on the configured interval
"""

import argparse
import json
import logging
import time
from datetime import datetime
from pathlib import Path

from feed import fetch_offers

BASE = Path(__file__).parent
STATE_FILE = BASE / "state.json"


def load_config(path=BASE / "config.json"):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def setup_logging(logfile):
    logfile = Path(logfile)
    logfile.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  %(levelname)-7s %(message)s",
        handlers=[logging.FileHandler(logfile, encoding="utf-8"), logging.StreamHandler()],
    )


def load_state():
    if STATE_FILE.exists():
        with open(STATE_FILE, encoding="utf-8") as f:
            return set(json.load(f).get("alerted", []))
    return set()


def save_state(alerted):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump({"alerted": sorted(alerted), "updated": datetime.now().isoformat()}, f, indent=2)


def matches(offer, rules):
    """Every rule must pass. Returns (ok, reason_it_failed)."""
    if offer["price"] > rules["max_price"]:
        return False, f"price {offer['price']} above {rules['max_price']}"
    if offer["seats"] < rules["min_seats"]:
        return False, f"only {offer['seats']} seats"
    if rules["routes"] and offer["route"] not in rules["routes"]:
        return False, f"route {offer['route']} not watched"
    if offer["date"] < rules["earliest_date"] or offer["date"] > rules["latest_date"]:
        return False, f"date {offer['date']} outside window"
    return True, ""


def notify(offer, channel):
    """
    Where an alert would go in production: email, Telegram, webhook.
    Kept as a log line here so the demo has no external dependency.
    """
    logging.warning("MATCH → %s | %s | %s | %s seats | $%s",
                    channel, offer["route"], offer["date"], offer["seats"], offer["price"])


def run_once(cfg, alerted):
    offers = fetch_offers()
    logging.info("checked %d offers", len(offers))

    found = 0
    for offer in offers:
        ok, reason = matches(offer, cfg["rules"])
        if not ok:
            logging.debug("skip %s: %s", offer["id"], reason)
            continue
        if offer["id"] in alerted:
            logging.info("already alerted %s — skipping", offer["id"])
            continue
        notify(offer, cfg["notify"]["channel"])
        alerted.add(offer["id"])
        found += 1

    if found == 0:
        logging.info("no new matches")
    return found


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true", help="run a single pass and exit")
    args = parser.parse_args()

    cfg = load_config()
    setup_logging(BASE / cfg["paths"]["log_file"])
    alerted = load_state()

    logging.info("bot started — watching %s, max price %s",
                 cfg["rules"]["routes"] or "all routes", cfg["rules"]["max_price"])

    if args.once:
        run_once(cfg, alerted)
        save_state(alerted)
        return

    interval = cfg["schedule"]["interval_seconds"]
    try:
        while True:
            run_once(cfg, alerted)
            save_state(alerted)
            time.sleep(interval)
    except KeyboardInterrupt:
        save_state(alerted)
        logging.info("bot stopped by user — state saved")


if __name__ == "__main__":
    main()
