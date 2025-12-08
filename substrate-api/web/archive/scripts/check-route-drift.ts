import fs from 'fs';
import path from 'path';

const expectedPath = path.join(__dirname, '..', 'route-contracts.json');
const actualPath = path.join(__dirname, '..', 'generated-route-registry.json');

const expected: string[] = JSON.parse(fs.readFileSync(expectedPath, 'utf-8'));
const actual: string[] = JSON.parse(fs.readFileSync(actualPath, 'utf-8'));

const missing = expected.filter((route) => !actual.includes(route));
const extra = actual.filter((route) => !expected.includes(route));

if (missing.length || extra.length) {
  console.error('❌ Route registry drift detected!');
  if (missing.length) {
    console.error('\nMissing in generated routes:');
    missing.forEach((r) => console.error(`  - ${r}`));
  }
  if (extra.length) {
    console.error('\nUnexpected extra routes:');
    extra.forEach((r) => console.error(`  - ${r}`));
  }
  process.exit(1);
} else {
  console.log('✅ Route registry matches expected routes.');
}
