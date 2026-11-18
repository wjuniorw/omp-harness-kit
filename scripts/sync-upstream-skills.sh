#!/usr/bin/env bash
set -euo pipefail

# Atualiza tlc-spec-driven e the-fool diretamente via `npx skills add` (upstream oficial)
# e reaplica automaticamente o overlay de Skill assertion do Meta-Harness.
#
# Uso:
#   ./scripts/sync-upstream-skills.sh [CAMINHO_PROJETO] [--in-agent-dir] [--with-qa] [--local]
#
# Flags:
#   --in-agent-dir  Copia o tlc-spec-driven baixado de .agents/skills/ para .agent/skills/
#                   (util para templates/projetos que versionam .agent/skills/tlc-spec-driven).
#   --with-qa       Tambem instala/atualiza qa-report e qa-execution (pedronauck/skills)
#                   para rodar junto com smoke-test-rounds em homologacao.
#   --local         Usa clone local em $UPSTREAM_SKILLS_DIR em vez de baixar via npx skills.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="."
IN_AGENT_DIR=0
WITH_QA=0
USE_LOCAL=0

for arg in "$@"; do
  case "$arg" in
    --in-agent-dir) IN_AGENT_DIR=1 ;;
    --with-qa) WITH_QA=1 ;;
    --local) USE_LOCAL=1 ;;
    -h|--help)
      sed -n '3,14p' "$0"
      exit 0
      ;;
    *) PROJECT_DIR="$arg" ;;
  esac
done

PROJECT_ABS="$(cd "$PROJECT_DIR" && pwd)"

if [[ "$USE_LOCAL" -eq 1 ]]; then
  UPSTREAM_DIR="${UPSTREAM_SKILLS_DIR:-$HOME/code/agent-skills/packages/skills-catalog/skills}"
  SRC_TLC="$(find "$UPSTREAM_DIR" -maxdepth 3 -type d -name "tlc-spec-driven" | head -n 1 || true)"
  if [[ -z "$SRC_TLC" ]]; then
    echo "ERRO: tlc-spec-driven nao encontrado em $UPSTREAM_DIR" >&2
    exit 1
  fi
  TARGET="$PROJECT_ABS/.agent/skills/tlc-spec-driven"
  mkdir -p "$TARGET"
  rsync -a --delete --exclude "__pycache__" "$SRC_TLC/" "$TARGET/"
else
  echo "-> Instalando/atualizando tlc-spec-driven via npx skills (tech-leads-club/agent-skills)..."
  (cd "$PROJECT_ABS" && npx --yes skills add tech-leads-club/agent-skills -s tlc-spec-driven -a universal -y)

  if [[ "$IN_AGENT_DIR" -eq 1 && -d "$PROJECT_ABS/.agents/skills/tlc-spec-driven" ]]; then
    echo "-> Espelhando para $PROJECT_ABS/.agent/skills/tlc-spec-driven (--in-agent-dir)..."
    mkdir -p "$PROJECT_ABS/.agent/skills/tlc-spec-driven"
    rsync -a --delete --exclude "__pycache__" "$PROJECT_ABS/.agents/skills/tlc-spec-driven/" "$PROJECT_ABS/.agent/skills/tlc-spec-driven/"
  fi

  echo "-> Atualizando the-fool global via npx skills (jeffallan/claude-skills)..."
  npx --yes skills add jeffallan/claude-skills -s the-fool -g -a universal -y
  if [[ "$WITH_QA" -eq 1 ]]; then
    echo "-> Instalando/atualizando qa-report e qa-execution via npx skills (pedronauck/skills)..."
    (cd "$PROJECT_ABS" && npx --yes skills add pedronauck/skills -s qa-report qa-execution -a universal -y)
  fi
fi

echo "-> Reaplicando overlay de Skill assertion..."
python3 "$SCRIPT_DIR/reapply-tlc-overlay.py" --project "$PROJECT_ABS"

echo "Concluido: skills upstream atualizadas e overlay preservado."
