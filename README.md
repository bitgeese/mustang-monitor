# mustang-monitor

Watches PL/DE/AT car marketplaces for a 1999–2004 Ford Mustang GT (manual, coupe)
matching `config/spec.yaml` and pushes Telegram alerts for new / price-dropped matches.

Pipeline per listing: `fetch (Apify) → normalize → free rules gate → free NHTSA vPIC VIN
decode → Claude Haiku score (survivors only) → SQLite dedup → Telegram`. Runs on GitHub
Actions cron; state (`state/monitor.db`) is committed back to the repo each run.

## Setup

1. Create a **public** GitHub repo and push this code (public = unlimited Actions minutes for 24/7 cron).
2. Create a Telegram bot via **@BotFather**; get the bot token and your chat id
   (message the bot, then read `https://api.telegram.org/bot<TOKEN>/getUpdates` and copy `chat.id`).
3. Get an **Apify** token (apify.com) and an **Anthropic** API key (console.anthropic.com).
4. Add repo **Settings → Secrets and variables → Actions**:
   `APIFY_TOKEN`, `TELEGRAM_TOKEN`, `TELEGRAM_CHAT_ID`, `ANTHROPIC_API_KEY`.
5. Confirm the `apify_actor` ids in `config/spec.yaml` exist on the Apify store, and adjust each
   site's `map_item` field names against one real dataset item (see "Per-site mapper check" below).

## Local run

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -e ".[dev]"
pytest -q
# dry-run uses an in-memory db and only prints would-be alerts (no Telegram, no state written):
APIFY_TOKEN=... ANTHROPIC_API_KEY=... python -m mustang_monitor.run --dry-run
```

## Per-site mapper check (before trusting a site)

Only `otomoto` has a verified field mapping. For each other site, run its Apify actor once,
copy one dataset item into `tests/fixtures/<site>_item.json`, add a `map_item` test mirroring
`tests/test_sources.py::test_otomoto_map_item`, and correct the `item.get(...)` keys in
`mustang_monitor/sources/<site>.py` to the actor's real field names.

## Tuning

Edit `config/spec.yaml` — model years, price/mileage bands, multilingual keyword lists,
per-site Apify actors + search URLs, and the score threshold. The Facebook group is out of
scope for automation (Meta deprecated the Groups API); use FB's in-app post notifications.

## Flags

- `--dry-run` — print would-be alerts, in-memory db, no sending/persisting.
- `--backfill-silent` — seed state without alerting (quiet first run).
- `--spec PATH` / `--db PATH` — override config / state-db locations.
