#!/usr/bin/env node

// Quick script to check Supabase environment variables
console.log('Checking Supabase environment variables...\n');

const requiredEnvVars = [
  'NEXT_PUBLIC_SUPABASE_URL',
  'NEXT_PUBLIC_SUPABASE_ANON_KEY',
  'SUPABASE_SERVICE_ROLE_KEY',
  'DATABASE_URL'
];

let allPresent = true;

requiredEnvVars.forEach(varName => {
  const value = process.env[varName];
  if (value) {
    // Show first 10 chars for security
    const preview = value.substring(0, 10) + '...';
    console.log(`✅ ${varName}: ${preview}`);
  } else {
    console.log(`❌ ${varName}: NOT SET`);
    allPresent = false;
  }
});

console.log('\nAPI Key format check:');
const anonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;
if (anonKey) {
  console.log(`- Length: ${anonKey.length} chars`);
  console.log(`- Starts with: ${anonKey.substring(0, 10)}...`);
  console.log(`- Ends with: ...${anonKey.substring(anonKey.length - 10)}`);
  
  // Check for common issues
  if (anonKey.includes('\n')) {
    console.log('⚠️  WARNING: API key contains newline character!');
  }
  if (anonKey.includes(' ')) {
    console.log('⚠️  WARNING: API key contains space character!');
  }
}

console.log('\n' + (allPresent ? '✅ All environment variables are set!' : '❌ Some environment variables are missing!'));