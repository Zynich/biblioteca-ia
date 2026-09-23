"""Testes do FaissVectorStore com vetores feitos à mão (sem modelo)."""

from pathlib import Path

import numpy as np
import pytest

from app.vector_store import ChunkRecord, FaissVectorStore


def make_store(tmp_path: Path) -> FaissVectorStore:
    store = FaissVectorStore(3, tmp_path / "i.faiss", tmp_path / "m.json")
    vectors = np.array([[1, 0, 0], [0, 1, 0], [0.6, 0.8, 0]], dtype=np.float32)
    records = [ChunkRecord(f"d{i}", f"Título {i}", f"texto {i}") for i in range(3)]
    store.add(vectors, records)
    return store


def test_search_returns_results_ordered_by_similarity(tmp_path: Path) -> None:
    store = make_store(tmp_path)

    hits = store.search(np.array([0, 1, 0], dtype=np.float32), k=3)

    assert [h.record.doc_id for h in hits] == ["d1", "d2", "d0"]
    assert hits[0].score == pytest.approx(1.0)
    assert hits[1].score == pytest.approx(0.8)
    assert hits[2].score == pytest.approx(0.0)


def test_k_larger_than_index_returns_everything(tmp_path: Path) -> None:
    store = make_store(tmp_path)

    assert len(store.search(np.array([1, 0, 0], dtype=np.float32), k=50)) == 3


def test_search_on_empty_store_returns_nothing(tmp_path: Path) -> None:
    store = FaissVectorStore(3, tmp_path / "i.faiss", tmp_path / "m.json")

    assert store.search(np.array([1, 0, 0], dtype=np.float32), k=5) == []


def test_save_and_load_roundtrip_gives_same_results(tmp_path: Path) -> None:
    store = make_store(tmp_path)
    query = np.array([0.6, 0.8, 0], dtype=np.float32)
    before = store.search(query, k=3)

    store.save()
    reloaded = FaissVectorStore.load(tmp_path / "i.faiss", tmp_path / "m.json")

    assert len(reloaded) == 3
    assert reloaded.search(query, k=3) == before


def test_wrong_dimension_is_rejected(tmp_path: Path) -> None:
    store = FaissVectorStore(3, tmp_path / "i.faiss", tmp_path / "m.json")

    with pytest.raises(ValueError, match="shape"):
        store.add(np.zeros((1, 5), dtype=np.float32), [ChunkRecord("d", "t", "x")])


def test_vectors_and_records_count_must_match(tmp_path: Path) -> None:
    store = FaissVectorStore(3, tmp_path / "i.faiss", tmp_path / "m.json")

    with pytest.raises(ValueError, match="igual"):
        store.add(np.zeros((2, 3), dtype=np.float32), [ChunkRecord("d", "t", "x")])


def test_load_detects_inconsistent_metadata(tmp_path: Path) -> None:
    store = make_store(tmp_path)
    store.save()
    (tmp_path / "m.json").write_text('{"dimension": 3, "records": []}')

    with pytest.raises(ValueError, match="inconsistentes"):
        FaissVectorStore.load(tmp_path / "i.faiss", tmp_path / "m.json")
