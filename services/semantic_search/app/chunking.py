"""Divide textos longos em pedaços com sobreposição.

Modelos de embedding têm limite de tokens por entrada (128 neste caso). Textos maiores
seriam truncados e perderiam conteúdo, então cada documento vira vários chunks. A
sobreposição evita que uma frase cortada na fronteira perca seu contexto.
"""


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    if chunk_size <= 0:
        raise ValueError("chunk_size deve ser positivo")
    if not 0 <= overlap < chunk_size:
        raise ValueError("overlap deve ser >= 0 e menor que chunk_size")

    text = text.strip()
    if not text:
        return []
    if len(text) <= chunk_size:
        return [text]

    chunks: list[str] = []
    step = chunk_size - overlap
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        # Recua até o último espaço para não cortar uma palavra ao meio (exceto no
        # último pedaço, que vai até o fim do texto).
        if end < len(text):
            last_space = text.rfind(" ", start + step, end)
            if last_space != -1:
                end = last_space
        piece = text[start:end].strip()
        if piece:
            chunks.append(piece)
        if end >= len(text):
            break
        start = max(end - overlap, start + 1)
        # A sobreposição pode cair no meio de uma palavra: avança até o início da
        # próxima para o chunk seguinte não começar com uma palavra cortada.
        if text[start - 1] != " ":
            next_space = text.find(" ", start, end)
            if next_space != -1:
                start = next_space + 1
    return chunks
