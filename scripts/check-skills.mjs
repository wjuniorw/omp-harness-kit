#!/usr/bin/env node
/**
 * check-skills.mjs - "pnpm check" para skills de agentes.
 * Valida:
 *  1) .gitignore contem .agents/ (quando skills-lock.json existe)
 *  2) Todas as skills em skills-lock.json existem localmente (.agents/skills ou ~/.agents/skills)
 *  3) Grafo de dependencias em .agent/skills-manifest.json esta satisfeito
 *     (ex.: audit-rounds -> architectural-analysis, security-best-practices, security-threat-model)
 */

import fs from "node:fs";
import path from "node:path";
import os from "node:os";

const args = process.argv.slice(2);
let root = process.cwd();
const rootIdx = args.indexOf("--root");
if (rootIdx !== -1 && args[rootIdx + 1]) {
  root = path.resolve(args[rootIdx + 1]);
}

const searchDirs = [
  path.join(root, ".agent", "skills"),
  path.join(root, ".agents", "skills"),
  path.join(os.homedir(), ".agents", "skills"),
];

function findSkill(name) {
  for (const dir of searchDirs) {
    const candidate = path.join(dir, name, "SKILL.md");
    if (fs.existsSync(candidate)) return candidate;
  }
  return null;
}

const errors = [];
const warnings = [];

// 1. Check .gitignore vs skills-lock.json
const lockPath = path.join(root, "skills-lock.json");
const gitignorePath = path.join(root, ".gitignore");
if (fs.existsSync(lockPath)) {
  if (!fs.existsSync(gitignorePath)) {
    warnings.push("skills-lock.json existe, mas .gitignore nao foi encontrado (adicione .agents/ no .gitignore).");
  } else {
    const gi = fs.readFileSync(gitignorePath, "utf8");
    if (!/^\s*\.agents\/?/m.test(gi)) {
      warnings.push(".gitignore ainda nao ignora .agents/ (recomendado manter .agents/ fora do git igual node_modules/).");
    }
  }

  try {
    const lock = JSON.parse(fs.readFileSync(lockPath, "utf8"));
    const locked = Object.keys(lock.skills || {});
    for (const skill of locked) {
      if (!findSkill(skill)) {
        errors.push(`Skill do lockfile ausente: '${skill}'. Rode: npx skills experimental_install --frozen-lockfile`);
      }
    }
  } catch (err) {
    errors.push(`Falha ao ler skills-lock.json: ${err.message}`);
  }
}

// 2. Check .agent/skills-manifest.json
const manifestPath = path.join(root, ".agent", "skills-manifest.json");
if (fs.existsSync(manifestPath)) {
  try {
    const manifest = JSON.parse(fs.readFileSync(manifestPath, "utf8"));
    for (const req of manifest.required || []) {
      if (!findSkill(req)) {
        errors.push(`Skill obrigatoria do projeto ausente: '${req}'`);
      }
    }
    const deps = manifest.dependencies || {};
    for (const [parent, children] of Object.entries(deps)) {
      if (findSkill(parent)) {
        for (const child of children) {
          if (!findSkill(child)) {
            errors.push(`Meta-skill '${parent}' depende de '${child}', que nao foi encontrada em .agent/skills, .agents/skills ou ~/.agents/skills.`);
          }
        }
      }
    }
    const recs = manifest.recommended || {};
    for (const [parent, children] of Object.entries(recs)) {
      if (findSkill(parent)) {
        for (const child of children) {
          if (!findSkill(child)) {
            warnings.push(`Skill recomendada para '${parent}' ausente: '${child}'. Instale via: npx skills add pedronauck/skills -s ${child} -a universal -y`);
          }
        }
      }
    }
  } catch (err) {
    errors.push(`Falha ao ler .agent/skills-manifest.json: ${err.message}`);
  }
}

for (const w of warnings) console.warn(`WARN: ${w}`);
for (const e of errors) console.error(`ERROR: ${e}`);

if (errors.length === 0) {
  console.log(`check-skills PASS (${root})`);
  process.exit(0);
}
process.exit(1);
