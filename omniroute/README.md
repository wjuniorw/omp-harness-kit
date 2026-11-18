# OmniRoute Local — Guia Rápido para Convidados

Se você está usando este kit **fora da infra Sigapro**, suba sua própria instância do **OmniRoute** (local ou VPS) e aponte o `install.sh` para `http://localhost:20128/v1`.

## 1. Subindo o OmniRoute (Docker)

```bash
docker run -d --name omniroute \
  -p 20128:20128 \
  -v omniroute-data:/app/data \
  omniroute/omniroute:latest
```

Acesse o painel local (`http://localhost:20128`), conecte os provedores que você possui cota/assinatura (ex.: Claude Web/API, Gemini/Vertex/AI Studio, DeepSeek, OpenRouter, etc.) e crie uma **API Key** para uso no `omp`.

## 2. Criando os Combos Recomendados

Importe ou recrie os combos descritos em `omniroute-combos.example.json`:

1. **`wjunior-coding`** (combo padrão de código — role `default`):
   - Roteia modelos rápidos de codificação primeiro (ex.: Gemini Hydrogen / Flash, DeepSeek Chat, Qwen Coder) com fallback automático para modelos de raciocínio se bater rate-limit.
2. **`claudio-combo`** (rotação de contas Claude):
   - Agrupa suas contas/conexões Claude (Opus/Sonnet) com `strategy: round-robin` ou `fill-first`, garantindo que o `spec-critic` e `slow`/`plan` aproveitem toda sua cota de Claude antes de cair para `gemini/gemini-4-argon`.
3. **`auto/coding`, `auto/coding:cheap`, `auto/coding:free`, `auto/coding:reliable`, `auto/best-coding-fast`**:
   - Combos auxiliares usados pelas roles `smol`, `commit`, `vision`, `judge` e cadeias de retry em `omp/config.yml`.

## 3. Boas Práticas de Isolamento de Cota

- Crie **chaves separadas** por perfil (ex.: `omp-dev-key` vs `sre-agent-key`).
- Na chave de desenvolvimento (`omp-dev-key`), habilite `model_access_mode: restricted` com `allowed_connections` contendo apenas suas conexões de desenvolvimento — nunca misture conexões reservadas a produção/SRE.
- Sempre que alterar permissões diretamente no SQLite do OmniRoute, reinicie o container para limpar o cache de autenticação em memória.
