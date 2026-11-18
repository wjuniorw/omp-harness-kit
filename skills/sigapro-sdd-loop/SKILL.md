---
name: sigapro-sdd-loop
description: End-to-end automated SDD orchestration for projects with .agent/ meta-harness: brainstorm & drafts (tlc-spec-driven) -> isolated strong-model spec-critic + the-fool -> HITL gate with BTW/increment support -> execute + verifier -> audit-rounds -> remediation loop.
---

# Sigapro SDD Autopilot Loop

Automates the full engineering cycle without manual copy-paste ("meat-proxy") between models, while preserving strict human-in-the-loop (HITL) control and zero-bias verification.

## Discovery (Run First)
Inspect the current workspace before acting:
1. Read `AGENTS.md` (or `.agent/AGENTS.md`) and `.agent/system-prompt.md` if present.
2. Locate existing `.agent/skills/tlc-spec-driven/`, `.agent/skills/audit-rounds/`, `.agent/rules/`, `.agent/harness/pipeline/`, and `.specs/`.
3. Locate global `the-fool` at `~/.agents/skills/the-fool/`.

If `.agent/skills/tlc-spec-driven/` is missing in the current project, stop and inform the user instead of inventing a parallel spec convention.

---

## Pipeline Stages

### Stage 1 — Brainstorm & SDD Drafts (Resume-Aware)
1. First inspect `.specs/features/<feature>/` (and `.specs/<feature>/` or `STATE.md` if present) to detect existing progress — **NEVER overwrite or redo already-approved artifacts**:
   - Missing `spec.md` → start at `SPECIFY -> DESIGN -> TASKS`.
   - `spec.md` exists, missing `design.md` → skip `SPECIFY`, start at `DESIGN -> TASKS`.
   - `spec.md` + `design.md` exist, missing `tasks.md` → skip `SPECIFY` and `DESIGN`, jump straight to `TASKS` (respecting the approved `design.md`).
   - `spec.md` + `design.md` + `tasks.md` exist with incomplete tasks → validate existing artifacts and jump straight to **Stage 2** (or **Stage 4** if `STATE.md` already records HITL approval for the current `tasks.md`).
   - All tasks completed / `validation.md` exists → jump straight to **Stage 5** (`audit-rounds`).
2. Run deterministic validators if present:
   - `python3 .agent/skills/tlc-spec-driven/scripts/validate_spec.py ...`
   - `python3 .agent/skills/tlc-spec-driven/scripts/validate_tasks.py ...`
   - `python3 .agent/harness/assert-task-skills.py ... --root .`
3. Do NOT start `EXECUTE` yet (wait for Stage 2 + Stage 3).

### Stage 2 — Automated Strong Review + `the-fool`
Spawn the `spec-critic` subagent (`agent: "spec-critic"`) in a fresh, isolated context passing:
- Paths to `.specs/<feature>/{spec.md,design.md,tasks.md,STATE.md}` (or `remediation-tasks.md` during Stage 5 remediation).
- Feature scope and relevant `.agent/rules/` or `.agent/api/contracts/` files.

Wait for `spec-critic` to return `verdict`, `blockers_and_gaps`, `fool_challenges`, `hitl_decisions`, and `auto_fixable`.

### Stage 3 — HITL Gate (Supports `BTW` & Option Increments)
Never skip this gate when `verdict` is `BLOCK` or `REVISE`, or before starting `Execute`.
Use the native `ask` tool (in Portuguese) to present:
- Concise summary of the `spec-critic` + `the-fool` findings (3–5 highest-signal risks/gaps).
- One `<fieldset>` per decision in `hitl_decisions` with the recommended option preselected.
- An explicit action `<fieldset name="gate_action">` with:
  - `approve_execute` — Aplicar ajustes e aprovar início do Execute
  - `revise_only` — Aplicar ajustes e rodar nova rodada do spec-critic antes de executar
  - `btw_or_increment` — Tirar dúvida / Incrementar uma opção (NÃO executar ainda)
- Always include `<label>Dúvidas (BTW) ou complemento para alguma opção <textarea name="btw_notes" placeholder="Ex.: btw, como fica a idempotência? Ou: na opção A, adicionar também X..."></textarea></label>`.

**Strict BTW / Increment Rule:**
- If the user selects `btw_or_increment`, fills `btw_notes`, selects `Other` with a question/addition, or cancels (`Esc`) to use `/btw` or chat directly:
  1. Answer the question directly or discuss the increment (consult `spec-critic` again if architectural trade-offs change).
  2. Update `spec.md`, `design.md`, `tasks.md`, and `STATE.md` with the agreed refinements.
  3. Re-run `validate_spec.py` / `validate_tasks.py`.
  4. **Re-present the Stage 3 HITL `ask` gate** — NEVER proceed to Stage 4 (`Execute`) until `gate_action == "approve_execute"` with no unresolved `btw_notes` questions.

