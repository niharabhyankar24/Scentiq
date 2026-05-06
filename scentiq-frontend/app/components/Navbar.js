"use client"

import Link from "next/link"
import { useRouter } from "next/navigation"
import { useEffect, useState } from "react"

export default function Navbar() {
  const router = useRouter()
  const [loggedIn, setLoggedIn] = useState(false)

  useEffect(() => {
  function checkAuth() {
      setLoggedIn(!!localStorage.getItem("token"))
    }
    checkAuth()
    window.addEventListener("storage", checkAuth)
    return () => window.removeEventListener("storage", checkAuth)
    }, []
  )

  function handleLogout() {
    localStorage.removeItem("token")
    setLoggedIn(false)
    router.push("/")
  }

  return (
    <nav className="sticky top-0 z-50 bg-white dark:bg-gray-950 border-b border-gray-100 dark:border-gray-800">
      <div className="max-w-4xl mx-auto px-6 py-4 flex items-center justify-between">
        <Link href="/">
          <span className="text-lg font-medium tracking-tight text-gray-900 dark:text-white">
            Scentiq
          </span>
        </Link>

        <div className="flex items-center gap-6">
          <Link href="/collection">
            <span className="text-sm text-gray-500 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors">
              Collection
            </span>
          </Link>
          <Link href="/wishlist">
            <span className="text-sm text-gray-500 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors">
              Wishlist
            </span>
          </Link>
          {loggedIn ? (
            <button
              onClick={handleLogout}
              className="text-sm px-4 py-2 border border-gray-200 dark:border-gray-700 rounded-lg text-gray-900 dark:text-white hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
            >
              Logout
            </button>
          ) : (
            <Link href="/login">
              <button className="text-sm px-4 py-2 border border-gray-200 dark:border-gray-700 rounded-lg text-gray-900 dark:text-white hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors">
                Login
              </button>
            </Link>
          )}
        </div>
      </div>
    </nav>
  )
}