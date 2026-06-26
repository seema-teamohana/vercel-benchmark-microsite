'use client'
import { RecentHire, MarketPrediction } from '../lib/api'

interface Props {
  hires: RecentHire[]
  market: MarketPrediction
}

export default function RecentHires({ hires, market }: Props) {
  if (hires.length === 0) {
    return (
      <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm">
        <h3 className="text-xs uppercase tracking-wider text-slate-500 font-semibold">Recent hires</h3>
        <div className="mt-4 text-slate-500 text-sm">
          No recent hires matching this combination.
        </div>
      </div>
    )
  }

  const canCompare = market.p25 !== null && market.p75 !== null

  return (
    <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm">
      <h3 className="text-xs uppercase tracking-wider text-slate-500 font-semibold">Recent hires</h3>
      <div className="mt-4 overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-xs uppercase tracking-wide text-slate-500 border-b border-slate-200">
              <th className="pb-2 pr-4 font-medium">Start date</th>
              <th className="pb-2 pr-4 font-medium">Role</th>
              <th className="pb-2 pr-4 font-medium">Level</th>
              <th className="pb-2 pr-4 font-medium">Location</th>
              <th className="pb-2 pr-4 font-medium text-right">Actual base</th>
              {canCompare && <th className="pb-2 font-medium">vs market</th>}
            </tr>
          </thead>
          <tbody>
            {hires.map((h, i) => (
              <tr key={i} className="border-b border-slate-100 last:border-0">
                <td className="py-3 pr-4 text-slate-600">{h.start_date || '—'}</td>
                <td className="py-3 pr-4 text-slate-800">{h.role}</td>
                <td className="py-3 pr-4 text-slate-600">{h.level}</td>
                <td className="py-3 pr-4 text-slate-600">{h.location}</td>
                <td className="py-3 pr-4 font-medium text-slate-900 text-right tabular-nums">
                  ${Math.round(h.actual_base).toLocaleString()}
                </td>
                {canCompare && (
                  <td className="py-3">
                    <MarketSignal actual={h.actual_base} p25={market.p25!} p75={market.p75!} />
                  </td>
                )}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

function MarketSignal({ actual, p25, p75 }: { actual: number; p25: number; p75: number }) {
  let label = 'In range'
  let cls = 'bg-emerald-50 text-emerald-700 ring-emerald-200'
  let dot = 'bg-emerald-500'
  if (actual > p75) {
    const pct = ((actual - p75) / p75 * 100).toFixed(0)
    label = `Above (+${pct}%)`
    cls = 'bg-rose-50 text-rose-700 ring-rose-200'
    dot = 'bg-rose-500'
  } else if (actual < p25) {
    const pct = ((p25 - actual) / p25 * 100).toFixed(0)
    label = `Below (-${pct}%)`
    cls = 'bg-amber-50 text-amber-700 ring-amber-200'
    dot = 'bg-amber-500'
  }
  return (
    <span className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-xs font-medium ring-1 ${cls}`}>
      <span className={`w-1.5 h-1.5 rounded-full ${dot}`} />
      {label}
    </span>
  )
}
