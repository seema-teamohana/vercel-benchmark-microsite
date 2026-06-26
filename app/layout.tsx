import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'TeamOhana — Salary Benchmark',
  description: 'Market benchmark, company band, recent hires',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className="min-h-screen">{children}</body>
    </html>
  )
}
