"""Dependencies compartilhadas entre rotas."""

from collections.abc import Callable

from langchain_core.runnables.history import RunnableWithMessageHistory

from app.chain import get_chatbot_chain

ChainProvider = Callable[[], RunnableWithMessageHistory]


def get_chain_provider() -> ChainProvider:
    """Retorna uma factory (não a chain já construída): o FastAPI resolve as
    dependencies antes de terminar de validar o body, então se `MissingAPIKeyError`
    fosse levantado aqui, um payload inválido retornaria 500 em vez do 422 esperado.
    Adiando a construção para dentro do try/except da rota, o 422 tem prioridade
    sobre falhas de configuração do servidor — como deveria ser."""
    return get_chatbot_chain
