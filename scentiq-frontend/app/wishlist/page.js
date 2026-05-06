"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import Link from "next/link"

export default function WishlistPage() {
  const router = useRouter()
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    loadWishlist()
  }, [])

  async function loadWishlist() {
    const token = localStorage.getItem("token")
    if (!token) {
      router.push("/login")
      return
    }
    try {
      const res = await fetch("/api/me/wishlist", {
        headers: { Authorization: `Bearer ${token}` }
      })
      if (!res.ok) throw new Error("Failed to load wishlist")
      const data = await res.json()

      const enriched = await Promise.all(
        data.map(async item => {
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
      setError("Something went wrong loading your wishlist.")
    } finally {
      setLoading(false)
    }
  }

  async function removeFromWishlist(fragranceId) {
    const token = localStorage.getItem("token")
    try {
      const res = await fetch(
        `/api/me/wishlist/${fragranceId}`,
        {
          method: "DELETE",
          headers: { Authorization: `Bearer ${token}` }
        }
      )
      if (res.ok) {
        setItems(prev =>
          prev.filter(item => item.fragrance_id !== fragranceId)
        )
      }
    } catch {}
  }

  const priorityStyles = {
    high: "bg-red-50 dark:bg-red-950 text-red-700 dark:text-red-300",
    medium: "bg-amber-50 dark:bg-amber-950 text-amber-700 dark:text-amber-300",
    low: "bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400"
  }

  if (loading) {
    return (
      <div className="max-w-3xl mx-auto">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-100 dark:bg-gray-800 rounded w-48 mb-8" />
          {[1, 2, 3].map(i => (
            <div key={i} className="h-24 bg-gray-100 dark:bg-gray-800 rounded-xl mb-3" />
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
            My Wishlist
          </h1>
          <p className="text-sm text-gray-400">
            {items.length} fragrance{items.length !== 1 ? "s" : ""}
          </p>
        </div>
      </div>

      {items.length === 0 ? (
        <div className="text-center py-20">
          <p className="text-gray-400 text-sm mb-4">
            Your wishlist is empty.
          </p>
          <Link href="/">
            <button className="text-sm px-4 py-2 border border-gray-200 dark:border-gray-700 rounded-lg text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors">
              Search fragrances
            </button>
          </Link>
        </div>
      ) : (
        <div className="flex flex-col gap-3">
          {items.map(item => (
            <div
              key={item.id}
              className="border border-gray-100 dark:border-gray-800 rounded-xl p-5"
            >
              <div className="flex justify-between items-start">
                <div
                  className="flex-1 cursor-pointer"
                  onClick={() => router.push(`/fragrance/${item.fragrance_id}`)}
                >
                  <p className="text-xs text-gray-400 uppercase tracking-widest mb-1">
                    {item.fragrance?.brand}
                  </p>
                  <h3 className="text-base font-medium text-gray-900 dark:text-white mb-2">
                    {item.fragrance?.name} {item.fragrance?.concentration}
                  </h3>
                  <div className="flex flex-wrap gap-2">
                    {item.priority && (
                      <span className={`text-xs px-3 py-1 rounded-full ${priorityStyles[item.priority] || "bg-gray-100 dark:bg-gray-800 text-gray-500"}`}>
                        {item.priority} priority
                      </span>
                    )}
                    {item.budget_ceiling && (
                      <span className="text-xs px-3 py-1 rounded-full bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400">
                        Budget ₹{item.budget_ceiling.toLocaleString()}
                      </span>
                    )}
                  </div>
                  {item.notes && (
                    <p className="text-xs text-gray-400 mt-3 leading-relaxed">
                      {item.notes}
                    </p>
                  )}
                </div>
                <button
                  onClick={() => removeFromWishlist(item.fragrance_id)}
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