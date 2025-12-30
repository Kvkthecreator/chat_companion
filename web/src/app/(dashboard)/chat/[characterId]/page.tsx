import { ChatContainer } from "@/components/chat";
interface ChatPageProps {
  params: Promise<{
    characterId: string;
  }>;
  searchParams: Promise<{
    episode?: string;
  }>;
}

export default async function ChatPage({ params, searchParams }: ChatPageProps) {
  const { characterId } = await params;
  const { episode: episodeTemplateId } = await searchParams;

  return (
    <div className="h-full w-full">
      <ChatContainer
        characterId={characterId}
        episodeTemplateId={episodeTemplateId}
      />
    </div>
  );
}
