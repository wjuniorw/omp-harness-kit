---
name: smoke-test-rounds
description: Orchestrate stack-agnostic smoke test execution rounds across local, staging/homologacao, and production (--readonly) environments. Discovers features from .specs/ and existing smoke runners without creating tests, tracks regressions across rounds, generates feature readiness reports, and integrates with qa-report + qa-execution for staging validation.
---

# Smoke Test Rounds — Orquestrador de Smoke Tests, Regressão & Readiness

Orquestra rodadas sequenciais e auditáveis de smoke tests sobre features já especificadas, comparando regressões entre rodadas e consolidando um **Readiness Report** por feature em `smoke-rounds/`.

> **Regra de ouro:** Esta skill **NÃO cria novos scripts de smoke test** (a menos que explicitamente solicitado). Ela **detecta features pelas specs**, **descobre os smoke tests já existentes** no projeto, **executa-os**, compara com a rodada anterior e — quando `qa-report` / `qa-execution` estiverem instalados — orquestra a validação complementar em homologação.

---

## Procedimento de Execução

### Passo 0 — Descoberta Dinâmica (Specs + Smoke Runners + QA Skills)
Execute o helper somente-leitura para mapear features em `.specs/features/` (ou `.agent/specs/`) e runners existentes (`scripts/smoke/`, `tests/smoke/`, `package.json`, `Makefile`):

```bash
python3 ~/.agents/skills/smoke-test-rounds/scripts/discover-smoke.py --root .
```
*(Se a skill estiver instalada localmente em `.agent/skills/smoke-test-rounds/` ou `.agents/skills/smoke-test-rounds/`, use o caminho local equivalente.)*

Verifique também quais skills complementares estão disponíveis:
- `qa-report` (`.agent/skills/qa-report` ou `.agents/skills/qa-report` ou `~/.agents/skills/qa-report`)
- `qa-execution` (`.agent/skills/qa-execution` ou `.agents/skills/qa-execution` ou `~/.agents/skills/qa-execution`)

*Done when:* Lista de features especificadas, mapa `feature -> smoke runner` (ou `UNCOVERED`) e disponibilidade de `qa-report`/`qa-execution` confirmados.

---

### Passo 1 — Calcular o Identificador Sequencial da Rodada
```bash
ROUND_ID=$(python3 ~/.agents/skills/smoke-test-rounds/scripts/next-round.py --dir smoke-rounds --env staging)
ROUND_DIR="smoke-rounds/${ROUND_ID}"
mkdir -p "${ROUND_DIR}/features"
```
Ambientes aceitos: `local`, `staging`, `homologacao`, `test`, `production` (em `production`, apenas `--readonly`).

---

### Passo 2 — Pré-voo e Guardas de Segurança
Consulte `references/environment-matrix.md` antes de disparar qualquer runner:
1. **Proteção de Produção:** Se `--env production`, exija `--readonly` e bloqueie qualquer comando mutável (`--full`).
2. **Isolamento de Dados:** Em `--full` (`local`/`staging`/`homologacao`), garanta prefixo isolado (`SMOKE_RUN_ID=smoke-test-...`) e limpeza ao final.
3. **Health Check Inicial:** Confirme que os endpoints/serviços alvo estão acessíveis antes de executar a bateria (evita centenas de falsos `FAIL` por serviço desligado).

---

### Passo 3 — Executar os Smoke Tests Descobertos (Sem Criar Novos)
Para cada runner descoberto no Passo 0:
1. Dispare o runner em modo `--readonly` (padrão seguro) ou `--full` redirecionando a saída bruta para `${ROUND_DIR}/raw-execution.log`:
   ```bash
   SMOKE_ENV=staging ./scripts/smoke/run.sh --readonly 2>&1 | tee "${ROUND_DIR}/raw-execution.log"
   ```
   *(Ou execute o comando específico detectado por feature no `discover-smoke.py`: `npm run test:smoke`, `pytest -m smoke`, `go test ./... -run Smoke`, etc.)*
