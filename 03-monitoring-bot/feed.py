"""
Stub data source.

Stands in for whatever the bot actually watches: a REST API, an HTML page, a
CSV drop. Replace fetch_offers() with a real request and the rest of the bot
keeps working unchanged, as long as it returns the same keys.
"""

import random

ROUTES = ["GRU-MIA", "GIG-LIS", "FLN-EZE", "GRU-JFK", "BSB-MAD"]


def fetch_offers(count=30, seed=None):
    """Return a list of offers. In production this is an HTTP call."""
    rng = random.Random(seed)
    offers = []
    for i in range(count):
        offers.append({
            "id": f"OF-{1000 + i}",
            "route": rng.choice(ROUTES),
            "date": f"2026-{rng.randint(9, 12):02d}-{rng.randint(1, 28):02d}",
            "seats": rng.choice([1, 2, 2, 4, 6]),
            "price": rng.randint(320, 1450),
        })
    return offers
