# Master Feature Catalog — Smoke Test & Readiness Verification

**Project**: `[PROJECT_NAME]`  
**Last Updated**: `[YYYY-MM-DD]`  
**Maintained By**: `smoke-test-rounds` (+ `qa-report` / `qa-execution` when present)

---

## 1. Registered Features & Readiness Matrix

| Feature Slug | Spec Source | Smoke Runner / Command | QA Charter (`qa-report`) | Last Verified Round | Local Status | Staging / Homologação Status | Readiness |
|---|---|---|---|---|---|---|---|
| `[feature-slug]` | `.specs/features/[feature-slug]/` | `[script or UNCOVERED]` | `[CH-slug or N/A]` | `[round-XX]` | `[PASS/FAIL/SKIP]` | `[PASS/FAIL/SKIP]` | `[READY / PARTIAL / BLOCKED / UNCOVERED]` |

---

## 2. Environment Catalog

| Environment | Base URL | Default Mode | Primary Purpose |
|---|---|---|---|
| `local` | `http://localhost:[PORT]` | `--full` / `--readonly` | Desenvolvimento local / Docker Compose |
| `staging` / `homologacao` | `https://[STAGING_URL]` | `--readonly` / `--full` | Homologação pré-produção + QA journeys |
| `production` | `https://[PROD_URL]` | `--readonly` ONLY | Saúde pós-deploy sem mutações |
