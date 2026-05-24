# Politikerapp — AI-assistent for kommunepolitikere

En lokal, sikker AI-assistent for Høyre-politikere som hjelper med å lese, analysere
og produsere innhold basert på kommunale saksdokumenter.

## Funksjoner

- **Dokumentbibliotek** — Last opp PDF-er eller skrap automatisk fra ACOS Møteportal
- **AI-oppsummering** — Streaming-oppsummering med justerbar lengde
- **Taler og leserinnlegg** — Generer politisk innhold med tone- og lengde-sliders
- **Berikelse** — Hent lover, nyheter, andre kommuners vedtak, budsjettdata og forskning
- **Politisk hukommelse** — Lagre din skrivestil og politiske standpunkter
- **Semantisk søk** — Finn relevante saker på tvers av alle dokumenter

All data lagres lokalt på din Mac. Ingenting sendes til skyen unntatt API-kall til Anthropic.

## Krav

- Python 3.11+
- Node.js 18+
- Anthropic API-nøkkel (fra [console.anthropic.com](https://console.anthropic.com/settings/keys))

## Kom i gang

```bash
# 1. Klon repoet
git clone <repo-url>
cd Politiccing

# 2. Kjør oppsett (én gang)
bash setup.sh

# 3. Legg til API-nøkkel
#    Enten via Innstillinger-siden i appen, eller:
nano ~/.politikerapp/.env
#    Sett: ANTHROPIC_API_KEY=sk-ant-...

# 4. Start appen
bash start.sh

# 5. Åpne i nettleser
#    http://localhost:3000
```

## Mappestruktur

```
Politiccing/
├── frontend/          React + Tailwind + shadcn/ui (port 3000)
├── backend/           Python + FastAPI (port 8000)
├── setup.sh           Oppsett-skript (kjør én gang)
├── start.sh           Start begge tjenestene
└── README.md

Lokal datalagring:
~/.politikerapp/
├── .env               API-nøkkel og innstillinger
├── data/
│   └── documents.db   SQLite-database
├── logs/              API-logg og app-logg
└── uploads/           Opplastede og skrapede PDF-er
```

## Bruk

### Last opp dokumenter
Klikk "Last opp PDF" og dra inn et kommunalt saksdokument.
AI-en ekstraherer automatisk tittel, dato, utvalg og dokumenttype.

### Skrap fra ACOS Møteportal
1. Klikk "Skrap møteportal" og skriv inn portal-URL
2. En nettleser åpnes — logg inn med BankID manuelt
3. Klikk "Fortsett" i appen
4. Alle tilgjengelige dokumenter lastes ned og analyseres automatisk

### Generer tale eller leserinnlegg
1. Åpne et dokument
2. Velg fanen "Tale" eller "Leserinnlegg"
3. Juster lengde- og tone-slider
4. Klikk "Generer"
5. Rediger teksten og lagre som stileksempel

### Politisk hukommelse
Gå til "Kontekst og hukommelse" for å:
- Lagre eksempler på din skrivestil
- Registrere politiske standpunkter (brukes automatisk i generering)
- Søke semantisk på tvers av alle dokumenter

## Teknisk informasjon

| Komponent | Teknologi |
|-----------|-----------|
| Frontend | React 18 + TypeScript + Tailwind CSS |
| Backend | Python + FastAPI |
| Database | SQLite + sqlite-vec |
| AI-modell | claude-sonnet-4-20250514 |
| Embeddings | intfloat/multilingual-e5-large |
| PDF-parsing | PyMuPDF |
| Browser-automasjon | Playwright |

## Personvern

- Alle dokumenter lagres kun lokalt i `~/politikerapp/`
- API-nøkkelen lagres i `~/.politikerapp/.env` og sendes kun til Anthropic
- Ingen data deles med tredjeparter

## Feilsøking

**Backend starter ikke:**
```bash
cd backend
source .venv/bin/activate
pip install -r requirements.txt
python database.py
```

**Embeddings-modell mangler:**
Første gang du bruker semantisk søk lastes modellen ned automatisk (~1.5 GB).
Dette kan ta noen minutter.

**Playwright finner ikke nettleser:**
```bash
cd backend
source .venv/bin/activate
python -m playwright install chromium
```
