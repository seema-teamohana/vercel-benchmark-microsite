'use client'
import { CalibrationNote, PayCalibration } from '../lib/api'

interface Props {
  payCalibration: PayCalibration
  customerCalibration: CalibrationNote
}

export default function CalibrationBanner({ payCalibration, customerCalibration }: Props) {
  // Highest-priority message: uncalibrated for this query
  if (payCalibration.status === 'uncalibrated') {
    return (
      <div className="bg-rose-50 border border-rose-200 rounded-xl p-4 flex items-start gap-3">
        <div className="text-rose-600 mt-0.5"><WarningIcon /></div>
        <div className="text-sm">
          <div className="font-medium text-rose-900">Not reliable for this role</div>
          <div className="text-rose-700 mt-1">{payCalibration.message}</div>
          {payCalibration.customer_median && payCalibration.training_median && (
            <div className="text-rose-600 text-xs mt-2">
              Your typical pay: ${Math.round(payCalibration.customer_median / 1000)}K&nbsp;·&nbsp;
              Training median: ${Math.round(payCalibration.training_median / 1000)}K
            </div>
          )}
        </div>
      </div>
    )
  }

  // Customer-level coverage warning
  if (customerCalibration.confidence_tier === 'low') {
    return (
      <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 flex items-start gap-3">
        <div className="text-amber-600 mt-0.5"><InfoIcon /></div>
        <div className="text-sm">
          <div className="font-medium text-amber-900">Treat as directional</div>
          <div className="text-amber-700 mt-1">{customerCalibration.note}</div>
        </div>
      </div>
    )
  }

  if (customerCalibration.confidence_tier === 'unknown') {
    return (
      <div className="bg-slate-50 border border-slate-200 rounded-xl p-4 flex items-start gap-3">
        <div className="text-slate-500 mt-0.5"><InfoIcon /></div>
        <div className="text-sm text-slate-700">{customerCalibration.note}</div>
      </div>
    )
  }

  // Soft note when calibrated but no_data for this specific query
  if (payCalibration.status === 'no_data') {
    return (
      <div className="bg-slate-50 border border-slate-200 rounded-xl p-3 text-xs text-slate-600 italic">
        {payCalibration.message} Prediction is based on cross-customer market patterns.
      </div>
    )
  }

  // Calibrated + medium/high confidence — no banner needed
  return null
}

function WarningIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
      <path d="M9.4 1.7a1 1 0 011.2 0c.3.2.5.4.6.7l8 13.6c.2.3.2.7.2 1s-.2.7-.4 1c-.2.2-.5.4-.8.5-.3.1-.6.2-1 .2H2.8c-.3 0-.7-.1-1-.2a2 2 0 01-.8-.5c-.2-.3-.4-.6-.4-1s0-.7.2-1l8-13.6c.1-.3.3-.5.6-.7zM10 7.5a.8.8 0 00-.8.8v3.4a.8.8 0 001.6 0V8.3a.8.8 0 00-.8-.8zm0 7.5a.8.8 0 100 1.7.8.8 0 000-1.7z"/>
    </svg>
  )
}

function InfoIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
      <path d="M10 1.7a8.3 8.3 0 100 16.6 8.3 8.3 0 000-16.6zm0 12.5a.8.8 0 110 1.7.8.8 0 010-1.7zm0-8.4a.8.8 0 01.8.8v5a.8.8 0 01-1.6 0v-5a.8.8 0 01.8-.8z"/>
    </svg>
  )
}
