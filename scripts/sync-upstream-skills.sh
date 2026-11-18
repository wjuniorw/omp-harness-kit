#!/usr/bin/env bash
set -euo pipefail

# Atualiza skills mantidas localmente (tlc-spec-driven / the-fool) a partir do
# repo upstream e reaplica automaticamente o hook de assert de skills.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
UPSTREAM_DIR="${UPSTREAM_SKILLS_DIR:-$HOME/code/agent-skills/packages/skills-catalog/skills}"
PROJECT_DIR="${1:-.}"

if [[ ! -d "$UPSTREAM_DIR" ]]; then
  echo "Diretorio upstream nao encontrado: $UPSTREAM_DIR" >&2
  echo "Defina UPSTREAM_SKILLS_DIR=/caminho/para/skills e tente novamente." >&2
  exit 1
fi

PROJECT_ABS="$(cd "$PROJECT_DIR" && pwd)"

if [[ -d "$UPSTREAM_DIR/tlc-spec-driven" ]]; then
  echo "-> Sincronizando tlc-spec-driven para $PROJECT_ABS/.agent/skills/tlc-spec-driven ..."
  mkdir -p "$PROJECT_ABS/.agent/skills/tlc-spec-driven"
  rsync -a --delete --exclude "__pycache__" "$UPSTREAM_DIR/tlc-spec-driven/" "$PROJECT_ABS/.agent/skills/tlc-spec-driven/"
  python3 "$SCRIPT_DIR/reapply-tlc-overlay.py" --project "$PROJECT_ABS"
else
  echo "Aviso: tlc-spec-driven nao encontrado em $UPSTREAM_DIR (pulando)"
fi

if [[ -d "$UPSTREAM_DIR/the-fool" ]]; then
  echo "-> Sincronizando the-fool para $HOME/.agents/skills/the-fool ..."
  mkdir -p "$HOME/.agents/skills/the-fool"
  rsync -a --delete "$UPSTREAM_DIR/the-fool/" "$HOME/.agents/skills/the-fool/"
fi

echo "Sync concluido com overlay preservado."
