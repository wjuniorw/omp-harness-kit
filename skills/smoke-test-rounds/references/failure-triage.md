# Smoke Test Failure Triage Guide

| Observed Symptom | Probable Cause | Corrective Action |
|---|---|---|
| Connection refused / HTTP `502`/`503` on healthcheck | Target service not running or deploy still warming up. | Abort round early before accumulating false `FAIL`s; verify container/server status. |
| HTTP `401`/`403` on protected smoke route | Missing or expired test credential / session cookie / API key in `.env`. | Check env vars without printing secrets into logs or reports. |
| HTTP `429 Too Many Requests` | Rate limiter triggered by burst requests in smoke runner. | Respect rate-limit backoff in existing runner; never disable production rate limiters. |
| Smoke runner missing for feature in `.specs/` | Feature has spec/code, no existing smoke script yet. | Mark `UNCOVERED` / `SKIP`; optionally run `qa-report` + `qa-execution` charter for staging readiness instead of fabricating smoke coverage. |
| E2E / UI friction or ambiguous behavior | API passed but UI flow has edge friction. | Run `qa-execution` charter and log `BUG-*.md` via `qa-report`. |
