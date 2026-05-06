"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import Link from "next/link"

export default function LoginPage() {
  const router = useRouter()
  const [mode, setMode] = useState("login")
  const [email, setEmail] = useState("")
  const [username, setUsername] = useState("")
  const [password, setPassword] = useState("")
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  async function handleSubmit(e) {
    e.preventDefault()
    setLoading(true)
    setError(null)

    try {
      const endpoint = mode === "login"
        ? "/api/auth/login"
        : "/api/auth/register"

      const body = mode === "login"
        ? { email, password }
        : { email, username, password }

      const res = await fetch(endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body)
      })

      const data = await res.json()

      if (!res.ok) {
        setError(data.detail || "Something went wrong.")
        return
      }

      localStorage.setItem("token", data.access_token)
      window.dispatchEvent(new Event("storage"))
      router.push("/")

    } catch (err) {
      setError("Something went wrong. Please try again.")
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-sm mx-auto pt-16">
      <div className="mb-8 text-center">
        <h1 className="text-2xl font-medium text-gray-900 dark:text-white mb-2">
          {mode === "login" ? "Welcome back" : "Create account"}
        </h1>
        <p className="text-sm text-gray-400">
          {mode === "login"
            ? "Sign in to access your collection"
            : "Start building your fragrance profile"}
        </p>
      </div>

      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
        <div>
          <label className="block text-xs text-gray-500 dark:text-gray-400 mb-1.5">
            Email
          </label>
          <input
            type="email"
            value={email}
            onChange={e => setEmail(e.target.value)}
            required
            placeholder="you@example.com"
            className="w-full px-4 py-2.5 text-sm border border-gray-200 dark:border-gray-700 rounded-lg outline-none bg-white dark:bg-gray-950 text-gray-900 dark:text-white placeholder-gray-300 dark:placeholder-gray-600 focus:border-gray-400 dark:focus:border-gray-500 transition-colors"
          />
        </div>

        {mode === "register" && (
          <div>
            <label className="block text-xs text-gray-500 dark:text-gray-400 mb-1.5">
              Username
            </label>
            <input
              type="text"
              value={username}
              onChange={e => setUsername(e.target.value)}
              required
              placeholder="yourname"
              className="w-full px-4 py-2.5 text-sm border border-gray-200 dark:border-gray-700 rounded-lg outline-none bg-white dark:bg-gray-950 text-gray-900 dark:text-white placeholder-gray-300 dark:placeholder-gray-600 focus:border-gray-400 dark:focus:border-gray-500 transition-colors"
            />
          </div>
        )}

        <div>
          <label className="block text-xs text-gray-500 dark:text-gray-400 mb-1.5">
            Password
          </label>
          <input
            type="password"
            value={password}
            onChange={e => setPassword(e.target.value)}
            required
            placeholder="••••••••"
            className="w-full px-4 py-2.5 text-sm border border-gray-200 dark:border-gray-700 rounded-lg outline-none bg-white dark:bg-gray-950 text-gray-900 dark:text-white placeholder-gray-300 dark:placeholder-gray-600 focus:border-gray-400 dark:focus:border-gray-500 transition-colors"
          />
        </div>

        {error && (
          <p className="text-xs text-red-500 text-center">
            {error}
          </p>
        )}

        <button
          type="submit"
          disabled={loading}
          className="w-full py-2.5 text-sm font-medium bg-gray-900 dark:bg-white text-white dark:text-gray-900 rounded-lg hover:bg-gray-700 dark:hover:bg-gray-100 transition-colors disabled:opacity-50 mt-2"
        >
          {loading
            ? "Please wait..."
            : mode === "login" ? "Sign in" : "Create account"}
        </button>
      </form>

      <p className="text-center text-xs text-gray-400 mt-6">
        {mode === "login"
          ? "Don't have an account?"
          : "Already have an account?"}{" "}
        <button
          onClick={() => {
            setMode(mode === "login" ? "register" : "login")
            setError(null)
          }}
          className="text-gray-600 dark:text-gray-300 underline"
        >
          {mode === "login" ? "Register" : "Sign in"}
        </button>
      </p>
    </div>
  )
}