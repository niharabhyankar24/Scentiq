"use client"

import { useState, useEffect } from "react"
import { useParams, useRouter } from "next/navigation"
import Link from "next/link"

export default function FragranceDetail() {
  const { id } = useParams()
  const router = useRouter()

  const [fragrance, setFragrance] = useState(null)
  const [comparison, setComparison] = useState(null)
  const [insights, setInsights] = useState(null)
  const [prices, setPrices] = useState([])
  const [decants, setDecants] = useState([])
  const [similar, setSimilar] = useState([])
  const [redundancy, setRedundancy] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [analysing, setAnalysing] = useState(false)
  const [jobId, setJobId] = useState(null)
  const [jobStatus, setJobStatus] = useState(null)
  const [inCollection, setInCollection] = useState(false)
  const [inWishlist, setInWishlist] = useState(false)
  const [addingCollection, setAddingCollection] = useState(false)
  const [addingWishlist, setAddingWishlist] = useState(false)

  useEffect(() => {
    if (id) loadAll()
  }, [id])

  useEffect(() => {
    if (!jobId) return
    const interval = setInterval(async () => {
      try {
        const res = await fetch(`/api/analysis/status/${jobId}`)
        const data = await res.json()
        setJobStatus(data.status)
        if (data.status === "complete") {
          clearInterval(interval)
          setJobId(null)
          setAnalysing(false)
          loadInsights()
        }
        if (data.status === "failed") {
          clearInterval(interval)
          setJobId(null)
          setAnalysing(false)
        }
      } catch {
        clearInterval(interval)
        setAnalysing(false)
      }
    }, 3000)
    return () => clearInterval(interval)
  }, [jobId])

  async function loadAll() {
    setLoading(true)
    setError(null)
    try {
      const [
        fragranceRes,
        comparisonRes,
        pricesRes,
        decantsRes,
        similarRes
      ] = await Promise.all([
        fetch(`/api/fragrances/${id}`),
        fetch(`/api/fragrances/${id}/compare`),
        fetch(`/api/fragrances/${id}/best-price`),
        fetch(`/api/fragrances/${id}/decants`),
        fetch(`/api/fragrances/${id}/similar`)
      ])

      if (fragranceRes.ok) {
        setFragrance(await fragranceRes.json())
      } else {
        setError("Fragrance not found.")
        return
      }

      if (comparisonRes.ok) setComparison(await comparisonRes.json())
      if (pricesRes.ok) setPrices(await pricesRes.json())
      if (decantsRes.ok) setDecants(await decantsRes.json())
      if (similarRes.ok) setSimilar(await similarRes.json())

      await loadInsights()

    } catch (err) {
      setError("Something went wrong loading this fragrance.")
    } finally {
      setLoading(false)
    }
  }

  async function loadInsights() {
    try {
      const token = localStorage.getItem("token")
      const insightsRes = await fetch(`/api/fragrances/${id}/insights`)
      if (insightsRes.ok) {
        setInsights(await insightsRes.json())
      }
      if (token) {
        const collectionRes = await fetch("/api/me/collection", {
          headers: { Authorization: `Bearer ${token}` }
        })
        if (collectionRes.ok) {
          const collection = await collectionRes.json()
          setInCollection(
            collection.some(item => item.fragrance_id === parseInt(id))
          )
        }

        const wishlistRes = await fetch("/api/me/wishlist", {
          headers: { Authorization: `Bearer ${token}` }
        })
        if (wishlistRes.ok) {
          const wishlist = await wishlistRes.json()
          setInWishlist(
            wishlist.some(item => item.fragrance_id === parseInt(id))
          )
        }

        const redundancyRes = await fetch(
          `/api/fragrances/${id}/redundancy-check`,
          { headers: { Authorization: `Bearer ${token}` } }
        )
        if (redundancyRes.ok) {
          setRedundancy(await redundancyRes.json())
        }
      }
    } catch {}
  }

  async function addToCollection() {
    const token = localStorage.getItem("token")
    if (!token) {
      router.push("/login")
      return
    }
    setAddingCollection(true)
    try {
      const res = await fetch("/api/me/collection", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({ fragrance_id: parseInt(id) })
      })
      if (res.ok) setInCollection(true)
      else if (res.status === 400) setInCollection(true)
    } catch {}
    finally { setAddingCollection(false) }
  }

  async function addToWishlist() {
    const token = localStorage.getItem("token")
    if (!token) {
      router.push("/login")
      return
    }
    setAddingWishlist(true)
    try {
      const res = await fetch("/api/me/wishlist", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({ fragrance_id: parseInt(id) })
      })
      if (res.ok) setInWishlist(true)
      else if (res.status === 400) setInWishlist(true)
    } catch {}
    finally { setAddingWishlist(false) }
  }

  async function triggerAnalysis() {
    const token = localStorage.getItem("token")
    if (!token) {
      alert("Please login to trigger analysis.")
      return
    }
    setAnalysing(true)
    setJobStatus("starting")
    try {
      const res = await fetch(
        `/api/fragrances/${id}/analyse`,
        {
          method: "POST",
          headers: { Authorization: `Bearer ${token}` }
        }
      )
      if (res.ok) {
        const data = await res.json()
        setJobId(data.job_id)
      }
    } catch {
      setAnalysing(false)
    }
  }

  function performanceWidth(value) {
    const map = {
      light: "25%",
      moderate: "50%",
      strong: "75%",
      "beast-mode": "95%",
      nuclear: "95%",
      legendary: "90%",
      poor: "20%",
      average: "50%",
      "long-lasting": "75%",
      heavy: "85%"
    }
    return map[value] || "50%"
  }

  if (loading) {
    return (
      <div className="max-w-3xl mx-auto">
        <div className="animate-pulse">
          <div className="h-4 bg-gray-100 dark:bg-gray-800 rounded w-32 mb-8" />
          <div className="h-8 bg-gray/100 dark:bg-gray-800 rounded w-64 mb-4" />
          <div className="h-4 bg-gray-100 dark:bg-gray-800 rounded w-48 mb-8" />
          <div className="grid grid-cols-2 gap-4">
            <div className="h-48 bg-gray-100 dark:bg-gray-800 rounded-xl" />
            <div className="h-48 bg-gray-100 dark:bg-gray-800 rounded-xl" />
          </div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="max-w-3xl mx-auto text-center py-20">
        <p className="text-gray-400 text-sm mb-4">{error}</p>
        <button
          onClick={() => router.push("/")}
          className="text-sm text-gray-500 underline"
        >
          Back to search
        </button>
      </div>
    )
  }

  if (!fragrance) return null

  const perf = insights?.insights?.performance
  const valuePerception = insights?.insights?.value_perception
  const polarising = insights?.insights?.polarising_elements || []
  const alsoMentions = insights?.insights?.community_also_mentions || []
  const perceivedNotes = insights?.insights?.perceived_notes || []
  const snapshot = insights?.insights?.character_snapshot

  return (
    <div className="max-w-3xl mx-auto">

{/* Breadcrumb */}
<div className="flex items-center gap-1.5 text-xs text-gray-400 mb-6">
  <Link
    href="/"
    className="hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
  >
    Fragrances
  </Link>
  <span className="text-gray-300 dark:text-gray-700">›</span>
  <Link
    href={`/brand/${encodeURIComponent(fragrance.brand)}`}
    className="hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
  >
    {fragrance.brand}
  </Link>
  <span className="text-gray-300 dark:text-gray-700">›</span>
  <span className="text-gray-600 dark:text-gray-300">
    {fragrance.name} {fragrance.concentration}
  </span>
</div>

{/* Header — two column layout */}
<div className="flex gap-8 mb-10 items-start">

  {/* Left — bottle image */}
  <div className="flex-shrink-0">
    {fragrance.image_url ? (
      <img
        src={fragrance.image_url}
        alt={`${fragrance.brand} ${fragrance.name}`}
        className="w-40 h-48 object-contain rounded-xl bg-gray-50 dark:bg-gray-900 p-3"
      />
    ) : (
      <div className="w-40 h-48 rounded-xl bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
        <span className="text-4xl text-gray-200 dark:text-gray-700 font-medium">
          {fragrance.brand?.[0]}
        </span>
      </div>
    )}
  </div>

  {/* Right — fragrance info */}
  <div className="flex-1 min-w-0">
    <p className="text-xs text-gray-400 uppercase tracking-widest mb-2">
      {fragrance.brand}
    </p>
    <h1 className="text-2xl font-medium text-gray-900 dark:text-white mb-3 leading-tight">
      {fragrance.name} {fragrance.concentration}
    </h1>
    <div className="flex flex-wrap gap-2 mb-4">
      {fragrance.gender_marker && (
        <span className="text-xs px-3 py-1 rounded-full bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400">
          {fragrance.gender_marker}
        </span>
      )}
      {fragrance.house_tier && (
        <span className="text-xs px-3 py-1 rounded-full bg-blue-50 dark:bg-blue-950 text-blue-700 dark:text-blue-300">
          {fragrance.house_tier}
        </span>
      )}
      {fragrance.release_year && (
        <span className="text-xs px-3 py-1 rounded-full bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400">
          {fragrance.release_year}
        </span>
      )}
    </div>
    {fragrance.official_description && (
      <p className="text-sm text-gray-500 dark:text-gray-400 leading-relaxed mb-5">
        {fragrance.official_description}
      </p>
    )}
    <div className="flex gap-3">
      <button
        onClick={addToCollection}
        disabled={addingCollection || inCollection}
        className="text-sm px-4 py-2 bg-gray-900 dark:bg-white text-white dark:text-gray-900 rounded-lg hover:bg-gray-700 dark:hover:bg-gray-100 transition-colors disabled:opacity-50"
      >
        {inCollection
          ? "In collection"
          : addingCollection
          ? "Adding..."
          : "Add to collection"}
      </button>
      <button
        onClick={addToWishlist}
        disabled={addingWishlist || inWishlist}
        className="text-sm px-4 py-2 border border-gray-200 dark:border-gray-700 rounded-lg text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors disabled:opacity-50"
      >
        {inWishlist
          ? "In wishlist"
          : addingWishlist
          ? "Adding..."
          : "Add to wishlist"}
      </button>
        </div>
      </div>

    </div>

      {/* Redundancy Warning */}
      {redundancy?.redundant && (
        <div className="mb-8 p-4 bg-amber-50 dark:bg-amber-950 border border-amber-200 dark:border-amber-800 rounded-xl">
          <p className="text-sm font-medium text-amber-800 dark:text-amber-300 mb-1">
            You may already own something similar
          </p>
          {redundancy.matches.map(match => (
            <p key={match.fragrance_id} className="text-xs text-amber-700 dark:text-amber-400">
              {match.brand} {match.name} {match.concentration} —{" "}
              {Math.round(match.similarity_score * 100)}% match
            </p>
          ))}
        </div>
      )}

      {/* Note Comparison */}
      {comparison && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8">
          <div className="border border-gray-100 dark:border-gray-800 rounded-xl p-5">
            <p className="text-xs text-gray-400 uppercase tracking-widest mb-4">
              Official notes
            </p>
            <div className="flex flex-col gap-3">
              {["top", "heart", "base"].map(position => (
                comparison.official_pyramid[position]?.length > 0 && (
                  <div key={position} className="flex gap-3">
                    <span className="text-xs text-gray-300 dark:text-gray-600 w-8 pt-1 flex-shrink-0 capitalize">
                      {position}
                    </span>
                    <div className="flex flex-wrap gap-1">
                      {comparison.official_pyramid[position].map(note => (
                        <span
                          key={note}
                          className="text-xs px-2 py-1 rounded bg-gray-50 dark:bg-gray-800 text-gray-600 dark:text-gray-400"
                        >
                          {note}
                        </span>
                      ))}
                    </div>
                  </div>
                )
              ))}
            </div>
          </div>

          <div className="border border-gray-100 dark:border-gray-800 rounded-xl p-5">
            <p className="text-xs text-gray-400 uppercase tracking-widest mb-4">
              What people actually smell
            </p>
            {perceivedNotes.length > 0 ? (
              <div className="flex flex-col gap-3">
                {["dominant", "prominent", "supporting"].map(prominence => {
                  const notes = perceivedNotes.filter(
                    n => n.prominence === prominence
                  )
                  if (!notes.length) return null
                  const colors = {
                    dominant: "bg-orange-50 dark:bg-orange-950 text-orange-700 dark:text-orange-300",
                    prominent: "bg-amber-50 dark:bg-amber-950 text-amber-700 dark:text-amber-300",
                    supporting: "bg-gray-50 dark:bg-gray-800 text-gray-600 dark:text-gray-400"
                  }
                  return (
                    <div key={prominence} className="flex gap-3">
                      <span className="text-xs text-gray-300 dark:text-gray-600 w-8 pt-1 flex-shrink-0">
                        {prominence === "dominant" ? "Main" :
                         prominence === "prominent" ? "Also" : "Hint"}
                      </span>
                      <div className="flex flex-wrap gap-1">
                        {notes.map(n => (
                          <span
                            key={n.note}
                            className={`text-xs px-2 py-1 rounded ${colors[prominence]}`}
                          >
                            {n.note}
                          </span>
                        ))}
                      </div>
                    </div>
                  )
                })}
              </div>
            ) : (
              <div>
                <p className="text-xs text-gray-400 mb-3">
                  No community analysis yet.
                </p>
                <button
                  onClick={triggerAnalysis}
                  disabled={analysing}
                  className="text-xs px-3 py-2 border border-gray-200 dark:border-gray-700 rounded-lg text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors disabled:opacity-50"
                >
                  {analysing
                    ? jobStatus === "starting"
                      ? "Starting..."
                      : "Analysing..."
                    : "Run AI analysis"}
                </button>
              </div>
            )}
            <p className="text-xs text-gray-300 dark:text-gray-600 mt-3">
              Based on Reddit and YouTube discussions
            </p>
          </div>
        </div>
      )}

      {/* Snapshot */}
      {snapshot && (
        <div className="mb-8 px-5 py-4 bg-gray-50 dark:bg-gray-900 rounded-xl border-l-2 border-gray-200 dark:border-gray-700">
          <p className="text-sm text-gray-600 dark:text-gray-400 leading-relaxed italic">
            "{snapshot}"
          </p>
        </div>
      )}

      {/* Performance */}
      {perf && (
        <div className="mb-8">
          <p className="text-xs text-gray-400 uppercase tracking-widest mb-4">
            Performance
          </p>
          <div className="grid grid-cols-3 gap-3">
            {[
              { label: "Projection", value: perf.projection },
              { label: "Sillage", value: perf.sillage },
              { label: "Longevity", value: perf.longevity }
            ].map(({ label, value }) => (
              <div
                key={label}
                className="border border-gray-100 dark:border-gray-800 rounded-xl p-4 text-center"
              >
                <p className="text-xs text-gray-400 uppercase tracking-widest mb-2">
                  {label}
                </p>
                <p className="text-sm font-medium text-gray-900 dark:text-white capitalize mb-2">
                  {value || "—"}
                </p>
                <div className="h-1 rounded-full bg-gray-100 dark:bg-gray-800">
                  <div
                    className="h-full rounded-full bg-gray-900 dark:bg-white transition-all"
                    style={{ width: performanceWidth(value) }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Value Perception */}
      {valuePerception && (
        <div className="mb-8 border border-gray-100 dark:border-gray-800 rounded-xl p-5">
          <p className="text-xs text-gray-400 uppercase tracking-widest mb-3">
            Value
          </p>
          <div className="flex gap-3 mb-3">
            <span className="text-xs px-3 py-1 rounded-full bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400">
              {valuePerception.price_perception}
            </span>
            <span className="text-xs px-3 py-1 rounded-full bg-green-50 dark:bg-green-950 text-green-700 dark:text-green-300">
              {valuePerception.value_for_money} value
            </span>
          </div>
          {valuePerception.community_note && (
            <p className="text-sm text-gray-500 dark:text-gray-400 leading-relaxed">
              {valuePerception.community_note}
            </p>
          )}
        </div>
      )}

      {/* Polarising Elements */}
      {polarising.length > 0 && (
        <div className="mb-8">
          <p className="text-xs text-gray-400 uppercase tracking-widest mb-3">
            Worth knowing
          </p>
          <div className="flex flex-col gap-2">
            {polarising.map((item, i) => (
              <div
                key={i}
                className="flex gap-3 items-start p-3 bg-gray-50 dark:bg-gray-900 rounded-lg"
              >
                <span className="text-gray-300 dark:text-gray-600 text-xs mt-0.5">
                  ◆
                </span>
                <p className="text-xs text-gray-600 dark:text-gray-400 leading-relaxed">
                  {item}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Best Prices */}
      {prices.length > 0 && (
        <div className="mb-8">
          <p className="text-xs text-gray-400 uppercase tracking-widest mb-4">
            Best prices
          </p>
          <div className="flex flex-col gap-2">
            {prices.map((price, i) => (
              <div
                key={i}
                className="flex justify-between items-center p-4 border border-gray-100 dark:border-gray-800 rounded-xl"
              >
                <div>
                  <p className="text-sm text-gray-900 dark:text-white">
                    {price.retailer_name}
                  </p>
                  <p className="text-xs text-gray-400 mt-0.5">
                    {price.volume_ml}ml · ₹{price.price_per_ml}/ml
                  </p>
                </div>
                <div className="text-right">
                  <p className="text-sm font-medium text-gray-900 dark:text-white">
                    ₹{price.best_price.toLocaleString()}
                  </p>
                  <p className="text-xs text-gray-400 mt-0.5">
                    MRP ₹{price.mrp.toLocaleString()}
                  </p>
                  {price.discount_percentage > 0 && (
                    <span className="text-xs text-green-600 dark:text-green-400">
                      {price.discount_percentage}% off
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Decants */}
      {decants.length > 0 && (
        <div className="mb-8">
          <p className="text-xs text-gray-400 uppercase tracking-widest mb-4">
            Decants available
          </p>
          <div className="flex flex-col gap-2">
            {decants.map((decant, i) => (
              <div
                key={i}
                className="flex justify-between items-center p-4 border border-gray-100 dark:border-gray-800 rounded-xl"
              >
                <div>
                  <p className="text-sm text-gray-900 dark:text-white">
                    {decant.seller_name}
                  </p>
                  <p className="text-xs text-gray-400 mt-0.5">
                    {decant.volume_ml}ml · {decant.seller_platform} · ₹{decant.price_per_ml}/ml
                  </p>
                </div>
                <div className="text-right">
                  <p className="text-sm font-medium text-gray-900 dark:text-white">
                    ₹{decant.price.toLocaleString()}
                  </p>
                  <p className="text-xs text-gray-400 mt-0.5">
                    Try before full bottle
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Similar Fragrances */}
      {similar?.similar?.length > 0 && (
        <div className="mb-8">
          <p className="text-xs text-gray-400 uppercase tracking-widest mb-4">
            Similar fragrances
          </p>
          <div className="flex flex-col gap-2">
            {similar.similar.map(item => (
              <div
                key={item.fragrance_id}
                onClick={() => router.push(`/fragrance/${item.fragrance_id}`)}
                className="flex justify-between items-center p-4 border border-gray-100 dark:border-gray-800 rounded-xl cursor-pointer hover:border-gray-300 dark:hover:border-gray-600 transition-colors"
              >
                <div>
                  <p className="text-sm text-gray-900 dark:text-white">
                    {item.brand} {item.name} {item.concentration}
                  </p>
                </div>
                <span className="text-xs text-gray-400">
                  {Math.round(item.similarity_score * 100)}% match
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Community Also Mentions */}
      {alsoMentions.length > 0 && (
        <div className="mb-8">
          <p className="text-xs text-gray-400 uppercase tracking-widest mb-3">
            Community also mentions
          </p>
          <div className="flex flex-wrap gap-2">
            {alsoMentions.map((name, i) => (
              <span
                key={i}
                className="text-xs px-3 py-1 rounded-full border border-gray-200 dark:border-gray-700 text-gray-600 dark:text-gray-400"
              >
                {name}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Refresh AI Analysis */}
      {insights && (
        <div className="mb-8 flex items-center gap-3">
          <button
            onClick={triggerAnalysis}
            disabled={analysing}
            className="text-xs px-3 py-2 border border-gray-200 dark:border-gray-700 rounded-lg text-gray-500 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors disabled:opacity-50"
          >
            {analysing ? "Analysing..." : "Refresh AI analysis"}
          </button>
          <p className="text-xs text-gray-300 dark:text-gray-600">
            Last updated:{" "}
            {new Date(insights.last_updated).toLocaleDateString()}
          </p>
        </div>
      )}

      {/* Disclaimer */}
      <p className="text-xs text-gray-300 dark:text-gray-700 text-center leading-relaxed mt-12 pb-8">
        Similarity scores and perceived notes are AI-generated
        from community discussions.
        Results improve as more fragrances are analysed.
        Use as a guide, not a definitive answer.
      </p>

    </div>
  )
}
