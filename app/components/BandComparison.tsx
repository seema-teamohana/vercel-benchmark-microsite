'use client'
import { CompanyBand, Comparison } from '../lib/api'

interface Props {
  band: CompanyBand | null
  comparison: Comparison | null
  customerName: string
}

export default function BandComparison({ band, comparison, customerName }: Props) {
  if (!band) {
    return (
      <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm">
        <h3 className="text-xs uppercase tracking-wider text-slate-500 font-semibold">
          {customerName} band
        </h3>
        <div className="mt-4 text-slate-500 text-sm">
          No approved band found for this role at {customerName}.
        </div>
      </div>
    )
  }

  const sigConfig = comparison ? signalConfig(comparison.signal) : null

  return (
    <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm">
      <h3 className="text-xs uppercase tracking-wider text-slate-500 font-semibold">
        {customerName} band
      </h3>
      <div className="mt-5 flex items-baseline gap-3">
        <span className="text-4xl font-semibold text-slate-900 tracking-tight">
          {formatUSD(band.low)}
        </span>
        <span className="text-slate-400">—</span>
        <span className="text-4xl font-semibold text-slate-900 tracking-tight">
          {formatUSD(band.high)}
        </span>
      </div>
      {band.mid && (
        <div className="mt-1 text-sm text-slate-500">
          Mid: <span className="font-medium text-slate-700">{formatUSD(band.mid)}</span>
        </div>
      )}

      {comparison && sigConfig && (
        <div className={`mt-5 pt-4 border-t border-slate-100 flex items-center gap-3`}>
          <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium ${sigConfig.pill}`}>
            <span className={sigConfig.dot} />
            {sigConfig.label}
          </span>
          <span className="text-sm text-slate-600">
            {Math.abs(comparison.band_vs_market_pct).toFixed(1)}% vs market
          </span>
        </div>
      )}
    </div>
  )
}

function signalConfig(signal: string) {
  if (signal === 'above_market') return {
    label: 'Above market',
    pill: 'bg-rose-50 text-rose-700 ring-1 ring-rose-200',
    dot: 'w-1.5 h-1.5 rounded-full bg-rose-500',
  }
  if (signal === 'below_market') return {
    label: 'Below market',
    pill: 'bg-amber-50 text-amber-700 ring-1 ring-amber-200',
    dot: 'w-1.5 h-1.5 rounded-full bg-amber-500',
  }
  return {
    label: 'In line with market',
    pill: 'bg-emerald-50 text-emerald-700 ring-1 ring-emerald-200',
    dot: 'w-1.5 h-1.5 rounded-full bg-emerald-500',
  }
}

function formatUSD(n: number): string {
  return `$${Math.round(n / 1000)}K`
}
