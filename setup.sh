#!/usr/bin/env bash
set -e

BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}==========================================${NC}"
echo -e "${BLUE}   Politikerapp — Oppsett               ${NC}"
echo -e "${BLUE}==========================================${NC}"
echo ""

# 1. Sjekk Python
echo -e "${YELLOW}1. Sjekker Python...${NC}"
if ! command -v python3 &>/dev/null; then
  echo -e "${RED}FEIL: Python 3 er ikke installert.${NC}"
  echo "  Installer fra https://www.python.org/ eller via brew: brew install python"
  exit 1
fi

PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 11 ]); then
  echo -e "${RED}FEIL: Python 3.11+ kreves. Du har Python $PYTHON_VERSION.${NC}"
  echo "  Installer nyere versjon: brew install python@3.11"
  exit 1
fi
echo -e "${GREEN}  Python $PYTHON_VERSION — OK${NC}"

# 2. Sjekk Node
echo -e "${YELLOW}2. Sjekker Node.js...${NC}"
if ! command -v node &>/dev/null; then
  echo -e "${RED}FEIL: Node.js er ikke installert.${NC}"
  echo "  Installer fra https://nodejs.org/ eller via brew: brew install node"
  exit 1
fi

NODE_VERSION=$(node --version | sed 's/v//')
NODE_MAJOR=$(echo $NODE_VERSION | cut -d. -f1)

if [ "$NODE_MAJOR" -lt 18 ]; then
  echo -e "${RED}FEIL: Node.js 18+ kreves. Du har Node $NODE_VERSION.${NC}"
  exit 1
fi
echo -e "${GREEN}  Node.js $NODE_VERSION — OK${NC}"

if ! command -v npm &>/dev/null; then
  echo -e "${RED}FEIL: npm er ikke installert.${NC}"
  exit 1
fi
echo -e "${GREEN}  npm $(npm --version) — OK${NC}"

# 3. Lag mappe-struktur
echo -e "${YELLOW}3. Oppretter mappestruktur...${NC}"
mkdir -p ~/.politikerapp/{data,logs,uploads,cache}
echo -e "${GREEN}  ~/.politikerapp/ opprettet${NC}"

# 4. Lag .env fil
if [ ! -f ~/.politikerapp/.env ]; then
  cat > ~/.politikerapp/.env << 'EOF'
ANTHROPIC_API_KEY=
PORTAL_URL=
USER_NAME=
PARTY=Høyre
EOF
  echo -e "${GREEN}  ~/.politikerapp/.env opprettet${NC}"
else
  echo -e "${GREEN}  ~/.politikerapp/.env finnes allerede${NC}"
fi

# 5. Sett opp Python venv
echo -e "${YELLOW}4. Setter opp Python-miljø...${NC}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

cd "$SCRIPT_DIR/backend"

if [ ! -d ".venv" ]; then
  python3 -m venv .venv
  echo -e "${GREEN}  Python venv opprettet${NC}"
fi

source .venv/bin/activate
echo -e "${GREEN}  Aktiverte Python venv${NC}"

echo -e "${YELLOW}  Installerer Python-pakker (dette kan ta noen minutter)...${NC}"
pip install --upgrade pip -q
pip install -r requirements.txt -q
echo -e "${GREEN}  Python-pakker installert${NC}"

# 6. Playwright
echo -e "${YELLOW}5. Installerer Playwright nettleser...${NC}"
python -m playwright install chromium
echo -e "${GREEN}  Playwright Chromium installert${NC}"

# 7. Node dependencies
echo -e "${YELLOW}6. Installerer Node-pakker...${NC}"
cd "$SCRIPT_DIR/frontend"
npm install --silent
echo -e "${GREEN}  Node-pakker installert${NC}"

# 8. Initialiser database
echo -e "${YELLOW}7. Initialiserer database...${NC}"
cd "$SCRIPT_DIR/backend"
source .venv/bin/activate
python database.py
echo -e "${GREEN}  Database initialisert: ~/.politikerapp/data/documents.db${NC}"

# 9. Lag start.sh
echo -e "${YELLOW}8. Lager start.sh...${NC}"
cat > "$SCRIPT_DIR/start.sh" << STARTSH
#!/usr/bin/env bash
SCRIPT_DIR="\$(cd "\$(dirname "\${BASH_SOURCE[0]}")" && pwd)"

echo "Starter Politikerapp..."
echo "  Backend:  http://localhost:8000"
echo "  Frontend: http://localhost:3000"
echo ""
echo "Trykk Ctrl+C for å stoppe."
echo ""

# Start backend
cd "\$SCRIPT_DIR/backend"
source .venv/bin/activate
uvicorn main:app --host 127.0.0.1 --port 8000 --reload &
BACKEND_PID=\$!

# Start frontend
cd "\$SCRIPT_DIR/frontend"
npm run dev &
FRONTEND_PID=\$!

# Vent og rydd opp ved Ctrl+C
trap "kill \$BACKEND_PID \$FRONTEND_PID 2>/dev/null; exit" INT TERM
wait
STARTSH
chmod +x "$SCRIPT_DIR/start.sh"
echo -e "${GREEN}  start.sh opprettet${NC}"

# Done
echo ""
echo -e "${GREEN}==========================================${NC}"
echo -e "${GREEN}   Oppsett fullført!                     ${NC}"
echo -e "${GREEN}==========================================${NC}"
echo ""
echo -e "${YELLOW}Viktig: Du må legge til Anthropic API-nøkkel!${NC}"
echo ""
echo "  1. Gå til: https://console.anthropic.com/settings/keys"
echo "  2. Klikk 'Create Key' og kopier nøkkelen"
echo "  3. Åpne appen og gå til Innstillinger, eller rediger:"
echo "     ~/.politikerapp/.env"
echo "     Sett: ANTHROPIC_API_KEY=sk-ant-..."
echo ""
echo -e "${BLUE}Start appen med:${NC}"
echo "  bash start.sh"
echo ""
echo "  Åpne: http://localhost:3000"
echo ""
