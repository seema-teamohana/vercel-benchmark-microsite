'use client'

import { useEffect, useMemo, useState } from 'react'
import { ReferenceResponse } from '../lib/api'

// Order to display levels in dropdowns. Anything not in this list appears alphabetically.
const LEVEL_ORDER = [
  'IC1', 'IC2', 'IC3', 'IC4', 'IC5', 'IC6', 'IC7',
  'M1', 'M2', 'M3', 'M4', 'M5', 'M6', 'M7', 'M8',
  'Director', 'Executive',
]

function sortLevels(levels: string[]): string[] {
  const orderMap = new Map(LEVEL_ORDER.map((l, i) => [l, i]))
  return [...levels].sort((a, b) => {
    const ia = orderMap.get(a) ?? 999
    const ib = orderMap.get(b) ?? 999
    if (ia !== ib) return ia - ib
    return a.localeCompare(b)
  })
}

// Default hire date: today + 60 days, so users get a forward-looking benchmark.
function defaultHireDate(): string {
  const d = new Date()
  d.setDate(d.getDate() + 60)
  return d.toISOString().slice(0, 10)  // YYYY-MM-DD
}

interface Props {
  reference: ReferenceResponse
  onSubmit: (payload: { role: string; level: string; location: string; hire_date: string }) => void
  isSubmitting: boolean
}

export default function BenchmarkForm({ reference, onSubmit, isSubmitting }: Props) {
  // Role → country → level cascade. Empty string = "not selected".
  const [role, setRole] = useState<string>('')
  const [country, setCountry] = useState<string>('')
  const [level, setLevel] = useState<string>('')
  const [hireDate, setHireDate] = useState<string>(defaultHireDate())

  // Derived dropdown options based on current selections.
  const availableCountries = useMemo(() => {
    if (!role) return []
    const countries = reference.available_combinations[role]
    if (!countries) return []
    return Object.keys(countries).sort()
  }, [role, reference])

  const availableLevels = useMemo(() => {
    if (!role || !country) return []
    const levels = reference.available_combinations[role]?.[country]
    if (!levels) return []
    return sortLevels(Object.keys(levels))
  }, [role, country, reference])

  // Reset downstream selections when upstream changes.
  useEffect(() => {
    if (country && !availableCountries.includes(country)) {
      setCountry('')
    }
  }, [availableCountries, country])

  useEffect(() => {
    if (level && !availableLevels.includes(level)) {
      setLevel('')
    }
  }, [availableLevels, level])

  const canSubmit = role && country && level && hireDate && !isSubmitting

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!canSubmit) return
    onSubmit({ role, level, location: country, hire_date: hireDate })
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-5">
      {/* Role */}
      <div>
        <label className="block text-sm font-medium text-brand-light mb-1.5">
          Role
        </label>
        <select
          value={role}
          onChange={(e) => setRole(e.target.value)}
          className="block w-full rounded-md border border-slate-300 bg-white px-3 py-2.5 text-brand focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent"
        >
          <option value="">Select a role…</option>
          {reference.roles.map((r) => (
            <option key={r} value={r}>{r}</option>
          ))}
        </select>
      </div>

      {/* Country */}
      <div>
        <label className="block text-sm font-medium text-brand-light mb-1.5">
          Country
        </label>
        <select
          value={country}
          onChange={(e) => setCountry(e.target.value)}
          disabled={!role}
          className="block w-full rounded-md border border-slate-300 bg-white px-3 py-2.5 text-brand focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent disabled:bg-slate-50 disabled:text-slate-400"
        >
          <option value="">{role ? 'Select a country…' : 'First select a role'}</option>
          {availableCountries.map((c) => (
            <option key={c} value={c}>{c}</option>
          ))}
        </select>
      </div>

      {/* Level */}
      <div>
        <label className="block text-sm font-medium text-brand-light mb-1.5">
          Seniority Level
        </label>
        <select
          value={level}
          onChange={(e) => setLevel(e.target.value)}
          disabled={!country}
          className="block w-full rounded-md border border-slate-300 bg-white px-3 py-2.5 text-brand focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent disabled:bg-slate-50 disabled:text-slate-400"
        >
          <option value="">{country ? 'Select a level…' : 'First select a country'}</option>
          {availableLevels.map((l) => (
            <option key={l} value={l}>{l}</option>
          ))}
        </select>
        {country && availableLevels.length > 0 && (
          <p className="mt-1.5 text-xs text-slate-500">
            IC = Individual Contributor · M = Manager
          </p>
        )}
      </div>

      {/* Hire date */}
      <div>
        <label className="block text-sm font-medium text-brand-light mb-1.5">
          Target hire date
        </label>
        <input
          type="date"
          value={hireDate}
          onChange={(e) => setHireDate(e.target.value)}
          className="block w-full rounded-md border border-slate-300 bg-white px-3 py-2.5 text-brand focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent"
        />
        <p className="mt-1.5 text-xs text-slate-500">
          Salaries drift over time. This adjusts the benchmark for when the hire actually starts.
        </p>
      </div>

      {/* Submit */}
      <div className="pt-2">
        <button
          type="submit"
          disabled={!canSubmit}
          className="w-full rounded-md bg-brand px-4 py-3 text-sm font-semibold text-white hover:bg-brand-light focus:outline-none focus:ring-2 focus:ring-accent focus:ring-offset-2 disabled:bg-slate-300 disabled:cursor-not-allowed transition"
        >
          {isSubmitting ? 'Loading benchmark…' : 'Get Benchmark'}
        </button>
      </div>
    </form>
  )
}
