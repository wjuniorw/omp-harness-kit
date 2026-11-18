#!/usr/bin/env bash
set -euo pipefail

KIT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OMP_AGENT_DIR="$HOME/.omp/agent"
GLOBAL_SKILLS_DIR="$HOME/.agents/skills"
CLAUDE_CMD_DIR="$HOME/.claude/commands"

echo "=== OMP Harness Kit — Instalador ==="

# Escolha de modo (env ou prompt interativo)
MODE="${OMP_MODE:-}"
if [[ -z "$MODE" ]]; then
  echo "Escolha o endpoint do gateway LLM:"
  echo "  1) Sigapro Gateway (https://ai.sigapro.com/v1)"
  echo "  2) OmniRoute Local (http://localhost:20128/v1)"
  read -r -p "Opcao [1/2]: " CHOICE
  if [[ "$CHOICE" == "2" ]]; then
    MODE="local"
  else
    MODE="sigapro"
  fi
fi

if [[ -z "${OMP_GATEWAY_URL:-}" ]]; then
  if [[ "$MODE" == "local" ]]; then
    OMP_GATEWAY_URL="http://localhost:20128/v1"
  else
    OMP_GATEWAY_URL="https://ai.sigapro.com/v1"
  fi
fi

if [[ -z "${OMP_API_KEY:-}" ]]; then
  read -r -s -p "Cole sua API Key do OmniRoute/Gateway (nao sera exibida): " OMP_API_KEY
  echo ""
fi

if [[ -z "$OMP_API_KEY" ]]; then
  echo "ERRO: OMP_API_KEY vazia." >&2
  exit 1
fi

mkdir -p "$OMP_AGENT_DIR/agents" "$GLOBAL_SKILLS_DIR" "$CLAUDE_CMD_DIR"

# Backup seguro se ja existir config/models
TS="$(date +%Y%m%d%H%M%S)"
for f in "$OMP_AGENT_DIR/config.yml" "$OMP_AGENT_DIR/models.yml"; do
  if [[ -f "$f" ]]; then
    cp "$f" "$f.bak.$TS"
  fi
done

cp "$KIT_DIR/omp/config.yml" "$OMP_AGENT_DIR/config.yml"
cp "$KIT_DIR/omp/agents/spec-critic.md" "$OMP_AGENT_DIR/agents/spec-critic.md"
cp "$KIT_DIR/commands/sdd-loop.md" "$CLAUDE_CMD_DIR/sdd-loop.md"

rm -rf "$GLOBAL_SKILLS_DIR/sigapro-sdd-loop" "$GLOBAL_SKILLS_DIR/the-fool"
cp -R "$KIT_DIR/skills/sigapro-sdd-loop" "$GLOBAL_SKILLS_DIR/sigapro-sdd-loop"
cp -R "$KIT_DIR/skills/the-fool" "$GLOBAL_SKILLS_DIR/the-fool"

# Renderiza models.yml sem expor segredos no git
python3 - "$KIT_DIR/omp/models.yml.template" "$OMP_AGENT_DIR/models.yml" "$OMP_GATEWAY_URL" "$OMP_API_KEY" <<'PY'
import sys
from pathlib import Path
tpl_path, out_path, url, key = sys.argv[1:]
content = Path(tpl_path).read_text(encoding="utf-8")
content = content.replace("__OMP_GATEWAY_URL__", url).replace("__OMP_GATEWAY_KEY__", key)
Path(out_path).write_text(content, encoding="utf-8")
PY

chmod 600 "$OMP_AGENT_DIR/config.yml" "$OMP_AGENT_DIR/models.yml"

echo ""
echo "Instalado com sucesso:"
echo "  - $OMP_AGENT_DIR/config.yml"
echo "  - $OMP_AGENT_DIR/models.yml (chmod 600)"
echo "  - $OMP_AGENT_DIR/agents/spec-critic.md"
echo "  - $CLAUDE_CMD_DIR/sdd-loop.md"
echo "  - $GLOBAL_SKILLS_DIR/sigapro-sdd-loop"
echo "  - $GLOBAL_SKILLS_DIR/the-fool"
echo ""
echo "Proximo passo: entre em um projeto com .agent/ e rode 'omp' -> '/sdd-loop <feature>'"
