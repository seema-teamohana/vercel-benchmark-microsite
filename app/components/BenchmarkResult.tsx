'use client'

import { PredictionResponse } from '../lib/api'
import ConfidenceBadge from './ConfidenceBadge'

function fmtUSD(n: number | null): string {
  if (n === null || n === undefined) return '—'
  return '$' + Math.round(n).toLocaleString('en-US')
}

// Compact currency for the range bar labels (e.g. "$220K")
function fmtUSDCompact(n: number | null): string {
  if (n === null || n === undefined) return '—'
  if (n >= 1_000_000) return '$' + (n / 1_000_000).toFixed(1) + 'M'
  return '$' + Math.round(n / 1000) + 'K'
}

interface Props {
  result: PredictionResponse
}

export default function BenchmarkResult({ result }: Props) {
  const m = result.market

  // Abstain case: no prediction available.
  if (m.p50 === null || m.p50 === undefined) {
    return (
      <div className="rounded-lg border border-amber-200 bg-amber-50 p-6">
        <p className="text-sm font-medium text-amber-900">Benchmark not available</p>
        <p className="mt-2 text-sm text-amber-800">
          {m.abstain_reason || 'We do not have enough data for this combination.'}
        </p>
      </div>
    )
  }

  const p25 = m.p25!
  const p50 = m.p50!
  const p75 = m.p75!
  const p90 = m.p90!

  // Query context
  const q = result.query

  return (
    <div className="space-y-6">
      {/* Query summary */}
      <div className="flex flex-wrap items-center gap-2 text-sm text-slate-600">
        <span className="font-medium text-brand">{q.raw_role}</span>
        <span className="text-slate-300">·</span>
        <span>{q.raw_level}</span>
        <span className="text-slate-300">·</span>
        <span>{q.raw_location}</span>
        <span className="text-slate-300">·</span>
        <span>starting {q.hire_date}</span>
        <div className="ml-auto">
          <ConfidenceBadge confidence={m.confidence} supportN={m.support_n} />
        </div>
      </div>

      {/* Headline: p50 */}
      <div className="rounded-xl bg-white p-8 shadow-sm ring-1 ring-slate-200">
        <p className="text-xs uppercase tracking-wide text-slate-500 font-medium">
          Market median base salary
        </p>
        <p className="mt-2 text-5xl font-bold text-brand tracking-tight">
          {fmtUSD(p50)}
        </p>
        <p className="mt-1 text-sm text-slate-500">USD, annual</p>

        {/* Range bar: p25 → p75, with p90 shown as extended tick */}
        <div className="mt-8">
          <RangeBar p25={p25} p50={p50} p75={p75} p90={p90} />
        </div>

        {/* Quantile labels row below the bar */}
        <div className="mt-4 grid grid-cols-4 gap-3 text-center text-xs">
          <QuantileCell label="25th percentile" value={p25} />
          <QuantileCell label="Median (50th)" value={p50} highlight />
          <QuantileCell label="75th percentile" value={p75} />
          <QuantileCell label="90th percentile" value={p90} />
        </div>
      </div>

      {/* Offer distribution */}
      <OfferDistribution result={result} />

      {/* CTA */}
      <div className="rounded-xl bg-brand p-6 text-white">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <p className="text-sm font-semibold">Want a customized benchmark for your team?</p>
            <p className="mt-1 text-sm text-slate-300">
              Compare this benchmark against your company&apos;s bands, actual offers, and hiring pipeline.
            </p>
          </div>
          <a
            href="mailto:sales@teamohana.com?subject=Custom%20benchmark%20request"
            className="whitespace-nowrap rounded-md bg-accent px-4 py-2.5 text-sm font-semibold text-white hover:bg-accent-light transition"
          >
            Contact Sales →
          </a>
        </div>
      </div>
    </div>
  )
}

