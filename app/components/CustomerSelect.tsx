'use client'

interface Props {
  customers: string[]
  selected: string
  onSelect: (id: string) => void
}

export default function CustomerSelect({ customers, selected, onSelect }: Props) {
  return (
    <div className="flex items-center gap-3">
      <label className="text-sm text-slate-500 uppercase tracking-wide">View as</label>
      <select
        value={selected}
        onChange={(e) => onSelect(e.target.value)}
        className="border border-slate-300 rounded-lg px-3 py-1.5 text-sm bg-white hover:border-slate-400 focus:outline-none focus:ring-2 focus:ring-accent/30 focus:border-accent"
      >
        {customers.map((c) => (
          <option key={c} value={c}>{c.charAt(0).toUpperCase() + c.slice(1)}</option>
        ))}
      </select>
    </div>
  )
}
