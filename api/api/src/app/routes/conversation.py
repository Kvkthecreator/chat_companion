"""Conversation API routes for Chat Companion."""
import json
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.deps import get_db
from app.dependencies import get_current_user_id

router = APIRouter(prefix="/conversations", tags=["Conversations"])


class MessageCreate(BaseModel):
    """Request body for sending a message."""
    content: str


class MessageResponse(BaseModel):
    """Response for a message."""
    id: str
    role: str
    content: str
    created_at: str


class ConversationResponse(BaseModel):
    """Response for a conversation."""
    id: str
    user_id: str
    channel: str
    started_at: str
    ended_at: Optional[str] = None
    message_count: int
    initiated_by: str
    mood_summary: Optional[str] = None
    topics: list = []


@router.get("", response_model=list[ConversationResponse])
async def list_conversations(
    limit: int = 10,
    offset: int = 0,
    user_id: UUID = Depends(get_current_user_id),
    db=Depends(get_db),
):
    """List user's conversations."""
    from app.services.conversation import ConversationService

    service = ConversationService(db)
    conversations = await service.list_conversations(
        user_id=user_id,
        limit=limit,
        offset=offset,
    )

    result = []
    for conv in conversations:
        result.append(ConversationResponse(
            id=str(conv["id"]),
            user_id=str(conv["user_id"]),
            channel=conv["channel"],
            started_at=conv["started_at"].isoformat() if conv.get("started_at") else "",
            ended_at=conv["ended_at"].isoformat() if conv.get("ended_at") else None,
            message_count=conv.get("message_count", 0),
            initiated_by=conv.get("initiated_by", "user"),
            mood_summary=conv.get("mood_summary"),
            topics=json.loads(conv["topics"]) if conv.get("topics") else [],
        ))
    return result


class ConversationCreate(BaseModel):
    """Request body for creating a conversation."""
    channel: str = "web"


@router.post("", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    data: ConversationCreate,
    user_id: UUID = Depends(get_current_user_id),
    db=Depends(get_db),
):
    """Create a new conversation or get existing one for today."""
    from app.services.conversation import ConversationService

    service = ConversationService(db)
    conversation = await service.get_or_create_conversation(
        user_id=user_id,
        channel=data.channel,
        initiated_by="user",
    )

    return ConversationResponse(
        id=str(conversation["id"]),
        user_id=str(conversation["user_id"]),
        channel=conversation["channel"],
        started_at=conversation["started_at"].isoformat() if conversation.get("started_at") else "",
        ended_at=conversation["ended_at"].isoformat() if conversation.get("ended_at") else None,
        message_count=conversation.get("message_count", 0),
        initiated_by=conversation.get("initiated_by", "user"),
        mood_summary=conversation.get("mood_summary"),
        topics=json.loads(conversation["topics"]) if conversation.get("topics") else [],
    )


@router.post("/send", response_model=MessageResponse)
async def send_message(
    data: MessageCreate,
    user_id: UUID = Depends(get_current_user_id),
    db=Depends(get_db),
):
    """Send a message to your companion and get a response.

    This is the main chat endpoint that:
    1. Gets or creates today's conversation
    2. Loads user context (memories, preferences)
    3. Sends to LLM with personalized system prompt
    4. Saves both messages
    5. Extracts new context from the exchange
    """
    from app.services.conversation import ConversationService

    service = ConversationService(db)

    # Get or create conversation for today
    conversation = await service.get_or_create_conversation(
        user_id=user_id,
        channel="web",
        initiated_by="user",
    )

    response = await service.send_message(
        user_id=user_id,
        conversation_id=UUID(str(conversation["id"])),
        content=data.content,
    )

    return MessageResponse(**response)


