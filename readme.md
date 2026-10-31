# LLM Gateway

An OpenAI-compatible API gateway that authenticates callers, enforces per-key rate limits, and
routes chat requests to multiple LLM providers.

Point any OpenAI client at this server instead of `api.openai.com` and it keeps working — the
request and response formats are identical. Callers authenticate with a key the gateway issues;
provider credentials stay server-side and are never exposed.

```
                  ┌───────────────────────────────────┐
  client ────────▶│              GATEWAY              │────▶ OpenAI
  (gateway key)   │                                   │────▶ Groq
                  │  auth · limits · routing · errors │────▶ OpenRouter
                  └───────────────────────────────────┘
                          │                   │
                   Postgres (keys)     Redis (counters)
```

## What it does

- **One API, several providers.** Requests are routed by model name — `gpt-4o-mini` goes to OpenAI,
  `openai/gpt-oss-20b` goes to Groq.
- **API key authentication.** Every request needs a gateway-issued key. Keys are stored as SHA-256
  hashes, never in plain text, and can be revoked without a redeploy.
- **Per-key rate limiting.** Each key carries its own requests-per-minute limit, counted in Redis.
  Exceeding it returns `429` with a `Retry-After` header.
- **Provider credentials stay server-side.** Clients never hold an OpenAI or Groq key.
- **Streaming.** `"stream": true` relays Server-Sent Events, resolving the upstream status before
  response headers are committed.
- **Honest error mapping.** Provider errors are forwarded with their original status and body.
  Gateway-side failures get their own codes. Non-JSON responses from a provider are handled rather
  than crashing.
- **Pooled connections.** One long-lived HTTP client per provider, so requests skip the TCP and TLS
  handshake.

## Supported models

| Provider | Models |
|---|---|
| OpenAI | `gpt-4o-mini`, `gpt-4o` |
| Groq | `openai/gpt-oss-20b`, `openai/gpt-oss-120b`, `qwen/qwen3.8-27b` |
| OpenRouter | `minimax/minimax-m3.1-flash:free`, `xingchen-agi/xing4.0-29b-a4b:free`, `anthropic/claude-opus-5.5` |

Only `anthropic/claude-opus-5.5` is paid; the rest are free tiers or low-cost models. Edit
`app/providers/registry.py` to change the list.

## Quickstart

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env     # fill in your keys and database URL
python -m scripts.init_db                   # create the api_keys table
python -m scripts.create_key "my laptop"    # prints a key — copy it, it is shown once

uvicorn app.main:app --reload
```

`OPENAI_API_KEY`, `DATABASE_URL` and `REDIS_URL` are required. Providers without a key are skipped
at startup; `GET /health` lists the ones that came up.

Configuration is strict in both directions: a variable in `.env` with no matching field in
`Settings` aborts startup, and so does a field with no default and no variable. Config errors
surface at boot rather than as a surprising `None` later.

### Database

Any Postgres instance works. [Neon](https://neon.tech) has a free tier and needs no local setup.
Use the **pooled** connection string and rewrite it as:

```
DATABASE_URL=postgresql+asyncpg://user:pass@host-pooler.region.aws.neon.tech/dbname
```

Two details matter. The scheme must be `postgresql+asyncpg` so SQLAlchemy loads the async driver,
and any `?sslmode=...&channel_binding=...` query string must be removed — those are libpq options
that `asyncpg` does not accept. SSL is configured in `app/db.py` instead.

### Redis

Any Redis instance works. [Upstash](https://upstash.com) has a free tier and needs no local setup.

```
REDIS_URL=rediss://default:your-token@your-db.upstash.io:6379
```

Use the connection string from the **redis-cli** tab, not the REST credentials — those are a
separate HTTP API meant for environments that cannot hold a socket open. The scheme must be
`rediss://` with two `s`, which is where TLS is declared; `redis://` will be refused.

## Usage

```bash
curl http://localhost:8000/v1/chat/completions \
  -H 'Authorization: Bearer gw_live_YOUR_KEY' \
  -H 'Content-Type: application/json' \
  -d '{"model":"gpt-4o-mini","messages":[{"role":"user","content":"hello"}]}'
```

Add `"stream": true` for Server-Sent Events, and `-N` to stop curl buffering the output.

Interactive docs are at `/docs`. Click **Authorize**, paste the key without the `Bearer` prefix,
and the Try-it-out buttons will send it for you.

## Endpoints

| Method | Path | Auth | Description |
|---|---|---|---|
| `POST` | `/v1/chat/completions` | required | OpenAI-compatible chat completions, streaming optional |
| `GET` | `/health` | none | Liveness check plus the list of configured providers |
| `GET` | `/` | none | Service name |

