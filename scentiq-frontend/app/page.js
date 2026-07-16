"use client"

import { useState, useEffect } from "react"
import FragranceCard from "./components/FragranceCard"

const TOP_PICKS = [
  {
    label: "For date nights",
    query: "warm sensual fragrance for evening romantic occasions"
  },
  {
    label: "Office friendly",
    query: "clean professional fragrance for daytime work environment"
  },
  {
    label: "Skin scents",
    query: "close to skin intimate subtle fragrance for private wear"
  },
  {
    label: "Cold weather",
    query: "warm amber oriental fragrance for cold winter days"
  },
  {
    label: "Fresh & clean",
    query: "fresh aquatic citrus fragrance for hot summer days"
  },
  {
    label: "Classic masculine",
    query: "sophisticated woody masculine fragrance with elegant character"
  }
]


export default function Home() {
  const [query, setQuery] = useState("")
  const [results, setResults] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [activePick, setActivePick] = useState(null)

  // Debounced keyword search when user types
  useEffect(() => {
    if (!query.trim()) {
      if (!activePick) setResults([])
      return
    }
    // Clear active pick if user starts typing
    if (activePick) setActivePick(null)
    const timer = setTimeout(() => {
      searchFragrances(query)
    }, 300)
    return () => clearTimeout(timer)
  }, [query])

  async function searchFragrances(searchQuery) {
    setLoading(true)
    setError(null)
    try {
      const response = await fetch(
        `/api/fragrances/search?q=${encodeURIComponent(searchQuery)}`
      )
      if (!response.ok) throw new Error("Search failed")
      const data = await response.json()
      setResults(data)
    } catch (err) {
      setError("Something went wrong. Please try again.")
      setResults([])
    } finally {
      setLoading(false)
    }
  }

  async function selectTopPick(pick) {
    // Toggle off if already active
    if (activePick?.label === pick.label) {
      setActivePick(null)
      setResults([])
      return
    }

    setActivePick(pick)
    setQuery("")
    setLoading(true)
    setError(null)
    try {
      const response = await fetch("/api/search/semantic", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: pick.query })
      })
      if (!response.ok) throw new Error("Search failed")
      const data = await response.json()
      setResults(data.results || [])
    } catch (err) {
      setError("Something went wrong. Please try again.")
      setResults([])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <div className="text-center mb-8 pt-8">
        <h1 className="font-serif text-4xl sm:text-5xl font-normal text-neutral-900 dark:text-white mb-3 tracking-tight">
          Discover fragrances honestly
        </h1>
        <p className="text-sm text-neutral-500 dark:text-neutral-400 mb-10">
          Real community insights, not marketing copy
        </p>

        <input
          type="text"
          placeholder="Search by name, brand, or note..."
          value={query}
          onChange={e => setQuery(e.target.value)}
          className="w-full max-w-xl px-5 py-3.5 text-base bg-white dark:bg-[#1a1918] border border-neutral-200 dark:border-white/[0.08] rounded-xl outline-none text-neutral-900 dark:text-white placeholder:text-neutral-400 dark:placeholder:text-neutral-600 focus:border-amber-500 dark:focus:border-amber-500 transition-colors"
        />
      </div>

      {/* Top picks chips */}
      <div className="flex flex-wrap justify-center gap-2 mb-12">
        {TOP_PICKS.map(pick => (
          <button
            key={pick.label}
            onClick={() => selectTopPick(pick)}
            className={`text-xs px-4 py-2 rounded-full border transition-colors ${
              activePick?.label === pick.label
                ? "border-amber-500 bg-amber-500/10 text-amber-500"
                : "border-neutral-200 dark:border-white/[0.08] text-neutral-600 dark:text-neutral-400 hover:border-amber-500/40 hover:text-amber-500"
            }`}
          >
            {pick.label}
          </button>
        ))}
      </div>

      {loading && (
        <p className="text-center text-sm text-neutral-500 dark:text-neutral-400">
          Searching...
        </p>
      )}

      {error && (
        <p className="text-center text-sm text-red-500">
          {error}
        </p>
      )}

      {!loading && results.length > 0 && (
        <div>
          {activePick && (
            <p className="text-xs uppercase tracking-widest text-amber-500 mb-3">
              {activePick.label}
            </p>
          )}
          <p className="text-xs text-neutral-500 dark:text-neutral-500 mb-3">
            {results.length} result{results.length !== 1 ? "s" : ""}
          </p>
          <div className="flex flex-col gap-2">
            {results.map(fragrance => (
              <FragranceCard
                key={fragrance.id}
                fragrance={fragrance}
              />
            ))}
          </div>
        </div>
      )}

      {!loading && (query || activePick) && results.length === 0 && !error && (
        <p className="text-center text-sm text-neutral-500 dark:text-neutral-400">
          No fragrances found
        </p>
      )}

      {!query && !activePick && (
        <div className="text-center mt-16">
          <p className="text-sm text-neutral-400 dark:text-neutral-500">
            Start typing to search, or pick a category above
          </p>
        </div>
      )}
    </div>
  )
}