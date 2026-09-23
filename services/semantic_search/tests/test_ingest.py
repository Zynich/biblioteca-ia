import json
from pathlib import Path

import pytest

from app import ingest
from app.core.config import settings
from app.vector_store import FaissVectorStore


@pytest.fixture()
def isolated_settings(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    articles_dir = tmp_path / "articles"
    articles_dir.mkdir()
    monkeypatch.setattr(settings, "articles_dir", str(articles_dir))
    monkeypatch.setattr(settings, "faiss_index_path", str(tmp_path / "out" / "a.faiss"))
    monkeypatch.setattr(settings, "faiss_metadata_path", str(tmp_path / "out" / "a.json"))
    return articles_dir


def test_ingest_builds_and_persists_index(isolated_settings: Path, fake_embedder) -> None:
    (isolated_settings / "a.json").write_text(
        json.dumps(
            [
                {"id": "1", "title": "Um", "content": "conteúdo um"},
                {"id": "2", "title": "Dois", "content": "conteúdo dois " * 80},
            ]
        )
    )

    exit_code = ingest.run(fake_embedder)

    assert exit_code == 0
    store = FaissVectorStore.load(settings.faiss_index_path, settings.faiss_metadata_path)
    assert len(store) > 2  # o artigo longo foi dividido em vários chunks


def test_ingest_fails_with_exit_code_1_when_no_articles(
    isolated_settings: Path, fake_embedder, capsys: pytest.CaptureFixture[str]
) -> None:
    assert ingest.run(fake_embedder) == 1
    assert "Nenhum artigo" in capsys.readouterr().err


def test_ingest_fails_with_exit_code_1_when_directory_missing(
    isolated_settings: Path, fake_embedder, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(settings, "articles_dir", str(isolated_settings / "nao-existe"))

    assert ingest.run(fake_embedder) == 1


def test_ingest_fails_on_malformed_article(isolated_settings: Path, fake_embedder) -> None:
    (isolated_settings / "a.json").write_text(json.dumps([{"id": "1", "title": "sem conteúdo"}]))

    assert ingest.run(fake_embedder) == 1
