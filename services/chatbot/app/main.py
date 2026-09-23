"""Ponto de entrada do chatbot Python (Questão 2)."""

from fastapi import FastAPI

from app.api.routes import chat, health

app = FastAPI(
    title="Chatbot Python",
    description="Chatbot especialista em Python via LangChain + OpenAI — Questão 2.",
    version="1.0.0",
)

app.include_router(health.router)
app.include_router(chat.router)
