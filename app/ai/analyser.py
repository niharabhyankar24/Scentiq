"""
Core AI analysis engine. Fetches community content,
calls Claude API, parses and stores structured insights.
"""

import os
import json
from anthropic import Anthropic
from sqlalchemy.orm import Session
from dotenv import load_dotenv
from datetime import datetime

from app.models.fragrance import Fragrance
from app.models.note import FragranceNote, PyramidPosition, NoteSource
from app.models.ai_insights import AIInsights
from app.ai.reddit_fetcher import (
    fetch_reddit_content,
    format_reddit_for_prompt
)
from app.ai.youtube_fetcher import (
    fetch_youtube_comments,
    format_youtube_for_prompt
)

load_dotenv()

SYSTEM_PROMPT = """
You are a fragrance analysis engine. Your job is to analyse
community discussions about a specific perfume and extract
structured insights about how real people actually perceive it.

You will receive:
- The fragrance name, brand, and concentration
- Its official note pyramid for reference
- A set of Reddit posts and YouTube comments, each tagged
  with engagement signals (upvotes, likes, comment count)

Your rules:
- Weight content by engagement. High engagement content
  carries more weight than low engagement content.
- Use plain English a fragrance beginner can understand.
  Never use marketing language or brand copy.
- Only extract what the data actually supports. If a field
  is not discussed in the source material, return null.
- Never hallucinate notes or characteristics not present
  in the source material.
For the character_full field:
- Write in the voice of an experienced fragrance enthusiast,
  not a marketing copywriter.
- Aim for 3 to 5 sentences of sensory, evocative language.
- Describe how the fragrance evolves on skin, what it evokes,
  what it reminds people of.
- Weave performance in naturally through the description
  rather than as separate tags. "Opens with...", "settles into...",
  "lingers as..." are stronger than "long-lasting" as a label.
- Never use brand marketing phrases. No "sophisticated,"
  "captivating," "unforgettable," "signature scent."
- Ground every claim in the source material. If the community
  is divided or the data is thin, acknowledge it directly.
- Prefer specific sensory references over abstract adjectives.
  "Reminds people of an old library" beats "sophisticated."
- For community_also_mentions: only include fragrances
  explicitly named in the source material as similar,
  alternative, or frequently compared. Never suggest
  fragrances yourself.
  For community_also_mentions: only include fragrances where 
  the source text explicitly uses language like "similar to", 
  "smells like", "alternative to", "dupe for", "reminds me of",
  "compares to", or "instead of". Fragrances merely mentioned 
  in the same post without a direct comparison phrase must 
  be excluded.
- confidence_score reflects source material quality.
  0.0 to 0.4 = thin data. 0.5 to 0.7 = reasonable data.
  0.8 to 1.0 = rich data with high engagement.
- Return ONLY a valid JSON object. No preamble, no
  explanation, no markdown fences. Raw JSON only.

Prominence definitions:
- dominant: mentioned constantly, defines the fragrance
- prominent: frequently mentioned, important character
- supporting: mentioned in detailed reviews as background

Scales:
- Projection: light / moderate / strong / nuclear
- Sillage: light / moderate / heavy
- Longevity: poor / average / long-lasting / legendary
- Price perception: budget / mid-range / premium / luxury
- Value for money: poor / fair / good / exceptional
- Sentiment: positive / mixed / polarised / negative

CONTEXT SCORES:
You must also assign ten context scores, each a float from
0.0 to 1.0, judging the fragrance's suitability for various
settings. Score from the COMMUNITY CONSENSUS in the source
material, not from your own taste. If the community is
divided on an axis, score toward the middle (that division
is itself the honest answer) and let confidence_score
reflect the uncertainty. If the source material genuinely
does not support a judgment on an axis, still give your best
estimate from the notes and performance, but keep
confidence_score low.

Nine axes are UNIPOLAR: 0.0 = not at all suitable, 1.0 =
perfectly suitable. One axis (day_night) is BIPOLAR.

- day_night (BIPOLAR): 0.0 = strictly a daytime scent,
  1.0 = strictly a nighttime scent, 0.5 = works either.
  Bright / fresh / sharp / citrusy leans day. Rich / dark /
  sweet / boozy / heavy leans night.

- office_safe: suitability for a shared enclosed workplace
  over a full day. Rewards restraint: low projection,
  inoffensive non-polarising notes, does not impose on
  people nearby. Loud, heavy, or divisive scents score low.

- date_safe: suitability for close, intimate settings —
  something with an alluring, mysterious edge that draws a
  person in. Rewards warmth that is NOT aggressively or
  hot-spicy (sharp spice is off-putting up close): boozy
  notes, controlled/soft spice, and sweetness WITH DEPTH
  rather than flat sugar. Penalised at BOTH extremes: too
  loud/screechy/harsh up close, OR too clean/sterile/
  functional to be alluring. A plain fresh "shower-clean"
  scent scores LOW here by default — inoffensive is not
  the same as seductive.

- daily_wear_safe: how wearable without thought, casually,
  frequently, including weekends. Rewards versatility and
  inoffensiveness. Loud, formal, or highly distinctive
  scents that draw attention score low. (Distinct from
  office_safe: a loud but casual scent can be high here
  yet low on office_safe.)

- gym_safe: suitability for working out — fresh, clean,
  inoffensive when heated by sweat, not precious. Rewards
  sporty freshness. Heavy, powdery, sweet, or "too nice to
  blast at the gym" scents score low.

- formal_occasion: suitability for formal / statement events
  (weddings, galas, special evenings) where presence is
  expected and appropriate. Rewards opulence, refinement,
  gravitas. Casual / sporty / fresh scents score low; here
  being noticed is the point, so restraint is less rewarded.

- season_summer: performance in heat. Fresh / citrus /
  aquatic / light scores high; heavy / sweet / ambery /
  cloying-in-heat scores low.

- season_winter: performance in cold. Warm / rich / sweet /
  spicy / ambery that projects through cold air scores high;
  light / fresh / thin that vanishes in cold scores low.

- season_fall: suitability for crisp cooler transitional
  weather. Woody / spicy / warm-but-not-suffocating / earthy
  scores high. Seasons may overlap — a scent can score high
  on both fall and winter, or both spring and summer.

- season_spring: suitability for mild fresh transitional
  weather. Green / floral / airy / fresh-but-slightly-warmer
  -than-peak-summer scores high. Heavy winter scents and
  blazing-summer sport scents score lower.

"""

