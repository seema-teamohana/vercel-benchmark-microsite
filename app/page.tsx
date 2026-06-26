'use client'

import { useEffect, useState } from 'react'
import { api, PredictionResponse } from './lib/api'
import CustomerSelect from './components/CustomerSelect'
import QueryForm from './components/QueryForm'
import MarketResult from './components/MarketResult'
import BandComparison from './components/BandComparison'
import RecentHires from './components/RecentHires'
import CalibrationBanner from './components/CalibrationBanner'

export default function Home() {
  const [customers, setCustomers] = useState<string[]>([])
  const [customerId, setCustomerId] = useState<string>('')
  const [result, setResult] = useState<PredictionResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Load customers on mount
  useEffect(() => {
    api.customers()
      .then(({ customers }) => {
        setCustomers(customers)
        if (customers.length > 0) setCustomerId(customers[0])
      })
      .catch((e) => setError(e.message))
  }, [])

  const onSubmit = async (q: { role: string; level: string; location: string; hire_date: string }) => {
    setLoading(true)
    setError(null)
    try {
      const r = await api.predict({ customer_id: customerId, ...q })
      setResult(r)
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : String(e)
      setError(msg)
      setResult(null)
    } finally {
      setLoading(false)
    }
  }

  const customerName = customerId ? customerId.charAt(0).toUpperCase() + customerId.slice(1) : ''

  return (
    <main className="max-w-6xl mx-auto px-6 py-10">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <div className="text-xs uppercase tracking-widest text-accent font-semibold">TeamOhana</div>
          <h1 className="text-2xl font-semibold text-slate-900 mt-1">Pay benchmark</h1>
          <p className="text-sm text-slate-500 mt-1">
            Compare market range, company band, and recent hires
          </p>
        </div>
        {customers.length > 0 && (
          <CustomerSelect
            customers={customers}
            selected={customerId}
            onSelect={(id) => { setCustomerId(id); setResult(null) }}
          />
        )}
      </div>

      {/* Query form */}
      {customerId && (
        <QueryForm
          customerId={customerId}
          onSubmit={onSubmit}
          loading={loading}
        />
      )}

      {/* Error */}
      {error && (
        <div className="mt-6 bg-rose-50 border border-rose-200 rounded-xl p-4 text-sm text-rose-800">
          {error}
        </div>
      )}

      {/* Results */}
      {result && (
        <div className="mt-8 space-y-6">
          <CalibrationBanner
            payCalibration={result.pay_calibration}
            customerCalibration={result.calibration}
          />

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <MarketResult market={result.market} hireQuarter={result.query.hire_quarter} />
            <BandComparison
              band={result.company_band}
              comparison={result.comparison}
              customerName={customerName}
            />
          </div>

          <RecentHires hires={result.recent_hires} market={result.market} />
        </div>
      )}
    </main>
  )
}
