"use client"

import { useRouter } from "next/navigation"

export default function FragranceCard({ fragrance }) {
  const router = useRouter()

  function handleClick() {
    router.push(`/fragrance/${fragrance.id}`)
  }

  const tierStyles = {
    designer: "bg-blue-50 text-blue-700 dark:bg-blue-950 dark:text-blue-300",
    niche: "bg-green-50 text-green-700 dark:bg-green-950 dark:text-green-300",
    "ultra-niche": "bg-purple-50 text-purple-700 dark:bg-purple-950 dark:text-purple-300"
  }

  const tierClass = tierStyles[fragrance.house_tier] ||
    "bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400"

  return (
    <div
      onClick={handleClick}
      className="border border-gray-100 dark:border-gray-800 rounded-xl p-4 cursor-pointer flex justify-between items-center hover:border-gray-300 dark:hover:border-gray-600 transition-colors bg-white dark:bg-gray-950"
    >
      <div className="flex items-center gap-4">
        {fragrance.image_url ? (
          <img
            src={fragrance.image_url}
            alt={fragrance.name}
            className="h-12 w-12 object-contain flex-shrink-0"
          />
        ) : (
          <div className="h-12 w-12 rounded-lg bg-gray-50 dark:bg-gray-800 flex items-center justify-center flex-shrink-0">
            <span className="text-sm text-gray-300 dark:text-gray-600 font-medium">
              {fragrance.brand?.[0]}
            </span>
          </div>
        )}
        <div>
          <p className="text-xs text-gray-400 dark:text-gray-500 uppercase tracking-widest mb-1">
            {fragrance.brand}
          </p>
          <h3 className="text-sm font-medium text-gray-900 dark:text-white mb-2">
            {fragrance.name} {fragrance.concentration}
          </h3>
          <div className="flex gap-2">
            {fragrance.scent_family_name && (
              <span className="text-xs px-3 py-1 rounded-full bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400">
                {fragrance.scent_family_name}
              </span>
            )}
            {fragrance.house_tier && (
              <span className={`text-xs px-3 py-1 rounded-full ${tierClass}`}>
                {fragrance.house_tier}
              </span>
            )}
          </div>
        </div>
      </div>
      <span className="text-gray-300 dark:text-gray-600 text-sm flex-shrink-0">
        →
      </span>
    </div>
  )
}
