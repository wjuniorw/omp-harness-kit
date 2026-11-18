# OMP Harness Kit (`omp` + SDD Loop + Critic + Supply Chain de Skills)

Kit portável para instalar em segundos o workflow completo de engenharia assistida por IA no **`omp` (Oh My Pi)**, preservando o Meta-Harness específico de cada projeto (`.agent/`) e mantendo skills externas (`.agents/`) gerenciadas como dependências (estilo `pnpm`).

> **Quer que o próprio agente diagnostique sua máquina/projeto e configure tudo para você?**
> ```bash
> git clone https://github.com/wjuniorw/omp-harness-kit.git ~/code/omp-harness-kit
> omp "Leia ~/code/omp-harness-kit/.llms.md, diagnostique meu ambiente e este projeto, e me guie na configuracao."
> ```

## Para quem é este repositório?

- **Para quem usa `omp` (Oh My Pi) / Claude Code** e quer um fluxo disciplinado de **Spec-Driven Development** (`/sdd-loop`) com revisão crítica automática (`spec-critic` + `the-fool`), checkpoints humanos conversacionais (`ask` + `/btw`) e auditoria pós-execução (`audit-rounds`).
- **Para quem quer manter skills externas como dependências** (`.agents/` no `.gitignore` + `skills-lock.json` + `.agent/skills-manifest.json`), sem poluir o repositório com arquivos baixados de terceiros.
- **Para quem personaliza regras por projeto** e quer atualizar `tlc-spec-driven` e `the-fool` do upstream sem perder o vínculo automático `Skill:` nas tasks.

---

## Arquitetura do Kit

```text
omp-harness-kit/
├── omp/
│   ├── config.yml                 # Roles + fallback chains (Claude -> Gemini 4 Argon -> DeepSeek)
│   ├── models.yml.template        # Catálogo de combos e modelos diretos (sem secrets)
│   └── agents/spec-critic.md      # Revisor independente (Pass A regras/contratos + Pass B the-fool)
├── commands/sdd-loop.md           # Comando /sdd-loop
├── skills/
│   ├── sigapro-sdd-loop/          # Orquestrador: TLC SDD -> spec-critic -> HITL (BTW) -> Execute -> Audit
│   ├── smoke-test-rounds/         # Orquestrador de smoke tests existentes, regressao e readiness (+ qa-report/qa-execution)
│   └── the-fool/                  # Devil's advocate, pre-mortem, red-team, scan de vieses
├── project-overlay/
│   ├── .agent/skills-manifest.json
│   ├── .agent/harness/
│   │   ├── assert-task-skills.py  # Assert deterministico de Skill: em tasks.md (independente de updates!)
│   │   └── skill-map.example.json # Roteamento camada/arquivo -> skill especifica da stack
│   ├── skills-lock.json           # Lockfile compatível com `npx skills experimental_install`
│   └── .gitignore.snippet         # `.agents/` gitignored (igual node_modules/)
├── scripts/
│   ├── apply-project-overlay.sh   # Bootstrap idempotente para projetos novos, sem .agent/ ou ja existentes
│   ├── reapply-tlc-overlay.py     # Reanexa hook no tlc-spec-driven apos update upstream
│   ├── sync-upstream-skills.sh    # Atualiza tlc-spec-driven / the-fool e reaplica overlay
│   └── check-skills.mjs           # "pnpm check" de skills (lockfile + grafo de dependencias)
└── omniroute/
    ├── README.md                  # Guia para subir OmniRoute local (ideal para convidados)
    └── omniroute-combos.example.json
```

---

## 1. Instalação Rápida (Notebook Novo ou Amigo)

### Pré-requisitos
- `omp` instalado (`oh-my-pi`)
- `python3` e `node` (18+)

### Modo A — Seu Notebook (Gateway Sigapro)
```bash
git clone git@github.com:wjuniorw/omp-harness-kit.git
cd omp-harness-kit
./install.sh
# Escolha: 1) Sigapro Gateway -> cole sua OMP-dev-key
```

Ou não-interativo:
```bash
OMP_MODE=sigapro OMP_API_KEY="sua-key" ./install.sh
```

