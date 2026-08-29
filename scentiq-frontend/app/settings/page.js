"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"

// The three consent axes, with user-facing copy. Keeping the
// metadata in one array keeps the render loop clean and makes
// adding/removing an axis a one-line change.
const AXES = [
  {
    key: "consent_collection",
    label: "Personalize from my collection",
    help: "Let Scentiq learn your taste from the fragrances you own and how you rate them.",
    offWarning:
      "Turning this off deletes what Scentiq has learned from your collection.",
  },
  {
    key: "consent_wishlist",
    label: "Personalize from my wishlist",
    help: "Let Scentiq learn from the fragrances you want, and how much you want them.",
    offWarning:
      "Turning this off deletes what Scentiq has learned from your wishlist.",
  },
  {
    key: "consent_search_history",
    label: "Personalize from my search history",
    help: "Let Scentiq learn from what you search for over time.",
    offWarning:
      "Turning this off permanently deletes your stored search history.",
  },
]

export default function SettingsPage() {
  const router = useRouter()

  // saved = what's currently persisted on the server.
  // draft = what the toggles currently show (may differ until Save).
  const [saved, setSaved] = useState(null)
  const [draft, setDraft] = useState(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState(null)
  const [savedFlash, setSavedFlash] = useState(false)

  // Confirmation state: when a save would turn one or more axes
  // OFF, we hold the pending draft here and require the user to
  // type "delete" before it goes through.
  const [pendingOff, setPendingOff] = useState(null) // array of axis labels, or null
  const [confirmText, setConfirmText] = useState("")

  useEffect(() => {
    loadConsent()
  }, [])

  async function loadConsent() {
    const token = localStorage.getItem("token")
    if (!token) {
      router.push("/login")
      return
    }
    try {
      const res = await fetch("/api/me/consent", {
        headers: { Authorization: `Bearer ${token}` },
      })
      if (!res.ok) throw new Error()
      const data = await res.json()
      setSaved(data)
      setDraft(data)
    } catch {
      setError("Couldn't load your settings. Please try again.")
    } finally {
      setLoading(false)
    }
  }

  function toggle(key) {
    setDraft((d) => ({ ...d, [key]: !d[key] }))
    setSavedFlash(false)
  }

  // Which axes are being turned OFF relative to what's saved.
  function axesBeingTurnedOff(nextDraft) {
    return AXES.filter(
      (axis) => saved[axis.key] && !nextDraft[axis.key]
    )
  }

  const dirty =
    saved &&
    draft &&
    AXES.some((axis) => saved[axis.key] !== draft[axis.key])

  function onSaveClick() {
    const turningOff = axesBeingTurnedOff(draft)
    if (turningOff.length > 0) {
      // Gate destructive changes behind type-to-confirm.
      setPendingOff(turningOff.map((a) => a.label))
      setConfirmText("")
      return
    }
    persist(draft)
  }

  async function persist(nextDraft) {
    const token = localStorage.getItem("token")
    setSaving(true)
    setError(null)
    try {
      const res = await fetch("/api/me/consent", {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        // Full-state snapshot — the API expects all three.
        body: JSON.stringify({
          consent_collection: nextDraft.consent_collection,
          consent_wishlist: nextDraft.consent_wishlist,
          consent_search_history: nextDraft.consent_search_history,
        }),
      })
      if (!res.ok) throw new Error()
      const data = await res.json()
      setSaved(data)
      setDraft(data)
      setPendingOff(null)
      setConfirmText("")
      setSavedFlash(true)
    } catch {
      setError("Couldn't save your settings. Please try again.")
    } finally {
      setSaving(false)
    }
  }

  if (loading) {
    return (
      <div className="max-w-2xl mx-auto">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-100 dark:bg-gray-800 rounded w-40 mb-8" />
          {[1, 2, 3].map((i) => (
            <div
              key={i}
              className="h-20 bg-gray-100 dark:bg-gray-800 rounded-xl mb-3"
            />
          ))}
        </div>
      </div>
    )
  }

  if (error && !draft) {
    return (
      <div className="max-w-2xl mx-auto text-center py-20">
        <p className="text-gray-400 text-sm">{error}</p>
      </div>
    )
  }

  return (
    <div className="max-w-2xl mx-auto">
      <h1 className="text-2xl font-medium text-gray-900 dark:text-white mb-2">
        Settings
      </h1>
      <p className="text-sm text-gray-400 mb-8 leading-relaxed">
        Control what Scentiq uses to personalize your experience.
        Everything is off by default. Turning something off deletes
        what was stored — off means gone.
      </p>

      <div className="flex flex-col gap-3">
        {AXES.map((axis) => {
          const on = draft[axis.key]
          return (
            <div
              key={axis.key}
              className="border border-gray-100 dark:border-gray-800 rounded-xl p-5 flex items-start justify-between gap-4"
            >
              <div className="flex-1">
                <p className="text-sm font-medium text-gray-900 dark:text-white mb-1">
                  {axis.label}
                </p>
                <p className="text-xs text-gray-500 dark:text-gray-400 leading-relaxed">
                  {axis.help}
                </p>
              </div>

              {/* Toggle */}
              <button
                role="switch"
                aria-checked={on}
                onClick={() => toggle(axis.key)}
                className={`relative shrink-0 w-11 h-6 rounded-full transition-colors ${
                  on
                    ? "bg-[#c9a254]"
                    : "bg-gray-200 dark:bg-gray-700"
                }`}
              >
                <span
                  className={`absolute top-0.5 left-0.5 w-5 h-5 rounded-full bg-white transition-transform ${
                    on ? "translate-x-5" : "translate-x-0"
                  }`}
                />
              </button>
            </div>
          )
        })}
      </div>

      {/* Save row */}
      <div className="flex items-center gap-4 mt-6">
        <button
          disabled={!dirty || saving}
          onClick={onSaveClick}
          className={`text-sm px-5 py-2 rounded-lg transition-colors ${
            dirty && !saving
              ? "bg-gray-900 dark:bg-white text-white dark:text-gray-900 hover:opacity-90"
              : "bg-gray-100 dark:bg-gray-800 text-gray-400 cursor-not-allowed"
          }`}
        >
          {saving ? "Saving…" : "Save changes"}
        </button>
        {savedFlash && (
          <span className="text-xs text-gray-400">Saved.</span>
        )}
        {error && draft && (
          <span className="text-xs text-red-400">{error}</span>
        )}
      </div>

      {/* Type-to-confirm dialog for destructive (turning-off) changes */}
      {pendingOff && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4">
          <div className="bg-white dark:bg-[#151412] border border-gray-100 dark:border-gray-800 rounded-2xl p-6 max-w-md w-full">
            <h2 className="text-lg font-medium text-gray-900 dark:text-white mb-3">
              Turn off personalization?
            </h2>
            <p className="text-sm text-gray-500 dark:text-gray-400 leading-relaxed mb-4">
              You're turning off:
            </p>
            <ul className="mb-4 flex flex-col gap-2">
              {pendingOff.map((label) => (
                <li
                  key={label}
                  className="text-sm text-gray-700 dark:text-gray-300 flex gap-2"
                >
                  <span className="text-red-400">•</span>
                  {label}
                </li>
              ))}
            </ul>
            <p className="text-xs text-gray-500 dark:text-gray-400 leading-relaxed mb-4">
              This permanently deletes what Scentiq stored for the
              above. This can't be undone. Type{" "}
              <span className="font-mono text-gray-900 dark:text-white">
                delete
              </span>{" "}
              to confirm.
            </p>
            <input
              autoFocus
              value={confirmText}
              onChange={(e) => setConfirmText(e.target.value)}
              placeholder="delete"
              className="w-full px-3 py-2 mb-4 rounded-lg border border-gray-200 dark:border-gray-700 bg-transparent text-sm text-gray-900 dark:text-white focus:outline-none focus:border-gray-400 dark:focus:border-gray-500"
            />
            <div className="flex gap-3 justify-end">
              <button
                onClick={() => {
                  setPendingOff(null)
                  setConfirmText("")
                }}
                className="text-sm px-4 py-2 rounded-lg text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
              >
                Cancel
              </button>
              <button
                disabled={confirmText !== "delete" || saving}
                onClick={() => persist(draft)}
                className={`text-sm px-4 py-2 rounded-lg transition-colors ${
                  confirmText === "delete" && !saving
                    ? "bg-red-500 text-white hover:bg-red-600"
                    : "bg-gray-100 dark:bg-gray-800 text-gray-400 cursor-not-allowed"
                }`}
              >
                {saving ? "Saving…" : "Turn off & delete"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}