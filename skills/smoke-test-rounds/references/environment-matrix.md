# Environment Matrix & Safety Guards

| Environment | Allowed Modes | Mutating Tests (`--full`) | Isolation & Safety Rule |
|---|---|---|---|
| `local` | `--readonly`, `--full` | Allowed | Use isolated test prefix (`smoke-test-*`) and local DB/Docker only. |
| `staging` / `homologacao` | `--readonly`, `--full` | Allowed with cleanup | Confirm `BASE_URL` is a staging/homolog host; verify cleanup trap runs after `--full`. Never forge third-party webhook HMACs unless using explicit sandbox secrets. |
| `production` | `--readonly` ONLY | **FORBIDDEN** | Abort immediately if `--full` or mutating flags are passed against production URLs. |
