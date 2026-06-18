# src/api/v1/endpoints/chat.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from src.db.database import get_db
from src.core.security import get_current_admin
from src.llm.context_builder import ContextBuilder
from src.llm.rag_pipeline import RAGPipeline

router = APIRouter(prefix="/chat", tags=["Chatbot"])


# ── Schemas ───────────────────────────────────────────────────────────────────

class ChatMessage(BaseModel):
    role: str     # "user" or "assistant"
    content: str


class ChatRequest(BaseModel):
    message: str
    organization_id: int | None = None
    history: list[ChatMessage] = []  # previous messages for multi-turn chat


class ChatResponse(BaseModel):
    reply: str
    context_used: str  # for debugging — shows what data the LLM saw


# ── Endpoint ──────────────────────────────────────────────────────────────────

@router.post("", response_model=ChatResponse)
def chat(
    body: ChatRequest,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    """
    Send a message to the AI attendance assistant.

    The assistant has access to today's attendance data for the given organization.
    It can answer questions like:
        - "Who is absent today?"
        - "How many students are late?"
        - "Who has low attendance this week?"
        - "من الغايبين النهارده؟"
    """
    try:

        # Scope enforcement
        org_id = body.organization_id
        if admin._scoped_org_id is not None:
            if org_id is not None and org_id != admin._scoped_org_id:
                raise HTTPException(status_code=403, detail="Cannot chat about foreign orgs.")
            org_id = admin._scoped_org_id
            
        # Step 1 — Build context from DB
        builder = ContextBuilder(db)
        context = builder.build_today_context(org_id)

        # Step 2 — Convert history to the format Groq expects
        history = [
            {"role": msg.role, "content": msg.content}
            for msg in body.history
        ]

        # Step 3 — Call the LLM
        pipeline = RAGPipeline()
        reply = pipeline.chat(
            user_message=body.message,
            context=context,
            history=history,
        )

        return ChatResponse(reply=reply, context_used=context)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chatbot error: {str(e)}",
        )