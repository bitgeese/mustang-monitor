# mustang_monitor/sources/base.py
from __future__ import annotations
from typing import Iterator


def run_apify(client, actor_id: str, run_input: dict) -> Iterator[dict]:
    """Run an Apify actor and yield its dataset items."""
    run = client.actor(actor_id).call(run_input)
    dataset_id = run["defaultDatasetId"]
    yield from client.dataset(dataset_id).iterate_items()
