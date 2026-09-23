import pytest

from app.chunking import chunk_text


def test_short_text_is_a_single_chunk() -> None:
    assert chunk_text("texto curto", chunk_size=500, overlap=50) == ["texto curto"]


def test_empty_text_returns_no_chunks() -> None:
    assert chunk_text("   ", chunk_size=100, overlap=10) == []


def test_long_text_is_split_and_respects_chunk_size() -> None:
    text = " ".join(f"palavra{i}" for i in range(200))

    chunks = chunk_text(text, chunk_size=100, overlap=20)

    assert len(chunks) > 1
    assert all(len(c) <= 100 for c in chunks)


def test_consecutive_chunks_overlap() -> None:
    text = " ".join(f"palavra{i}" for i in range(200))

    chunks = chunk_text(text, chunk_size=100, overlap=20)

    for previous, current in zip(chunks, chunks[1:], strict=False):
        # a(s) última(s) palavra(s) do chunk anterior reaparece(m) no início do seguinte
        assert previous.split()[-1] in current.split()[:6]


def test_chunks_cover_the_whole_text() -> None:
    words = [f"palavra{i}" for i in range(200)]

    chunks = chunk_text(" ".join(words), chunk_size=100, overlap=20)

    seen = {w for c in chunks for w in c.split()}
    assert seen == set(words)


def test_does_not_cut_words_in_half() -> None:
    words = {f"palavra{i}" for i in range(200)}

    chunks = chunk_text(" ".join(f"palavra{i}" for i in range(200)), chunk_size=100, overlap=20)

    assert all(w in words for c in chunks for w in c.split())


@pytest.mark.parametrize(("size", "overlap"), [(0, 0), (-5, 0), (10, 10), (10, -1), (10, 20)])
def test_invalid_parameters_raise(size: int, overlap: int) -> None:
    with pytest.raises(ValueError):
        chunk_text("qualquer texto", chunk_size=size, overlap=overlap)
