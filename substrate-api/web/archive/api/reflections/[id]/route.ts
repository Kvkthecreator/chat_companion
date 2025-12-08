import { NextRequest, NextResponse } from 'next/server';
import { createServerSupabaseClient } from '@/lib/supabase/server';
import { getAuthenticatedUser } from '@/lib/auth/getAuthenticatedUser';

interface RouteContext {
  params: Promise<{ id: string }>;
}

export async function GET(req: NextRequest, ctx: RouteContext) {
  try {
    const { id } = await ctx.params;
    const supabase = createServerSupabaseClient();
    const { userId } = await getAuthenticatedUser(supabase);

    const { data: reflection, error } = await supabase
      .from('reflections_artifact')
      .select('*')
      .eq('id', id)
      .maybeSingle();

    if (error || !reflection) {
      return NextResponse.json({ error: 'Reflection not found' }, { status: 404 });
    }

    return NextResponse.json(reflection, { status: 200 });
  } catch (e) {
    console.error('Reflection fetch error:', e);
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
}
