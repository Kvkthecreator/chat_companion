import { createRouteHandlerClient } from "@/lib/supabase/clients";
import { cookies } from "next/headers";
import { NextResponse } from "next/server";

export async function POST() {
  const cookieStore = cookies();
  const supabase = createRouteHandlerClient({ cookies: () => cookieStore });

  const {
    data: { user },
    error: authError,
  } = await supabase.auth.getUser();

  if (authError || !user) {
    return NextResponse.json({ status: "error", message: "Unauthorized" }, { status: 401 });
  }

  try {
    const { data: membership, error: membershipError } = await supabase
      .from("workspace_memberships")
      .select("workspace_id")
      .eq("user_id", user.id)
      .maybeSingle();

    if (membershipError) {
      console.error("❌ Error checking workspace membership:", membershipError);
      return NextResponse.json(
        { status: "error", message: membershipError.message },
        { status: 500 },
      );
    }

    if (membership?.workspace_id) {
      return NextResponse.json({ status: "exists", workspace_id: membership.workspace_id });
    }

    const { data: workspace, error: wsError } = await supabase
      .from("workspaces")
      .insert({ owner_id: user.id, name: `${user.email}'s Workspace` })
      .select("id")
      .single();

    if (wsError || !workspace) {
      console.error("❌ Error creating workspace:", wsError);
      return NextResponse.json(
        { status: "error", message: wsError?.message ?? "Workspace creation failed" },
        { status: 500 },
      );
    }

    const { error: memberInsertError } = await supabase
      .from("workspace_memberships")
      .insert({ user_id: user.id, workspace_id: workspace.id, role: "owner" });

    if (memberInsertError) {
      console.error("❌ Error creating workspace membership:", memberInsertError);
      return NextResponse.json(
        { status: "error", message: memberInsertError.message },
        { status: 500 },
      );
    }

    return NextResponse.json({ status: "created", workspace_id: workspace.id });
  } catch (err) {
    console.error("❌ Unexpected error during workspace bootstrap:", err);
    return NextResponse.json({ status: "error", message: "Unexpected error" }, { status: 500 });
  }
}