// Horizontal bar showing p25-p75 range as the "typical" band, with p50 marker
// and p90 as a lighter extension.
function RangeBar({ p25, p50, p75, p90 }: { p25: number; p50: number; p75: number; p90: number }) {
  // We visualise from p25 to p90. The p25-p75 area is the primary band.
  // p50 sits inside as a vertical marker.
  const min = p25
  const max = p90
  const span = max - min
  if (span <= 0) {
    // Degenerate case: all quantiles collapsed. Just show the number.
    return null
  }
  const p50Pos = ((p50 - min) / span) * 100
  const p75Pos = ((p75 - min) / span) * 100

  return (
    <div className="relative">
      {/* Full range bar (p25 to p90, lighter shade) */}
      <div className="relative h-3 rounded-full bg-slate-100 overflow-hidden">
        {/* Highlighted band: p25 to p75 (typical range) */}
        <div
          className="absolute inset-y-0 bg-accent/25"
          style={{ left: '0%', width: `${p75Pos}%` }}
        />
        {/* Extended band: p75 to p90 (tail) */}
        <div
          className="absolute inset-y-0 bg-accent/10"
          style={{ left: `${p75Pos}%`, width: `${100 - p75Pos}%` }}
        />
        {/* p50 marker */}
        <div
          className="absolute top-1/2 h-5 w-0.5 -translate-x-1/2 -translate-y-1/2 bg-brand"
          style={{ left: `${p50Pos}%` }}
        />
      </div>
      {/* Tick labels */}
      <div className="relative mt-2 text-[11px] font-medium text-slate-500">
        <span className="absolute left-0 -translate-x-1/2">{fmtUSDCompact(p25)}</span>
        <span
          className="absolute -translate-x-1/2 text-brand font-semibold"
          style={{ left: `${p50Pos}%` }}
        >
          {fmtUSDCompact(p50)}
        </span>
        <span
          className="absolute -translate-x-1/2"
          style={{ left: `${p75Pos}%` }}
        >
          {fmtUSDCompact(p75)}
        </span>
        <span className="absolute right-0 translate-x-1/2">{fmtUSDCompact(p90)}</span>
      </div>
    </div>
  )
}

function QuantileCell({ label, value, highlight }: { label: string; value: number; highlight?: boolean }) {
  return (
    <div className={`rounded-md px-2 py-2 ${highlight ? 'bg-slate-50' : ''}`}>
      <p className="text-slate-500">{label}</p>
      <p className={`mt-0.5 font-semibold ${highlight ? 'text-brand' : 'text-brand-light'}`}>
        {fmtUSDCompact(value)}
      </p>
    </div>
  )
}

// Historical offer distribution: for the same role/level/country, how many
// actual offers fell in each predicted band over the last 3 years.
function OfferDistribution({ result }: { result: PredictionResponse }) {
  const od = result.offer_distribution
  if (!od || od.n_total === 0) {
    return null
  }

  // Colors per band — soft, non-alarmist.
  const rangeColors: Record<string, string> = {
    'Below p25': 'bg-slate-300',
    'p25 – p50': 'bg-accent/60',
    'p50 – p75': 'bg-accent',
    'p75 – p90': 'bg-accent/60',
    'Above p90': 'bg-slate-300',
  }

  return (
    <div className="rounded-xl bg-white p-6 shadow-sm ring-1 ring-slate-200">
      <div className="flex items-baseline justify-between mb-1">
        <h3 className="text-sm font-semibold text-brand">
          How the last {od.n_total} actual offers fall in this range
        </h3>
        <span className="text-xs text-slate-500">Last {od.time_window_years} years</span>
      </div>
      <p className="mb-4 text-xs text-slate-500">
        This shows the actual distribution of hires — most companies land within the p25-p75 &quot;typical&quot; range.
      </p>

      <div className="space-y-2">
        {od.ranges.map((r) => (
          <div key={r.label} className="flex items-center gap-3">
            <span className="w-20 text-xs text-slate-600">{r.label}</span>
            <div className="flex-1 relative h-6 rounded bg-slate-50 overflow-hidden">
              <div
                className={`absolute inset-y-0 left-0 ${rangeColors[r.label] || 'bg-slate-300'} transition-all`}
                style={{ width: `${Math.max(2, r.pct)}%` }}
              />
            </div>
            <span className="w-16 text-right text-xs font-medium text-brand-light">
              {r.n} <span className="text-slate-400 font-normal">({r.pct.toFixed(0)}%)</span>
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}
