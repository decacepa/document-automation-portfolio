# Monitoring bot

Watches a source on a schedule, keeps only what matches your criteria, and never alerts twice for
the same thing.

## The problem

The data you care about changes constantly, and only a narrow slice of it is worth acting on.
Checking manually means either looking twenty times a day or missing the window. The bot does the
checking; you only hear from it when something actually matches.

## Run it

```bash
python bot.py --once    # single pass
python bot.py           # loop on the configured interval
```

Sample output:

```
bot started — watching ['GRU-MIA', 'GRU-JFK'], max price 700
checked 30 offers
MATCH → email | GRU-MIA | 2026-12-02 | 2 seats | $568
already alerted OF-1013 — skipping
```

## Design decisions

**The rules are in `config.json`, not in the code.** Routes, price ceiling, minimum seats and the
date window are all editable by someone who has never written Python:

```json
"rules": {
  "routes": ["GRU-MIA", "GRU-JFK"],
  "max_price": 700,
  "min_seats": 2,
  "earliest_date": "2026-09-01",
  "latest_date": "2026-12-20"
}
```

**State is persisted.** `state.json` remembers what was already reported, so restarting the bot
does not re-alert on everything it has seen. A monitor that cries wolf gets muted, and a muted
monitor is worthless.

**The source is one swappable function.** `feed.py` is a stub returning generated data. Pointing
the bot at a real API or an HTML page means rewriting `fetch_offers()` and nothing else.

**Failures are visible.** Every check is logged with a timestamp, including the reason an offer
was skipped, so "the bot found nothing" can always be distinguished from "the bot is broken".

## Files

```
bot.py         the loop, matching and deduplication
feed.py        the data source (stub — replace with a real one)
config.json    rules, schedule, notification channel
state.json     what has already been alerted
logs/bot.log   every check
```

## A note on the data

`feed.py` generates its data locally. The bot makes no external requests in this repository.
