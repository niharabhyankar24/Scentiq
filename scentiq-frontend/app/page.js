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
      <div style={{ marginBottom: "40px", textAlign: "center" }}>
        <h1 style={{
          fontSize: "28px",
          fontWeight: "500",
          marginBottom: "8px",
          color: "#1a1a1a"
        }}>
          Discover fragrances honestly
        </h1>
        <p style={{
          fontSize: "15px",
          color: "#888",
          marginBottom: "28px"
        }}>
          Real community insights, not marketing copy
        </p>

        <input
          type="text"
          placeholder="Search by name or brand..."
          value={query}
          onChange={e => setQuery(e.target.value)}
          style={{
            width: "100%",
            maxWidth: "560px",
            padding: "14px 20px",
            fontSize: "15px",
            border: "0.5px solid #ddd",
            borderRadius: "10px",
            outline: "none",
            color: "#1a1a1a"
          }}
          onFocus={e => {
            e.target.style.borderColor = "#1a1a1a"
          }}
          onBlur={e => {
            e.target.style.borderColor = "#ddd"
          }}
        />
      </div>

      {loading && (
        <p style={{
          textAlign: "center",
          color: "#999",
          fontSize: "14px"
        }}>
          Searching...
        </p>
      )}

      {error && (
        <p style={{
          textAlign: "center",
          color: "#e53e3e",
          fontSize: "14px"
        }}>
          {error}
        </p>
      )}

      {!loading && results.length > 0 && (
        <div>
          <p style={{
            fontSize: "12px",
            color: "#999",
            marginBottom: "12px"
          }}>
            {results.length} result{results.length !== 1 ? "s" : ""}
          </p>
          <div style={{
            display: "flex",
            flexDirection: "column",
            gap: "8px"
          }}>
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
        <p style={{
          textAlign: "center",
          color: "#999",
          fontSize: "14px"
        }}>
          No fragrances found for "{query}"
        </p>
      )}

      {!query && (
        <div style={{
          textAlign: "center",
          marginTop: "60px",
          color: "#ccc"
        }}>
          <p style={{ fontSize: "14px" }}>
            Start typing to search 
          </p>
        </div>
      )}
    </div>
  )
}