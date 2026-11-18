#!/usr/bin/env bash
set -euo pipefail

# Aplica o overlay SDD do omp-harness-kit de forma idempotente em qualquer projeto
# (novo/em andamento SEM .agent/ ou projeto existente COM .agent/, como o sigapro).
#
#   ./scripts/apply-project-overlay.sh [CAMINHO_PROJETO] [--in-agent-dir] [--with-qa] [--skip-sync] [--local]
#
# Flags:
#   --in-agent-dir  Espelha skills instaladas de .agents/skills/ para .agent/skills/
#   --with-qa       Instala qa-report e qa-execution (pedronauck/skills)
#   --skip-sync     Copia apenas o overlay (.agent/harness, manifest, lockfile, .gitignore) sem rodar npx skills
#   --local         Repassa --local para sync-upstream-skills.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
KIT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
OVERLAY_DIR="$KIT_DIR/project-overlay"

PROJECT_DIR="."
IN_AGENT_DIR=0
WITH_QA=0
SKIP_SYNC=0
USE_LOCAL=0

for arg in "$@"; do
  case "$arg" in
    --in-agent-dir) IN_AGENT_DIR=1 ;;
    --with-qa) WITH_QA=1 ;;
    --skip-sync) SKIP_SYNC=1 ;;
    --local) USE_LOCAL=1 ;;
    -h|--help)
      sed -n '4,13p' "$0"
      exit 0
      ;;
    *) PROJECT_DIR="$arg" ;;
  esac
done

PROJECT_ABS="$(cd "$PROJECT_DIR" && pwd)"
echo "=== OMP Harness Kit — Apply Project Overlay ==="
echo "Projeto: $PROJECT_ABS"

mkdir -p "$PROJECT_ABS/.agent/harness"

# 1. assert-task-skills.py (motor deterministico do kit — sempre atualizado)
cp "$OVERLAY_DIR/.agent/harness/assert-task-skills.py" "$PROJECT_ABS/.agent/harness/assert-task-skills.py"
echo "[OK] .agent/harness/assert-task-skills.py"

# 2. Arquivos customizaveis por projeto — cria apenas se ainda nao existirem
if [[ ! -f "$PROJECT_ABS/.agent/harness/skill-map.json" ]]; then
  cp "$OVERLAY_DIR/.agent/harness/skill-map.example.json" "$PROJECT_ABS/.agent/harness/skill-map.json"
  echo "[NEW] .agent/harness/skill-map.json (criado a partir do exemplo — ajuste para sua stack)"
else
  echo "[KEEP] .agent/harness/skill-map.json ja existe (preservado)"
fi

if [[ ! -f "$PROJECT_ABS/.agent/skills-manifest.json" ]]; then
  cp "$OVERLAY_DIR/.agent/skills-manifest.json" "$PROJECT_ABS/.agent/skills-manifest.json"
  echo "[NEW] .agent/skills-manifest.json"
else
  echo "[KEEP] .agent/skills-manifest.json ja existe (preservado)"
fi

if [[ ! -f "$PROJECT_ABS/skills-lock.json" ]]; then
  cp "$OVERLAY_DIR/skills-lock.json" "$PROJECT_ABS/skills-lock.json"
  echo "[NEW] skills-lock.json"
else
  echo "[KEEP] skills-lock.json ja existe (preservado)"
fi

# 3. Garante .agents/ no .gitignore
GITIGNORE_PATH="$PROJECT_ABS/.gitignore"
if [[ ! -f "$GITIGNORE_PATH" ]]; then
  cp "$OVERLAY_DIR/.gitignore.snippet" "$GITIGNORE_PATH"
  echo "[NEW] .gitignore (.agents/ adicionado)"
elif ! grep -Eq '^\s*\.agents/?\s*$' "$GITIGNORE_PATH"; then
  printf "\n%s\n" "$(cat "$OVERLAY_DIR/.gitignore.snippet")" >> "$GITIGNORE_PATH"
  echo "[OK] .agents/ adicionado ao .gitignore"
else
  echo "[KEEP] .gitignore ja ignora .agents/"
fi

# 4. Instala/atualiza skills upstream + reaplica hook no tlc-spec-driven
if [[ "$SKIP_SYNC" -eq 0 ]]; then
  SYNC_FLAGS=()
  [[ "$IN_AGENT_DIR" -eq 1 ]] && SYNC_FLAGS+=(--in-agent-dir)
  [[ "$WITH_QA" -eq 1 ]] && SYNC_FLAGS+=(--with-qa)
  [[ "$USE_LOCAL" -eq 1 ]] && SYNC_FLAGS+=(--local)
  "$SCRIPT_DIR/sync-upstream-skills.sh" "$PROJECT_ABS" "${SYNC_FLAGS[@]}"

else
  echo "-> Pulando sync online (--skip-sync); reaplicando overlay se tlc-spec-driven existir..."
  python3 "$SCRIPT_DIR/reapply-tlc-overlay.py" --project "$PROJECT_ABS" || true
fi
if command -v node >/dev/null 2>&1; then
  node "$SCRIPT_DIR/check-skills.mjs" --root "$PROJECT_ABS" || true
fi

echo "Concluido! Rode '/sdd-loop <feature>' dentro de $PROJECT_ABS."