### Modo B — Seu Amigo (OmniRoute Local Próprio)
1. Suba o OmniRoute local seguindo [`omniroute/README.md`](./omniroute/README.md) e importe/configure os combos de [`omniroute/omniroute-combos.example.json`](./omniroute/omniroute-combos.example.json).
2. Rode:
```bash
git clone git@github.com:wjuniorw/omp-harness-kit.git
cd omp-harness-kit
OMP_MODE=local OMP_API_KEY="sua-key-local" ./install.sh
```

> **Segurança:** `install.sh` nunca envia secrets para o Git; o arquivo `~/.omp/agent/models.yml` é gerado localmente com permissão `600`.

---

## 2. Como Funciona o Fluxo `/sdd-loop`

Dentro de qualquer projeto que possua `.agent/`, execute no `omp`:

```text
/sdd-loop <feature ou descrição>
```

0. **Detecção automática de progresso (*Resume-Aware*)**: se a feature já tiver `spec.md` e `design.md` aprovados em `.specs/features/<feature>/`, o loop **não refaz** Spec/Design — pula direto para gerar `tasks.md` (ou para a etapa pendente).
1. **Stage 1 — Drafts (`tlc-spec-driven`)**: gera `spec.md`, `design.md` e `tasks.md` e roda `validate_spec.py`, `validate_tasks.py` + `assert-task-skills.py`.
2. **Stage 2 — Revisor Forte + `the-fool` (`spec-critic`)**: dispara o subagente `spec-critic` em contexto limpo (ordem **`claudio-combo` → `cw/claude-sonnet-5-high` → `gemini/gemini-4-argon` → `ds-web/deepseek-v4-pro-think`**) para auditar regras/contratos e rodar pre-mortem/red-team.
3. **Stage 3 — HITL com BTW e Incremento**: abre formulário `ask` apenas para decisões reais, sempre com a opção **"Tirar dúvida / Incrementar esta opção"** e campo `btw_notes` (além de `/btw` ou `Esc`). **Nunca avança para `Execute`** enquanto houver dúvida ou ajuste pendente.
4. **Stage 4 — Execute + Verifier**: executa as tasks ativando a `Skill:` de cada uma, dispara hooks de `.agent/harness/pipeline/` e roda o `Verifier` independente (`validate_state.py`, gerando `validation.md`).
5. **Stage 4.5 — Auditoria Pós-Validação (`spec-critic` Mode 2)**: o modelo pensante compara `validation.md` × `tasks.md` × `spec.md` × `design.md` contra o código/diff real para detectar drift, critérios faltantes ou falsos `PASS`, abrindo remediação antes de fechar.
6. **Stage 5 — `audit-rounds` → Remediação**: roda auditoria pós-execução (`architectural-analysis`, `security-best-practices`, `security-threat-model` → `risk-register.md`) e reinicia o loop em `remediation-tasks.md` se houver riscos pendentes.

### Modo Noturno Seguro (`--yolo` / `--overnight`, sem deploy)
Quer deixar o agente trabalhando numa feature enquanto você descansa e revisar tudo pronto de manhã?
```bash
# Opção 1 — Headless (salva log completo e encerra ao terminar, com teto de tempo e custo):
omp -p --approval-mode=yolo --max-time=2h --max-cost=15 \
  "/sdd-loop <feature ou descrição> --yolo" | tee /tmp/sdd-overnight.log

# Opção 2 — Interativo (abra com yolo e rode /sdd-loop com --yolo):
omp --approval-mode=yolo --max-time=2h --max-cost=15
# dentro do omp: /sdd-loop <feature> --yolo
```
- Cria/trabalha em branch `feat/<feature>-yolo` (nunca altera `main` direto).
- **Proibido** `git push`, deploy, `eas submit`, `docker push`, `kubectl`, `terraform` ou migração em produção.
- Registra decisões tomadas automaticamente em `.specs/features/<feature>/YOLO-DECISIONS.md` e entrega um resumo matinal em `.specs/features/<feature>/MORNING-REVIEW.md` (ou para imediatamente se o `spec-critic` der `BLOCK` por ambiguidade crítica de negócio).

