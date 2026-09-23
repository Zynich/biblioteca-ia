"""Testes da interface CLI (`python -m app.cli`) — o requisito de "receber perguntas
via input de texto". Usa um LLM fake e mocka `input()`, sem chamar a OpenAI."""

import pytest
from langchain_core.language_models.fake_chat_models import FakeListChatModel

from app import cli
from app.chain import MissingAPIKeyError, build_chain


def test_cli_loop_prints_answers_and_exits_on_sair(monkeypatch: pytest.MonkeyPatch, capsys) -> None:
    fake_chain = build_chain(
        llm=FakeListChatModel(responses=["Resposta simulada sobre listas em Python."])
    )
    monkeypatch.setattr(cli, "get_chatbot_chain", lambda: fake_chain)

    inputs = iter(["Como criar uma lista em Python?", "sair"])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))

    cli.main()

    out = capsys.readouterr().out
    assert "Resposta simulada sobre listas em Python." in out


def test_cli_skips_blank_lines(monkeypatch: pytest.MonkeyPatch, capsys) -> None:
    fake_chain = build_chain(llm=FakeListChatModel(responses=["primeira resposta real"]))
    monkeypatch.setattr(cli, "get_chatbot_chain", lambda: fake_chain)

    inputs = iter(["", "   ", "pergunta válida", "sair"])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))

    cli.main()

    out = capsys.readouterr().out
    assert "primeira resposta real" in out


def test_cli_exits_cleanly_on_keyboard_interrupt(monkeypatch: pytest.MonkeyPatch, capsys) -> None:
    fake_chain = build_chain(llm=FakeListChatModel(responses=["nunca deveria ser chamado"]))
    monkeypatch.setattr(cli, "get_chatbot_chain", lambda: fake_chain)

    def raise_interrupt(_: str) -> str:
        raise KeyboardInterrupt

    monkeypatch.setattr("builtins.input", raise_interrupt)

    cli.main()  # não deve propagar a exceção


def test_cli_missing_api_key_prints_error_without_crashing(
    monkeypatch: pytest.MonkeyPatch, capsys
) -> None:
    def raise_missing_key() -> None:
        raise MissingAPIKeyError

    monkeypatch.setattr(cli, "get_chatbot_chain", raise_missing_key)

    cli.main()

    out = capsys.readouterr().out
    assert "OPENAI_API_KEY" in out
