from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.model import LLMModel
from app.schemas.model import LLMModelCreate, LLMModelResponse, LLMModelUpdate
from app.services.model_service import LLMClient

import httpx

router = APIRouter(prefix="/api/models", tags=["models"])


@router.get("", response_model=List[LLMModelResponse])
async def list_models(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(LLMModel).order_by(LLMModel.sort_order, LLMModel.id))
    return result.scalars().all()


@router.get("/ollama-list")
async def list_ollama_models(api_base: str = Query("http://localhost:11434")):
    """Fetch available models from a local Ollama instance."""
    try:
        url = f"{api_base.rstrip('/')}/api/tags"
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            data = resp.json()
            models = data.get("models", [])
            return [{"name": m.get("name", ""), "size": m.get("size", 0)} for m in models]
    except httpx.ConnectError:
        raise HTTPException(400, f"Cannot connect to Ollama at {api_base}. Is it running?")
    except Exception as e:
        raise HTTPException(400, f"Failed to fetch models: {e}")


@router.get("/{model_id}", response_model=LLMModelResponse)
async def get_model(model_id: int, db: AsyncSession = Depends(get_db)):
    model = await db.get(LLMModel, model_id)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    return model


@router.post("", response_model=LLMModelResponse, status_code=201)
async def create_model(data: LLMModelCreate, db: AsyncSession = Depends(get_db)):
    model = LLMModel(**data.model_dump())
    db.add(model)
    await db.commit()
    await db.refresh(model)
    return model


@router.put("/{model_id}", response_model=LLMModelResponse)
async def update_model(model_id: int, data: LLMModelUpdate, db: AsyncSession = Depends(get_db)):
    model = await db.get(LLMModel, model_id)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(model, key, value)
    await db.commit()
    await db.refresh(model)
    return model


@router.delete("/{model_id}", status_code=204)
async def delete_model(model_id: int, db: AsyncSession = Depends(get_db)):
    model = await db.get(LLMModel, model_id)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    await db.delete(model)
    await db.commit()


class TestModelRequest(BaseModel):
    test_message: str = "Hello, are you working?"


class TestModelResponse(BaseModel):
    success: bool
    message: str
    response: str = ""


@router.post("/{model_id}/test", response_model=TestModelResponse)
async def test_model(model_id: int, req: TestModelRequest, db: AsyncSession = Depends(get_db)):
    """Test model connectivity by sending a simple message."""
    model = await db.get(LLMModel, model_id)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    
    try:
        client = LLMClient(
            provider=model.provider or "openai",
            api_base=model.api_base,
            api_key=model.api_key or "",
            model_name=model.model_name or "",
            temperature=model.temperature if model.temperature is not None else 0.7,
            max_tokens=model.max_tokens or 4096,
        )
        data = await client.chat_completion([
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": req.test_message},
        ])
        response = data["choices"][0]["message"]["content"]
        return TestModelResponse(
            success=True,
            message="Model connection successful",
            response=response,
        )
    except Exception as e:
        return TestModelResponse(
            success=False,
            message=f"Connection failed: {str(e)}",
        )
