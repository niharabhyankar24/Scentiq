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
  const [focused, setFocused] = useState(false)

  // Debounced keyword search when user types
  useEffect(() => {
    if (!query.trim()) {
      if (!activePick) setResults([])
      return
    }
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
      const token = localStorage.getItem("token")
      const response = await fetch("/api/search/semantic", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {})
        },
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

  const hasResults = !loading && results.length > 0
  const isEmpty = !query && !activePick

  return (
    <div className="relative">
      {/* Warm radial glow behind the hero — gives the flat near-black
          depth so the minimal layout reads as deliberate, not empty.
          Pointer-events-none so it never interferes with interaction. */}
      <div
        aria-hidden
        className="pointer-events-none absolute inset-x-0 -top-24 mx-auto h-[520px] max-w-3xl
                   bg-[radial-gradient(ellipse_at_center,rgba(201,162,84,0.10),transparent_70%)]
                   blur-2xl"
      />

      {/* Hero cluster — headline, tagline, search, chips grouped tightly
          as one intentional unit in the upper-middle. */}
      <div className="relative flex flex-col items-center text-center pt-14 sm:pt-20">
        <h1 className="font-serif text-5xl sm:text-6xl font-normal text-neutral-900 dark:text-white tracking-tight leading-[1.05]">
          Discover fragrances honestly
        </h1>
        <p className="mt-4 text-sm sm:text-base text-neutral-500 dark:text-neutral-400 tracking-wide">
          Real community insights, not marketing copy
        </p>

        {/* Search — the hero action. Confident surface, real border,
            gold focus ring so it clearly invites a touch. */}
        <div className="w-full max-w-xl mt-9">
          <div
            className={`group relative rounded-2xl transition-all duration-300 ${
              focused
                ? "shadow-[0_0_0_1px_rgba(201,162,84,0.5),0_8px_40px_-12px_rgba(201,162,84,0.25)]"
                : "shadow-[0_8px_40px_-16px_rgba(0,0,0,0.6)]"
            }`}
          >
            <input
              type="text"
              placeholder="Search by name, brand, or note…"
              value={query}
              onChange={e => setQuery(e.target.value)}
              onFocus={() => setFocused(true)}
              onBlur={() => setFocused(false)}
              className="w-full px-6 py-4 text-base rounded-2xl outline-none
                         bg-neutral-50 dark:bg-[#1c1b19]
                         border border-neutral-200 dark:border-white/[0.10]
                         text-neutral-900 dark:text-white
                         placeholder:text-neutral-400 dark:placeholder:text-neutral-500
                         focus:border-transparent transition-colors"
            />
          </div>
        </div>

        {/* Chips — curated entry points. Warmer, a touch larger,
            gold-tinted hover so they invite rather than filter. */}
        <div className="flex flex-wrap justify-center gap-2.5 mt-6">
          {TOP_PICKS.map(pick => (
            <button
              key={pick.label}
              onClick={() => selectTopPick(pick)}
              className={`text-[13px] px-4 py-2 rounded-full border transition-all duration-200 ${
                activePick?.label === pick.label
                  ? "border-amber-500 bg-amber-500/[0.12] text-amber-500"
                  : "border-neutral-200 dark:border-white/[0.09] text-neutral-600 dark:text-neutral-300 hover:border-amber-500/50 hover:bg-amber-500/[0.06] hover:text-amber-500"
              }`}
            >
              {pick.label}
            </button>
          ))}
        </div>
      </div>

      {/* Results / states */}
      <div className="relative mt-14">
        {loading && (
          <p className="text-center text-sm text-neutral-500 dark:text-neutral-400">
            Searching…
          </p>
        )}

        {error && (
          <p className="text-center text-sm text-red-500">
            {error}
          </p>
        )}

        {hasResults && (
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
                <FragranceCard key={fragrance.id} fragrance={fragrance} />
              ))}
            </div>
          </div>
        )}

        {!loading && (query || activePick) && results.length === 0 && !error && (
          <p className="text-center text-sm text-neutral-500 dark:text-neutral-400">
            No fragrances found
          </p>
        )}

        {isEmpty && (
          <p className="text-center text-xs text-neutral-400 dark:text-neutral-600 tracking-wide">
            Start typing, or pick a category above
          </p>
        )}
      </div>
    </div>
  )
}