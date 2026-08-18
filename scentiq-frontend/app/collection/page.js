"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import Link from "next/link"

// --- Rating control -------------------------------------------------
// Interactive 1-10 rating. Muted traffic-light bands:
//   1-3 red (weak) · 4-7 amber/gold (mid) · 8-10 green (strong)
// Monochrome at rest, band color on hover (ghost) and when selected.
// Sends a NARROW payload ({personal_rating: n}) so it can never
// clobber other collection fields. Optimistic: updates immediately,
// reverts on failure.
function RatingControl({ fragranceId, value, onChange }) {
  const [hover, setHover] = useState(null)
  const [saving, setSaving] = useState(false)

  // Which band a given score falls into.
  const band = (v) => (v <= 3 ? "r" : v <= 7 ? "a" : "g")

  // Solid fill (selected) — muted, desaturated to fit the aesthetic.
  const solid = {
    r: "#a85a4a", // dusty terracotta
    a: "#c9a254", // the app's existing gold
    g: "#6f9463", // muted sage
  }
  // Ghost fill (hover preview) — same hues, translucent.
  const ghost = {
    r: "rgba(168,90,74,0.28)",
    a: "rgba(201,162,84,0.28)",
    g: "rgba(111,148,99,0.28)",
  }

  async function persist(newValue) {
    const token = localStorage.getItem("token")
    const previous = value
    onChange(newValue) // optimistic
    setSaving(true)
    try {
      const res = await fetch(`/api/me/collection/${fragranceId}`, {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ personal_rating: newValue }),
      })
      if (!res.ok) throw new Error()
    } catch {
      onChange(previous) // revert on failure
    } finally {
      setSaving(false)
    }
  }

  return (
    <div
      className="flex items-center gap-2"
      onClick={(e) => e.stopPropagation()} // don't trigger card navigation
    >
      <span className="text-[11px] uppercase tracking-widest text-gray-400 dark:text-gray-500 min-w-[48px]">
        Rating
      </span>
      <div className="flex gap-[3px]" onMouseLeave={() => setHover(null)}>
        {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map((n) => {
          const isFilledBySelection = value && n <= value
          const isFilledByHover = hover && n <= hover

          let style = {}
          let textClass =
            "text-gray-400 dark:text-gray-500 border-gray-200 dark:border-gray-700"

          if (isFilledByHover) {
            // hover preview: ghost fill of the hovered band
            style = { background: ghost[band(hover)] }
            textClass =
              "text-gray-900 dark:text-white border-gray-200 dark:border-gray-700"
          } else if (isFilledBySelection) {
            // committed: solid fill of the selected band
            style = {
              background: solid[band(value)],
              borderColor: solid[band(value)],
            }
            textClass = "text-[#100f0d] border-transparent"
          }

          return (
            <button
              key={n}
              disabled={saving}
              style={style}
              onMouseEnter={() => setHover(n)}
              onClick={() => persist(n)}
              className={`w-[26px] h-[26px] flex items-center justify-center text-xs rounded-md border-[0.5px] transition-colors ${textClass}`}
            >
              {n}
            </button>
          )
        })}
      </div>
      {value ? (
        <button
          title="Clear rating"
          disabled={saving}
          onClick={() => persist(null)}
          className="text-[15px] leading-none text-gray-300 dark:text-gray-600 hover:text-gray-500 dark:hover:text-gray-400 transition-colors ml-1"
        >
          &times;
        </button>
      ) : null}
    </div>
  )
}