USER_PROMPT_TEMPLATE = """
Analyse this fragrance based on the community discussions below.

Fragrance: {brand} {name} {concentration}

Official notes for reference:
Top: {top_notes}
Heart: {heart_notes}
Base: {base_notes}

Community discussions:

{community_content}

Return a JSON object with exactly this structure:
{{
  "perceived_notes": [
    {{
      "note": "string",
      "prominence": "dominant|prominent|supporting"
    }}
  ],
  "character_snapshot": "string, max 200 characters,\
 plain English, no marketing language",
 "character_full": "string, 3-5 sentences, sensory language, no marketing",
  "occasions": ["string"],
  "performance": {{
    "projection": "light|moderate|strong|beast-mode",
    "sillage": "light|moderate|heavy",
    "longevity": "poor|average|long-lasting|nuclear"
  }},
  "value_perception": {{
    "price_perception": "budget|mid-range|premium|luxury",
    "value_for_money": "poor|fair|good|exceptional",
    "community_note": "one plain English sentence"
  }},
  "sentiment": "positive|mixed|polarised|negative",
  "polarising_elements": [
    "specific elements people strongly love or hate"
  ],
  "community_also_mentions": [
    "fragrances explicitly named in source as similar\
 or alternative"
  ],
  "context_scores": {{
    "day_night": 0.0,
    "office_safe": 0.0,
    "date_safe": 0.0,
    "daily_wear_safe": 0.0,
    "gym_safe": 0.0,
    "formal_occasion": 0.0,
    "season_summer": 0.0,
    "season_fall": 0.0,
    "season_winter": 0.0,
    "season_spring": 0.0
  }},
  "confidence_score": 0.0
}}
"""


def get_fragrance_notes_by_position(
    db: Session,
    fragrance_id: int,
    position: PyramidPosition
) -> str:
    """
    Return a comma separated string of official note names
    for a given fragrance and pyramid position.
    """
    links = db.query(FragranceNote).filter(
        FragranceNote.fragrance_id == fragrance_id,
        FragranceNote.pyramid_position == position,
        FragranceNote.source == NoteSource.official
    ).all()
    if not links:
        return "not listed"
    return ", ".join([link.note.name for link in links])


def build_user_prompt(
    fragrance: Fragrance,
    community_content: str,
    db: Session
) -> str:
    """
    Assemble the user prompt with fragrance data and
    community content.
    """
    top = get_fragrance_notes_by_position(
        db, fragrance.id, PyramidPosition.top
    )
    heart = get_fragrance_notes_by_position(
        db, fragrance.id, PyramidPosition.heart
    )
    base = get_fragrance_notes_by_position(
        db, fragrance.id, PyramidPosition.base
    )
    return USER_PROMPT_TEMPLATE.format(
        brand=fragrance.brand,
        name=fragrance.name,
        concentration=fragrance.concentration,
        top_notes=top,
        heart_notes=heart,
        base_notes=base,
        community_content=community_content
    )