@router.post("/send/stream")
async def send_message_stream(
    data: MessageCreate,
    user_id: UUID = Depends(get_current_user_id),
    db=Depends(get_db),
):
    """Send a message and stream the response.

    Returns a Server-Sent Events stream with the companion's response.
    """
    from app.services.conversation import ConversationService

    service = ConversationService(db)

    # Get or create conversation for today
    conversation = await service.get_or_create_conversation(
        user_id=user_id,
        channel="web",
        initiated_by="user",
    )

    async def generate():
        try:
            async for chunk in service.send_message_stream(
                user_id=user_id,
                conversation_id=UUID(str(conversation["id"])),
                content=data.content,
            ):
                yield f"data: {chunk}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            import logging
            import traceback
            log = logging.getLogger(__name__)
            log.error(f"Streaming error: {type(e).__name__}: {str(e)}")
            log.error(traceback.format_exc())
            error_msg = f"{type(e).__name__}: {str(e)}" if str(e) else type(e).__name__
            yield f"data: [ERROR] {error_msg}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )


@router.post("/{conversation_id}/messages/stream")
async def send_message_to_conversation_stream(
    conversation_id: UUID,
    data: MessageCreate,
    user_id: UUID = Depends(get_current_user_id),
    db=Depends(get_db),
):
    """Send a message to a specific conversation and stream the response."""
    from app.services.conversation import ConversationService

    service = ConversationService(db)

    # Verify conversation belongs to user
    conversation = await service.get_conversation(conversation_id)
    if not conversation or str(conversation["user_id"]) != str(user_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )

    async def generate():
        try:
            async for chunk in service.send_message_stream(
                user_id=user_id,
                conversation_id=conversation_id,
                content=data.content,
            ):
                yield f"data: {chunk}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            import logging
            import traceback
            log = logging.getLogger(__name__)
            log.error(f"Streaming error: {type(e).__name__}: {str(e)}")
            log.error(traceback.format_exc())
            error_msg = f"{type(e).__name__}: {str(e)}" if str(e) else type(e).__name__
            yield f"data: [ERROR] {error_msg}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )


@router.get("/current", response_model=ConversationResponse)
async def get_current_conversation(
    user_id: UUID = Depends(get_current_user_id),
    db=Depends(get_db),
):
    """Get the current (today's) conversation."""
    from app.services.conversation import ConversationService

    service = ConversationService(db)

    conversation = await service.get_or_create_conversation(
        user_id=user_id,
        channel="web",
        initiated_by="user",
    )

    return ConversationResponse(
        id=str(conversation["id"]),
        user_id=str(conversation["user_id"]),
        channel=conversation["channel"],
        started_at=conversation["started_at"].isoformat() if conversation.get("started_at") else "",
        ended_at=conversation["ended_at"].isoformat() if conversation.get("ended_at") else None,
        message_count=conversation.get("message_count", 0),
        initiated_by=conversation.get("initiated_by", "user"),
        mood_summary=conversation.get("mood_summary"),
        topics=json.loads(conversation["topics"]) if conversation.get("topics") else [],
    )


@router.get("/{conversation_id}/messages")
async def get_conversation_messages(
    conversation_id: UUID,
    limit: int = 50,
    offset: int = 0,
    user_id: UUID = Depends(get_current_user_id),
    db=Depends(get_db),
):
    """Get messages from a conversation."""
    from app.services.conversation import ConversationService

    service = ConversationService(db)

    # Verify conversation belongs to user
    conversation = await service.get_conversation(conversation_id)
    if not conversation or str(conversation["user_id"]) != str(user_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )

    messages = await service.get_messages(
        conversation_id=conversation_id,
        limit=limit,
        offset=offset,
    )

    return messages


@router.post("/{conversation_id}/end")
async def end_conversation(
    conversation_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    db=Depends(get_db),
):
    """End a conversation and generate summary."""
    from app.services.conversation import ConversationService

    service = ConversationService(db)

    # Verify conversation belongs to user
    conversation = await service.get_conversation(conversation_id)
    if not conversation or str(conversation["user_id"]) != str(user_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )

    result = await service.end_conversation(conversation_id)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not end conversation",
        )

    return {
        "id": str(result["id"]),
        "ended_at": result["ended_at"].isoformat() if result.get("ended_at") else None,
        "mood_summary": result.get("mood_summary"),
        "topics": json.loads(result["topics"]) if result.get("topics") else [],
    }
