// Small pill showing prediction confidence. Uses training-data support count
// to categorize: >= 20 rows = high, 5-19 = medium, < 5 = low (should not happen
// in the UI since dropdowns are filtered to >= 5).

interface Props {
  confidence: string
  supportN: number
}

export default function ConfidenceBadge({ confidence, supportN }: Props) {
  const styles: Record<string, string> = {
    high:   'bg-emerald-50 text-emerald-800 ring-emerald-200',
    medium: 'bg-amber-50 text-amber-800 ring-amber-200',
    low:    'bg-slate-100 text-slate-700 ring-slate-200',
  }
  const cls = styles[confidence] || styles.low

  const labels: Record<string, string> = {
    high:   'High confidence',
    medium: 'Medium confidence',
    low:    'Low confidence',
  }
  const label = labels[confidence] || 'Confidence unknown'

  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium ring-1 ring-inset ${cls}`}>
      <span className="h-1.5 w-1.5 rounded-full bg-current opacity-80" />
      {label}
      <span className="text-slate-500 font-normal">· {supportN.toLocaleString()} data points</span>
    </span>
  )
}
