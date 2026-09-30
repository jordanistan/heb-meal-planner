"""Catalog refresh worker (scheduled, decoupled from user traffic).

Runs as a Docker Compose one-shot / k8s CronJob. In v1 it validates that every
mapped query resolves to a brand and reports coverage; later it will refresh a
product + price catalog from a licensed feed or a controlled, rate-limited
source (never per-user, never from the request path). It deliberately does NOT
scrape heb.com on our infrastructure — see the architecture doc.
"""
from __future__ import annotations

import logging

from ..planning import mapping

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("catalog")


def refresh() -> dict:
    total = len(mapping.INGREDIENT_LOOKUP)
    branded = sum(
        1 for q in mapping.INGREDIENT_LOOKUP.values() if mapping.brand_of(q)
    )
    log.info("catalog check: %d mappings, %d resolve to an H-E-B brand", total, branded)
    return {"mappings": total, "branded": branded}


if __name__ == "__main__":
    result = refresh()
    log.info("done: %s", result)