| Parâmetro / Comando | Função |
| :--- | :--- |
| `omp -p "..."` | Modo headless não-interativo (processa o prompt, grava saída e encerra). |
| `--approval-mode=yolo` | Aprova chamadas de tools sem travar o terminal esperando confirmação. |
| `--max-time=90m` / `2h` | Encerra a sessão automaticamente ao atingir o tempo máximo. |
| `--warn-cost=3` | Emite aviso único ao atingir o custo estimado em USD. |
| `--max-cost=8` | Bloqueia novas chamadas de LLM ao atingir o teto estimado (inclui subagentes; em `-p` sai com código `3`). |
| `caffeinate -i <cmd>` | Utilitário nativo do macOS (`/usr/bin/caffeinate`) que impede o Mac de dormir por ociosidade enquanto o comando roda. |

### Smoke Tests, Regressão & Readiness (`smoke-test-rounds` + `qa-report` / `qa-execution`)
Depois de implementar ou antes de liberar homologação, use a skill `smoke-test-rounds`:
- **Não cria smoke tests novos**: lê `.specs/features/*` e descobre os runners já existentes no repo (`scripts/smoke/`, `tests/smoke/`, `package.json`, `Makefile`).
- **Calcula regressão entre rodadas** (`smoke-rounds/round-{N}-{env}-{YYYY-MM-DD}/`) e gera relatório de **Readiness** (`READY` / `PARTIAL` / `BLOCKED` / `UNCOVERED`).
- **Integra com `qa-report` e `qa-execution`** (`pedronauck/skills`) em staging/homologação para validar jornadas de usuário e registrar bugs em `.agent/qa/bugs/`.

```bash
# Opcional: instalar qa-report e qa-execution junto na sincronizacao do projeto
./scripts/sync-upstream-skills.sh /caminho/do/seu/projeto --with-qa
```

---

## 3. Como Atualizar `tlc-spec-driven` e `the-fool` Sem Perder Seu Assert de Skills

O problema clássico: editar `tlc-spec-driven/SKILL.md`, `references/tasks.md` e `scripts/validate_tasks.py` diretamente faz o próximo `git pull` / `npx skills` sobrescrever seu mapeamento de skills.

**A solução neste kit separa o motor da extensão:**
1. **Motor externo estável** (fora da pasta `tlc-spec-driven/`):
   - `.agent/harness/skill-map.json`: mapeia paths/camadas da sua stack (NextJS, NestJS, Go, Expo, RN, Rust) para a skill obrigatória (`create-use-case`, `create-component`, `golang-pro`, etc.).
   - `.agent/harness/assert-task-skills.py`: lê `tasks.md` + `skill-map.json` e falha determinísticamente se alguma task de código ficar com `Skill: NONE` ou apontar para skill inexistente.
2. **Atualização 1-comando com reaplicação automática do hook:**
```bash
# Atualiza via npx skills add (tech-leads-club/agent-skills + jeffallan/claude-skills)
# e reaplica o overlay em .agents/skills/tlc-spec-driven (ou .agent/skills/ com --in-agent-dir):
./scripts/sync-upstream-skills.sh /caminho/do/seu/projeto
./scripts/sync-upstream-skills.sh /caminho/do/seu/projeto --in-agent-dir --with-qa
# Modo offline usando clone local em ~/code/agent-skills:
./scripts/sync-upstream-skills.sh /caminho/do/seu/projeto --local
```
O script baixa `tlc-spec-driven` via `npx skills add` (e `the-fool` global), e depois roda `reapply-tlc-overlay.py` injetando apenas o marcador `<!-- META-HARNESS-SKILL-ASSERT:START --> ... <!-- META-HARNESS-SKILL-ASSERT:END -->` apontando para `.agent/harness/assert-task-skills.py`.

---

## 4. "pnpm de Skills" — `.agent/` vs `.agents/` (Supply Chain)

| Pasta / Arquivo | Vai para o Git? | Função |
| :--- | :--- | :--- |
| `.agent/` | **Sim** | Meta-harness opinativo do projeto (`rules/`, `system-prompt.md`, `harness/`, skills de arquitetura/scaffold do kit) |
| `.agents/` | **Não** (`.gitignore`) | Skills externas instaladas via CLI (`npx skills`), equivalente a `node_modules/` |
| `skills-lock.json` | **Sim** | Lockfile reproduzível com hashes (`npx skills experimental_install --frozen-lockfile`) |
| `.agent/skills-manifest.json` | **Sim** | Declara dependências entre meta-skills (ex.: `audit-rounds` → 3 skills de auditoria) |

