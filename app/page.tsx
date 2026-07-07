'use client'

import { useEffect, useState } from 'react'
import { api, ReferenceResponse, PredictionResponse } from './lib/api'
import BenchmarkForm from './components/BenchmarkForm'
import BenchmarkResult from './components/BenchmarkResult'

export default function Home() {
  const [reference, setReference] = useState<ReferenceResponse | null>(null)
  const [refError, setRefError] = useState<string | null>(null)

  const [result, setResult] = useState<PredictionResponse | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [submitError, setSubmitError] = useState<string | null>(null)

  // Load reference (roles + countries + available combinations) once on mount.
  useEffect(() => {
    api.reference()
      .then((r) => setReference(r))
      .catch((e) => setRefError(e.message))
  }, [])

  async function handleSubmit(payload: { role: string; level: string; location: string; hire_date: string }) {
    setIsSubmitting(true)
    setSubmitError(null)
    setResult(null)
    try {
      const r = await api.predict(payload)
      setResult(r)
    } catch (e) {
      setSubmitError(e instanceof Error ? e.message : 'Something went wrong')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <main className="min-h-screen">
      {/* Header */}
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto max-w-4xl px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-lg font-bold text-brand tracking-tight">TeamOhana</span>
            <span className="text-slate-300">·</span>
            <span className="text-sm text-slate-600">Tech Comp Benchmark</span>
          </div>
          <a
            href="https://www.teamohana.com"
            target="_blank"
            rel="noopener noreferrer"
            className="text-sm text-slate-600 hover:text-brand"
          >
            teamohana.com →
          </a>
        </div>
      </header>

      <div className="mx-auto max-w-4xl px-6 py-10">
        {/* Hero */}
        <section className="mb-10">
          <h1 className="text-3xl sm:text-4xl font-bold text-brand tracking-tight">
            Free market benchmarks for tech &amp; sales roles
          </h1>
          <p className="mt-3 text-slate-600 max-w-2xl">
            Real hire data from 30+ high-growth companies. Pick a role, level, and country
            to see the market range and how actual offers distribute across it.
          </p>
        </section>

        {/* Form */}
        <section className="rounded-xl bg-white p-6 sm:p-8 shadow-sm ring-1 ring-slate-200">
          {refError && (
            <div className="rounded-md bg-red-50 p-4 text-sm text-red-800 mb-6">
              Couldn&apos;t load benchmark options: {refError}. Please try refreshing.
            </div>
          )}
          {!reference && !refError && (
            <div className="text-sm text-slate-500">Loading…</div>
          )}
          {reference && (
            <BenchmarkForm
              reference={reference}
              onSubmit={handleSubmit}
              isSubmitting={isSubmitting}
            />
          )}
        </section>

        {/* Errors + results */}
        {submitError && (
          <div className="mt-8 rounded-md bg-red-50 p-4 text-sm text-red-800">
            {submitError}
          </div>
        )}

        {result && (
          <section className="mt-8">
            <BenchmarkResult result={result} />
          </section>
        )}

        {/* Methodology note */}
        <section className="mt-12 text-xs text-slate-500 border-t border-slate-200 pt-6">
          <p className="mb-1"><strong>How this works:</strong> Predictions come from a quantile regression model
            trained on real hire data from 30+ high-growth tech companies. We show a market range
            (25th to 90th percentile) and a &quot;typical&quot; band (25th to 75th).</p>
          <p>Data updated periodically. Individual offers vary based on candidate specifics, equity, and cash-vs-equity mix.
            For a customized benchmark for your team, <a href="mailto:sales@teamohana.com" className="text-accent underline">contact us</a>.</p>
        </section>
      </div>
    </main>
  )
}
