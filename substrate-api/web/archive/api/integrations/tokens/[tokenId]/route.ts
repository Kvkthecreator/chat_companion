import { NextRequest, NextResponse } from "next/server";
import { cookies } from "next/headers";
import { createRouteHandlerClient } from "@/lib/supabase/clients";

const API_BASE_URL = process.env.BACKEND_URL || process.env.NEXT_PUBLIC_API_BASE_URL;

async function getSessionToken() {
  const supabase = createRouteHandlerClient({ cookies });
  const { data: { session }, error } = await supabase.auth.getSession();
  if (error || !session) {
    return null;
  }
  return session.access_token ?? null;
}

export async function DELETE(
  _req: NextRequest,
  { params }: { params: { tokenId: string } }
) {
  if (!API_BASE_URL) {
    return NextResponse.json({ error: "Backend URL not configured" }, { status: 500 });
  }
  const token = await getSessionToken();
  if (!token) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }
  const response = await fetch(`${API_BASE_URL}/api/integrations/tokens/${params.tokenId}`, {
    method: "DELETE",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
  });

  if (response.status === 204) {
    return NextResponse.json({ success: true }, { status: 204 });
  }

  const data = await response.json().catch(() => ({}));
  return NextResponse.json(data, { status: response.status });
}
