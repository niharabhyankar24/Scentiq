"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import Link from "next/link"

// Each axis knows: its consent flag, its heading, the action a
// user takes to feed it, and where that action lives. This lets
// every axis explain its own state — off, on-but-empty, or full —
// so the user is never staring at absence with no explanation.
const AXES = [
  {
    key: "collection",
    consentKey: "consent_collection",
    heading: "From your collection",
    noun: "your collection",
    action: "rate the fragrances you own",
    href: "/collection",
  },
  {
    key: "wishlist",
    consentKey: "consent_wishlist",
    heading: "From your wishlist",
    noun: "your wishlist",
    action: "add fragrances to your wishlist",
    href: "/wishlist",
  },
  {
    key: "search",
    consentKey: "consent_search_history",
    heading: "From your searches",
    noun: "your searches",
    action: "search for fragrances",
    href: "/",
  },
]

export default function SignaturePage() {
  const router = useRouter()
  const [memory, setMemory] = useState(null)
  const [consent, setConsent] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

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
      const [memRes, conRes] = await Promise.all([
        fetch("/api/me/memory", {
          headers: { Authorization: `Bearer ${token}` },
        }),
        fetch("/api/me/consent", {
          headers: { Authorization: `Bearer ${token}` },
        }),
      ])
      if (!memRes.ok || !conRes.ok) throw new Error()
      setMemory(await memRes.json())
      setConsent(await conRes.json())
    } catch {
      setError("Couldn't load your signature. Please try again.")
    } finally {
      setLoading(false)
    }
  }

  async function deleteObservation(axisKey, observationId) {
    const token = localStorage.getItem("token")
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
      load()
    }
  }

  if (loading) {
    return (
      <div className="max-w-2xl mx-auto">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-100 dark:bg-gray-800 rounded w-48 mb-8" />
          {[1, 2, 3].map((i) => (
            <div key={i} className="mb-8">
              <div className="h-4 bg-gray-100 dark:bg-gray-800 rounded w-40 mb-3" />
              <div className="h-16 bg-gray-100 dark:bg-gray-800 rounded-xl" />
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

      <div className="flex flex-col gap-10">
        {AXES.map((axis) => {
          const enabled = consent && consent[axis.consentKey]
          const block = memory && memory[axis.key]

          return (
            <section key={axis.key}>
              <h2 className="text-xs uppercase tracking-widest text-gray-400 mb-3">
                {axis.heading}
              </h2>

              {!enabled ? (
                // Axis is off. Explain neutrally, point to Settings.
                <p className="text-sm text-gray-400 dark:text-gray-500 leading-relaxed">
                  Off. Scentiq isn't drawing on {axis.noun}. You can
                  change this in{" "}
                  <Link
                    href="/settings"
                    className="underline underline-offset-2 hover:text-gray-600 dark:hover:text-gray-300"
                  >
                    Settings
                  </Link>
                  .
                </p>
              ) : !block ? (
                // On, but nothing generated yet. Confirm it's working,
                // name the action that will fill it.
                <p className="text-sm text-gray-500 dark:text-gray-400 leading-relaxed">
                  On, with nothing to read yet. Your signature here
                  will take shape once you{" "}
                  <Link
                    href={axis.href}
                    className="underline underline-offset-2 text-gray-700 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white"
                  >
                    {axis.action}
                  </Link>
                  .
                </p>
              ) : (
                // On, with content.
                <>
                  {block.status === "stale" && (
                    <p className="text-xs text-gray-400 italic mb-2">
                      Couldn't refresh just now — showing your last signature.
                    </p>
                  )}
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
                            onClick={() =>
                              deleteObservation(axis.key, obs.id)
                            }
                            title="Remove this — Scentiq will stop drawing on it"
                            className="opacity-0 group-hover:opacity-100 text-gray-300 dark:text-gray-600 hover:text-red-400 dark:hover:text-red-400 transition-all text-sm shrink-0"
                          >
                            &times;
                          </button>
                        </li>
                      ))}
                    </ul>
                  )}
                </>
              )}
            </section>
          )
        })}
      </div>
    </div>
  )
}