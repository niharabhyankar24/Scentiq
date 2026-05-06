"use client"

import { useState, useEffect } from "react"
import { useParams, useRouter } from "next/navigation"
import Link from "next/link"
import FragranceCard from "../../components/FragranceCard"

export default function BrandPage() {
  const { name } = useParams()
  const router = useRouter()
  const [fragrances, setFragrances] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    if (name) loadBrand()
  }, [name])

  async function loadBrand() {
    setLoading(true)
    setError(null)
    try {
      const res = await fetch(
        `/api/fragrances/brand/${encodeURIComponent(name)}`
      )
      if (!res.ok) throw new Error("Brand not found")
      const data = await res.json()
      setFragrances(data)
    } catch (err) {
      setError("No fragrances found for this brand.")
    } finally {
      setLoading(false)
    }
  }

  const decodedName = decodeURIComponent(name)

  if (loading) {
    return (
      <div className="max-w-3xl mx-auto">
        <div className="animate-pulse">
          <div className="h-4 bg-gray-100 dark:bg-gray-800 rounded w-32 mb-8" />
          <div className="h-8 bg-gray-100 dark:bg-gray-800 rounded w-48 mb-6" />
          {[1, 2, 3].map(i => (
            <div key={i} className="h-20 bg-gray-100 dark:bg-gray-800 rounded-xl mb-3" />
          ))}
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="max-w-3xl mx-auto text-center py-20">
        <p className="text-gray-400 text-sm mb-4">{error}</p>
        <Link href="/">
          <button className="text-sm text-gray-500 underline">
            Back to search
          </button>
        </Link>
      </div>
    )
  }

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
        <span className="text-gray-600 dark:text-gray-300">
          {decodedName}
        </span>
      </div>

      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-medium text-gray-900 dark:text-white mb-1">
          {decodedName}
        </h1>
        <p className="text-sm text-gray-400">
          {fragrances.length} fragrance{fragrances.length !== 1 ? "s" : ""}
        </p>
      </div>

      {/* Fragrance List */}
      <div className="flex flex-col gap-2">
        {fragrances.map(fragrance => (
          <FragranceCard
            key={fragrance.id}
            fragrance={fragrance}
          />
        ))}
      </div>

    </div>
  )
}