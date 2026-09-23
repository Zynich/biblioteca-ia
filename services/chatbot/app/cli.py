"""Interface CLI do chatbot — atende literalmente ao requisito de "receber perguntas
dos usuários via input de texto". Roda com `make chat` ou `python -m app.cli`."""

from app.chain import MissingAPIKeyError, get_chatbot_chain

SESSION_ID = "cli-session"
EXIT_WORDS = {"sair", "exit", "quit"}


def main() -> None:
    print("Chatbot Python — tire suas dúvidas sobre programação em Python.")
    print("Digite 'sair' para encerrar.\n")

    try:
        chain = get_chatbot_chain()
    except MissingAPIKeyError as exc:
        print(f"Erro: {exc}")
        return

    while True:
        try:
            question = input("Você: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not question:
            continue
        if question.lower() in EXIT_WORDS:
            break

        try:
            answer = chain.invoke(
                {"question": question},
                config={"configurable": {"session_id": SESSION_ID}},
            )
        except Exception as exc:
            print(f"[erro ao consultar o modelo: {exc}]\n")
            continue

        print(f"Bot: {answer}\n")


if __name__ == "__main__":
    main()
