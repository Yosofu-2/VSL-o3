"""Agent router with conversation context support."""

import json
from typing import Optional, List, AsyncGenerator
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.model import LLMModel, Conversation, Message
from app.services.db_agent import DBAgent

router = APIRouter(prefix="/api/agent", tags=["agent"])


class AgentRequest(BaseModel):
    """Single-turn agent request."""
    instruction: str
    model_id: int


class AgentChatRequest(BaseModel):
    """Multi-turn agent chat request with conversation context."""
    message: str
    model_id: int
    conversation_id: Optional[int] = None
    system_prompt: Optional[str] = None


class AgentResponse(BaseModel):
    result: str


class AgentChatResponse(BaseModel):
    conversation_id: int
    reply: str
    tokens_in: int = 0
    tokens_out: int = 0


@router.post("", response_model=AgentResponse)
async def agent_execute(req: AgentRequest, db: AsyncSession = Depends(get_db)):
    """Execute a single-turn agent instruction."""
    model = await db.get(LLMModel, req.model_id)
    if not model:
        raise HTTPException(404, f"Model #{req.model_id} not found")
    agent = DBAgent(model_id=req.model_id, db=db)
    result = await agent.execute(req.instruction)
    return AgentResponse(result=result)


@router.post("/chat", response_model=AgentChatResponse)
async def agent_chat(req: AgentChatRequest, db: AsyncSession = Depends(get_db)):
    """Multi-turn agent chat with conversation history and tool calling."""
    model = await db.get(LLMModel, req.model_id)
    if not model:
        raise HTTPException(404, f"Model #{req.model_id} not found")

    # Get or create conversation
    conv_id = req.conversation_id
    if not conv_id:
        title = req.message[:64] if req.message else "Agent Chat"
        conv = Conversation(
            model_id=req.model_id,
            title=title,
            system_prompt=req.system_prompt,
        )
        db.add(conv)
        await db.commit()
        await db.refresh(conv)
        conv_id = conv.id

    # Save user message
    user_msg = Message(
        conversation_id=conv_id,
        role="user",
        content=req.message,
    )
    db.add(user_msg)
    await db.commit()

    # Execute agent with conversation context
    agent = DBAgent(model_id=req.model_id, db=db)
    
    # Build conversation history for context
    history_result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conv_id)
        .order_by(Message.created_at)
    )
    history = history_result.scalars().all()
    
    # Build full instruction with history context
    if len(history) > 1:
        history_context = "\n".join([
            f"{'User' if m.role == 'user' else 'Assistant'}: {m.content}"
            for m in history[:-1]  # Exclude current message
        ])
        full_instruction = f"Conversation history:\n{history_context}\n\nCurrent instruction: {req.message}"
    else:
        full_instruction = req.message

    result = await agent.execute(full_instruction)

    # Save assistant response
    assistant_msg = Message(
        conversation_id=conv_id,
        role="assistant",
        content=result,
    )
    db.add(assistant_msg)
    await db.commit()

    return AgentChatResponse(
        conversation_id=conv_id,
        reply=result,
    )


@router.post("/chat-stream")
async def agent_chat_stream(req: AgentChatRequest, db: AsyncSession = Depends(get_db)):
    """Multi-turn agent chat with streaming response (SSE)."""
    model = await db.get(LLMModel, req.model_id)
    if not model:
        raise HTTPException(404, f"Model #{req.model_id} not found")

    # Get or create conversation
    conv_id = req.conversation_id
    if not conv_id:
        title = req.message[:64] if req.message else "Agent Chat"
        conv = Conversation(
            model_id=req.model_id,
            title=title,
            system_prompt=req.system_prompt,
        )
        db.add(conv)
        await db.commit()
        await db.refresh(conv)
        conv_id = conv.id

    # Save user message
    user_msg = Message(
        conversation_id=conv_id,
        role="user",
        content=req.message,
    )
    db.add(user_msg)
    await db.commit()

    # Build conversation history for context
    history_result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conv_id)
        .order_by(Message.created_at)
    )
    history = history_result.scalars().all()
    
    # Build full instruction with history context
    if len(history) > 1:
        history_context = "\n".join([
            f"{'User' if m.role == 'user' else 'Assistant'}: {m.content}"
            for m in history[:-1]
        ])
        full_instruction = f"Conversation history:\n{history_context}\n\nCurrent instruction: {req.message}"
    else:
        full_instruction = req.message

    async def generate() -> AsyncGenerator[str, None]:
        """Generate SSE stream."""
        full_response = ""
        try:
            # Use DBAgent which handles both keyword dispatch and LLM fallback
            agent = DBAgent(model_id=req.model_id, db=db)
            full_response = await agent.execute(full_instruction)

            # Send as chunks for typing effect
            chunk_size = 20
            for i in range(0, len(full_response), chunk_size):
                chunk = full_response[i:i+chunk_size]
                yield f"data: {json.dumps({'type': 'chunk', 'content': chunk})}\n\n"
                import asyncio
                await asyncio.sleep(0.02)

            # Send completion signal
            yield f"data: {json.dumps({'type': 'done', 'conversation_id': conv_id, 'full_response': full_response})}\n\n"

            # Save assistant response
            assistant_msg = Message(
                conversation_id=conv_id,
                role="assistant",
                content=full_response,
            )
            db.add(assistant_msg)
            await db.commit()

        except Exception as e:
            error_msg = f"[Error] {str(e)}"
            yield f"data: {json.dumps({'type': 'error', 'content': error_msg})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


@router.get("/models", response_model=list[dict])
async def agent_list_models(db: AsyncSession = Depends(get_db)):
    """List available models for agent."""
    result = await db.execute(select(LLMModel).order_by(LLMModel.id))
    models = result.scalars().all()
    return [{"id": m.id, "name": m.name, "provider": m.provider, "model_name": m.model_name} for m in models]


@router.get("/conversations", response_model=List[dict])
async def list_agent_conversations(db: AsyncSession = Depends(get_db)):
    """List all agent conversations."""
    result = await db.execute(
        select(Conversation)
        .options(selectinload(Conversation.messages))
        .order_by(desc(Conversation.updated_at))
    )
    convs = result.scalars().all()
    return [
        {
            "id": c.id,
            "title": c.title,
            "model_id": c.model_id,
            "created_at": str(c.created_at) if c.created_at else "",
            "updated_at": str(c.updated_at) if c.updated_at else "",
            "message_count": len(c.messages),
        }
        for c in convs
    ]


@router.get("/conversations/{conv_id}", response_model=dict)
async def get_agent_conversation(conv_id: int, db: AsyncSession = Depends(get_db)):
    """Get a specific agent conversation with messages."""
    result = await db.execute(
        select(Conversation)
        .options(selectinload(Conversation.messages))
        .where(Conversation.id == conv_id)
    )
    conv = result.scalar_one_or_none()
    if not conv:
        raise HTTPException(404, "Conversation not found")
    
    return {
        "id": conv.id,
        "title": conv.title,
        "model_id": conv.model_id,
        "created_at": str(conv.created_at) if conv.created_at else "",
        "messages": [
            {
                "id": m.id,
                "role": m.role,
                "content": m.content,
                "created_at": str(m.created_at) if m.created_at else "",
            }
            for m in conv.messages
        ],
    }


@router.delete("/conversations/{conv_id}", status_code=204)
async def delete_agent_conversation(conv_id: int, db: AsyncSession = Depends(get_db)):
    """Delete an agent conversation."""
    conv = await db.get(Conversation, conv_id)
    if not conv:
        raise HTTPException(404, "Conversation not found")
    await db.delete(conv)
    await db.commit()
