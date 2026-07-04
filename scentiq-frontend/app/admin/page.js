"use client"

import { useEffect, useState, useCallback } from "react"
import { useRouter } from "next/navigation"

export default function AdminPage() {
  const router = useRouter()
  const [status, setStatus] = useState("checking")
  const [dashboard, setDashboard] = useState(null)
  const [error, setError] = useState(null)
  const [refreshingId, setRefreshingId] = useState(null)
  const [showForm, setShowForm] = useState(false)
  const [activeFragrance, setActiveFragrance] = useState(null)

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

  const fetchDashboard = useCallback(async () => {
    const token = localStorage.getItem("token")
    try {
      const res = await fetch("/api/admin/dashboard", {
        headers: { Authorization: `Bearer ${token}` }
      })
      if (!res.ok) throw new Error("Failed to load dashboard")
      const data = await res.json()
      setDashboard(data)
      setError(null)
    } catch (err) {
      setError("Could not load dashboard data.")
    }
  }, [])

  useEffect(() => {
    if (status === "ready") fetchDashboard()
  }, [status, fetchDashboard])

  async function handleRefresh(fragranceId) {
    const token = localStorage.getItem("token")
    setRefreshingId(fragranceId)
    try {
      const res = await fetch(
        `/api/admin/fragrances/${fragranceId}/refresh-analysis`,
        {
          method: "POST",
          headers: { Authorization: `Bearer ${token}` }
        }
      )
      if (!res.ok) throw new Error()
      setTimeout(() => {
        setRefreshingId(null)
        fetchDashboard()
      }, 1500)
    } catch (err) {
      setRefreshingId(null)
      setError("Refresh failed.")
    }
  }

  function handleFragranceCreated(fragrance) {
    setActiveFragrance(fragrance)
    setShowForm(false)
    fetchDashboard()
  }

  function handleDoneAssigning() {
    setActiveFragrance(null)
    fetchDashboard()
  }

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
      <div className="mb-10 flex items-end justify-between">
        <div>
          <h1 className="font-serif text-4xl font-normal text-neutral-900 dark:text-white tracking-tight mb-2">
            Admin
          </h1>
          <p className="text-sm text-neutral-500 dark:text-neutral-400">
            Manage the fragrance catalogue
          </p>
        </div>
        {!showForm && !activeFragrance && (
          <button
            onClick={() => setShowForm(true)}
            className="text-sm px-4 py-2 bg-amber-500 hover:bg-amber-600 text-neutral-950 font-medium rounded-lg transition-colors"
          >
            Add fragrance
          </button>
        )}
      </div>

      {error && <p className="text-sm text-red-500 mb-6">{error}</p>}

      {showForm && (
        <CreateFragranceForm
          onCancel={() => setShowForm(false)}
          onCreated={handleFragranceCreated}
        />
      )}

      {activeFragrance && (
        <NoteAssignmentPanel
          fragrance={activeFragrance}
          onDone={handleDoneAssigning}
        />
      )}

      {!dashboard && !error && (
        <p className="text-sm text-neutral-500 dark:text-neutral-500">
          Loading dashboard...
        </p>
      )}

      {dashboard && !activeFragrance && (
        <>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-10">
            <StatCard label="Total" value={dashboard.stats.total_fragrances} />
            <StatCard label="Analyzed" value={dashboard.stats.analyzed} accent="green" />
            <StatCard label="Pending" value={dashboard.stats.pending} accent="amber" />
            <StatCard label="Missing" value={dashboard.stats.missing_insights} accent="red" />
          </div>

          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-xs uppercase tracking-widest text-neutral-500 dark:text-neutral-500">
              Fragrances
            </h2>
            <span className="text-xs text-neutral-400 dark:text-neutral-600">
              {dashboard.fragrances.length} total
            </span>
          </div>

          <div className="flex flex-col gap-1">
            {dashboard.fragrances.map(f => (
              <FragranceRow
                key={f.id}
                fragrance={f}
                refreshing={refreshingId === f.id}
                onRefresh={() => handleRefresh(f.id)}
                onAssignNotes={() => setActiveFragrance(f)}
              />
            ))}
          </div>
        </>
      )}
    </div>
  )
}

