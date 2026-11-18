# OMP Harness Kit (`omp` + SDD Loop + Critic + Supply Chain de Skills)

Kit portável para instalar em segundos o workflow completo de engenharia assistida por IA no **`omp` (Oh My Pi)**, preservando o Meta-Harness específico de cada projeto (`.agent/`) e mantendo skills externas (`.agents/`) gerenciadas como dependências (estilo `pnpm`).

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
│   └── the-fool/                  # Devil's advocate, pre-mortem, red-team, scan de vieses
├── project-overlay/
│   ├── .agent/skills-manifest.json
│   ├── .agent/harness/
│   │   ├── assert-task-skills.py  # Assert deterministico de Skill: em tasks.md (independente de updates!)
│   │   └── skill-map.example.json # Roteamento camada/arquivo -> skill especifica da stack
│   ├── skills-lock.json           # Lockfile compatível com `npx skills experimental_install`
│   └── .gitignore.snippet         # `.agents/` gitignored (igual node_modules/)
├── scripts/
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

1. **Stage 1 — Drafts (`tlc-spec-driven`)**: gera `spec.md`, `design.md` e `tasks.md` e roda `validate_spec.py`, `validate_tasks.py` + `assert-task-skills.py`.
2. **Stage 2 — Revisor Forte + `the-fool` (`spec-critic`)**: dispara o subagente `spec-critic` em contexto limpo (ordem **`claudio-combo` → `cw/claude-sonnet-5-high` → `gemini/gemini-4-argon` → `ds-web/deepseek-v4-pro-think`**) para auditar regras/contratos e rodar pre-mortem/red-team.
3. **Stage 3 — HITL com BTW e Incremento**: abre formulário `ask` apenas para decisões reais, sempre com a opção **"Tirar dúvida / Incrementar esta opção"** e campo `btw_notes` (além de `/btw` ou `Esc`). **Nunca avança para `Execute`** enquanto houver dúvida ou ajuste pendente.
4. **Stage 4 — Execute + Verifier**: executa as tasks ativando a `Skill:` de cada uma, dispara hooks de `.agent/harness/pipeline/` e roda o `Verifier` independente (`validate_state.py`).
5. **Stage 5 — `audit-rounds` → Remediação**: roda auditoria pós-execução (`architectural-analysis`, `security-best-practices`, `security-threat-model` → `risk-register.md`) e reinicia o loop em `remediation-tasks.md` se houver riscos pendentes.

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
./scripts/sync-upstream-skills.sh /caminho/do/seu/projeto --in-agent-dir
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

## 5. Aplicando em Projetos e Templates Existentes (`~/code/templates/`)

Para equipar qualquer template ou projeto existente sem recriar nada do zero:
```bash
cp project-overlay/.agent/skills-manifest.json <projeto>/.agent/
cp project-overlay/.agent/harness/assert-task-skills.py <projeto>/.agent/harness/
cp project-overlay/.agent/harness/skill-map.example.json <projeto>/.agent/harness/skill-map.json
# Adicione .agents/ ao .gitignore do projeto e ajuste skill-map.json para a stack
```

> **Onde ficam as `rules/` e ferramentas de scaffold (`scaffold-feature.sh`, `scaffold-use-case.sh`, etc.)?**
> Este repositório é agnóstico de stack (runtime `omp` + SDD loop + critic + supply chain). Regras e scaffolds opinativos por tecnologia continuam nos kits dedicados (`nextjs-ai-ready-kit`, `nestjs-api-ai-ready-kit`, `golang-api-ai-ready-kit`, `expo-mobile-ai-ready-kit`, `rn-community-cli-ai-ready-kit` e futuro Rust).

---

## 6. Diagnóstico & Setup Assistido por IA (`.llms.md`)

Prefere que um agente diagnostique sua máquina, teste o OmniRoute/Gateway, detecte a stack do projeto e configure o overlay automaticamente? Aponte seu agente para `.llms.md`:

```bash
omp "Leia ~/code/omp-harness-kit/.llms.md, diagnostique meu ambiente e este projeto, e configure o que faltar."
```
