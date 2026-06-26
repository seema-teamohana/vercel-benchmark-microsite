'use client'
import { MarketPrediction } from '../lib/api'

interface Props {
  market: MarketPrediction
  hireQuarter: string
}

export default function MarketResult({ market, hireQuarter }: Props) {
  // Abstained
  if (market.p25 === null || market.p75 === null) {
    return (
      <div className="bg-white border border-amber-200 rounded-xl p-6 shadow-sm">
        <Title>Market range</Title>
        <div className="mt-3 flex items-start gap-3 p-4 bg-amber-50 border border-amber-100 rounded-lg">
          <div className="text-amber-600 mt-0.5">
            <ExclamationIcon />
          </div>
          <div>
            <div className="font-medium text-amber-900">No reliable prediction available</div>
            <div className="text-sm text-amber-700 mt-1">{market.abstain_reason}</div>
          </div>
        </div>
      </div>
    )
  }

  const median = (market.p25 + market.p75) / 2
  const confColor =
    market.confidence === 'high'   ? 'text-emerald-600' :
    market.confidence === 'medium' ? 'text-amber-600' :
                                     'text-slate-500'

  return (
    <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm">
      <Title>Market range</Title>
      <div className="mt-2 text-sm text-slate-500">{hireQuarter}</div>

      <div className="mt-5 flex items-baseline gap-3">
        <span className="text-4xl font-semibold text-slate-900 tracking-tight">
          {formatUSD(market.p25)}
        </span>
        <span className="text-slate-400">—</span>
        <span className="text-4xl font-semibold text-slate-900 tracking-tight">
          {formatUSD(market.p75)}
        </span>
      </div>

      <div className="mt-1 text-sm text-slate-500">
        Median: <span className="font-medium text-slate-700">{formatUSD(median)}</span>
      </div>

      <div className="mt-5 pt-4 border-t border-slate-100 flex flex-wrap gap-4 text-sm">
        <Stat label="Comparable hires" value={market.support_n.toLocaleString()} />
        <Stat label="Confidence" value={
          <span className={confColor + ' font-medium capitalize'}>{market.confidence}</span>
        } />
        <Stat label="Match level" value={
          <span className="text-slate-700">{market.fallback_level.replace(/\+/g, ' + ')}</span>
        } />
      </div>
    </div>
  )
}

function Title({ children }: { children: React.ReactNode }) {
  return <h3 className="text-xs uppercase tracking-wider text-slate-500 font-semibold">{children}</h3>
}

function Stat({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div>
      <div className="text-xs uppercase tracking-wide text-slate-400">{label}</div>
      <div className="text-sm mt-0.5">{value}</div>
    </div>
  )
}

function formatUSD(n: number): string {
  return `$${Math.round(n / 1000)}K`
}

function ExclamationIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
      <path d="M10 1.667a8.333 8.333 0 100 16.666 8.333 8.333 0 000-16.666zm0 11.25a.833.833 0 110 1.666.833.833 0 010-1.666zm0-7.5a.833.833 0 01.833.833v5a.833.833 0 11-1.666 0v-5A.833.833 0 0110 5.417z"/>
    </svg>
  )
}
