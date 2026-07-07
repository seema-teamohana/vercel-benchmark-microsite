// API client for the TeamOhana public salary benchmark v2 backend.
// Backend URL comes from NEXT_PUBLIC_API_URL.
//   - Local dev: http://localhost:8000
//   - Vercel prod: https://teamohana-pay-benchmark.onrender.com

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

// GET /reference — dropdown options for the microsite.
// available_combinations is a nested map: role → country → { level: rowCount }.
// The frontend uses it for cascading dropdowns so the user only sees combinations
// with sufficient training-data support (>= 5 rows).
export interface ReferenceResponse {
  roles: string[]
  countries: string[]
  available_combinations: {
    [role: string]: {
      [country: string]: {
        [level: string]: number
      }
    }
  }
}

// POST /predict request
export interface PredictionRequest {
  role: string
  level: string
  location: string
  hire_date: string  // YYYY-MM-DD
}

// POST /predict response
export interface MarketPrediction {
  p25: number | null
  p50: number | null
  p75: number | null
  p90: number | null
  currency: string
  support_n: number
  fallback_level: string
  confidence: 'high' | 'medium' | 'low' | string
  raw_level_used: string | null
  abstain_reason: string | null
}

export interface OfferRange {
  label: string
  n: number
  pct: number
}

export interface OfferDistribution {
  n_total: number
  match_level: string
  time_window_years: number
  ranges: OfferRange[]
}

export interface PredictionResponse {
  query: {
    raw_role: string
    raw_level: string
    raw_location: string
    hire_date: string
    hire_quarter: string
    canonical: Record<string, unknown>
  }
  market: MarketPrediction
  offer_distribution: OfferDistribution
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
  if (!r.ok) {
    // Rate-limit case returns 429 with a helpful body
    if (r.status === 429) {
      throw new Error('You have hit the rate limit (10 requests per minute). Please wait a moment and try again.')
    }
    throw new Error(`${r.status}: ${await r.text()}`)
  }
  return r.json() as Promise<T>
}

export const api = {
  reference: () => get<ReferenceResponse>('/reference'),
  predict: (req: PredictionRequest) => post<PredictionResponse>('/predict', req),
}
