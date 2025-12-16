import { ChatContainer } from "@/components/chat/ChatContainer";

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
    <div className="h-[calc(100vh-4rem)] -mx-6 -my-8 lg:-mx-10 bg-transparent">
      <ChatContainer
        characterId={characterId}
        episodeTemplateId={episodeTemplateId}
      />
    </div>
  );
}
