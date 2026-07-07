# TeamOhana Public Salary Benchmark — Frontend

Next.js + Tailwind microsite for the public salary benchmark. Public-facing lead-gen page — no auth, no customer selector.

## Local development

```bash
# Install
npm install

# Point at a local backend (or the Render URL)
cp .env.example .env.local
# Edit .env.local: NEXT_PUBLIC_API_URL=http://localhost:8000

# Run
npm run dev
```

Open http://localhost:3000.

## Deployment to Vercel

1. Push this folder to a GitHub repo.
2. On Vercel: New Project → import the repo.
3. Set environment variable in Vercel dashboard: `NEXT_PUBLIC_API_URL` = your Render backend URL (e.g. `https://teamohana-pay-benchmark.onrender.com`).
   - **Important:** uncheck the "Sensitive" toggle so the value is baked into the client build.
4. Deploy. Vercel auto-detects Next.js from `vercel.json`.

If the API URL changes, update the env var and trigger a redeploy (without cache) — the URL is baked at build time.

## Structure

```
app/
├── layout.tsx              — HTML shell + Inter font
├── page.tsx                — main page (form + result)
├── globals.css             — Tailwind base
├── lib/
│   └── api.ts              — typed API client
└── components/
    ├── BenchmarkForm.tsx   — cascading role → country → level dropdowns
    ├── BenchmarkResult.tsx — quantile range bar + offer distribution + CTA
    └── ConfidenceBadge.tsx — confidence pill (high / medium / low)
```

## How the cascading dropdowns work

The backend's `/reference` endpoint returns an `available_combinations` map:

```
{
  "Software Engineering": {
    "US": { "IC1": 71, "IC2": 201, "IC3": 312, ... },
    "UK": { "IC3": 21, "IC4": 48, ... }
  },
  ...
}
```

The form filters options as the user picks:
1. Role dropdown shows all keys of `available_combinations`.
2. Country dropdown shows only countries under the selected role.
3. Level dropdown shows only levels under the selected role + country.

This means every combination the user can submit has at least 5 rows of training-data support. No dead-ends.

## Notes

- Rate limit: 10 requests/minute per IP (enforced by backend). Frontend surfaces a friendly error on 429.
- The hire-date default is today + 60 days (typical planning horizon).
- CTA below results is `mailto:sales@teamohana.com`.
