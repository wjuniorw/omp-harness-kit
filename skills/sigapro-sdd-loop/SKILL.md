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

### Stage 1 — Brainstorm & SDD Drafts
1. Follow `.agent/skills/tlc-spec-driven/SKILL.md` through `SPECIFY -> DESIGN -> TASKS` (with user brainstorm when requirements are open).
2. Run deterministic validators if present:
   - `python3 .agent/skills/tlc-spec-driven/scripts/validate_spec.py ...`
   - `python3 .agent/skills/tlc-spec-driven/scripts/validate_tasks.py ...`
3. Do NOT start `EXECUTE` yet.

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
