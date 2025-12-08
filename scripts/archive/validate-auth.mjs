import { createClient } from '@supabase/supabase-js';

async function main() {
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const anon = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;
  const email = process.env.TEST_EMAIL;
  const password = process.env.TEST_PASSWORD;
  const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL;
  if (!url || !anon || !email || !password || !apiBase) {
    console.error('Missing required env vars');
    process.exit(1);
  }
  const supabase = createClient(url, anon, { auth: { persistSession: false } });
  const { data, error } = await supabase.auth.signInWithPassword({ email, password });
  if (error || !data.session) {
    console.error('Login failed:', error);
    process.exit(1);
  }
  const token = data.session.access_token;
  const res = await fetch(`${apiBase}/api/workspaces`, {
    headers: {
      Authorization: `Bearer ${token}`,
      apikey: anon,
      'sb-access-token': token,
    },
  });
  console.log('Status:', res.status);
  const text = await res.text();
  console.log(text);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