export default function CollectionPage() {
  const router = useRouter()
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    loadCollection()
  }, [])

  async function loadCollection() {
    const token = localStorage.getItem("token")
    if (!token) {
      router.push("/login")
      return
    }
    try {
      const res = await fetch("/api/me/collection", {
        headers: { Authorization: `Bearer ${token}` },
      })
      if (!res.ok) throw new Error("Failed to load collection")
      const data = await res.json()

      const enriched = await Promise.all(
        data.map(async (item) => {
          const fragranceRes = await fetch(
            `/api/fragrances/${item.fragrance_id}`
          )
          const fragrance = fragranceRes.ok
            ? await fragranceRes.json()
            : null
          return { ...item, fragrance }
        })
      )
      setItems(enriched)
    } catch (err) {
      setError("Something went wrong loading your collection.")
    } finally {
      setLoading(false)
    }
  }

  async function removeFromCollection(fragranceId) {
    const token = localStorage.getItem("token")
    try {
      const res = await fetch(`/api/me/collection/${fragranceId}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` },
      })
      if (res.ok) {
        setItems((prev) =>
          prev.filter((item) => item.fragrance_id !== fragranceId)
        )
      }
    } catch {}
  }

  // Update one item's rating in local state (used by RatingControl
  // for optimistic updates and reverts).
  function setItemRating(fragranceId, newRating) {
    setItems((prev) =>
      prev.map((item) =>
        item.fragrance_id === fragranceId
          ? { ...item, personal_rating: newRating }
          : item
      )
    )
  }

  const bottleStatusColor = {
    full: "bg-green-50 dark:bg-green-950 text-green-700 dark:text-green-300",
    mostly_full:
      "bg-green-50 dark:bg-green-950 text-green-700 dark:text-green-300",
    half: "bg-amber-50 dark:bg-amber-950 text-amber-700 dark:text-amber-300",
    low: "bg-red-50 dark:bg-red-950 text-red-700 dark:text-red-300",
    empty: "bg-gray-100 dark:bg-gray-800 text-gray-500 dark:text-gray-400",
  }

  if (loading) {
    return (
      <div className="max-w-3xl mx-auto">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-100 dark:bg-gray-800 rounded w-48 mb-8" />
          {[1, 2, 3].map((i) => (
            <div
              key={i}
              className="h-24 bg-gray-100 dark:bg-gray-800 rounded-xl mb-3"
            />
          ))}
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="max-w-3xl mx-auto text-center py-20">
        <p className="text-gray-400 text-sm">{error}</p>
      </div>
    )
  }

  return (
    <div className="max-w-3xl mx-auto">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-medium text-gray-900 dark:text-white mb-1">
            My Collection
          </h1>
          <p className="text-sm text-gray-400">
            {items.length} fragrance{items.length !== 1 ? "s" : ""}
          </p>
        </div>
      </div>

      {items.length === 0 ? (
        <div className="text-center py-20">
          <p className="text-gray-400 text-sm mb-4">
            Your collection is empty.
          </p>
          <Link href="/">
            <button className="text-sm px-4 py-2 border border-gray-200 dark:border-gray-700 rounded-lg text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors">
              Search fragrances
            </button>
          </Link>
        </div>
      ) : (
        <div className="flex flex-col gap-3">
          {items.map((item) => (
            <div
              key={item.id}
              className="border border-gray-100 dark:border-gray-800 rounded-xl p-5"
            >
              <div className="flex justify-between items-start">
                <div className="flex-1">
                  <div
                    className="cursor-pointer"
                    onClick={() =>
                      router.push(`/fragrance/${item.fragrance_id}`)
                    }
                  >
                    <p className="text-xs text-gray-400 uppercase tracking-widest mb-1">
                      {item.fragrance?.brand}
                    </p>
                    <h3 className="text-base font-medium text-gray-900 dark:text-white mb-2">
                      {item.fragrance?.name} {item.fragrance?.concentration}
                    </h3>
                    <div className="flex flex-wrap gap-2 mb-3">
                      {item.bottle_status && (
                        <span
                          className={`text-xs px-3 py-1 rounded-full ${
                            bottleStatusColor[item.bottle_status] ||
                            "bg-gray-100 dark:bg-gray-800 text-gray-500"
                          }`}
                        >
                          {item.bottle_status.replace("_", " ")}
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Rating control — outside the navigation click region */}
                  <RatingControl
                    fragranceId={item.fragrance_id}
                    value={item.personal_rating}
                    onChange={(newRating) =>
                      setItemRating(item.fragrance_id, newRating)
                    }
                  />

                  <div
                    className="cursor-pointer"
                    onClick={() =>
                      router.push(`/fragrance/${item.fragrance_id}`)
                    }
                  >
                    {item.snapshot_summary && (
                      <p className="text-xs text-gray-500 dark:text-gray-400 mt-3 leading-relaxed italic">
                        "{item.snapshot_summary}"
                      </p>
                    )}
                    {item.personal_notes && (
                      <p className="text-xs text-gray-400 mt-2 leading-relaxed">
                        {item.personal_notes}
                      </p>
                    )}
                  </div>
                </div>
                <button
                  onClick={() => removeFromCollection(item.fragrance_id)}
                  className="text-xs text-gray-300 dark:text-gray-600 hover:text-red-400 dark:hover:text-red-400 transition-colors ml-4 mt-1"
                >
                  Remove
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}