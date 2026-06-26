# TeamOhana Microsite — Frontend

Next.js + Tailwind + TypeScript. Calls the FastAPI backend over HTTPS.

## Local development

```bash
npm install

# Copy the env example and edit if needed (default points to localhost:8000)
cp .env.example .env.local

# Run dev server (port 3000)
npm run dev
```

Open http://localhost:3000. The backend needs to be running locally too (see ../backend/README.md).

## Deploy to Vercel

1. Push this folder's contents to a GitHub repo (or use Vercel CLI).
2. On Vercel: New Project → import from GitHub.
3. Set environment variable `NEXT_PUBLIC_API_URL` to your Render backend URL.
4. Vercel auto-detects Next.js. Click Deploy.

## Project structure

```
app/
├── page.tsx                     # main page composition
├── layout.tsx                   # root layout (fonts, body)
├── globals.css                  # Tailwind + Inter font
├── components/
│   ├── CustomerSelect.tsx       # "view as customer" dropdown
│   ├── QueryForm.tsx            # role/level/location/date inputs
│   ├── MarketResult.tsx         # predicted p25-p75 range
│   ├── BandComparison.tsx       # customer band vs market
│   ├── RecentHires.tsx          # recent hire details with market signal
│   └── CalibrationBanner.tsx    # honest-uncertainty messaging
└── lib/
    └── api.ts                   # typed backend client
```

## Configuring the backend URL

The frontend reads `NEXT_PUBLIC_API_URL` at build time. To change it:
- Local: edit `.env.local`
- Production: set in Vercel dashboard → Project Settings → Environment Variables
