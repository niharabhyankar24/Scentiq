"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import Link from "next/link"

// The three axes, in display order, with user-facing headings.
const AXES = [
  {
    key: "collection",
    heading: "From your collection",
  },
  {
    key: "wishlist",
    heading: "From your wishlist",
  },
  {
    key: "search",
    heading: "From your searches",
  },
]

export default function SignaturePage() {
  const router = useRouter()
  const [memory, setMemory] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  // Load once on mount. Freshness is handled by the backend:
  // GET regenerates any axis whose data changed since last
  // time (fingerprint comparison), so simply arriving on this
  // page shows current content. No in-page refresh needed —
  // navigating here, or a browser reload, is the refresh.
  useEffect(() => {
    load()
  }, [])

  async function load() {
    const token = localStorage.getItem("token")
    if (!token) {
      router.push("/login")
      return
    }
    setLoading(true)
    setError(null)
    try {
      const res = await fetch("/api/me/memory", {
        headers: { Authorization: `Bearer ${token}` },
      })
      if (!res.ok) throw new Error()
      const data = await res.json()
      setMemory(data)
    } catch {
      setError("Couldn't load your signature. Please try again.")
    } finally {
      setLoading(false)
    }
  }

  async function deleteObservation(axisKey, observationId) {
    const token = localStorage.getItem("token")
    // Optimistic: remove from local state immediately.
    setMemory((prev) => {
      if (!prev || !prev[axisKey]) return prev
      return {
        ...prev,
        [axisKey]: {
          ...prev[axisKey],
          observations: prev[axisKey].observations.filter(
            (o) => o.id !== observationId
          ),
        },
      }
    })
    try {
      const res = await fetch(
        `/api/me/memory/observations/${axisKey}/${observationId}`,
        {
          method: "DELETE",
          headers: { Authorization: `Bearer ${token}` },
        }
      )
      if (!res.ok) throw new Error()
    } catch {
      // On failure, reload to restore truth.
      load()
    }
  }

  const activeAxes = memory ? AXES.filter((a) => memory[a.key]) : []
  const nothingOptedIn = memory && activeAxes.length === 0

  // --- First-load skeleton ---
  if (loading) {
    return (
      <div className="max-w-2xl mx-auto">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-100 dark:bg-gray-800 rounded w-48 mb-8" />
          {[1, 2].map((i) => (
            <div key={i} className="mb-8">
              <div className="h-4 bg-gray-100 dark:bg-gray-800 rounded w-40 mb-3" />
              <div className="h-20 bg-gray-100 dark:bg-gray-800 rounded-xl" />
            </div>
          ))}
        </div>
      </div>
    )
  }

  if (error && !memory) {
    return (
      <div className="max-w-2xl mx-auto text-center py-20">
        <p className="text-gray-400 text-sm mb-4">{error}</p>
        <button
          onClick={load}
          className="text-sm px-4 py-2 border border-gray-200 dark:border-gray-700 rounded-lg text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
        >
          Try again
        </button>
      </div>
    )
  }

  return (
    <div className="max-w-2xl mx-auto">
      <h1 className="text-2xl font-medium text-gray-900 dark:text-white mb-2">
        Your Signature
      </h1>
      <p className="text-sm text-gray-400 mb-8 leading-relaxed">
        What Scentiq has learned about your taste, in its own words.
      </p>

      {nothingOptedIn ? (
        <div className="border border-gray-100 dark:border-gray-800 rounded-xl p-8 text-center">
          <p className="text-sm text-gray-500 dark:text-gray-400 mb-4 leading-relaxed">
            Your signature is built from what you choose to share.
            Turn on personalization to begin.
          </p>
          <Link href="/settings">
            <button className="text-sm px-4 py-2 border border-gray-200 dark:border-gray-700 rounded-lg text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors">
              Go to Settings
            </button>
          </Link>
        </div>
      ) : (
        <div className="flex flex-col gap-10">
          {activeAxes.map((axis) => {
            const block = memory[axis.key]
            const isStale = block.status === "stale"

            return (
              <section key={axis.key}>
                <div className="mb-3">
                  <h2 className="text-xs uppercase tracking-widest text-gray-400 mb-1">
                    {axis.heading}
                  </h2>
                  {isStale && (
                    <p className="text-xs text-gray-400 italic">
                      Couldn't refresh just now — showing your last signature.
                    </p>
                  )}
                </div>

                <p className="text-[15px] text-gray-800 dark:text-gray-200 leading-relaxed mb-5">
                  {block.paragraph}
                </p>

                {block.observations && block.observations.length > 0 && (
                  <ul className="flex flex-col gap-2">
                    {block.observations.map((obs) => (
                      <li
                        key={obs.id}
                        className="group flex items-start gap-3 text-sm text-gray-600 dark:text-gray-400 leading-relaxed"
                      >
                        <span className="mt-1.5 shrink-0 w-1 h-1 rounded-full bg-[#c9a254]" />
                        <span className="flex-1">{obs.text}</span>
                        <button
                          onClick={() => deleteObservation(axis.key, obs.id)}
                          title="Remove this — Scentiq will stop drawing on it"
                          className="opacity-0 group-hover:opacity-100 text-gray-300 dark:text-gray-600 hover:text-red-400 dark:hover:text-red-400 transition-all text-sm shrink-0"
                        >
                          &times;
                        </button>
                      </li>
                    ))}
                  </ul>
                )}
              </section>
            )
          })}
        </div>
      )}
    </div>
  )
}