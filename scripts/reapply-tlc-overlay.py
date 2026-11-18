#!/usr/bin/env python3
"""
reapply-tlc-overlay.py - Idempotentemente reanexa o gancho de assert de skills
em tlc-spec-driven (.agent/skills/ ou .agents/skills/) apos updates upstream.

O assert real vive fora da pasta da skill (.agent/harness/assert-task-skills.py
+ .agent/harness/skill-map.json), entao updates upstream nunca apagam suas regras.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

START = "<!-- META-HARNESS-SKILL-ASSERT:START -->"
END = "<!-- META-HARNESS-SKILL-ASSERT:END -->"

BLOCKS = {
    "SKILL.md": f"""{START}
## Meta-Harness Skill Binding (Overlay Preservado)
Antes de aprovar `tasks.md` e antes de executar qualquer task:
1. Consulte `.agent/harness/skill-map.json` (se existir) para mapear automaticamente a camada/arquivo da task para a skill nativa correta do projeto.
2. Nunca deixe `Skill: NONE` em tasks de codigo quando houver skill correspondente no mapa ou em `.agent/skills/`.
3. Execute `python3 .agent/harness/assert-task-skills.py --root .` junto com `validate_tasks.py`.
{END}""",
    "references/tasks.md": f"""{START}
### Meta-Harness Skill Assertion (Obrigatorio)
Toda task que cria/altera codigo ou testes deve preencher `- Skill: <nome-da-skill>` consultando `.agent/harness/skill-map.json` (fallback: `.agent/skills/*/SKILL.md`).
Antes de apresentar `tasks.md` ao humano, execute:
`python3 .agent/harness/assert-task-skills.py <tasks-path> --root .`
{END}""",
    "references/implement.md": f"""{START}
### Meta-Harness Skill Activation (Antes de Codar)
Antes de editar arquivos de uma task, leia obrigatoriamente `skill://<skill>` (ou `.agent/skills/<skill>/SKILL.md` / `.agents/skills/<skill>/SKILL.md`) declarada no campo `Skill:` da task.
{END}""",
}


def upsert_block(file_path: Path, block: str) -> str:
    if not file_path.exists():
        return "missing"
    text = file_path.read_text(encoding="utf-8")
    if START in text and END in text:
        before = text.split(START, 1)[0].rstrip()
        after = text.split(END, 1)[1].lstrip()
        new_text = f"{before}\n\n{block}\n" + (f"\n{after}" if after else "")
        if new_text == text:
            return "unchanged"
        file_path.write_text(new_text, encoding="utf-8")
        return "updated"
    new_text = text.rstrip() + "\n\n" + block + "\n"
    file_path.write_text(new_text, encoding="utf-8")
    return "injected"


def main() -> int:
    parser = argparse.ArgumentParser(description="Reaplica overlay de Skill assertion no tlc-spec-driven")
    parser.add_argument("--project", default=".", help="Raiz do projeto ou template")
    args = parser.parse_args()

    root = Path(args.project).resolve()
    candidates = [
        root / ".agent" / "skills" / "tlc-spec-driven",
        root / ".agents" / "skills" / "tlc-spec-driven",
    ]
    found = [p for p in candidates if p.is_dir()]
    if not found:
        print(f"ERRO: tlc-spec-driven nao encontrado em .agent/skills/ nem .agents/skills/ de {root}", file=sys.stderr)
        return 2

    for tlc_dir in found:
        for rel, block in BLOCKS.items():
            status = upsert_block(tlc_dir / rel, block)
            print(f"{tlc_dir / rel}: {status}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
