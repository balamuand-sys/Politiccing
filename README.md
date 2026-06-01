# Politikerapp — AI-assistent for kommunepolitikere

En AI-assistent for Høyre-politikere som hjelper med å lese, analysere
og produsere innhold basert på kommunale saksdokumenter.

**Stack:** React + FastAPI (Vercel serverless) + Supabase (PostgreSQL + pgvector + Storage)

## Funksjoner

- **Dokumentbibliotek** — Last opp PDF-er, søk semantisk på norsk
- **AI-oppsummering** — Streaming med justerbar lengde
- **Taler og leserinnlegg** — Lengde- og tone-sliders, Høyre-perspektiv
- **Berikelse** — Hent lover, nyheter, andre kommuners vedtak, budsjettdata, forskning
- **Politisk hukommelse** — Skrivestil-eksempler og politiske standpunkter

## Oppsett

### 1. Supabase

1. Åpne [Supabase SQL Editor](https://supabase.com/dashboard) for prosjektet ditt
2. Kjør hele innholdet i `supabase/migration.sql`
3. Gå til **Storage** → Opprett ny bucket `pol-documents` (privat)
4. Kopier:
   - **Project URL** (`Settings → API → Project URL`)
   - **service_role key** (`Settings → API → Project API keys → service_role`)

### 2. API-nøkler du trenger

| Nøkkel | Hvor du får den |
|--------|-----------------|
| `ANTHROPIC_API_KEY` | [console.anthropic.com](https://console.anthropic.com/settings/keys) |
| `VOYAGE_API_KEY` | [app.voyageai.com](https://www.voyageai.com) (gratis tier) |
| `SUPABASE_URL` | Supabase → Settings → API |
| `SUPABASE_SERVICE_ROLE_KEY` | Supabase → Settings → API |

### 3. Vercel

1. Importer dette repoet på [vercel.com/new](https://vercel.com/new)
2. Gå til **Settings → Environment Variables** og legg til alle 4 nøkler
3. Klikk **Redeploy**

Appen er nå live! Gå til Innstillinger-siden og klikk "Test Anthropic-tilkobling" for å verifisere.

## Mappestruktur

```
Politiccing/
├── api/                    FastAPI serverless (Vercel Python)
│   ├── index.py            Entry point
│   ├── requirements.txt    Python-avhengigheter
│   ├── database.py         Supabase-klient
│   ├── models.py           Pydantic-modeller
│   ├── routers/            7 API-rutere
│   └── services/           Claude, Voyage AI, PDF, kontekstbygging
├── frontend/               React 18 + TypeScript + Tailwind CSS
│   └── src/
│       ├── pages/          4 sider
│       └── components/     AI, dokumenter, layout
├── supabase/
│   └── migration.sql       Kjør dette i Supabase SQL Editor
└── vercel.json             Vercel-konfigurasjon
```

## Lokal utvikling

```bash
# Backend
cd api
pip install -r requirements.txt
# Sett env vars i .env og kjør:
uvicorn index:app --port 8000 --reload

# Frontend (separat terminal)
cd frontend
npm install
npm run dev
# Åpne http://localhost:3000
```

## Teknisk informasjon

| Komponent | Teknologi |
|-----------|-----------|
| Frontend | React 18 + TypeScript + Tailwind CSS |
| Backend | Python + FastAPI (Vercel serverless) |
| Database | Supabase PostgreSQL + pgvector |
| AI-modell | claude-sonnet-4-20250514 |
| Embeddings | Voyage AI voyage-multilingual-2 (1024-dim, norsk) |
| PDF-parsing | PyMuPDF |
| Fillagring | Supabase Storage |