def call_claude(user_prompt: str) -> dict:
    """
    Call the Claude API and return parsed JSON response.
    Raises ValueError if response cannot be parsed.
    """
    client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    response = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=1500,
        system=SYSTEM_PROMPT,
        messages=[
            {"role": "user", "content": user_prompt}
        ]
    )
    raw = response.content[0].text.strip()
    clean = raw.replace("```json", "").replace("```", "").strip()
    try:
        return json.loads(clean)
    except json.JSONDecodeError as e:
        raise ValueError(f"Claude returned invalid JSON: {e}\n{raw}")


# The ten context-score columns, kept in one place so the
# parser and any future validation iterate the same list.
CONTEXT_SCORE_KEYS = [
    "day_night",
    "office_safe",
    "date_safe",
    "daily_wear_safe",
    "gym_safe",
    "formal_occasion",
    "season_summer",
    "season_fall",
    "season_winter",
    "season_spring",
]


def _clean_score(value) -> float | None:
    """
    Coerce one context score to a float in [0, 1].
    Returns None if the value is missing or unusable, so a
    malformed score becomes 'not scored' (NULL) rather than
    a wrong number. NULL and 0.0 mean different things
    downstream, so we never silently substitute 0.0.
    """
    if value is None:
        return None
    try:
        f = float(value)
    except (TypeError, ValueError):
        return None
    if f < 0.0:
        return 0.0
    if f > 1.0:
        return 1.0
    return f


def _apply_context_scores(record: AIInsights, insights: dict) -> None:
    """
    Write the ten context scores from the insights payload
    onto the record. Missing or malformed scores are left as
    None (not scored) rather than defaulted to 0.0.
    """
    scores = insights.get("context_scores") or {}
    for key in CONTEXT_SCORE_KEYS:
        setattr(record, key, _clean_score(scores.get(key)))


def store_insights(
    db: Session,
    fragrance_id: int,
    insights: dict,
    sources_used: list[str]
) -> None:
    """
    Store or update AI insights for a fragrance in the database.
    """
    existing = db.query(AIInsights).filter(
        AIInsights.fragrance_id == fragrance_id
    ).first()

    perceived_summary = ", ".join([
        f"{n['note']} ({n['prominence']})"
        for n in insights.get("perceived_notes", [])
    ])

    if existing:
        existing.perceived_summary = perceived_summary
        existing.snapshot_draft = insights.get(
            "character_snapshot", []
        )
        existing.sentiment = insights.get("sentiment")
        existing.confidence_score = insights.get(
            "confidence_score", 0.0
        )
        existing.full_insights = json.dumps(insights)
        existing.sources_used = json.dumps(sources_used)
        existing.last_updated = datetime.utcnow()
        existing.character_full = insights.get("character_full")
        _apply_context_scores(existing, insights)

    else:
        record = AIInsights(
            fragrance_id=fragrance_id,
            perceived_summary=perceived_summary,
            snapshot_draft=insights.get("character_snapshot"),
            sentiment=insights.get("sentiment"),
            confidence_score=insights.get("confidence_score", 0.0),
            full_insights=json.dumps(insights),
            sources_used=json.dumps(sources_used),
            last_updated=datetime.utcnow(),
            character_full=insights.get("character_full"),
        )
        _apply_context_scores(record, insights)
        db.add(record)

    db.commit()


def analyse_fragrance(
    fragrance_id: int,
    db: Session
) -> dict:
    """
    Full pipeline: fetch community content, call Claude,
    store and return structured insights.
    """
    fragrance = db.query(Fragrance).filter(
        Fragrance.id == fragrance_id
    ).first()
    if not fragrance:
        raise ValueError(f"Fragrance {fragrance_id} not found.")

    print(f"Fetching Reddit content for "
          f"{fragrance.brand} {fragrance.name}...")
    reddit_content = fetch_reddit_content(
        fragrance.name, fragrance.brand
    )
    reddit_text = format_reddit_for_prompt(reddit_content)

    print(f"Fetching YouTube comments for "
          f"{fragrance.brand} {fragrance.name}...")
    youtube_content = fetch_youtube_comments(
        fragrance.name, fragrance.brand
    )
    youtube_text = format_youtube_for_prompt(youtube_content)

    community_content = "\n\n".join(filter(None, [
        reddit_text, youtube_text
    ]))

    if not community_content.strip():
        raise ValueError(
            "No community content found for this fragrance."
        )

    sources_used = (
        [item["url"] for item in reddit_content
         if "url" in item] +
        [f"youtube:{item['video_id']}"
         for item in youtube_content]
    )

    print("Calling Claude API...")
    user_prompt = build_user_prompt(fragrance, community_content, db)
    insights = call_claude(user_prompt)

    print("Storing insights...")
    store_insights(db, fragrance_id, insights, sources_used)

    print(f"Analysis complete for "
          f"{fragrance.brand} {fragrance.name}.")
    return insights