"""Endpoint de chat — Questão 2. Recebe uma mensagem + session_id e responde usando a
chain LangChain (prompt | LLM | parser) com memória de conversa por sessão."""

import json
from collections.abc import Generator

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from langchain_core.runnables import RunnableConfig
from pydantic import BaseModel, Field

from app.api.deps import ChainProvider, get_chain_provider
from app.chain import MissingAPIKeyError

router = APIRouter(prefix="/api/v1", tags=["chat"])


class ChatRequest(BaseModel):
    session_id: str = Field(..., min_length=1, description="Identificador da conversa")
    message: str = Field(..., min_length=1, description="Pergunta do usuário sobre Python")


class ChatResponse(BaseModel):
    session_id: str
    answer: str


def _invoke_config(session_id: str) -> RunnableConfig:
    return RunnableConfig(configurable={"session_id": session_id})


@router.post(
    "/chat",
    response_model=ChatResponse,
    summary="Envia uma mensagem ao chatbot",
    description=(
        "Responde perguntas sobre programação em Python. O histórico da conversa é "
        "mantido em memória por `session_id` — reenvie o mesmo `session_id` para "
        "perguntas de follow-up."
    ),
    responses={
        500: {"description": "Chave do provedor (OPENAI_API_KEY / GOOGLE_API_KEY) não configurada"},
        502: {"description": "Erro ao consultar o modelo de linguagem"},
        504: {"description": "Tempo limite excedido ao consultar o modelo"},
    },
)
def chat(
    payload: ChatRequest,
    chain_provider: ChainProvider = Depends(get_chain_provider),
) -> ChatResponse:
    try:
        chain = chain_provider()
        answer = chain.invoke(
            {"question": payload.message},
            config=_invoke_config(payload.session_id),
        )
    except MissingAPIKeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)
        ) from exc
    except (TimeoutError, httpx.TimeoutException) as exc:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Tempo limite excedido ao consultar o modelo",
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Erro ao consultar o modelo de linguagem",
        ) from exc

    return ChatResponse(session_id=payload.session_id, answer=answer)


@router.post(
    "/chat/stream",
    summary="Envia uma mensagem ao chatbot com resposta via streaming (SSE)",
)
def chat_stream(
    payload: ChatRequest,
    chain_provider: ChainProvider = Depends(get_chain_provider),
) -> StreamingResponse:
    try:
        chain = chain_provider()
    except MissingAPIKeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)
        ) from exc

    def event_stream() -> Generator[str, None, None]:
        try:
            for chunk in chain.stream(
                {"question": payload.message},
                config=_invoke_config(payload.session_id),
            ):
                yield f"data: {json.dumps({'chunk': chunk})}\n\n"
            yield "event: done\ndata: {}\n\n"
        except Exception as exc:
            yield f"event: error\ndata: {json.dumps({'detail': str(exc)})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
