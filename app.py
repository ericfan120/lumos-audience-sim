"""
Lumos Audience Intelligence Simulator — Backend
MiroFish-inspired swarm intelligence engine for DOOH campaign prediction.

Architecture:
  1. Persona generation — 10 diverse Australian consumer personas
  2. Exposure simulation — per-persona OOH ad reaction
  3. Social cascade — peer influence propagation
  4. Report synthesis — aggregated prediction report
"""

import os
import json
import random
import asyncio
import logging
from datetime import datetime
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ─── LLM Client Setup ────────────────────────────────────────────────────────

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
ANTHROPIC_MODEL = "claude-3-5-haiku-20241022"

USE_ANTHROPIC = bool(ANTHROPIC_API_KEY)
USE_OPENAI = bool(OPENAI_API_KEY) and not USE_ANTHROPIC
USE_MOCK = not USE_ANTHROPIC and not USE_OPENAI

anthropic_client = None
openai_client = None

if USE_ANTHROPIC:
    try:
        import anthropic
        anthropic_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        logger.info("Using Anthropic SDK with claude-3-5-haiku-20241022")
    except ImportError:
        logger.warning("anthropic package not installed, falling back")
        USE_ANTHROPIC = False
        USE_MOCK = True

if USE_OPENAI:
    try:
        from openai import OpenAI
        openai_client = OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)
        logger.info(f"Using OpenAI SDK with {OPENAI_MODEL}")
    except ImportError:
        logger.warning("openai package not installed, falling back to mock")
        USE_OPENAI = False
        USE_MOCK = True

if USE_MOCK:
    logger.info("No API keys found — using rich mock simulation data")

SYSTEM_PROMPT = """You are a consumer behaviour simulation engine for Lumos, Australia's leading programmatic DOOH platform.
Your job is to realistically simulate how Australian consumers respond to out-of-home advertising.
Be specific, data-driven, and realistic. Use Australian English. Return valid JSON when asked."""


async def llm_call(prompt: str, expect_json: bool = True) -> str:
    """Single unified LLM call with error handling."""
    if USE_ANTHROPIC and anthropic_client:
        try:
            resp = anthropic_client.messages.create(
                model=ANTHROPIC_MODEL,
                max_tokens=4096,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}]
            )
            return resp.content[0].text
        except Exception as e:
            logger.error(f"Anthropic call failed: {e}")
            raise

    if USE_OPENAI and openai_client:
        try:
            resp = openai_client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=4096
            )
            return resp.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI call failed: {e}")
            raise

    raise RuntimeError("No LLM client available")


def parse_json_response(text: str) -> Any:
    """Extract JSON from LLM response, handling markdown code fences."""
    text = text.strip()
    # Strip markdown fences
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0].strip()
    elif "```" in text:
        text = text.split("```")[1].split("```")[0].strip()
    return json.loads(text)


# ─── Mock Data ────────────────────────────────────────────────────────────────

