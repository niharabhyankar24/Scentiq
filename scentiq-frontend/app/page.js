"use client"

import { useState, useEffect } from "react"
import FragranceCard from "./components/FragranceCard"

export default function Home() {
  const [query, setQuery] = useState("")
  const [results, setResults] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    if (!query.trim()) {
      setResults([])
      return
    }
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

  return (
    <div>
      <div className="text-center mb-12 pt-8">
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

      {!loading && query && results.length === 0 && !error && (
        <p className="text-center text-sm text-neutral-500 dark:text-neutral-400">
          No fragrances found for "{query}"
        </p>
      )}

      {!query && (
        <div className="text-center mt-16">
          <p className="text-sm text-neutral-400 dark:text-neutral-500">
            Start typing to search
          </p>
        </div>
      )}
    </div>
  )
}