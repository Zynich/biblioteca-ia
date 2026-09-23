"""Geração de embeddings com `transformers` puro (sem sentence-transformers).

Pipeline: texto -> tokens -> modelo (um vetor por token) -> mean pooling (um vetor por
texto) -> normalização L2. É exatamente o que a biblioteca sentence-transformers faz
por baixo dos panos para este modelo.
"""

from typing import Protocol

import numpy as np
import torch
import torch.nn.functional as F
from numpy.typing import NDArray
from transformers import AutoModel, AutoTokenizer

# O paraphrase-multilingual-MiniLM-L12-v2 foi treinado com no máximo 128 tokens.
MAX_TOKENS = 128


class TextEmbedder(Protocol):
    dimension: int

    def embed(self, texts: list[str]) -> NDArray[np.float32]: ...


class TransformersEmbedder:
    def __init__(self, model_name: str, batch_size: int = 32, num_threads: int = 1) -> None:
        self.batch_size = batch_size
        # Determinismo: no ambiente testado (CPU x86 sob WSL2, torch 2.14 CPU), a inferência
        # com o backend oneDNN (mkldnn) ou com várias threads gerou vetores DIFERENTES para a
        # mesma entrada (até ~5e-2 por componente, de forma intermitente), o que fazia os
        # scores da busca oscilarem entre chamadas. Com mkldnn desligado e 1 thread o
        # resultado é exato entre execuções. Para um modelo pequeno (MiniLM) e textos curtos,
        # o custo de performance é desprezível.
        torch.backends.mkldnn.enabled = False  # type: ignore[assignment]
        torch.set_num_threads(num_threads)
        # O tokenizer quebra o texto em sub-palavras e converte para ids numéricos.
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModel.from_pretrained(model_name)
        # eval() desliga dropout: queremos resultados determinísticos, não treino.
        self.model.eval()
        self.dimension: int = int(self.model.config.hidden_size)

    def embed(self, texts: list[str]) -> NDArray[np.float32]:
        if not texts:
            return np.empty((0, self.dimension), dtype=np.float32)

        batches = []
        for start in range(0, len(texts), self.batch_size):
            batches.append(self._embed_batch(texts[start : start + self.batch_size]))
        return np.vstack(batches).astype(np.float32)

    def _embed_batch(self, texts: list[str]) -> NDArray[np.float32]:
        # padding=True iguala o tamanho dos textos do lote (attention_mask marca o que é
        # preenchimento); truncation=True corta o que passar do limite do modelo.
        encoded = self.tokenizer(
            texts,
            padding=True,
            truncation=True,
            max_length=MAX_TOKENS,
            return_tensors="pt",
        )
        # no_grad: sem cálculo de gradientes, pois só fazemos inferência (menos memória).
        with torch.no_grad():
            output = self.model(**encoded)

        # output.last_hidden_state: (lote, tokens, dimensão) — um vetor por token.
        pooled = mean_pooling(output.last_hidden_state, encoded["attention_mask"])
        # Normalização L2: cada vetor passa a ter norma 1, então produto interno == cosseno.
        normalized = F.normalize(pooled, p=2, dim=1)
        return normalized.numpy()


def mean_pooling(token_embeddings: torch.Tensor, attention_mask: torch.Tensor) -> torch.Tensor:
    """Média dos vetores dos tokens, ignorando os tokens de preenchimento (padding)."""
    # (lote, tokens) -> (lote, tokens, 1) para poder multiplicar pelos vetores.
    mask = attention_mask.unsqueeze(-1).to(token_embeddings.dtype)
    summed = (token_embeddings * mask).sum(dim=1)
    # clamp evita divisão por zero caso algum texto tenha máscara toda zerada.
    counts = mask.sum(dim=1).clamp(min=1e-9)
    return summed / counts
