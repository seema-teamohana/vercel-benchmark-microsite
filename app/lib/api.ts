// API client. Backend URL is configured via NEXT_PUBLIC_API_URL.
// In development, set it to http://localhost:8000 in .env.local.
// In production (Vercel), set it to the Render URL.

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export type Customer = string

export interface CustomerOptions {
  roles: string[]
  levels: string[]
  locations: string[]
}

export interface RecommendedDate {
  hire_date: string
  ttf_days: number
  source: string
}

export interface PredictionRequest {
  customer_id: string
  role: string
  level: string
  location: string
  hire_date: string  // YYYY-MM-DD
}

export interface MarketPrediction {
  p25: number | null
  p75: number | null
  currency: string
  support_n: number
  fallback_level: string
  confidence: 'high' | 'medium' | 'low' | string
  abstain_reason: string | null
}

export interface CompanyBand {
  low: number
  mid: number | null
  high: number
  currency: string
  n_rows: number
}

export interface Comparison {
  band_vs_market_pct: number
  signal: 'in_line' | 'above_market' | 'below_market'
}

export interface RecentHire {
  role: string
  level: string
  location: string
  actual_base: number
  currency: string
  start_date: string | null
  time_to_fill: number | null
}

export interface PayCalibration {
  status: 'calibrated' | 'uncalibrated' | 'no_data' | 'no_training_data'
  deviation_pct: number | null
  customer_median: number | null
  training_median: number | null
  message: string
}

export interface CalibrationNote {
  confidence_tier: 'high' | 'medium' | 'low' | 'unknown'
  coverage_pct: number | null
  note: string
}

export interface PredictionResponse {
  query: {
    customer_id: string
    raw_role: string
    raw_level: string
    raw_location: string
    hire_date: string
    hire_quarter: string
    canonical: Record<string, unknown>
  }
  market: MarketPrediction
  pay_calibration: PayCalibration
  company_band: CompanyBand | null
  comparison: Comparison | null
  recent_hires: RecentHire[]
  calibration: CalibrationNote
}

async function get<T>(path: string): Promise<T> {
  const r = await fetch(`${API_URL}${path}`)
  if (!r.ok) throw new Error(`${r.status}: ${await r.text()}`)
  return r.json() as Promise<T>
}

async function post<T>(path: string, body: unknown): Promise<T> {
  const r = await fetch(`${API_URL}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!r.ok) throw new Error(`${r.status}: ${await r.text()}`)
  return r.json() as Promise<T>
}

export const api = {
  customers: () => get<{ customers: Customer[] }>('/customers'),
  customerOptions: (id: string) => get<CustomerOptions>(`/customer/${id}/options`),
  recommendDate: (id: string, role: string) =>
    get<RecommendedDate>(`/recommend-date?customer_id=${encodeURIComponent(id)}&role=${encodeURIComponent(role)}`),
  predict: (req: PredictionRequest) => post<PredictionResponse>('/predict', req),
}
