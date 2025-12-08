import { cookies } from 'next/headers';
import { notFound } from 'next/navigation';
import { createServerComponentClient } from '@/lib/supabase/clients';
import { getAuthenticatedUser } from '@/lib/auth/getAuthenticatedUser';
import { ensureWorkspaceForUser } from '@/lib/workspaces/ensureWorkspaceForUser';
import { ProductBrainSetupWizard, type SetupWizardStepSpec } from '@/components/wizard/ProductBrainSetupWizard';

interface PageProps {
  params: Promise<{ id: string }>;
}

const DEFAULT_SETUP_STEPS: SetupWizardStepSpec[] = [
  {
    id: 'step1_vision',
    field: 'product_vision',
    question: 'What product are you building, and why now?',
    prompt: 'Describe your product vision in 2-3 sentences. What makes this the right solution at this moment?',
    placeholder: 'e.g., "AI-powered PRD assistant for solo founders who waste weeks writing specs."',
    inputType: 'textarea',
    anchorRefs: ['product_vision', 'core_solution'],
    minLength: 50,
  },
  {
    id: 'step2_problem',
    field: 'core_problem',
    question: 'What problem does this solve?',
    prompt: 'What is the specific pain your users experience today?',
    placeholder: 'e.g., "Solo founders spend 40+ hours writing PRDs instead of building."',
    inputType: 'textarea',
    anchorRefs: ['core_problem'],
    minLength: 30,
  },
  {
    id: 'step3_customer',
    field: 'core_customer',
    question: 'Who are you building for?',
    prompt: 'Describe your primary customer profile and their context.',
    placeholder: 'e.g., "Founders shipping MVPs with limited engineering bandwidth."',
    inputType: 'textarea',
    anchorRefs: ['core_customer'],
    minLength: 30,
  },
  {
    id: 'step4_solution',
    field: 'core_solution',
    question: 'How does your solution address the problem?',
    prompt: 'Outline the core capabilities or experience customers receive.',
    placeholder: 'e.g., "Structured capture -> governance approval -> PRD + prompt pack generation."',
    inputType: 'textarea',
    anchorRefs: ['core_solution'],
    minLength: 40,
  },
  {
    id: 'step5_metrics',
    field: 'success_metrics',
    question: 'How will you measure success?',
    prompt: 'List 2-3 metrics or signals that prove the product is working.',
    placeholder: 'e.g., "Time to first PRD < 30 minutes" · "2 retained teams after pilot"',
    inputType: 'textarea',
    anchorRefs: ['success_metrics'],
    optional: true,
  },
];

export default async function SetupWizardPage({ params }: PageProps) {
  const { id: basketId } = await params;
  const supabase = createServerComponentClient({ cookies });
  const { userId } = await getAuthenticatedUser(supabase);
  const workspace = await ensureWorkspaceForUser(userId, supabase);

  const { data: basket, error } = await supabase
    .from('baskets')
    .select('id, workspace_id, name, status')
    .eq('id', basketId)
    .maybeSingle();

  if (error || !basket || basket.workspace_id !== workspace.id) {
    notFound();
  }

  return (
    <ProductBrainSetupWizard
      basketId={basketId}
      steps={DEFAULT_SETUP_STEPS}
      basketName={basket.name || 'your basket'}
    />
  );
}