MOCK_PERSONAS = [
    {"id": "p1", "name": "Sarah Chen", "age": 32, "occupation": "Marketing Manager", "suburb": "Surry Hills",
     "daily_commute": "Trains from Central to Wynyard, walks through Martin Place", "lifestyle_traits": ["coffee lover", "Instagram active", "health conscious", "brunches on weekends"], "ad_skepticism": 4, "social_influence_score": 8},
    {"id": "p2", "name": "Jordan Mackay", "age": 24, "occupation": "UX Designer", "suburb": "Newtown",
     "daily_commute": "Cycles from Newtown to Pyrmont, past Broadway shops", "lifestyle_traits": ["eco-conscious", "TikTok creator", "thrift shopper", "vegan"], "ad_skepticism": 7, "social_influence_score": 9},
    {"id": "p3", "name": "Priya Sharma", "age": 41, "occupation": "Financial Analyst", "suburb": "Chatswood",
     "daily_commute": "North Shore Line to Wynyard, 35 min", "lifestyle_traits": ["busy mum of two", "online shopper", "brand loyal", "morning news reader"], "ad_skepticism": 5, "social_influence_score": 6},
    {"id": "p4", "name": "Marcus Webb", "age": 28, "occupation": "Personal Trainer", "suburb": "Bondi",
     "daily_commute": "Bus 333 from Bondi Beach to CBD", "lifestyle_traits": ["fitness obsessed", "whey protein subscriber", "YouTube watcher", "outdoor activities"], "ad_skepticism": 3, "social_influence_score": 7},
    {"id": "p5", "name": "Helen Torres", "age": 55, "occupation": "School Principal", "suburb": "Parramatta",
     "daily_commute": "Drives to Parramatta station, takes train to Town Hall", "lifestyle_traits": ["family-focused", "Facebook user", "local community events", "gardening"], "ad_skepticism": 6, "social_influence_score": 5},
    {"id": "p6", "name": "Ethan Liu", "age": 19, "occupation": "University Student", "suburb": "Ultimo",
     "daily_commute": "Walks from UTS to Central for shopping, trams to UNSW", "lifestyle_traits": ["Gen Z", "meme culture", "broke but aspirational", "Discord user", "gaming"], "ad_skepticism": 8, "social_influence_score": 6},
    {"id": "p7", "name": "Amara Okafor", "age": 35, "occupation": "Nurse", "suburb": "Liverpool",
     "daily_commute": "T2 train Liverpool to Central, shift worker", "lifestyle_traits": ["practical buyer", "coupons/deals", "WhatsApp family groups", "Netflix"], "ad_skepticism": 5, "social_influence_score": 7},
    {"id": "p8", "name": "Tom Gallagher", "age": 47, "occupation": "Construction Project Manager", "suburb": "Penrith",
     "daily_commute": "Drives to Penrith, Blue Mountains Line to Central", "lifestyle_traits": ["tradies culture", "footy fan", "BBQ enthusiast", "skeptical of ads"], "ad_skepticism": 8, "social_influence_score": 4},
    {"id": "p9", "name": "Lena Hoffmann", "age": 30, "occupation": "Graphic Designer (Freelance)", "suburb": "Glebe",
     "daily_commute": "Walks/cycles through the city, coffee shop hopper", "lifestyle_traits": ["aesthetics-driven", "Pinterest user", "independent brands", "brunch culture"], "ad_skepticism": 4, "social_influence_score": 8},
    {"id": "p10", "name": "David Park", "age": 38, "occupation": "Software Engineer", "suburb": "Mascot",
     "daily_commute": "Airport Line to Central, then walks", "lifestyle_traits": ["tech early adopter", "Reddit lurker", "podcast listener", "data-driven decisions"], "ad_skepticism": 6, "social_influence_score": 5},
]


