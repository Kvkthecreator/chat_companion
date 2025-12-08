import fs from "fs";
import path from "path";

const rules = JSON.parse(fs.readFileSync(path.join(process.cwd(), "api/pipelines/_rules/rpc_allowlist.json"), "utf8"));

type Rule = { dir: string, allowed: string[] };
const sets: Rule[] = [
  { dir: "api/pipelines/p4_presentation", allowed: rules["p4_presentation"] }
];

let violations = 0;

function scan(dir: string, allowed: string[]) {
  const files = fs.readdirSync(dir, { withFileTypes: true });
  for (const f of files) {
    const p = path.join(dir, f.name);
    if (f.isDirectory()) scan(p, allowed);
    else {
      const src = fs.readFileSync(p, "utf8");
      const calls = (src.match(/public\.fn_[a-zA-Z0-9_]+/g) || []).map(s => s.replace(/^public\./, ""));
      for (const c of calls) {
        if (!allowed.includes(`public.${c}`)) {
          console.error(`[P4 Guard] Disallowed RPC in ${p}: public.${c}`);
          violations++;
        }
      }
    }
  }
}

scan("api/pipelines/p4_presentation", sets[0].allowed);

if (violations) process.exit(1);
else console.log("[P4 Guard] OK");