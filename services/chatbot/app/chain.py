"""Monta a chain LCEL (prompt | llm | parser) com memória de conversa por sessão.

A chain é construída uma vez (módulo-level, via `get_chatbot_chain`) e reaproveitada
entre requisições — recriar um `ChatOpenAI` a cada request seria desperdício. Os
testes injetam um LLM fake através de `build_chain(llm=...)`, então nunca chamam a
API da OpenAI de verdade.
"""

from functools import lru_cache

from langchain_core.chat_history import BaseChatMessageHistory, InMemoryChatMessageHistory
from langchain_core.language_models import BaseChatModel
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory

from app.core.config import settings

SYSTEM_PROMPT = """Você é um assistente especialista em programação Python.

Regras:
- Responda sempre em português do Brasil.
- Toda resposta sobre Python deve conter uma explicação clara E um exemplo de código \
funcional, formatado em bloco de código.
- Se a pergunta não for sobre programação em Python, recuse educadamente e explique \
que seu escopo é apenas dúvidas de Python — não tente responder mesmo que saiba a \
resposta.
"""

# Histórico em memória, indexado por session_id. Em produção seria Redis (sobrevive a
# reinícios e funciona com múltiplas instâncias do serviço) — ver docs/decisions.md.
_history_store: dict[str, InMemoryChatMessageHistory] = {}


def get_session_history(session_id: str) -> BaseChatMessageHistory:
    if session_id not in _history_store:
        _history_store[session_id] = InMemoryChatMessageHistory()
    return _history_store[session_id]


def clear_session_history(session_id: str) -> None:
    _history_store.pop(session_id, None)


def reset_history_store() -> None:
    """Usado pelos testes para isolar sessões entre casos de teste."""
    _history_store.clear()


class MissingAPIKeyError(Exception):
    def __init__(self) -> None:
        super().__init__("OPENAI_API_KEY não configurada. Defina a variável no .env.")


def _default_llm() -> BaseChatModel:
    # Falha explícita e imediata (sem tentar uma chamada de rede primeiro) quando a
    # chave não está configurada — melhor um erro claro do que um stack trace da
    # biblioteca da OpenAI vazando pra resposta HTTP.
    if not settings.openai_api_key:
        raise MissingAPIKeyError

    from langchain_openai import ChatOpenAI
    from pydantic import SecretStr

    return ChatOpenAI(model=settings.openai_model, api_key=SecretStr(settings.openai_api_key))


def build_chain(llm: BaseChatModel | None = None) -> RunnableWithMessageHistory:
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", SYSTEM_PROMPT),
            MessagesPlaceholder("history"),
            ("human", "{question}"),
        ]
    )
    model = llm or _default_llm()
    base_chain = prompt | model | StrOutputParser()

    return RunnableWithMessageHistory(
        base_chain,
        get_session_history,
        input_messages_key="question",
        history_messages_key="history",
    )


@lru_cache(maxsize=1)
def get_chatbot_chain() -> RunnableWithMessageHistory:
    """Singleton da chain de produção (usa ChatOpenAI de verdade). Sobrescrita nos
    testes via `app.dependency_overrides`."""
    return build_chain()
