"use client"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"

export default function AdminPage() {
  const router = useRouter()
  const [status, setStatus] = useState("checking")
  // status: "checking" | "ready" | "denied"

  useEffect(() => {
    async function verifyAdmin() {
      const token = localStorage.getItem("token")
      if (!token) {
        router.replace("/login")
        return
      }

      try {
        const res = await fetch("/api/auth/me", {
          headers: { Authorization: `Bearer ${token}` }
        })
        if (!res.ok) {
          // Token invalid or expired.
          router.replace("/login")
          return
        }
        const user = await res.json()
        if (!user.is_admin) {
          router.replace("/")
          return
        }
        setStatus("ready")
      } catch (err) {
        router.replace("/login")
      }
    }

    verifyAdmin()
  }, [router])

  if (status === "checking") {
    return (
      <div className="text-center py-16">
        <p className="text-sm text-neutral-500 dark:text-neutral-500">
          Verifying access...
        </p>
      </div>
    )
  }

  return (
    <div>
      <h1 className="font-serif text-4xl font-normal text-neutral-900 dark:text-white tracking-tight mb-2">
        Admin
      </h1>
      <p className="text-sm text-neutral-500 dark:text-neutral-400 mb-10">
        Manage the fragrance catalogue
      </p>

      <div className="border border-neutral-200 dark:border-white/[0.04] rounded-xl p-8 text-center">
        <p className="text-sm text-neutral-500 dark:text-neutral-500">
          Dashboard coming next
        </p>
      </div>
    </div>
  )
}