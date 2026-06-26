'use client'
import { useEffect, useState } from 'react'
import { api, CustomerOptions } from '../lib/api'

interface Props {
  customerId: string
  onSubmit: (q: { role: string; level: string; location: string; hire_date: string }) => void
  loading: boolean
}

export default function QueryForm({ customerId, onSubmit, loading }: Props) {
  const [options, setOptions] = useState<CustomerOptions | null>(null)
  const [role, setRole] = useState<string>('')
  const [level, setLevel] = useState<string>('')
  const [location, setLocation] = useState<string>('')
  const [hireDate, setHireDate] = useState<string>('')
  const [dateSource, setDateSource] = useState<string>('')

  // Load customer's role/level/location options when the customer changes
  useEffect(() => {
    let cancelled = false
    api.customerOptions(customerId).then((opts) => {
      if (cancelled) return
      setOptions(opts)
      // Set initial selections to first option of each (let user override)
      if (opts.roles.length && !role) setRole(opts.roles[0])
      if (opts.levels.length && !level) setLevel(opts.levels[0])
      if (opts.locations.length && !location) setLocation(opts.locations[0])
    })
    return () => { cancelled = true }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [customerId])

  // When role changes, recompute the recommended hire date
  useEffect(() => {
    if (!role || !customerId) return
    let cancelled = false
    api.recommendDate(customerId, role).then((r) => {
      if (cancelled) return
      setHireDate(r.hire_date)
      setDateSource(r.source)
    })
    return () => { cancelled = true }
  }, [customerId, role])

  const submit = () => {
    if (!role || !level || !location || !hireDate) return
    onSubmit({ role, level, location, hire_date: hireDate })
  }

  if (!options) {
    return <div className="text-slate-500">Loading customer options...</div>
  }

  return (
    <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm">
      <h2 className="text-base font-semibold text-slate-700 mb-4">Pay benchmark query</h2>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Field label="Role">
          <select value={role} onChange={(e) => setRole(e.target.value)} className={selectClass}>
            {options.roles.map((r) => <option key={r} value={r}>{r}</option>)}
          </select>
        </Field>
        <Field label="Level">
          <select value={level} onChange={(e) => setLevel(e.target.value)} className={selectClass}>
            {options.levels.map((l) => <option key={l} value={l}>{l}</option>)}
          </select>
        </Field>
        <Field label="Location">
          <select value={location} onChange={(e) => setLocation(e.target.value)} className={selectClass}>
            {options.locations.map((l) => <option key={l} value={l}>{l}</option>)}
          </select>
        </Field>
        <Field label="Hire date" hint={dateSource}>
          <input
            type="date"
            value={hireDate}
            onChange={(e) => setHireDate(e.target.value)}
            className={selectClass}
          />
        </Field>
      </div>
      <div className="mt-5 flex justify-end">
        <button
          onClick={submit}
          disabled={loading}
          className="bg-accent hover:bg-accent/90 disabled:bg-slate-300 disabled:cursor-not-allowed text-white font-medium px-5 py-2 rounded-lg text-sm transition-colors"
        >
          {loading ? 'Calculating...' : 'Get benchmark'}
        </button>
      </div>
    </div>
  )
}

const selectClass =
  "w-full border border-slate-300 rounded-lg px-3 py-2 text-sm bg-white hover:border-slate-400 focus:outline-none focus:ring-2 focus:ring-accent/30 focus:border-accent"

function Field({ label, hint, children }: { label: string; hint?: string; children: React.ReactNode }) {
  return (
    <div>
      <label className="block text-xs uppercase tracking-wide text-slate-500 mb-1.5">{label}</label>
      {children}
      {hint && <div className="mt-1 text-xs text-slate-400 italic">{hint}</div>}
    </div>
  )
}