function NoteAssignmentPanel({ fragrance, onDone }) {
  const [allNotes, setAllNotes] = useState([])
  const [assignedNotes, setAssignedNotes] = useState([])
  const [position, setPosition] = useState("top")
  const [searchTerm, setSearchTerm] = useState("")
  const [selectedNoteId, setSelectedNoteId] = useState(null)
  const [creatingNew, setCreatingNew] = useState(false)
  const [newNoteCategory, setNewNoteCategory] = useState("")
  const [newNoteDescription, setNewNoteDescription] = useState("")
  const [newNotePolarizing, setNewNotePolarizing] = useState(false)
  const [newNoteIntensity, setNewNoteIntensity] = useState("")
  const [submitting, setSubmitting] = useState(false)
  const [panelError, setPanelError] = useState(null)

  // Load all notes once for the search dropdown.
  useEffect(() => {
    async function loadNotes() {
      try {
        const res = await fetch("/api/notes")
        if (res.ok) {
          const data = await res.json()
          setAllNotes(data)
        }
      } catch (err) {
        setPanelError("Could not load existing notes.")
      }
    }
    loadNotes()
  }, [])

  // Filter notes by search term, case-insensitive.
  const filtered = searchTerm.trim()
    ? allNotes.filter(n =>
        n.name.toLowerCase().includes(searchTerm.trim().toLowerCase())
      )
    : []

  const exactMatch = allNotes.find(
    n => n.name.toLowerCase() === searchTerm.trim().toLowerCase()
  )

  async function handleAdd() {
    setSubmitting(true)
    setPanelError(null)
    const token = localStorage.getItem("token")

    const payload = { pyramid_position: position }

    if (creatingNew) {
      payload.note_name = searchTerm.trim()
      payload.note_category = newNoteCategory
      if (newNoteDescription) payload.note_description = newNoteDescription
      if (newNotePolarizing) payload.note_polarizing = true
      if (newNoteIntensity) payload.note_intensity = newNoteIntensity
    } else if (selectedNoteId) {
      payload.note_id = selectedNoteId
    } else {
      setPanelError("Pick a note or create a new one.")
      setSubmitting(false)
      return
    }

    try {
      const res = await fetch(
        `/api/admin/fragrances/${fragrance.id}/notes`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`
          },
          body: JSON.stringify(payload)
        }
      )
      if (!res.ok) {
        const data = await res.json()
        throw new Error(data.detail || "Could not assign note")
      }
      const link = await res.json()
      // Add to visible list. Also push new note into allNotes
      // so subsequent searches find it.
      setAssignedNotes(prev => [...prev, link])
      if (creatingNew) {
        setAllNotes(prev => [
          ...prev,
          {
            id: link.note_id,
            name: link.note_name,
            category: newNoteCategory
          }
        ])
      }
      // Reset form for next note.
      setSearchTerm("")
      setSelectedNoteId(null)
      setCreatingNew(false)
      setNewNoteCategory("")
      setNewNoteDescription("")
      setNewNotePolarizing(false)
      setNewNoteIntensity("")
    } catch (err) {
      setPanelError(err.message)
    } finally {
      setSubmitting(false)
    }
  }

  async function handleRemove(link) {
    const token = localStorage.getItem("token")
    try {
      const res = await fetch(
        `/api/admin/fragrances/${fragrance.id}/notes/${link.note_id}`,
        {
          method: "DELETE",
          headers: { Authorization: `Bearer ${token}` }
        }
      )
      if (!res.ok) throw new Error()
      setAssignedNotes(prev => prev.filter(n => n.id !== link.id))
    } catch (err) {
      setPanelError("Could not remove note.")
    }
  }

  const inputClass = "w-full px-3 py-2 text-sm bg-white dark:bg-[#1a1918] border border-neutral-200 dark:border-white/[0.08] rounded-lg outline-none text-neutral-900 dark:text-white placeholder:text-neutral-400 dark:placeholder:text-neutral-600 focus:border-amber-500 transition-colors"

  const labelClass = "block text-xs uppercase tracking-wider text-neutral-500 dark:text-neutral-500 mb-1.5"

  return (
    <div className="border border-neutral-200 dark:border-white/[0.04] rounded-xl p-6 mb-8">
      <div className="flex items-center justify-between mb-6">
        <div>
          <p className="text-xs uppercase tracking-widest text-amber-500 mb-1">
            Assigning notes
          </p>
          <h2 className="font-serif text-2xl text-neutral-900 dark:text-white">
            {fragrance.brand} {fragrance.name}
          </h2>
        </div>
        <button
          onClick={onDone}
          className="text-sm px-4 py-2 bg-amber-500 hover:bg-amber-600 text-neutral-950 font-medium rounded-lg transition-colors"
        >
          Done
        </button>
      </div>

      {/* Assigned notes list */}
      {assignedNotes.length > 0 && (
        <div className="mb-6">
          <p className={labelClass}>Assigned so far</p>
          <div className="flex flex-wrap gap-2">
            {assignedNotes.map(link => (
              <div
                key={link.id}
                className="flex items-center gap-2 px-3 py-1.5 bg-neutral-100 dark:bg-white/[0.04] rounded text-xs text-neutral-700 dark:text-neutral-300"
              >
                <span className="text-amber-500 uppercase tracking-wider text-[10px]">
                  {link.pyramid_position}
                </span>
                <span>{link.note_name}</span>
                <button
                  onClick={() => handleRemove(link)}
                  className="text-neutral-400 hover:text-red-500 ml-1"
                  title="Remove"
                >
                  ×
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Add note form */}
      <div className="border-t border-neutral-200 dark:border-white/[0.04] pt-6">
        <p className={labelClass}>Add a note</p>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mb-3">
          <div>
            <label className={labelClass}>Position</label>
            <select
              value={position}
              onChange={e => setPosition(e.target.value)}
              className={inputClass}
            >
              <option value="top">Top</option>
              <option value="heart">Heart</option>
              <option value="base">Base</option>
            </select>
          </div>
          <div className="sm:col-span-2 relative">
            <label className={labelClass}>Note</label>
            <input
              type="text"
              value={searchTerm}
              onChange={e => {
                setSearchTerm(e.target.value)
                setSelectedNoteId(null)
                setCreatingNew(false)
              }}
              placeholder="Search or type a new note..."
              className={inputClass}
            />
            {searchTerm && filtered.length > 0 && !selectedNoteId && !creatingNew && (
              <div className="absolute z-10 left-0 right-0 mt-1 bg-white dark:bg-[#1a1918] border border-neutral-200 dark:border-white/[0.08] rounded-lg max-h-48 overflow-y-auto shadow-lg">
                {filtered.slice(0, 8).map(n => (
                  <button
                    key={n.id}
                    type="button"
                    onClick={() => {
                      setSelectedNoteId(n.id)
                      setSearchTerm(n.name)
                    }}
                    className="block w-full text-left px-3 py-2 text-sm text-neutral-900 dark:text-white hover:bg-amber-500/10 transition-colors"
                  >
                    {n.name}
                    {n.category && (
                      <span className="text-xs text-neutral-400 ml-2">
                        {n.category}
                      </span>
                    )}
                  </button>
                ))}
              </div>
            )}
            {searchTerm && !exactMatch && !creatingNew && !selectedNoteId && (
              <button
                type="button"
                onClick={() => setCreatingNew(true)}
                className="text-xs text-amber-500 hover:text-amber-600 mt-2"
              >
                + Create "{searchTerm.trim()}" as a new note
              </button>
            )}
          </div>
        </div>

        {/* Inline note creation fields */}
        {creatingNew && (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-3 p-4 bg-amber-500/5 border border-amber-500/20 rounded-lg">
            <div>
              <label className={labelClass}>Category *</label>
              <input
                type="text"
                value={newNoteCategory}
                onChange={e => setNewNoteCategory(e.target.value)}
                placeholder="citrus, woody, gourmand..."
                className={inputClass}
              />
            </div>
            <div>
              <label className={labelClass}>Intensity</label>
              <select
                value={newNoteIntensity}
                onChange={e => setNewNoteIntensity(e.target.value)}
                className={inputClass}
              >
                <option value="">—</option>
                <option value="light">Light</option>
                <option value="moderate">Moderate</option>
                <option value="heavy">Heavy</option>
              </select>
            </div>
            <div className="sm:col-span-2">
              <label className={labelClass}>Description</label>
              <input
                type="text"
                value={newNoteDescription}
                onChange={e => setNewNoteDescription(e.target.value)}
                placeholder="Optional"
                className={inputClass}
              />
            </div>
            <div className="sm:col-span-2 flex items-center gap-2">
              <input
                type="checkbox"
                id="polarizing"
                checked={newNotePolarizing}
                onChange={e => setNewNotePolarizing(e.target.checked)}
                className="accent-amber-500"
              />
              <label htmlFor="polarizing" className="text-xs text-neutral-700 dark:text-neutral-300">
                Polarizing (some people love it, some hate it)
              </label>
            </div>
          </div>
        )}

        {panelError && (
          <p className="text-sm text-red-500 mb-3">{panelError}</p>
        )}

        <button
          onClick={handleAdd}
          disabled={submitting || (!selectedNoteId && !creatingNew)}
          className="text-sm px-4 py-2 bg-amber-500 hover:bg-amber-600 disabled:opacity-30 disabled:cursor-not-allowed text-neutral-950 font-medium rounded-lg transition-colors"
        >
          {submitting ? "Adding..." : "Add note"}
        </button>
      </div>
    </div>
  )
}

function CreateFragranceForm({ onCancel, onCreated }) {
  const [brand, setBrand] = useState("")
  const [name, setName] = useState("")
  const [concentration, setConcentration] = useState("EDP")
  const [releaseYear, setReleaseYear] = useState("")
  const [genderMarker, setGenderMarker] = useState("unisex")
  const [houseTier, setHouseTier] = useState("designer")
  const [scentFamilyId, setScentFamilyId] = useState("")
  const [description, setDescription] = useState("")
  const [imageUrl, setImageUrl] = useState("")
  const [refreshIntervalDays, setRefreshIntervalDays] = useState(90)
  const [scentFamilies, setScentFamilies] = useState([])
  const [submitting, setSubmitting] = useState(false)
  const [formError, setFormError] = useState(null)

  useEffect(() => {
    async function loadFamilies() {
      try {
        const res = await fetch("/api/scent-families")
        if (res.ok) {
          const data = await res.json()
          setScentFamilies(data)
        }
      } catch (err) {
        // silent
      }
    }
    loadFamilies()
  }, [])

  async function handleSubmit(e) {
    e.preventDefault()
    setSubmitting(true)
    setFormError(null)
    const token = localStorage.getItem("token")
    const payload = {
      brand, name, concentration,
      gender_marker: genderMarker,
      house_tier: houseTier,
      scent_family_id: parseInt(scentFamilyId),
      refresh_interval_days: refreshIntervalDays
    }
    if (releaseYear) payload.release_year = parseInt(releaseYear)
    if (description) payload.official_description = description
    if (imageUrl) payload.image_url = imageUrl

    try {
      const res = await fetch("/api/admin/fragrances", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify(payload)
      })
      if (!res.ok) {
        const data = await res.json()
        throw new Error(data.detail || "Creation failed")
      }
      const fragrance = await res.json()
      onCreated(fragrance)
    } catch (err) {
      setFormError(err.message)
    } finally {
      setSubmitting(false)
    }
  }

  const inputClass = "w-full px-3 py-2 text-sm bg-white dark:bg-[#1a1918] border border-neutral-200 dark:border-white/[0.08] rounded-lg outline-none text-neutral-900 dark:text-white placeholder:text-neutral-400 dark:placeholder:text-neutral-600 focus:border-amber-500 transition-colors"
  const labelClass = "block text-xs uppercase tracking-wider text-neutral-500 dark:text-neutral-500 mb-1.5"

  return (
    <form onSubmit={handleSubmit} className="border border-neutral-200 dark:border-white/[0.04] rounded-xl p-6 mb-8">
      <div className="flex items-center justify-between mb-6">
        <h2 className="font-serif text-2xl text-neutral-900 dark:text-white">
          New fragrance
        </h2>
        <button
          type="button"
          onClick={onCancel}
          className="text-xs text-neutral-500 dark:text-neutral-400 hover:text-neutral-900 dark:hover:text-white"
        >
          Cancel
        </button>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-4">
        <div><label className={labelClass}>Brand *</label><input type="text" required value={brand} onChange={e => setBrand(e.target.value)} className={inputClass} placeholder="Dior" /></div>
        <div><label className={labelClass}>Name *</label><input type="text" required value={name} onChange={e => setName(e.target.value)} className={inputClass} placeholder="Sauvage Elixir" /></div>
        <div><label className={labelClass}>Concentration *</label><select value={concentration} onChange={e => setConcentration(e.target.value)} className={inputClass}><option value="EDT">EDT</option><option value="EDP">EDP</option><option value="Parfum">Parfum</option><option value="Extrait">Extrait</option><option value="Other">Other</option></select></div>
        <div><label className={labelClass}>Release year</label><input type="number" value={releaseYear} onChange={e => setReleaseYear(e.target.value)} className={inputClass} placeholder="2024" min="1900" max="2100" /></div>
        <div><label className={labelClass}>Gender marker</label><select value={genderMarker} onChange={e => setGenderMarker(e.target.value)} className={inputClass}><option value="masculine">Masculine</option><option value="feminine">Feminine</option><option value="unisex">Unisex</option></select></div>
        <div><label className={labelClass}>House tier</label><select value={houseTier} onChange={e => setHouseTier(e.target.value)} className={inputClass}><option value="designer">Designer</option><option value="niche">Niche</option><option value="ultra-niche">Ultra-niche</option></select></div>
        <div><label className={labelClass}>Scent family *</label><select required value={scentFamilyId} onChange={e => setScentFamilyId(e.target.value)} className={inputClass}><option value="">Select...</option>{scentFamilies.map(sf => <option key={sf.id} value={sf.id}>{sf.name}</option>)}</select></div>
        <div><label className={labelClass}>Refresh interval</label><select value={refreshIntervalDays} onChange={e => setRefreshIntervalDays(parseInt(e.target.value))} className={inputClass}><option value={30}>Monthly</option><option value={90}>Quarterly</option><option value={365}>Yearly</option></select></div>
      </div>

      <div className="mb-4"><label className={labelClass}>Image URL</label><input type="url" value={imageUrl} onChange={e => setImageUrl(e.target.value)} className={inputClass} placeholder="https://cloudinary.com/..." /></div>
      <div className="mb-6"><label className={labelClass}>Official description</label><textarea value={description} onChange={e => setDescription(e.target.value)} rows={3} className={inputClass} placeholder="Optional" /></div>

      {formError && <p className="text-sm text-red-500 mb-4">{formError}</p>}

      <button type="submit" disabled={submitting} className="text-sm px-5 py-2.5 bg-amber-500 hover:bg-amber-600 disabled:opacity-50 text-neutral-950 font-medium rounded-lg transition-colors">
        {submitting ? "Creating..." : "Create fragrance"}
      </button>
    </form>
  )
}

function StatCard({ label, value, accent }) {
  const accentClasses = { green: "text-emerald-500", amber: "text-amber-500", red: "text-red-500" }
  return (
    <div className="border border-neutral-200 dark:border-white/[0.04] rounded-xl p-4">
      <div className={`font-serif text-3xl ${accentClasses[accent] || "text-neutral-900 dark:text-white"}`}>{value}</div>
      <div className="text-[10px] uppercase tracking-widest text-neutral-500 dark:text-neutral-500 mt-1">{label}</div>
    </div>
  )
}

function FragranceRow({ fragrance, refreshing, onRefresh, onAssignNotes }) {
  const statusStyles = {
    complete: "bg-emerald-500/10 text-emerald-500",
    pending: "bg-amber-500/10 text-amber-500",
    missing: "bg-red-500/10 text-red-500"
  }
  return (
    <div className="flex items-center justify-between border border-neutral-200 dark:border-white/[0.04] rounded-lg px-4 py-3 hover:border-amber-500/30 transition-colors">
      <div className="min-w-0 flex-1">
        <div className="text-xs uppercase tracking-wider text-neutral-500 dark:text-neutral-500">{fragrance.brand}</div>
        <div className="text-sm font-medium text-neutral-900 dark:text-white truncate">{fragrance.name}</div>
      </div>
      <div className="flex items-center gap-3 ml-3">
        <span className={`text-[10px] uppercase tracking-widest px-2 py-1 rounded ${statusStyles[fragrance.analysis_status]}`}>
          {fragrance.analysis_status}
        </span>
        <span className="hidden sm:inline text-[11px] text-neutral-400 dark:text-neutral-600">
          {fragrance.analysis_refresh_due ? `Due ${fragrance.analysis_refresh_due}` : "—"}
        </span>
        <button onClick={onAssignNotes} className="text-[11px] px-3 py-1.5 border border-neutral-200 dark:border-white/[0.08] rounded text-neutral-600 dark:text-neutral-300 hover:border-amber-500 hover:text-amber-500 transition-colors">
          Notes
        </button>
        <button onClick={onRefresh} disabled={refreshing} className="text-[11px] px-3 py-1.5 border border-neutral-200 dark:border-white/[0.08] rounded text-neutral-600 dark:text-neutral-300 hover:border-amber-500 hover:text-amber-500 transition-colors disabled:opacity-50">
          {refreshing ? "Queued..." : "Refresh"}
        </button>
      </div>
    </div>
  )
}