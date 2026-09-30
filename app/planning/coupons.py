"""Weekly-ad coupons.

SAMPLE DATA for v1. Real coupons come from H-E-B's weekly ad, which would be
loaded by the catalog worker from a licensed/partner feed — not scraped. The
shape here is what the planner and UI consume, so swapping in a real source is
a data change, not a code change.
"""
from __future__ import annotations

# Each coupon matches shopping-list items by a lowercase substring.
COUPONS: list[dict] = [
    {"match": "chicken breast", "title": "Boneless Chicken Breast", "deal": "$1.00/lb off", "savings": 1.5},
    {"match": "ground beef", "title": "H-E-B Ground Beef", "deal": "$2.00 off 2 lb", "savings": 2.0},
    {"match": "salmon", "title": "Atlantic Salmon Fillet", "deal": "$3.00/lb off", "savings": 3.0},
    {"match": "shrimp", "title": "Raw Peeled Shrimp", "deal": "$2.00/lb off", "savings": 2.0},
    {"match": "avocado", "title": "Hass Avocados", "deal": "5 for $3", "savings": 1.5},
    {"match": "tortillas", "title": "Mi Tienda Tortillas", "deal": "Buy 1 Get 1 Free", "savings": 2.5},
    {"match": "feta", "title": "Central Market Feta", "deal": "$1.50 off", "savings": 1.5},
    {"match": "coconut milk", "title": "Coconut Milk", "deal": "2 for $3", "savings": 0.5},
    {"match": "pasta", "title": "H-E-B Pasta", "deal": "3 for $2", "savings": 1.0},
    {"match": "cheddar", "title": "Shredded Cheddar", "deal": "$1.00 off", "savings": 1.0},
    {"match": "canned tomatoes", "title": "H-E-B Organics Diced Tomatoes", "deal": "4 for $4", "savings": 0.8},
    {"match": "rice", "title": "H-E-B Long Grain Rice", "deal": "$1.00 off", "savings": 1.0},
]


def current() -> list[dict]:
    return COUPONS


def match_for(*texts: str) -> dict | None:
    """First coupon whose match substring appears in any of the given texts."""
    blob = " ".join(texts).lower()
    for c in COUPONS:
        if c["match"] in blob:
            return c
    return None
