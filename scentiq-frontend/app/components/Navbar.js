"use client"

import Link from "next/link"
import { useRouter } from "next/navigation"
import { useEffect, useState } from "react"

export default function Navbar() {
  const router = useRouter()
  const [loggedIn, setLoggedIn] = useState(false)
  const [isAdmin, setIsAdmin] = useState(false)

  useEffect(() => {
    async function checkAuth() {
      const token = localStorage.getItem("token")
      setLoggedIn(!!token)
      if (!token) {
        setIsAdmin(false)
        return
      }
      try {
        const res = await fetch("/api/auth/me", {
          headers: { Authorization: `Bearer ${token}` }
        })
        if (res.ok) {
          const user = await res.json()
          setIsAdmin(!!user.is_admin)
        } else {
          setIsAdmin(false)
        }
      } catch {
        setIsAdmin(false)
      }
    }
    checkAuth()
    window.addEventListener("storage", checkAuth)
    return () => window.removeEventListener("storage", checkAuth)
  }, [])

  function handleLogout() {
    localStorage.removeItem("token")
    setLoggedIn(false)
    setIsAdmin(false)
    router.push("/")
  }

  const linkClass = "text-sm text-gray-500 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors"
  const buttonClass = "text-sm px-4 py-2 border border-gray-200 dark:border-gray-700 rounded-lg text-gray-900 dark:text-white hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"

  return (
    <nav className="sticky top-0 z-50 bg-white dark:bg-[#100f0d] border-b border-neutral-200 dark:border-white/[0.06]">
      <div className="max-w-4xl mx-auto px-6 py-4 flex items-center justify-between">
        <Link href="/" className="flex items-center gap-2">
          <svg width="14" height="20" viewBox="0 0 14 20" fill="none" aria-hidden="true">
            <rect x="4.5" y="0.5" width="5" height="3" rx="0.5" stroke="#c9a254" strokeWidth="1" />
            <path d="M3 6 L11 6 L11.5 19 L2.5 19 Z" stroke="#c9a254" strokeWidth="1" fill="none" />
          </svg>
          <span className="font-serif text-2xl tracking-tight text-neutral-900 dark:text-white">
            Scentiq
          </span>
        </Link>

        <div className="flex items-center gap-6">
          <Link href="/collection"><span className={linkClass}>Collection</span></Link>
          <Link href="/wishlist"><span className={linkClass}>Wishlist</span></Link>
          {isAdmin && (
            <Link href="/admin">
              <span className="text-sm text-amber-500 hover:text-amber-600 transition-colors">
                Admin
              </span>
            </Link>
          )}
          {loggedIn ? (
            <button onClick={handleLogout} className={buttonClass}>Logout</button>
          ) : (
            <Link href="/login"><button className={buttonClass}>Login</button></Link>
          )}
        </div>
      </div>
    </nav>
  )
}