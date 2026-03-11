"""
tools.py — thin wrapper around the REST Countries API.

Keeping network I/O isolated here means:
  • nodes.py stays pure / easy to unit-test with mocks
  • retries / timeouts / error normalisation live in one place
"""

import logging
from typing import Any, Optional

import httpx
from async_lru import alru_cache

logger = logging.getLogger(__name__)

_BASE_URL = "https://restcountries.com/v3.1"
_TIMEOUT = httpx.Timeout(10.0)

# Fields we actually need — reduces payload size
_FIELDS = "name,capital,population,currencies,languages,region,subregion,flags,area"


@alru_cache(maxsize=128)
async def fetch_country(country_name: str) -> tuple[Optional[dict[str, Any]], Optional[str]]:
    """
    Fetch country data from the REST Countries API.

    Returns:
        (data, None)  on success  — data is the first matching country dict
        (None, error) on failure  — error is a human-readable message
    """
    url = f"{_BASE_URL}/name/{country_name.strip()}"
    params = {"fields": _FIELDS, "fullText": "false"}

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(url, params=params)

        if response.status_code == 404:
            return None, f"No country found matching '{country_name}'."

        response.raise_for_status()
        results: list[dict] = response.json()

        if not results:
            return None, f"No country found matching '{country_name}'."

        # Return the best match (exact name match preferred, else first result)
        best = _pick_best_match(country_name, results)
        return best, None

    except httpx.TimeoutException:
        logger.error("Timeout fetching country data for '%s'", country_name)
        return None, "The countries data service timed out. Please try again."

    except httpx.HTTPStatusError as exc:
        logger.error("HTTP %s for '%s': %s", exc.response.status_code, country_name, exc)
        return None, f"Data service returned an unexpected error (HTTP {exc.response.status_code})."

    except Exception as exc:  # noqa: BLE001
        logger.exception("Unexpected error fetching country '%s'", country_name)
        return None, f"An unexpected error occurred: {exc}"


# ── helpers ───────────────────────────────────────────────────────────────────

def _pick_best_match(query: str, results: list[dict]) -> dict:
    """Prefer an exact common-name match; fall back to first result."""
    q = query.lower()
    for r in results:
        common = r.get("name", {}).get("common", "").lower()
        official = r.get("name", {}).get("official", "").lower()
        if q in (common, official):
            return r
    return results[0]
