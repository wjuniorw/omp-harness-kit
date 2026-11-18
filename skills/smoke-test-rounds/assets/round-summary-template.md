# Smoke Test & Readiness Round Summary: [ROUND-ID]

**Environment**: `[local | staging | homologacao | production]`  
**Target Base URL**: `[BASE_URL]`  
**Execution Date**: `[YYYY-MM-DD HH:MM:SS UTC]`  
**Execution Mode**: `[--full | --readonly]`  
**Git Commit**: `[COMMIT_HASH]` (`[BRANCH]`)  
**Overall Verdict**: **[PASS | FAIL | PARTIAL]**

---

## 1. Executive Metrics

| Metric | Value |
|---|---|
| Features Detected (`.specs/`) | `[TOTAL_FEATURES]` |
| Smoke Assertions Checked | `[TOTAL_CHECKED]` |
| Passed / Failed / Skipped | `[COUNT_PASS]` / `[COUNT_FAIL]` / `[COUNT_SKIP]` |
| QA Journeys (`qa-execution`) | `[PASS_QA]` / `[FRICTION_QA]` / `[FAIL_QA]` |
| Total Execution Duration | `[TOTAL_DURATION]s` |

---

## 2. Feature Readiness Breakdown

| Feature Slug | Runner | PASS | FAIL | SKIP | QA Execution | Readiness |
|---|---|:---:|:---:|:---:|:---:|:---:|
| `[feature-slug]` | `[runner or UNCOVERED]` | `[P]` | `[F]` | `[S]` | `[pass/friction/fail/N/A]` | `[READY/PARTIAL/BLOCKED/UNCOVERED]` |

---

## 3. Regression Delta vs. Previous Round (`[PREV_ROUND_ID]`)

- **New Regressions**: `[None / List of failed criteria]`
- **Fixed Issues**: `[None / List of resolved items]`
- **Newly Uncovered Features**: `[None / List]`

---

## 4. Skipped & Uncovered Justification Log

| Feature | Criterion / Gap | Reason |
|---|---|---|
| `[Feature]` | `[ID or Missing Smoke Runner]` | `[Justification]` |

---

## 5. Linked QA Artifacts (`qa-report` / `qa-execution`)

- **QA Execution Report**: `[.agent/qa/reports/YYYY-MM-DD-scope.md or N/A]`
- **Bugs Filed / Updated**: `[.agent/qa/bugs/BUG-*.md or None]`

---

## 6. Next Actions

1. `[Action or remediation recommendation]`
