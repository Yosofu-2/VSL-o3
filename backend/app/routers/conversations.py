from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

import json

from app.database import get_db
from app.models.model import Book, Conversation, LLMModel, Message
from app.schemas.model import ChatRequest, ChatResponse, ConversationResponse

router = APIRouter(prefix="/api/conversations", tags=["conversations"])


@router.get("", response_model=List[ConversationResponse])
async def list_conversations(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Conversation)
        .options(selectinload(Conversation.messages))
        .order_by(desc(Conversation.updated_at))
    )
    return result.scalars().all()


@router.get("/{conv_id}", response_model=ConversationResponse)
async def get_conversation(conv_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Conversation)
        .options(selectinload(Conversation.messages))
        .where(Conversation.id == conv_id)
    )
    conv = result.scalar_one_or_none()
    if not conv:
        raise HTTPException(404, "Conversation not found")
    return conv


@router.delete("/{conv_id}", status_code=204)
async def delete_conversation(conv_id: int, db: AsyncSession = Depends(get_db)):
    conv = await db.get(Conversation, conv_id)
    if not conv:
        raise HTTPException(404, "Conversation not found")
    await db.delete(conv)
    await db.commit()


@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest, db: AsyncSession = Depends(get_db)):
    model = await db.get(LLMModel, req.model_id)
    if not model:
        raise HTTPException(404, "Model not found")

    conv_id = req.conversation_id
    if not conv_id:
        title = req.message[:64] if len(req.message) > 0 else "New conversation"
        ctx_ids = json.dumps(req.book_context_ids) if req.book_context_ids else None
        conv = Conversation(
            model_id=req.model_id,
            title=title,
            system_prompt=req.system_prompt,
            context_book_ids=ctx_ids,
        )
        db.add(conv)
        await db.commit()
        await db.refresh(conv)
        conv_id = conv.id

    msg_user = Message(conversation_id=conv_id, role="user", content=req.message)
    db.add(msg_user)
    await db.commit()

    # Build message history for LLM
    hist_result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conv_id)
        .order_by(Message.created_at)
    )
    history = hist_result.scalars().all()

    messages = []
    if req.system_prompt:
        messages.append({"role": "system", "content": req.system_prompt})

    # Add book context if available
    book_context_ids = req.book_context_ids
    if not book_context_ids:
        conv = await db.get(Conversation, conv_id)
        if conv and conv.context_book_ids:
            try:
                book_context_ids = json.loads(conv.context_book_ids)
            except Exception:
                pass

    if book_context_ids:
        book_result = await db.execute(
            select(Book).where(Book.id.in_(book_context_ids))
        )
        book_entries = book_result.scalars().all()
        if book_entries:
            ctx = "\n\n".join(
                f"[ID:{b.id}] {b.title}\n  Authors: {b.authors}\n  Publisher: {b.publisher or '(none)'}"
                for b in book_entries
            )
            messages.append({
                "role": "system",
                "content": f"Related book context:\n{ctx}\n\nAnswer questions based on this context when applicable."
            })

    for m in history:
        messages.append({"role": m.role, "content": m.content})

    # Call LLM
    from app.services.model_service import LLMClient

    client = LLMClient(
        provider=model.provider,
        api_base=model.api_base,
        api_key=model.api_key or "",
        model_name=model.model_name,
        temperature=model.temperature,
        max_tokens=model.max_tokens,
    )

    try:
        data = await client.chat_completion(messages)
        reply = data["choices"][0]["message"]["content"]
        usage = data.get("usage", {})
        tokens_in = usage.get("prompt_tokens", 0)
        tokens_out = usage.get("completion_tokens", 0)
    except Exception as e:
        reply = f"[AI response error: {e}]"
        tokens_in = sum(len(m["content"]) for m in messages)
        tokens_out = len(reply)

    msg_assistant = Message(
        conversation_id=conv_id,
        role="assistant",
        content=reply,
        tokens_in=tokens_in,
        tokens_out=tokens_out,
    )
    db.add(msg_assistant)
    await db.commit()

    return ChatResponse(
        conversation_id=conv_id,
        reply=reply,
        tokens_in=tokens_in,
        tokens_out=tokens_out,
    )


