import fs from 'fs';
import path from 'path';

const apiDir = path.join(__dirname, '..', 'app', 'api');
const outputFile = path.join(__dirname, '..', 'generated-route-registry.json');

function scanRoutes(dir: string, baseRoute = '/api'): string[] {
  const entries = fs.readdirSync(dir, { withFileTypes: true });
  let routes: string[] = [];

  for (const entry of entries) {
    const fullPath = path.join(dir, entry.name);
    const routePath = path.join(baseRoute, entry.name).replace(/\\/g, '/');

    if (entry.isDirectory()) {
      routes = routes.concat(scanRoutes(fullPath, routePath));
    } else if (entry.isFile() && entry.name === 'route.ts') {
      const cleanRoute = baseRoute.replace(/\\/g, '/');
      routes.push(cleanRoute);
    }
  }

  return routes;
}

const routes = scanRoutes(apiDir).sort();
fs.writeFileSync(outputFile, JSON.stringify(routes, null, 2) + '\n');
console.log(`✅ Route registry written to ${outputFile}`);
