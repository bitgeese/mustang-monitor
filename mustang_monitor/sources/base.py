# mustang_monitor/sources/base.py
from __future__ import annotations
from typing import Iterator


def run_apify(client, actor_id: str, run_input: dict) -> Iterator[dict]:
    """Run an Apify actor and yield its dataset items.

    Matches apify-client 3.x: ActorClient.call is keyword-only and returns a
    Run pydantic model (or None if the run didn't finish in time).
    """
    run = client.actor(actor_id).call(run_input=run_input)
    if run is None:
        raise RuntimeError(f"Apify actor {actor_id!r} did not complete")
    yield from client.dataset(run.default_dataset_id).iterate_items()
