"use client"

// Blind-buy risk card.
//
// The honest-friend signal: how safe is this to buy *unsniffed*?
//
// Verdict logic, in priority order — divisiveness EVIDENCE beats an
// optimistic label. The polarising_elements array is the strongest
// signal: if the community lists specific things it fights about,
// the fragrance is divisive no matter what the one-word sentiment
// says. "Safe blind buy" is deliberately HARD to earn, because the
// cost of a wrong "safe" (someone blind-buys a divisive scent and
// hates it) is exactly the harm this feature exists to prevent.
//
//   confidence < MIN            -> unknown (never let thin data read as safe)
//   2+ polarising elements      -> high risk (overrides any sentiment)
//   sentiment "polarised"       -> high risk
//   1 polarising element        -> some risk
//   sentiment "mixed"/"negative"-> some risk
//   sentiment "positive" + no
//     polarising elements + conf -> safe blind buy
//   anything else               -> unknown (fail safe, never "safe")

const MIN_CONFIDENCE = 0.4

function computeVerdict(sentiment, polarising, confidence) {
  const conf = typeof confidence === "number" ? confidence : 0
  const s = (sentiment || "").trim().toLowerCase()
  const elements = Array.isArray(polarising) ? polarising.filter(Boolean) : []
  const count = elements.length

  // Not enough evidence — honest unknown. Absence is NOT safety.
  if (conf < MIN_CONFIDENCE) {
    return { level: "unknown" }
  }

  // Divisiveness evidence takes precedence over the sentiment label.
  if (count >= 2) return { level: "high" }
  if (s === "polarised") return { level: "high" }

  if (count === 1) return { level: "some" }
  if (s === "mixed" || s === "negative") return { level: "some" }

  // Safe must be affirmatively earned: positive AND nothing the
  // community fights about AND real confidence behind it.
  if (s === "positive" && count === 0) return { level: "safe" }

  // Anything we can't confidently place is unknown, never safe.
  return { level: "unknown" }
}

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

  const named = (Array.isArray(polarisingElements) ? polarisingElements : [])
    .filter(Boolean)
    .slice(0, 2)

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
                <span className="text-gray-900 dark:text-gray-100">{el}</span>
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