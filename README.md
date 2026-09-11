# Scentiq

**Discover fragrances honestly — real community insights, not marketing copy.**

Scentiq is an AI-powered fragrance discovery platform. Instead of repeating brand
copy, it reads what real people say about a fragrance across the web, distills it
into an honest picture — how it actually smells, how it performs, where it fits —
and learns your taste over time, with your explicit consent, to give the kind of
advice a knowledgeable friend would.

**Live:** [scentiq-chi.vercel.app](https://scentiq-chi.vercel.app)

<!-- Screenshot goes here — a shot of the homepage or the Signature page is the
     single highest-value addition to this README if added later. -->

---

## What it does

- **Honest fragrance profiles.** For each fragrance, Scentiq aggregates community
  discussion (Reddit, YouTube) and uses an LLM to extract a plain-English picture:
  perceived notes, character, performance, sentiment, and how divided opinion is —
  including when the community genuinely disagrees, rather than papering over it.

- **Occasion-aware search.** Fragrance suitability for a setting ("office friendly",
  "for date nights", "cold weather") is a *judgment*, not something text-similarity
  can infer. Scentiq scores every fragrance on ten continuous axes — day/night,
  office, date, gym, formal, daily wear, and the four seasons — and ranks by those
  real judgments. A quiet office scent no longer gets buried under a famous
  projection monster just because the monster is discussed more.

- **A signature that learns you.** With your explicit, per-axis consent, Scentiq
  builds a private "signature" — a set of AI-written observations about your taste,
  derived from your collection, wishlist, and searches. You can delete any
  observation, and revoking consent genuinely deletes the derived data.

- **Consent as a first principle.** Everything personal is off by default. Turning
  a data source off doesn't just hide it — it purges what was derived from it.
  "Off means gone" is enforced in code, not just promised in a policy.

---

## Why it's built this way

A few design decisions define the project. They're the interesting part.

**Consent is three independent axes, not one switch.** A user can let Scentiq learn
from their collection but not their searches, or any combination. Each axis is
independently revocable, and revoking one purges only that axis's derived data. This
makes personalization a series of specific, reversible choices rather than a single
all-or-nothing bargain.

**Occasion suitability is scored, not inferred.** Early versions relied on semantic
(embedding) search for occasion queries — and it failed, because "office safe" is a
judgment the embeddings don't encode, so loud, heavily-discussed fragrances
dominated every query. The fix was to have the analysis pipeline assign explicit
0–1 scores per occasion axis, from community consensus, and rank on those. Scores,
not booleans, because "how office-safe" is a gradient, not a yes/no.

**Memory is generated lazily and cached by fingerprint.** The per-user signature is
regenerated only when the underlying data has *materially* changed — detected by
hashing the meaningful inputs (owned fragrances and ratings, not incidental fields).
Idle page views cost nothing; the LLM is called only when there's genuinely
something new to say. This keeps a personalization feature that could be expensive
essentially free at rest.

**Every LLM call goes through one hardened client.** A single wrapper handles the
Anthropic API with structured error handling — categorized failures, consistent
logging, and graceful degradation. If the model is unavailable, features fall back
to their last-known state and report an honest status rather than crashing or
showing an error.

For a deeper walkthrough of the architecture, see
[`ARCHITECTURE.md`](ARCHITECTURE.md) *(coming soon)*.

---

## Tech stack

**Backend** — Python, FastAPI, SQLAlchemy, PostgreSQL (with `pgvector` for
embeddings), Celery + Redis for background analysis jobs, and the Anthropic API for
LLM analysis. Local sentence-transformer embeddings power semantic search.

**Frontend** — Next.js (App Router) and Tailwind CSS.

**Infrastructure** — backend and worker on Railway, frontend on Vercel.

The interactive API reference is auto-generated and available at
`/docs` on the backend (FastAPI / OpenAPI).

---

## Project layout

```
app/
  ai/         # analysis pipeline, LLM client, embeddings, memory engine
  models/     # SQLAlchemy models
  routes/     # FastAPI routers (auth, search, collection, consent, memory, admin...)
  schemas/    # Pydantic request/response schemas
  utils/      # auth, security, JWT, shared dependencies
  tasks.py    # Celery tasks (background fragrance analysis)
  worker.py   # Celery app configuration
  main.py     # FastAPI app entry point
```

---

## Status

Scentiq is an actively developed project. The core platform — honest community
analysis, occasion-aware search, and consent-gated personalization — is complete and
live. Current focus is on expanding the fragrance catalogue toward broader,
more affordable coverage, where the honest-advice model is most useful.

It's a real, working product and an evolving one; some directions are still being
figured out. That's deliberate.

---

## License

This project is not currently licensed for reuse. The code is public to be read and
learned from, but is not offered under an open-source license at this time.