### Stage 4 — Execute + Independent Verifier
1. Apply approved edits to `spec.md`, `design.md`, `tasks.md`, and `STATE.md` and re-run validators.
2. Execute tasks per `tlc-spec-driven` (`EXECUTE`), running `.agent/harness/pipeline/on-task-complete.sh` / `check_commit.py` if configured.
3. Run the independent `Verifier` (`author != verifier`) and `validate_state.py`.

### Stage 5 — Post-Execute `audit-rounds` & Remediation Loop
If `.agent/skills/audit-rounds/` exists (or `.agent/harness/pipeline/on-feature-complete.sh`):
1. Run `audit-rounds` to execute the 3 parallel audits (`architectural-analysis`, `security-best-practices`, `security-threat-model`), update `audits-rounds/risk-register.md`, and generate `summary.md` + `remediation-tasks.md` when defects exist.
2. Present the audit summary via HITL `ask` (with the same `btw_notes` + `btw_or_increment` support):
   - Approve remediation loop (`remediation-tasks.md` -> **Stage 2** `spec-critic` -> **Stage 3** HITL -> **Stage 4** `Execute` -> re-audit)
   - Accept residual risk / defer specific `RISK-XXX` items
   - Ask a question / increment remediation scope (`btw`)
3. Repeat until open high/critical defects and rule violations are resolved or explicitly accepted by the user.

---

## Safe Overnight Mode (`--yolo` / `--overnight`)

Activated when the invocation includes `--yolo` or `--overnight` (e.g., `/sdd-loop <feature> --yolo`). Designed for unattended overnight execution so the developer can review everything in the morning.

### Hard Safety Guardrails (NEVER Violated)
1. **NO deploys, NO remote pushes, NO production mutations:** NEVER execute `git push`, `gh pr merge`, `vercel`, `eas build/submit`, `docker push`, `kubectl`, `terraform apply`, `fly deploy`, `npm publish`, or production DB migrations/writes.
2. **Branch isolation:** Before editing code, if currently on `main`, `master`, `develop`, or `production`, create and switch to a feature branch (`git checkout -b feat/<feature>-yolo`). Local commits on the feature branch are allowed; `main` stays untouched.
3. **Never silence checks:** NEVER skip/delete failing tests, linters, or `.agent/harness/assert-task-skills.py` to force a green run.

### Behavior Overrides Under `--yolo`
- **Stage 1 (Drafts):** Use documented project conventions/contracts to fill minor ambiguities instead of waiting on `ask`, recording assumptions in `spec.md`. Run `validate_spec.py`, `validate_tasks.py`, and `assert-task-skills.py`.
- **Stage 2 (`spec-critic` + `the-fool`):** Runs identically in isolated context.
- **Stage 3 (Auto-Resolve Gate):** Do NOT block on `ask`.
  - If `verdict == "BLOCK"` due to missing business rules or contradicting contracts that cannot be inferred safely from the codebase: **STOP cleanly**, do not enter Stage 4, and write `.specs/features/<feature>/MORNING-REVIEW.md` detailing the exact blocker.
  - Otherwise (`APPROVE` or `REVISE` with `auto_fixable` / clear recommended `hitl_decisions`): apply `auto_fixable` and the conservative/recommended option for each `hitl_decisions` item, log every decision and rationale in `.specs/features/<feature>/YOLO-DECISIONS.md`, re-run validators, and proceed to **Stage 4**.
- **Stage 4 (Execute + Verifier):** Execute all tasks (reading each task's `Skill:` first), run full relevant tests/lint/typecheck, and run the independent `Verifier` (`author != verifier`) + `validate_state.py`.
- **Stage 5 (`audit-rounds` + Bounded Remediation):** Run `audit-rounds` and auto-execute at most **2 remediation rounds** for `HIGH`/`CRITICAL` findings or rule violations. Any remaining `MEDIUM`/`LOW` or architectural trade-offs stay logged in `audits-rounds/risk-register.md` and `MORNING-REVIEW.md`.
- **Final Morning Deliverable:** Write `.specs/features/<feature>/MORNING-REVIEW.md` containing: branch name, `git diff --stat`, tasks completed vs blocked, auto-decisions taken (`YOLO-DECISIONS.md`), test/lint/verifier outputs, open risks, and recommended next commands for human review.
