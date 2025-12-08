import fs from 'fs';
import path from 'path';

function extractRef(url) {
  const match = url?.match(/^https:\/\/([^.]+)\.supabase\.co/);
  return match ? match[1] : null;
}

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
const jwksUrl = process.env.SUPABASE_JWKS_URL;
const issuer = process.env.SUPABASE_JWKS_ISSUER;

if (!supabaseUrl || !jwksUrl || !issuer) {
  console.error('Missing Supabase env vars');
  process.exit(1);
}

const refUrl = extractRef(supabaseUrl);
const refJwks = extractRef(jwksUrl);
const refIssuer = extractRef(issuer);

if (!refUrl || refUrl !== refJwks || refUrl !== refIssuer) {
  console.error('Supabase project refs mismatch');
  process.exit(1);
}

function walk(dir, cb) {
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const res = path.join(dir, entry.name);
    if (entry.isDirectory()) walk(res, cb);
    else cb(res);
  }
}

// Ensure all API proxies using NEXT_PUBLIC_API_BASE_URL run on node and forward tokens
const routeFiles = [];
walk('web/app/api', (file) => {
  if (file.endsWith('route.ts')) routeFiles.push(file);
});
for (const file of routeFiles) {
  const content = fs.readFileSync(file, 'utf8');
  if (content.includes('NEXT_PUBLIC_API_BASE_URL')) {
    if (!content.includes('export const runtime = "nodejs"')) {
      console.error(`${file} missing runtime export`);
      process.exit(1);
    }
    if (!content.includes('cache: "no-store"') && !content.includes("cache: 'no-store'")) {
      console.error(`${file} missing cache no-store`);
      process.exit(1);
    }
    if (!content.includes('sb-access-token') || !content.includes('Authorization: `Bearer')) {
      console.error(`${file} missing auth header forwarding`);
      process.exit(1);
    }
    if (content.includes('next/headers')) {
      console.warn(`WARN: ${file} uses next/headers()`);
    }
  }
}

// Fail on hardcoded api.yarnnn.com
let literalFound = false;
walk('web', (file) => {
  if (file.includes('node_modules')) return;
  if (
    file.includes(`${path.sep}tests${path.sep}`) ||
    file.includes(`${path.sep}__tests__${path.sep}`) ||
    file.includes(`${path.sep}__mocks__${path.sep}`) ||
    file.includes(`${path.sep}fixtures${path.sep}`)
  )
    return;
  if (!file.match(/\.(tsx?|jsx?|mjs|cjs)$/)) return;
  const content = fs.readFileSync(file, 'utf8');
  if (content.includes('https://api.yarnnn.com')) {
    console.error(`Disallowed api.yarnnn.com literal in ${file}`);
    literalFound = true;
  }
});
if (literalFound) process.exit(1);

// Ensure client code doesn't send workspace_id
walk('web', (file) => {
  if (file.includes(`${path.sep}app${path.sep}api${path.sep}`)) return;
  if (file.includes(`${path.sep}lib${path.sep}`)) return;
  if (!file.match(/\.(tsx?|jsx?)$/)) return;
  const content = fs.readFileSync(file, 'utf8');
  if (
    content.includes("localStorage.getItem('workspace_id')") ||
    content.includes('X-Workspace-Id')
  ) {
    console.error(`workspace_id found in client code: ${file}`);
    process.exit(1);
  }
});

console.log('Auth handshake check passed');