2. Features especificadas que **não possuem** smoke test existente ficam explicitamente marcadas como `UNCOVERED` / `SKIP` (nunca invente um `PASS` nem gere testes silenciosamente).
3. Em caso de falhas HTTP/infra inesperadas, consulte `references/failure-triage.md`.

---

### Passo 4 — Integração com `qa-report` + `qa-execution` (Homologação / Readiness E2E)
Quando `qa-report` e `qa-execution` existirem (ou forem solicitados para homologação / release candidate):
1. **`qa-report` (Planejamento & Bugs):**
   - Para features em `staging`/`homologacao` com UI/jornadas de usuário ou marcadas como `PARTIAL`/`UNCOVERED` nos smoke scripts, acione `qa-report` lendo `.specs/features/<feature>/spec.md` para manter `.agent/qa/journeys/` e `.agent/qa/charters/` atualizados.
   - Se o Passo 3 detectou falhas reais em smoke tests, passe os detalhes para `qa-report` registrar/deduplicar em `.agent/qa/bugs/BUG-YYYYMMDD-<slug>.md`.
2. **`qa-execution` (Execução de Jornadas / Persona):**
   - Execute os charters relevantes contra o ambiente alvo (`local` ou `staging`), coletando o status por jornada (`pass` | `friction` | `fail`) e o relatório em `.agent/qa/reports/`.
3. **Unificação no Readiness:**
   - Combine o resultado objetivo dos smoke tests (`PASS`/`FAIL`/`SKIP`) com o resultado das jornadas do `qa-execution` para calcular o **Readiness** final de cada feature.

---

### Passo 5 — Relatórios por Feature, Delta Regressivo e Readiness Summary
1. Para cada feature detectada em `.specs/features/`, gere `${ROUND_DIR}/features/{feature}.md` usando `assets/feature-report-template.md` com:
   - Status dos critérios de smoke + status `qa-execution` (se rodado).
   - Veredito de **Readiness**:
     - `READY` — Smoke assertions passaram (0 FAIL) e jornada QA sem `fail` crítico.
     - `PARTIAL` — Smoke passou parcialmente ou possui `SKIP`/`friction`/cobertura incompleta.
     - `BLOCKED` — 1+ `FAIL` em smoke test, regressão confirmada ou bug crítico no `qa-execution`.
     - `UNCOVERED` — Feature existe em `.specs/`, mas não há smoke test nem charter QA cobrindo.
2. Compare `${ROUND_DIR}` com a rodada imediatamente anterior (`round-{N-1}`) identificando:
   - **New Regressions** (passavam antes e falharam agora)
   - **Fixed Issues** (falhavam antes e passaram agora)
   - **Readiness Delta**
3. Consolide `${ROUND_DIR}/summary.md` (`assets/round-summary-template.md`) e atualize `smoke-rounds/catalog.md` (`assets/feature-catalog-template.md`).

---

## Regras Críticas

1. **Nunca crie smoke tests sem pedido explícito:** seu papel é detectar, orquestrar, medir regressão e reportar readiness.
2. **Proteção de Produção:** Nunca rode `--full` / mutações fora de `local`, `staging` ou `homologacao`.
3. **Mascaramento de Segredos:** Nunca grave tokens, API keys, senhas ou JWTs completos em `raw-execution.log`, `summary.md`, `features/*.md` ou `.agent/qa/bugs/`.
4. **Rastreabilidade:** Toda asserção falhada deve citar o ID da spec (`REQ-XX` / `AC-XX`) ou rota + link para o `BUG-*.md` quando registrado via `qa-report`.
5. **Zero Falsos Verdes:** Serviço fora do ar, credencial ausente ou endpoint inexistente nunca vira `PASS`; registre `FAIL` ou `SKIP` com motivo explícito.
