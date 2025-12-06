/**
 * Page: /projects/[id]/context/new/[schemaRole] - Create New Context Item
 *
 * This page handles creation of new context items by schema role.
 * It loads the schema and renders the detail client in "new" mode.
 */

import { cookies } from "next/headers";
import { createServerComponentClient } from "@/lib/supabase/clients";
import { getAuthenticatedUser } from "@/lib/auth/getAuthenticatedUser";
import Link from "next/link";
import { Button } from "@/components/ui/Button";
import { ArrowLeft } from "lucide-react";
import ContextItemDetailClient from "../../[itemId]/ContextItemDetailClient";

interface PageProps {
  params: Promise<{ id: string; schemaRole: string }>;
}

export default async function NewContextItemPage({ params }: PageProps) {
  const { id: projectId, schemaRole } = await params;

  const supabase = createServerComponentClient({ cookies });
  const { userId } = await getAuthenticatedUser(supabase);

  // Fetch project
  const { data: project, error: projectError } = await supabase
    .from('projects')
    .select('id, name, basket_id, workspace_id')
    .eq('id', projectId)
    .maybeSingle();

  if (projectError || !project) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="text-center">
          <h2 className="text-xl font-semibold text-foreground">Project not found</h2>
          <Link href="/projects" className="mt-4 inline-block">
            <Button variant="outline">Back to Projects</Button>
          </Link>
        </div>
      </div>
    );
  }

  if (!project.basket_id) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="text-center">
          <h2 className="text-xl font-semibold text-foreground">No Context Available</h2>
          <Link href={`/projects/${projectId}`} className="mt-4 inline-block">
            <Button variant="outline">Back to Project</Button>
          </Link>
        </div>
      </div>
    );
  }

  // Fetch the schema for this role
  const { data: schema, error: schemaError } = await supabase
    .from('context_entry_schemas')
    .select('*')
    .eq('anchor_role', schemaRole)
    .maybeSingle();

  if (schemaError || !schema) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="text-center">
          <h2 className="text-xl font-semibold text-foreground">Schema not found</h2>
          <p className="text-muted-foreground mt-2">
            Unable to find schema for &quot;{schemaRole}&quot;
          </p>
          <Link href={`/projects/${projectId}/context`} className="mt-4 inline-block">
            <Button variant="outline">Back to Context</Button>
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <div className="border-b border-border bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 sticky top-0 z-10">
        <div className="mx-auto max-w-7xl px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Link
                href={`/projects/${projectId}/context`}
                className="inline-flex items-center text-sm text-muted-foreground hover:text-foreground transition-colors"
              >
                <ArrowLeft className="h-4 w-4 mr-1" />
                Back to Context
              </Link>
              <div className="h-4 w-px bg-border" />
              <span className="text-sm text-muted-foreground">{project.name}</span>
              <div className="h-4 w-px bg-border" />
              <span className="text-sm font-medium">New {schema.display_name}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <ContextItemDetailClient
        projectId={projectId}
        basketId={project.basket_id}
        item={null}
        schema={schema}
        isNew={true}
        schemaRole={schemaRole}
      />
    </div>
  );
}
