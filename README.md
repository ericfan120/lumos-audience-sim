# 🧠 Lumos Audience Intelligence Simulator

> *MiroFish-inspired swarm intelligence engine for DOOH campaign prediction*

A **proof-of-concept** multi-agent audience simulator that predicts how Australian consumers will respond to your out-of-home advertising campaigns — before you spend a dollar.

---

## What It Does

Inspired by [MiroFish](https://github.com/666ghj/MiroFish), this tool simulates a "swarm" of synthetic consumer personas who encounter your OOH ad and interact with each other, producing a rich prediction report with:

| Output | Description |
|--------|-------------|
| **Brand Recall %** | Estimated awareness lift from OOH exposure |
| **Purchase Intent %** | Share of audience likely to act |
| **Reach Estimate** | Weekly impressions based on location + budget |
| **ROAS Prediction** | Return on ad spend forecast with justification |
| **Persona Reactions** | 10 diverse Sydney consumers, each with a unique voice |
| **Social Cascade** | How word-of-mouth and social posts amplify reach |
| **Full Report** | Markdown report with AU DOOH benchmarks |
| **Chat Interface** | Ask any persona a question or query the Lumos Engine |

---

## Why It Matters for DOOH

Traditional DOOH planning is based on aggregate audience data — impressions, demographics, OTS (opportunity to see). But **how** those impressions land, which segments remember the message, and how it spreads organically is invisible.

Lumos Audience Intelligence Simulator addresses this by:

1. **Synthesising realistic personas** — not demographics, but people with commute routes, lifestyle habits, ad skepticism levels, and social influence scores
2. **Simulating individual encounters** — each persona reasons about whether they noticed the ad, what they felt, and what they'll do next
3. **Modelling social cascades** — some personas mention the ad to friends on Instagram or WhatsApp, creating earned amplification
4. **Generating actionable predictions** — the report references real Australian DOOH benchmarks (OMA data, industry averages)

This is the intelligence layer between media planning and outcomes.

---

## Architecture

```
┌─────────────────────────────────────┐
│  Campaign Brief (brand, message,    │
│  location, budget, duration)        │
└────────────────┬────────────────────┘
                 │ POST /api/simulate
                 ▼
┌─────────────────────────────────────┐
│  Step 1: Persona Generation         │
│  → 10 synthetic Sydney consumers    │
│    with commute routes, habits,     │
│    skepticism + influence scores    │
└────────────────┬────────────────────┘
                 ▼
┌─────────────────────────────────────┐
│  Step 2: Exposure Simulation        │
│  → Per-persona OOH encounter        │
│    (noticed? recall? emotion?       │
│     likely action? quote?)          │
└────────────────┬────────────────────┘
                 ▼
┌─────────────────────────────────────┐
│  Step 3: Social Cascade             │
│  → Peer interaction simulation      │
│    (conversation, Instagram,        │
│     WhatsApp — influence delta)     │
└────────────────┬────────────────────┘
                 ▼
┌─────────────────────────────────────┐
│  Step 4: Report Synthesis           │
│  → Aggregated prediction report:    │
│    recall, intent, ROAS, segments,  │
│    benchmarks, recommendations      │
└────────────────┬────────────────────┘
                 ▼
         Interactive Frontend
         (persona cards, cascade
          flow, chat interface)
```

---

## Setup

### 1. Install dependencies

```bash
cd /path/to/audience-sim
python3.13 -m pip install -r requirements.txt
```

### 2. Configure API key (optional — demo works without one)

```bash
cp .env.example .env
# Edit .env — add ANTHROPIC_API_KEY for live AI simulation
```

The simulator runs in **demo mode** with rich mock data if no API key is provided. Add your Anthropic key for live AI-powered simulations.

### 3. Start the server

```bash
python3.13 -m uvicorn app:app --reload --port 8000
```

Open [http://localhost:8000](http://localhost:8000) in your browser.

---

## Example Campaign Brief

| Field | Example |
|-------|---------|
| **Brand** | Koala Mattresses |
| **Message** | "Better sleep starts tonight. Try free for 120 nights." |
| **Target Audience** | Urban professionals 25–45, health-conscious, recently moved |
| **OOH Location** | Sydney CBD digital billboards + Town Hall Station concourse |
| **Duration** | 4 weeks |
| **Budget** | $75,000 AUD |

Expected output:
- ~80% recall rate
- ~40% positive intent
- ~937,500 estimated reach
- ~2.8x ROAS prediction

---

## API Reference

### `GET /api/health`
Returns server status and active mode (anthropic / openai / mock).

### `POST /api/simulate`
```json
{
  "brand_name": "string",
  "campaign_message": "string",
  "target_audience": "string",
  "ooh_location": "string",
  "campaign_duration": "string",
  "budget_aud": 75000
}
```

Returns: full simulation result with `personas`, `exposures`, `social_cascade`, `report`, and `stats`.

### `POST /api/chat`
```json
{
  "simulation_id": "sim_1234567890",
  "question": "Would you buy this product?",
  "persona_id": "p3"  // optional — omit to chat with the Lumos Engine
}
```

---

## LLM Configuration

| Priority | SDK | Env Var | Model |
|----------|-----|---------|-------|
| 1st | `anthropic` | `ANTHROPIC_API_KEY` | `claude-3-5-haiku-20241022` |
| 2nd | `openai` | `OPENAI_API_KEY` | `gpt-4o-mini` (configurable) |
| Fallback | Mock | *(none)* | Rich synthetic data |

Custom OpenAI-compatible endpoints (OpenRouter, Together, etc.) are supported via `OPENAI_BASE_URL`.

---

## Screenshot

*(Coming soon — run the app and take a screenshot!)*

---

## Inspiration

Built on ideas from [MiroFish](https://github.com/666ghj/MiroFish) — a multi-agent swarm intelligence engine that spawns AI agents with unique personas, long-term memory, and social behaviour to simulate complex human systems.

Adapted for Lumos' programmatic DOOH context: instead of general social simulation, Lumos Audience Intelligence focuses on the specific moment of OOH ad encounter and the downstream social amplification it creates.

---

*Built by Lumos · [spotlumos.com](https://spotlumos.com) · Powered by Claude + FastAPI*
