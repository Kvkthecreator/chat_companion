import { createServerComponentClient } from "@supabase/auth-helpers-nextjs";
import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import type { Database } from "@/lib/dbTypes";

import SettingsSection from "@/components/settings/SettingsSection";
import DisplayBox from "@/components/settings/DisplayBox";
import { DangerZone } from "@/components/settings/DangerZone";
import { ArrowLeft, Settings as SettingsIcon } from "lucide-react";
import Link from "next/link";
import { ensureWorkspaceServer } from "@/lib/workspaces/ensureWorkspaceServer";

export default async function SettingsPage() {
  const supabase = createServerComponentClient<Database>({ cookies });
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    redirect("/login?redirect=/dashboard/settings");
  }

  const displayName =
    (user.user_metadata?.full_name as string) ||
    (user.user_metadata?.name as string) ||
    "Unknown";

  const workspace = await ensureWorkspaceServer(supabase);
  const workspaceId = workspace?.id ?? null;

  return (
    <div className="max-w-4xl mx-auto space-y-6 px-6 py-8">
      {/* Header */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Link
              href="/dashboard/home"
              className="inline-flex items-center gap-2 text-sm text-gray-700 hover:text-gray-900"
              aria-label="Back to Dashboard"
            >
              <ArrowLeft className="h-4 w-4" />
              Back
            </Link>
            <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
              <SettingsIcon className="h-5 w-5 text-blue-600" />
            </div>
            <div>
              <h1 className="text-xl font-semibold text-gray-900">Account Settings</h1>
              <p className="text-gray-600 text-sm">Manage your account and workspace details</p>
            </div>
          </div>
        </div>
      </div>
      <SettingsSection
        title="Settings"
        description="Manage your account preferences and profile details"
      >
        <DisplayBox label="UID" value={user.id} />
        <DisplayBox label="Display Name" value={displayName} />
        <DisplayBox label="Email" value={user.email ?? "Unknown"} />

        {workspaceId ? (
          <DisplayBox label="Workspace ID" value={workspaceId} />
        ) : (
          <div className="rounded-md bg-red-50 p-4 text-red-800 border border-red-200">
            <strong>⚠️ Workspace creation failed</strong>
            <p className="mt-1 text-sm">
              We couldn’t create your workspace. Please try again later or contact support.
            </p>
          </div>
        )}
      </SettingsSection>

      <DangerZone userEmail={user.email ?? ''} />
    </div>
  );
}