Comandos do dia a dia em qualquer projeto:
```bash
# 1. Restaurar skills externas do lockfile (como pnpm install --frozen-lockfile)
npx skills experimental_install --frozen-lockfile

# 2. Verificar lockfile + grafo de dependências do .agent/skills-manifest.json
node scripts/check-skills.mjs --root .

# 3. Validar se tasks.md vinculou as skills de camada corretamente
python3 .agent/harness/assert-task-skills.py --root .
```

---

## 5. Instalando Atualizações em Projetos (Novos, Sem `.agent/` e Já Existentes)

### A) Atualizar Skills Globais da Máquina (`sigapro-sdd-loop`, `smoke-test-rounds`, `the-fool`, `spec-critic`)
As skills orquestradoras e o `spec-critic` ficam **globais** em `~/.agents/skills/` e `~/.omp/agent/agents/` (por isso não precisam estar copiadas dentro de `<projeto>/.agent/skills/`):
```bash
cd ~/code/omp-harness-kit && git pull && ./install.sh
```

### B) Projeto Novo ou em Andamento **SEM** `.agent/`
Rode 1 comando para criar `.agent/harness/`, `skills-manifest.json`, `skills-lock.json`, `.gitignore` e instalar `tlc-spec-driven` + `qa-report` + `qa-execution`:
```bash
./scripts/apply-project-overlay.sh /caminho/do/seu/projeto --with-qa
```
Depois ajuste `.agent/harness/skill-map.json` caso sua stack tenha skills específicas.

### C) Projeto Existente que **JÁ TEM** `.agent/` (ex.: `sigapro`)
Se o projeto já possui `.agent/rules/`, `audit-rounds`, `tlc-spec-driven` etc., rode o overlay com `--in-agent-dir` (preserva `rules/`, `skill-map.json`, `skills-lock.json` e `.agent/skills/*` existentes):
```bash
# Apenas overlay (assert-task-skills.py, skills-manifest.json, skills-lock.json) + hook no tlc-spec-driven:
./scripts/apply-project-overlay.sh ~/envolva-ti/sigapro --in-agent-dir --skip-sync

# Ou tambem atualizar tlc-spec-driven + qa-report + qa-execution upstream:
./scripts/apply-project-overlay.sh ~/envolva-ti/sigapro --in-agent-dir --with-qa
```

> **Procurando kits completos já opinativos por stack (`rules/`, scaffolds, arquitetura)?**
> Este repositório é o **motor global agnóstico de stack**. Para projetos prontos com regras de arquitetura, scaffolds (`scaffold-feature.sh`, `scaffold-use-case.sh`, etc.) e skills nativas, confira os starter kits irmãos:
>
> | Stack | Repositório |
> | :--- | :--- |
> | **Next.js 16 + React 19 + Vanilla Extract (Clean Arch + FSD + MVVM)** | [`wjuniorw/nextjs-ai-ready-kit`](https://github.com/wjuniorw/nextjs-ai-ready-kit) |
> | **NestJS 11+ Modular Monolith + Tactical DDD + CBAC** | [`wjuniorw/nestjs-api-ai-ready-kit`](https://github.com/wjuniorw/nestjs-api-ai-ready-kit) |
> | **Golang API + Standard Layout + Clean Arch** | [`wjuniorw/golang-api-ai-ready-kit`](https://github.com/wjuniorw/golang-api-ai-ready-kit) |
> | **Expo Mobile + Expo Router + Unistyles + MVVM** | [`wjuniorw/expo-mobile-ai-ready-kit`](https://github.com/wjuniorw/expo-mobile-ai-ready-kit) |
> | **Bare React Native CLI (New Arch) + React Navigation + MVVM** | [`wjuniorw/rn-community-cli-ai-ready-kit`](https://github.com/wjuniorw/rn-community-cli-ai-ready-kit) |

---

## 6. Diagnóstico & Setup Assistido por IA (`.llms.md`)

Prefere que um agente diagnostique sua máquina, teste o OmniRoute/Gateway, detecte a stack do projeto e configure o overlay automaticamente? Aponte seu agente para `.llms.md`:

```bash
omp "Leia ~/code/omp-harness-kit/.llms.md, diagnostique meu ambiente e este projeto, e configure o que faltar."
```
