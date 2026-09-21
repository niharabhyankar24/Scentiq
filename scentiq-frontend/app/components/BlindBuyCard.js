"use client"

// Blind-buy risk card.
//
// The honest-friend signal: how safe is this to buy *unsniffed*?
// Driven entirely by data the detail page already holds —
//   sentiment            ("positive" | "mixed" | "polarised" | "negative")
//   polarising_elements  (the specific things people split on)
//   confidence_score     (how much community data backed the verdict)
//
// Confidence gates the verdict: a "polarised" call on thin data isn't
// "high risk", it's "unknown" — we never fake certainty either way,
// and we never let absence-of-data read as safety.
//
// Objective-only for now; a personalized line (taste axes) can be
// layered in later without changing this contract.

const MIN_CONFIDENCE = 0.4 // below this, we don't trust the verdict

function computeVerdict(sentiment, polarising, confidence) {
  const conf = typeof confidence === "number" ? confidence : 0
  const s = (sentiment || "").toLowerCase()

  // Not enough evidence to judge divisiveness — honest unknown.
  // Absence of data is NOT safety.
  if (conf < MIN_CONFIDENCE || !s) {
    return { level: "unknown" }
  }

  if (s === "polarised") {
    return { level: "high" }
  }
  if (s === "mixed" || s === "negative") {
    return { level: "some" }
  }
  // positive, with real confidence behind it
  return { level: "safe" }
}

// Visual + copy config per verdict. Colors mirror the rating
// control (terracotta / gold / sage) for a consistent language.
const STYLES = {
  high: {
    dot: "#a85a4a",
    border: "rgba(168,90,74,0.4)",
    bg: "rgba(168,90,74,0.07)",
    label: "High blind-buy risk",
    labelColor: "#c47a68",
    action: "Sample before you commit.",
  },
  some: {
    dot: "#c9a254",
    border: "rgba(201,162,84,0.4)",
    bg: "rgba(201,162,84,0.07)",
    label: "Some blind-buy risk",
    labelColor: "#c9a254",
    action: "A sample is the safer bet.",
  },
  safe: {
    dot: "#6f9463",
    border: "rgba(111,148,99,0.4)",
    bg: "rgba(111,148,99,0.07)",
    label: "Safe blind buy",
    labelColor: "#8fae84",
    action: "Low risk if the notes appeal to you.",
  },
  unknown: {
    dot: "#6b6a66",
    border: "rgba(255,255,255,0.10)",
    bg: "rgba(255,255,255,0.02)",
    label: "Not enough data yet",
    labelColor: "#9a9892",
    action: null,
  },
}

export default function BlindBuyCard({
  sentiment,
  polarisingElements = [],
  confidenceScore,
}) {
  const { level } = computeVerdict(
    sentiment,
    polarisingElements,
    confidenceScore
  )
  const style = STYLES[level]

  // Body copy per level. For high/some risk we name the specific
  // polarising elements (up to two) — that's what makes it read
  // like a knowledgeable friend rather than a generic label.
  const named = (polarisingElements || []).slice(0, 2)
  let body
  if (level === "high" || level === "some") {
    body = (
      <>
        The community is genuinely split on this
        {named.length > 0 ? (
          <>
            {" "}— chiefly its{" "}
            {named.map((el, i) => (
              <span key={i}>
                <span className="text-gray-900 dark:text-gray-100">
                  {el}
                </span>
                {i < named.length - 1 ? " and " : ""}
              </span>
            ))}
            .
          </>
        ) : (
          "."
        )}{" "}
        Loved by many, off-putting to others.
      </>
    )
  } else if (level === "safe") {
    body =
      "Broadly well-liked, with little disagreement. A dependable, crowd-pleasing profile."
  } else {
    body =
      "Too few community sources to judge how divisive this is. Treat it as unknown, not a safe blind buy."
  }

  return (
    <div
      className="rounded-xl p-4 sm:p-5 mb-10"
      style={{ border: `0.5px solid ${style.border}`, background: style.bg }}
    >
      <div className="flex items-center gap-2.5 mb-2">
        <span
          className="w-2.5 h-2.5 rounded-full flex-shrink-0"
          style={{ background: style.dot }}
        />
        <span
          className="text-xs tracking-widest uppercase font-medium"
          style={{ color: style.labelColor }}
        >
          {style.label}
        </span>
      </div>

      <p className="text-sm leading-relaxed text-gray-700 dark:text-gray-300">
        {body}
      </p>

      {style.action && (
        <p className="text-[13px] mt-2.5" style={{ color: "#c9a254" }}>
          → {style.action}
        </p>
      )}
    </div>
  )
}
