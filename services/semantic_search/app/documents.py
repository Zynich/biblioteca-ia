"""Leitura dos documentos-fonte (JSON com id, title, content)."""

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Article:
    id: str
    title: str
    content: str


def load_articles(directory: str | Path) -> list[Article]:
    """Lê todos os .json do diretório; cada arquivo pode ter um objeto ou uma lista."""
    directory = Path(directory)
    if not directory.is_dir():
        raise FileNotFoundError(f"diretório de artigos não encontrado: {directory}")

    articles: list[Article] = []
    for path in sorted(directory.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        items = data if isinstance(data, list) else [data]
        for item in items:
            try:
                articles.append(
                    Article(id=item["id"], title=item["title"], content=item["content"])
                )
            except KeyError as exc:
                raise ValueError(f"{path.name}: campo obrigatório ausente {exc}") from exc

    ids = [a.id for a in articles]
    if len(ids) != len(set(ids)):
        raise ValueError("ids de artigos duplicados")
    return articles
