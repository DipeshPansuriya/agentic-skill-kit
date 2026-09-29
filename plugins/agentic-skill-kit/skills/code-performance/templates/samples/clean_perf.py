# Clean sample for perf_smells.py: expected 0 HIGH / 0 MED.
import asyncio
import re

import httpx

AWB_RE = re.compile(r"^\d{3}-\d{8}$")


def manifest(awbs, blocked_ids):
    blocked = set(blocked_ids)
    return "\n".join(a["number"] for a in awbs if a["id"] not in blocked and AWB_RE.match(a["number"]))


async def fetch_rates(ids, limit=10):
    sem = asyncio.Semaphore(limit)
    async with httpx.AsyncClient(timeout=5) as client:
        async def one(i):
            async with sem:
                return (await client.get(f"/rates/{i}")).json()
        return await asyncio.gather(*(one(i) for i in ids))


def totals(df):
    return (df["weight"] * df["rate"]).sum()
