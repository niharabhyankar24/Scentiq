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
        max_tokens=1000,
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