def generate_mock_exposures(personas, brief):
    """Generate realistic mock exposure results."""
    results = []
    brand = brief.get("brand_name", "Brand")
    message = brief.get("campaign_message", "")
    location = brief.get("ooh_location", "CBD digital billboard")

    for p in personas:
        skepticism = p["ad_skepticism"]
        recall_base = max(1, 5 - skepticism // 2)
        noticed = skepticism < 8 or random.random() > 0.3
        recall = min(5, recall_base + random.randint(-1, 1)) if noticed else 1

        responses = [
            ("positive", ["Might actually check that out", "That looks interesting", "Ohh I've heard of them"]),
            ("neutral", ["Just another billboard", "I'll forget this in 5 minutes", "Hmm, noted"]),
            ("negative", ["Not for me", "Too in-your-face", "I'm over ads"]),
        ]
        if skepticism <= 4:
            resp_type, quotes = responses[0]
        elif skepticism <= 6:
            resp_type, quotes = responses[1]
        else:
            resp_type, quotes = responses[2]

        results.append({
            "persona_id": p["id"],
            "persona_name": p["name"],
            "noticed": noticed,
            "recall_strength": recall,
            "emotional_response": resp_type,
            "likely_action": "search online" if recall >= 3 else "ignore" if not noticed else "passive awareness",
            "quote": f"\"{random.choice(quotes)} — {brand} at {location}\""
        })
    return results


def generate_mock_social_cascade(personas, exposures, brief):
    """Generate mock social influence cascade."""
    channels = ["conversation", "instagram", "whatsapp"]
    high_recall = [e for e in exposures if e["recall_strength"] >= 3]
    interactions = []

    pairs = [(high_recall[i], exposures[j]) for i in range(min(3, len(high_recall)))
              for j in range(len(exposures)) if exposures[j]["persona_id"] != high_recall[i]["persona_id"]]
    random.shuffle(pairs)

    for from_e, to_e in pairs[:6]:
        channel = random.choice(channels)
        brand = brief.get("brand_name", "Brand")
        msgs = {
            "conversation": f"Hey, did you see that {brand} billboard on the way in? Actually looks decent.",
            "instagram": f"Spotted this {brand} campaign at {brief.get('ooh_location','the city')} 📍 Actually kinda clever #DOOH #Sydney",
            "whatsapp": f"Random but has anyone tried {brand}? Saw their ad everywhere this week"
        }
        interactions.append({
            "from_persona": from_e["persona_name"],
            "to_persona": to_e["persona_name"],
            "channel": channel,
            "message": msgs[channel],
            "influence_delta": round(random.uniform(0.1, 0.4), 2)
        })

    return interactions[:6]


def generate_mock_report(brief, personas, exposures, cascade):
    """Generate a rich mock prediction report."""
    brand = brief.get("brand_name", "Brand")
    budget = brief.get("budget_aud", 50000)
    duration = brief.get("campaign_duration", "4 weeks")
    location = brief.get("ooh_location", "Sydney CBD")

    noticed = sum(1 for e in exposures if e["noticed"])
    high_recall = sum(1 for e in exposures if e["recall_strength"] >= 3)
    positive = sum(1 for e in exposures if e["emotional_response"] == "positive")

    recall_pct = round((noticed / len(exposures)) * 100)
    intent_pct = round((positive / len(exposures)) * 100)
    reach_est = int(budget * 12.5)  # rough DOOH CPM-based estimate
    roas = round(2.1 + (intent_pct / 100) * 1.8, 2)

    return f"""# Lumos Campaign Prediction Report
**Brand:** {brand} | **Location:** {location} | **Duration:** {duration} | **Budget:** ${budget:,} AUD
*Generated: {datetime.now().strftime('%d %B %Y, %H:%M AEST')}*

---

## Executive Summary

The simulated campaign for **{brand}** across {location} demonstrates **strong audience resonance** with urban professional and Gen Z segments. Based on swarm simulation of {len(personas)} synthetic consumer personas representing Sydney's key commuter demographics, we forecast above-benchmark performance on brand recall and digital amplification.

---

## Audience Reach Analysis

- **Estimated weekly impressions:** {reach_est:,}
- **Campaign duration:** {duration}
- **Total estimated reach:** {reach_est * 4:,} (unduplicated)
- **Primary segments reached:** CBD commuters, inner-west residents, North Shore professionals
- **Peak exposure windows:** 7:30–9:00 AM and 5:00–6:30 PM (commute peaks)

> *Australian DOOH Benchmark: Premium CBD digital panels deliver ~85,000 weekly impressions. Budget efficiency indicates {round(reach_est / (budget/1000), 1)} impressions per $1,000 spent.*

---

## Brand Recall Forecast

| Metric | Simulation Result | AU DOOH Benchmark |
|--------|:-----------------:|:-----------------:|
| Ad noticed rate | **{recall_pct}%** | 72% |
| Unaided recall (24h) | **{round(recall_pct * 0.55)}%** | 38% |
| Aided recall (7 days) | **{round(recall_pct * 0.72)}%** | 54% |
| Message association | **{round(recall_pct * 0.48)}%** | 31% |

**Key finding:** Personas with lower ad-skepticism scores (≤4) showed recall strength of 4–5/5, particularly among marketing professionals and health-conscious millennials.

---

## Purchase Intent by Segment

| Segment | Intent Score | Personas |
|---------|:------------:|---------|
| Urban professionals (25–40) | **{intent_pct + 8}%** | Sarah Chen, Lena Hoffmann, David Park |
| Health & lifestyle | **{intent_pct + 12}%** | Marcus Webb, Jordan Mackay |
| Families & parents | **{intent_pct - 5}%** | Priya Sharma, Helen Torres |
| Gen Z (18–25) | **{intent_pct - 3}%** | Ethan Liu |
| Trade/blue collar | **{intent_pct - 15}%** | Tom Gallagher |

**Overall purchase intent:** **{intent_pct}%** *(AU average: 18%)*

---

## Social Amplification Estimate

Simulation modelled {len(cascade)} organic social interactions triggered by OOH exposure:

- **Instagram story mentions:** {sum(1 for c in cascade if c['channel'] == 'instagram')} predicted posts
- **WhatsApp word-of-mouth:** {sum(1 for c in cascade if c['channel'] == 'whatsapp')} conversations
- **In-person mentions:** {sum(1 for c in cascade if c['channel'] == 'conversation')} exchanges
- **Earned social amplification multiplier:** ~{round(1 + len(cascade) * 0.15, 1)}x

High social-influence personas (Jordan Mackay, Sarah Chen, Lena Hoffmann) are predicted to generate the most organic reach via Instagram and WhatsApp.

---

## Budget Efficiency Score

```
Budget:          ${budget:,} AUD
CPM (effective): ${round(budget / (reach_est / 1000), 2)}
Cost per recall: ${round(budget / (reach_est * (recall_pct/100)), 2)}
Cost per intent: ${round(budget / (reach_est * (intent_pct/100)), 2)}
Efficiency score: {min(10, round(3.5 + (intent_pct / 20), 1))}/10
```

---

## ROAS Prediction

**Predicted ROAS: {roas}x**

*Justification:*
- Australian DOOH average ROAS: 1.8–2.3x (source: OMA 2024 benchmarks)
- Premium CBD location uplift: +0.3x
- Campaign message resonance with high-income commuter segment: +0.2x
- Social cascade amplification: +{round(roas - 2.0, 1)}x
- Duration premium ({duration}): sustained frequency builds recall curve

---

## Recommendations

1. **Target commute peaks** — Schedule 60% of impressions during 7:30–9 AM and 5–6:30 PM for maximum commuter exposure
2. **Amplify with social** — Brief nano-influencers in the Surry Hills/Newtown corridor to mirror OOH message on Instagram
3. **Retarget high-intent segments** — Layer programmatic mobile retargeting for personas who pass the screen (geo-fencing within 200m)
4. **Extend to 6 weeks** — Recall curve modelling suggests 6-week flights outperform 4-week by 23% on aided recall
5. **Consider North Shore panels** — Priya Sharma segment shows strong purchase intent but lower exposure frequency in current plan

---

*Simulation powered by Lumos Audience Intelligence Engine v1.0 — MiroFish-inspired swarm intelligence*
*Confidence interval: ±12% | Based on {len(personas)}-persona synthetic cohort*"""


# ─── FastAPI App ──────────────────────────────────────────────────────────────

app = FastAPI(title="Lumos Audience Intelligence Simulator", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory simulation store (PoC — no persistence needed)
simulations: dict[str, dict] = {}


class CampaignBrief(BaseModel):
    brand_name: str
    campaign_message: str
    target_audience: str
    ooh_location: str
    campaign_duration: str
    budget_aud: float


class ChatRequest(BaseModel):
    simulation_id: str
    question: str
    persona_id: str | None = None


@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "mode": "anthropic" if USE_ANTHROPIC else "openai" if USE_OPENAI else "mock",
        "model": ANTHROPIC_MODEL if USE_ANTHROPIC else OPENAI_MODEL if USE_OPENAI else "mock",
        "timestamp": datetime.now().isoformat()
    }


@app.post("/api/simulate")
async def simulate(brief: CampaignBrief):
    """
    Run a full audience simulation for the given campaign brief.
    Returns simulation_id + full results.
    """
    brief_dict = brief.model_dump()
    sim_id = f"sim_{int(datetime.now().timestamp() * 1000)}"

    try:
        # ── Step 1: Persona Generation ──────────────────────────────────────
        logger.info(f"[{sim_id}] Generating personas...")

        if not USE_MOCK:
            persona_prompt = f"""Generate exactly 10 diverse Australian consumer personas relevant to this campaign.

Campaign: {brief.brand_name} — "{brief.campaign_message}"
Target audience: {brief.target_audience}
Location: {brief.ooh_location}

Return a JSON array of exactly 10 personas. Each persona object must have these exact fields:
- id: string (p1 through p10)
- name: string (realistic Australian name)
- age: number
- occupation: string
- suburb: string (Sydney suburb)
- daily_commute: string (describe route and transport mode)
- lifestyle_traits: array of strings (4-6 traits)
- ad_skepticism: number 1-10 (10 = very skeptical)
- social_influence_score: number 1-10

Make them diverse: mix of ages, suburbs (inner city, suburbs, western Sydney), occupations, and demographics.
Return ONLY the JSON array, no other text."""

            try:
                raw = await llm_call(persona_prompt)
                personas = parse_json_response(raw)
                if len(personas) < 8:
                    raise ValueError(f"Only got {len(personas)} personas")
            except Exception as e:
                logger.warning(f"Persona generation failed ({e}), using mock")
                personas = MOCK_PERSONAS
        else:
            await asyncio.sleep(0.5)  # Simulate processing time
            personas = MOCK_PERSONAS

        # ── Step 2: Exposure Simulation ──────────────────────────────────────
        logger.info(f"[{sim_id}] Simulating exposures for {len(personas)} personas...")

        if not USE_MOCK:
            exposures = []
            for persona in personas:
                exposure_prompt = f"""Simulate {persona['name']}'s reaction to seeing this OOH ad.

Persona: {persona['name']}, {persona['age']}, {persona['occupation']} from {persona['suburb']}
Daily commute: {persona['daily_commute']}
Lifestyle: {', '.join(persona['lifestyle_traits'])}
Ad skepticism: {persona['ad_skepticism']}/10

OOH Location: {brief.ooh_location}
Campaign message: "{brief.campaign_message}"
Brand: {brief.brand_name}

Return a single JSON object with these exact fields:
- persona_id: "{persona['id']}"
- persona_name: "{persona['name']}"
- noticed: boolean (did they actually register the ad?)
- recall_strength: number 1-5 (1=barely, 5=strong)
- emotional_response: string ("positive", "neutral", or "negative")
- likely_action: string (what they'll do next, e.g. "search online", "ignore", "tell a friend")
- quote: string (a realistic first-person quote in their voice, in quotes)

Be realistic based on their skepticism level and lifestyle. Return ONLY the JSON object."""

                try:
                    raw = await llm_call(exposure_prompt)
                    exposure = parse_json_response(raw)
                    exposures.append(exposure)
                except Exception as e:
                    logger.warning(f"Exposure sim failed for {persona['name']}: {e}")
                    # Fallback for this persona
                    exposures.append({
                        "persona_id": persona["id"],
                        "persona_name": persona["name"],
                        "noticed": persona["ad_skepticism"] < 7,
                        "recall_strength": max(1, 4 - persona["ad_skepticism"] // 3),
                        "emotional_response": "neutral",
                        "likely_action": "passive awareness",
                        "quote": f"\"Just another ad in the city.\""
                    })
                await asyncio.sleep(0.1)  # Rate limiting courtesy
        else:
            await asyncio.sleep(1.0)
            exposures = generate_mock_exposures(personas, brief_dict)

        # ── Step 3: Social Cascade ────────────────────────────────────────────
        logger.info(f"[{sim_id}] Running social cascade simulation...")

        if not USE_MOCK:
            persona_summary = json.dumps([
                {"name": e["persona_name"], "noticed": e["noticed"],
                 "recall": e["recall_strength"], "response": e["emotional_response"],
                 "action": e["likely_action"]} for e in exposures
            ], indent=2)

            cascade_prompt = f"""Given these persona reactions to a {brief.brand_name} OOH campaign at {brief.ooh_location}:

{persona_summary}

Simulate 5-6 natural social interactions where ad awareness spreads between personas.
These should be realistic: some might post on Instagram, text a friend, mention it in conversation.

Return a JSON array of interaction objects, each with:
- from_persona: string (name of person sharing)
- to_persona: string (name of recipient)
- channel: string ("conversation", "instagram", or "whatsapp")
- message: string (realistic message content, in Australian English)
- influence_delta: number 0.1-0.5 (how much this shifts the recipient's awareness)

Only include interactions where the sharer actually noticed/recalled the ad.
Return ONLY the JSON array."""

            try:
                raw = await llm_call(cascade_prompt)
                cascade = parse_json_response(raw)
            except Exception as e:
                logger.warning(f"Social cascade failed ({e}), using mock")
                cascade = generate_mock_social_cascade(personas, exposures, brief_dict)
        else:
            await asyncio.sleep(0.8)
            cascade = generate_mock_social_cascade(personas, exposures, brief_dict)

        # ── Step 4: Report Generation ─────────────────────────────────────────
        logger.info(f"[{sim_id}] Generating prediction report...")

        # Compute stats for report context
        noticed_count = sum(1 for e in exposures if e.get("noticed"))
        high_recall_count = sum(1 for e in exposures if e.get("recall_strength", 0) >= 3)
        positive_count = sum(1 for e in exposures if e.get("emotional_response") == "positive")
        recall_pct = round((noticed_count / len(exposures)) * 100)
        intent_pct = round((positive_count / len(exposures)) * 100)
        reach_est = int(brief.budget_aud * 12.5)
        roas_pred = round(2.1 + (intent_pct / 100) * 1.8, 2)

        if not USE_MOCK:
            report_prompt = f"""Generate a comprehensive DOOH campaign prediction report for Lumos.

Campaign Brief:
- Brand: {brief.brand_name}
- Message: "{brief.campaign_message}"
- Target audience: {brief.target_audience}
- Location: {brief.ooh_location}
- Duration: {brief.campaign_duration}
- Budget: ${brief.budget_aud:,.0f} AUD

Simulation Results Summary:
- {len(personas)} personas simulated
- {noticed_count}/{len(personas)} ({recall_pct}%) noticed the ad
- {high_recall_count}/{len(personas)} showed strong recall (3+/5)
- {positive_count}/{len(personas)} had positive emotional response
- {len(cascade)} social interactions triggered
- Estimated reach: {reach_est:,}

Write a professional, data-driven report in Markdown. Include:
1. **Executive Summary** (2-3 paragraphs)
2. **Audience Reach Analysis** (with numbers and benchmarks)
3. **Brand Recall Forecast** (table format with AU DOOH benchmarks)
4. **Purchase Intent by Segment** (breakdown by persona type)
5. **Social Amplification Estimate** (organic reach multiplier)
6. **Budget Efficiency Score** (CPM, cost per recall, efficiency rating)
7. **ROAS Prediction** (justify with Australian DOOH data — industry avg 1.8–2.3x)
8. **Recommendations** (5 actionable items)

Use Australian English. Be specific with numbers. Reference Australian DOOH industry benchmarks where relevant.
Include a note that this was generated by the Lumos Audience Intelligence Engine."""

            try:
                report = await llm_call(report_prompt, expect_json=False)
            except Exception as e:
                logger.warning(f"Report generation failed ({e}), using mock")
                report = generate_mock_report(brief_dict, personas, exposures, cascade)
        else:
            await asyncio.sleep(1.2)
            report = generate_mock_report(brief_dict, personas, exposures, cascade)

        # ── Store & Return ────────────────────────────────────────────────────
        result = {
            "simulation_id": sim_id,
            "brief": brief_dict,
            "mode": "anthropic" if USE_ANTHROPIC else "openai" if USE_OPENAI else "mock",
            "personas": personas,
            "exposures": exposures,
            "social_cascade": cascade,
            "report": report,
            "stats": {
                "recall_pct": recall_pct,
                "intent_pct": intent_pct,
                "reach_estimate": reach_est,
                "roas_prediction": roas_pred,
                "personas_count": len(personas),
                "noticed_count": noticed_count,
                "social_interactions": len(cascade)
            },
            "timestamp": datetime.now().isoformat()
        }
        simulations[sim_id] = result
        logger.info(f"[{sim_id}] Simulation complete.")
        return result

    except Exception as e:
        logger.error(f"[{sim_id}] Simulation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/chat")
async def chat(req: ChatRequest):
    """Chat with the simulated world — ask any persona a question."""
    sim = simulations.get(req.simulation_id)
    if not sim:
        raise HTTPException(status_code=404, detail="Simulation not found. Run /api/simulate first.")

    # Build context
    personas = sim["personas"]
    exposures = sim["exposures"]
    brief = sim["brief"]

    if req.persona_id:
        persona = next((p for p in personas if p["id"] == req.persona_id), None)
        exposure = next((e for e in exposures if e.get("persona_id") == req.persona_id), None)
        if not persona:
            raise HTTPException(status_code=404, detail=f"Persona {req.persona_id} not found")

        context = f"""You are {persona['name']}, {persona['age']}, {persona['occupation']} from {persona['suburb']}.
Your commute: {persona['daily_commute']}
Your lifestyle: {', '.join(persona['lifestyle_traits'])}
Your ad skepticism: {persona['ad_skepticism']}/10

You recently {'saw' if exposure and exposure.get('noticed') else 'may have missed'} the {brief['brand_name']} campaign at {brief['ooh_location']}.
{"Your reaction: " + exposure.get('emotional_response', '') + ". " + exposure.get('quote', '') if exposure else ''}

Answer the following question in character, in first person, as this Australian consumer would naturally speak."""

        question = req.question

    else:
        # General simulation question
        stats = sim["stats"]
        context = f"""You are the Lumos Audience Intelligence Engine.

Campaign simulated: {brief['brand_name']} — "{brief['campaign_message']}"
Location: {brief['ooh_location']} | Duration: {brief['campaign_duration']} | Budget: ${brief['budget_aud']:,.0f} AUD

Simulation results:
- {stats['personas_count']} personas | {stats['recall_pct']}% recall | {stats['intent_pct']}% purchase intent
- Reach estimate: {stats['reach_estimate']:,} | Predicted ROAS: {stats['roas_prediction']}x
- {stats['social_interactions']} social cascade interactions

Answer as a data-driven DOOH intelligence system, referencing the simulation results."""

        question = req.question

    if not USE_MOCK:
        try:
            prompt = f"{context}\n\nQuestion: {question}"
            answer = await llm_call(prompt, expect_json=False)
        except Exception as e:
            logger.warning(f"Chat LLM call failed: {e}")
            answer = _mock_chat_response(req, sim)
    else:
        answer = _mock_chat_response(req, sim)

    return {
        "simulation_id": req.simulation_id,
        "persona_id": req.persona_id,
        "question": req.question,
        "answer": answer
    }


def _mock_chat_response(req: ChatRequest, sim: dict) -> str:
    """Generate a mock chat response."""
    brief = sim["brief"]
    personas = sim["personas"]
    exposures = sim["exposures"]

    if req.persona_id:
        persona = next((p for p in personas if p["id"] == req.persona_id), None)
        exposure = next((e for e in exposures if e.get("persona_id") == req.persona_id), None)
        if persona and exposure:
            return (f"As {persona['name']}, to be honest — {exposure.get('quote', '\"I noticed the ad.\"').strip('\"')}. "
                    f"In terms of {req.question.lower()}, I'd say my {exposure['emotional_response']} reaction "
                    f"to the {brief['brand_name']} campaign reflects how most people like me in {persona['suburb']} feel. "
                    f"We're busy, but good creative cuts through. This one {'did' if exposure['noticed'] else 'barely'} catch my eye.")

    stats = sim["stats"]
    return (f"Based on the simulation data for {brief['brand_name']}: "
            f"With {stats['recall_pct']}% recall rate and {stats['intent_pct']}% purchase intent, "
            f"this campaign is {'outperforming' if stats['recall_pct'] > 70 else 'tracking at'} "
            f"Australian DOOH benchmarks. The {stats['roas_prediction']}x ROAS prediction is "
            f"{'above' if stats['roas_prediction'] > 2.3 else 'within'} the industry average of 1.8–2.3x. "
            f"Regarding '{req.question}' — the simulation suggests strong performance in urban professional segments.")


@app.get("/")
async def serve_frontend():
    frontend_path = os.path.join(os.path.dirname(__file__), "index.html")
    return FileResponse(frontend_path)
