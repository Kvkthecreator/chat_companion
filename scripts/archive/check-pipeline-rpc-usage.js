const fs = require("fs");
const path = require("path");

const RULES = JSON.parse(fs.readFileSync(path.join(process.cwd(), "api/pipelines/_rules/rpc_allowlist.json"), "utf8"));

const SETS = [
  { dir: "api/pipelines/p0_capture",      allowed: RULES["p0_capture"] || [] },
  { dir: "api/pipelines/p1_substrate",    allowed: RULES["p1_substrate"] || [] },
  { dir: "api/pipelines/p2_graph",        allowed: RULES["p2_graph"] || [] },
  { dir: "api/pipelines/p3_signals",      allowed: RULES["p3_signals"] || [] },
  { dir: "api/pipelines/p4_presentation", allowed: RULES["p4_presentation"] || [] }
];

let violations = 0;

function scanFile(file, allowed) {
  const src = fs.readFileSync(file, "utf8");
  const calls = (src.match(/public\.fn_[a-zA-Z0-9_]+/g) || []).map(s => s.replace(/^public\./, ""));
  for (const c of calls) {
    const fq = `public.${c}`;
    if (!allowed.includes(fq)) {
      console.error(`[Guard] Disallowed RPC in ${file}: ${fq}`);
      violations++;
    }
  }
}

function walk(dir, allowed) {
  if (!fs.existsSync(dir)) return;
  for (const ent of fs.readdirSync(dir, { withFileTypes: true })) {
    const p = path.join(dir, ent.name);
    if (ent.isDirectory()) walk(p, allowed);
    else if (/\.(ts|tsx|js|mjs|cjs)$/.test(ent.name)) scanFile(p, allowed);
  }
}

for (const set of SETS) walk(set.dir, set.allowed);

if (violations) process.exit(1);
console.log("[Guard] OK");