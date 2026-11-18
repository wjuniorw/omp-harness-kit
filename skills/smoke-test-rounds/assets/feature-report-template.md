# Feature Smoke & Readiness Report: [FEATURE_SLUG]

**Round**: `[ROUND_ID]`  
**Environment**: `[local | staging | homologacao | production]`  
**Runner / Command**: `[SMOKE_COMMAND_OR_UNCOVERED]`  
**Execution Mode**: `[--full | --readonly]`  
**QA Journey (`qa-execution`)**: `[pass | friction | fail | not-run]`  
**Feature Readiness**: **[READY | PARTIAL | BLOCKED | UNCOVERED]**

---

## 1. Specification & Coverage Mapping

- **Spec Directory**: `.specs/features/[FEATURE_SLUG]/`
- **Surfaces Tested**: `[ROUTES_PAGES_WORKERS]`
- **QA Charter**: `[.agent/qa/charters/CH-*.md or N/A]`

---

## 2. Smoke Execution Details

| Criterion / Spec ID | Action / Surface | Expected | Actual | Status | Duration |
|---|---|---|---|:---:|:---:|
| `[ID]` | `[METHOD / FLOW]` | `[EXPECTED]` | `[ACTUAL]` | `[PASS/FAIL/SKIP]` | `[D]s` |

---

## 3. Regression & QA Findings

- **Delta vs Previous Round**: `[Unchanged | New Regression | Fixed]`
- **Linked Bugs (`qa-report`)**: `[.agent/qa/bugs/BUG-*.md or None]`
- **Paper Cuts / Friction (`qa-execution`)**: `[Notes or None]`
