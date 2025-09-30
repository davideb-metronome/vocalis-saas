# Vocalis

FastAPI backend + static frontend with Metronome billing via the official Python SDK (metronome-sdk). Supports prepaid credits, plan selection, usage ingest, auto‑recharge (threshold billing), and realtime updates via SSE.

## Requirements

- Python 3.10+
- Root `.env` with:
  - `METRONOME_API_KEY`
  - `METRONOME_API_URL=https://api.metronome.com`
  - `METRONOME_RATE_CARD_NAME` (exact rate card name in Metronome)
  - `VOCALIS_CREDIT_TYPE_ID` (your custom credit type id)
  - `METRONOME_WEBHOOK_SECRET` (optional, to verify webhooks)

## Quick Start

1) Install dependencies

```
python3 -m venv venv
source venv/bin/activate
cd backend
pip install -r requirements.txt
```

2) Configure environment

```
cp .env.example ../.env
# Edit ../.env with your Metronome keys and names
```

3) Run the server

```
python -m app.main
```

Visit http://localhost:8000

Health: http://localhost:8000/health/integrations

## SDK‑Only

- All Metronome calls use `metronome-sdk`.
- Temporary shim: threshold‑billing release (POST `/v1/contracts/commits/threshold-billing/release`) is invoked via a tiny internal HTTP call until the SDK exposes it.

## Metronome Setup

- Rate card: create/confirm a card whose name equals `METRONOME_RATE_CARD_NAME`.
- Credit type: ensure `VOCALIS_CREDIT_TYPE_ID` is valid on that rate card.
- Product: "Vocalis Credits" is created on demand if missing.
- Usage meters:
  - `voice_generation`: properties include `text_length` and `voice_type` ("standard" | "premium").
  - `voice_cloning`: one‑time setup event (configure a meter if you want a 25,000 credit deduction).
- Webhooks (ngrok/public URL):
  - Alerts → `POST /api/webhooks/metronome/alerts`
  - Payment gating → `POST /api/webhooks/metronome/payment-gating`
  - If `METRONOME_WEBHOOK_SECRET` is set, signatures must match.

## Core Flows

- Signup → creates customer with ingest aliases.
- Plan selection (Trial/Creator/Pro) → creates contract with initial credits.
- Usage (Standard/Premium/Clone) → ingests events; balance updates.
- Auto‑recharge → on `external_initiate` webhook, app releases threshold billing and broadcasts `balance_updated`.

## Realtime (SSE)

- Client connects to `GET /api/webhooks/events/{customer_id}`.
- Server streams initial `connected` and subsequent `balance_updated` events.
