# LLM Gateway

An OpenAI-compatible API gateway that routes chat requests to multiple LLM providers.

Point any OpenAI client at this server instead of `api.openai.com` and it keeps working — the
request and response formats are identical. Provider credentials stay server-side, so callers
never hold an API key.

```
client ──▶ gateway ──┬──▶ OpenAI
                     ├──▶ Groq
                     └──▶ OpenRouter
```

## What it does

- **One API, several providers.** Requests are routed by model name, so `gpt-4o-mini` goes to
  OpenAI and `openai/gpt-oss-20b` goes to Groq.
- **Credentials stay server-side.** Clients send no API key; the gateway attaches the right one
  per provider.
- **Streaming.** `"stream": true` relays Server-Sent Events, resolving the upstream status before
  response headers are committed.
- **Honest error mapping.** Provider errors are forwarded with their original status and body.
  Gateway-side failures get `504` (upstream timed out) or `502` (upstream unreachable); an unknown
  model gets `404` with no upstream call at all.
- **Pooled connections.** One long-lived HTTP client per provider, so requests skip the TCP and TLS
  handshake.

## Quickstart

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env     # add your API keys
uvicorn app.main:app --reload
```

Only `OPENAI_API_KEY` is required. Providers without a key are skipped at startup — `GET /health`
lists the ones that came up.

## Usage

```bash
curl http://localhost:8000/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{"model":"gpt-4o-mini","messages":[{"role":"user","content":"hello"}]}'
```

Add `"stream": true` for Server-Sent Events. Interactive docs at `/docs`.

## Endpoints

| Method | Path | Description |
|---|---|---|
| `POST` | `/v1/chat/completions` | OpenAI-compatible chat completions, streaming optional |
| `GET` | `/health` | Liveness check plus the list of configured providers |

## Adding a provider

Any OpenAI-compatible provider is three lines of data. Add its base URL and key to `config.py`,
then an entry to `PROVIDERS` in `app/providers/registry.py`. The router and startup code read from
that registry, so neither needs changing.

## Project layout

```
app/
  main.py                   app setup; builds one pooled HTTP client per provider
  config.py                 typed settings loaded from environment variables
  schemas.py                request validation
  routers/chat.py           the endpoint, routing and error policy
  providers/registry.py     which provider owns which models
  providers/compatible.py   the upstream call
```

## Status

Working: multi-provider routing, streaming, error mapping, configurable providers.

Planned: API key auth, per-key rate limiting, usage and cost tracking, response caching, retries
and provider failover, tests and Docker.

Not production-ready — there is no authentication yet, so don't expose it to a network.
