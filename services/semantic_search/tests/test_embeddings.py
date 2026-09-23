"""Testes com o modelo real de embeddings."""

import numpy as np

from app.embeddings import TransformersEmbedder


def test_embedding_has_expected_dimension(embedder: TransformersEmbedder) -> None:
    vectors = embedder.embed(["olá mundo", "segundo texto"])

    assert vectors.shape == (2, 384)
    assert vectors.dtype == np.float32
    assert embedder.dimension == 384


def test_embeddings_are_l2_normalized(embedder: TransformersEmbedder) -> None:
    vectors = embedder.embed(["um texto qualquer", "outro texto bem diferente do primeiro"])

    norms = np.linalg.norm(vectors, axis=1)
    np.testing.assert_allclose(norms, 1.0, atol=1e-5)


def test_similar_sentences_score_higher_than_unrelated(embedder: TransformersEmbedder) -> None:
    a, b, c = embedder.embed(
        ["Como fazer um bolo de chocolate", "Receita de bolo de cenoura", "Regras do impedimento"]
    )

    assert float(a @ b) > float(a @ c)


def test_padding_does_not_change_the_embedding(embedder: TransformersEmbedder) -> None:
    short = "gato"
    alone = embedder.embed([short])[0]
    # Em lote com um texto bem mais longo, o curto recebe padding; o mean pooling deve
    # ignorar esse padding e produzir (praticamente) o mesmo vetor. Compara por cosseno:
    # padding vazando derrubaria isso para bem menos que 0.99.
    batched = embedder.embed([short, "um texto muito mais longo " * 10])[0]

    assert float(alone @ batched) > 0.999


def test_empty_input_returns_empty_matrix(embedder: TransformersEmbedder) -> None:
    assert embedder.embed([]).shape == (0, 384)


def test_embedding_is_stable_across_calls(embedder: TransformersEmbedder) -> None:
    # Regressão: a inferência CPU do torch variava entre chamadas idênticas neste ambiente
    # (ver comentário em TransformersEmbedder). Ruído numérico raro é tolerado (cosseno),
    # mas a mesma entrada não pode gerar vetores materialmente diferentes.
    reference = embedder.embed(["como fazer bolo"])[0]

    for _ in range(50):
        assert float(embedder.embed(["como fazer bolo"])[0] @ reference) > 0.99