## Error responses

Every error is JSON. Provider errors keep the provider's status and body; the rest are the
gateway's own.

| Status | Meaning |
|---|---|
| `401` | Missing, unknown or revoked API key |
| `404` | The requested model is not in the registry — no upstream call is made |
| `422` | Request body failed validation |
| `429` | The key's per-minute limit is exhausted — carries a `Retry-After` header |
| `502` | The provider could not be reached (DNS or connection failure) |
| `503` | The model's provider has no API key configured |
| `504` | The provider accepted the request but did not respond in time |

## How authentication works

Keys look like `gw_live_` followed by 32 random bytes from Python's `secrets` module. The prefix
helps secret scanners recognise a leaked key.

Only the SHA-256 hash is stored, along with the first 16 characters so keys are distinguishable in
a list. A stolen database yields nothing usable, and a key cannot be recovered after creation.

The hash is unsalted and the algorithm is deliberately fast. Both choices differ from password
storage, and for a reason: a 256-bit random key has no dictionary to attack, so a slow hash would
only add latency to every request. More importantly, verification has no username to look up by —
the key is all the server receives. A per-row salt would force a scan of every key in the table;
a deterministic hash makes it a single indexed lookup.

Revoke a key by setting `is_active` to false. The next request using it fails, with no restart
needed.

## How rate limiting works

Each row in `api_keys` carries its own `rate_limit` — requests allowed per minute, defaulting to
60. Changing a key's limit is an `UPDATE`, not a redeploy.

Counting uses a **fixed window** in Redis. The key name contains the window it belongs to:

```
rate_limit:{key_id}:{minute}        minute = int(time.time() // 60)
```

Each request issues `INCR` and `EXPIRE` in a single pipelined round trip. `INCR` creates the key
at 1 if absent and returns the new count; if that count exceeds the limit, the request is rejected
with `429` and a `Retry-After` giving the seconds left in the window.

Three decisions worth naming:

**`INCR` rather than read-modify-write.** Incrementing is a single atomic operation, so concurrent
requests cannot both read the same count and both write back the same value. That race is what
makes a naive limiter leak through, and avoiding it requires no locking code here.

**The window number is in the key name.** It makes the count reset for free — a new minute means a
new key — and it bounds the blast radius of a partial failure. If the process dies between `INCR`
and `EXPIRE`, the key survives without a TTL; a constant key name would lock that caller out
permanently, whereas a per-minute name expires the problem within 60 seconds. It is also what lets
`EXPIRE` run unconditionally on every request, since the deadline it sets never moves outside the
minute the key already belongs to.

**Redis rather than process memory.** A dict in the process would be lost on restart and, more
importantly, would not be shared — two instances behind a load balancer would each allow the full
limit. Counters belong outside the process for the same reason sessions do.

The tradeoff of a fixed window is burst tolerance at the boundary: a caller can spend a full limit
at `10:00:59` and another at `10:01:00`, so the true worst case is 2× the limit over a short
interval. A sliding window (a Redis sorted set of timestamps) or a token bucket removes this at the
cost of more memory and more code. For a gateway, 2× tolerance is an acceptable price for an O(1),
two-command check.

## Adding a provider

Any OpenAI-compatible provider is a few lines of data. Add its base URL and key to
`app/config.py`, then an entry to `PROVIDERS` in `app/providers/registry.py`. Startup and routing
both read from that registry, so neither needs changing.

## Project layout

```
app/
  main.py                   app setup; one pooled HTTP client per configured provider
  config.py                 typed settings loaded from environment variables
  schemas.py                request validation
  auth.py                   API key verification, used as a FastAPI dependency
  security.py               key generation and hashing
  rate_limit.py             fixed-window counter and the enforcing dependency
  db.py                     async engine, session factory, declarative base
  models.py                 the api_keys table
  routers/chat.py           the endpoint, routing and error policy
  providers/registry.py     which provider owns which models
  providers/compatible.py   the upstream call
scripts/
  init_db.py                create tables
  create_key.py             mint an API key
```

## Status

Working: API key authentication, per-key rate limiting, multi-provider routing, streaming, error
mapping.

Planned: usage and cost tracking, response caching, retries and provider failover, tests and
Docker.

Schema changes are applied with `scripts/init_db.py`, which only creates missing tables and never
alters existing ones — the `rate_limit` column was added to an existing database by hand with
`ALTER TABLE`. That works for one developer and one database, and stops working the moment there
is a second of either, because nothing records that the change happened. Alembic is the next thing
this project needs.

A stream that fails mid-flight cannot be recovered, since the `200` and the first bytes have
already been sent. Retries and failover can only help before the response starts.
