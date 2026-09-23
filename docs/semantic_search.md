# Busca semântica (Questão 3)

Como o serviço [`semantic_search`](../services/semantic_search) transforma texto em busca por
significado — e não por palavra-chave.

## Pipeline

```
INGESTÃO (make ingest)
  articles.json ──► chunking ──► tokenização ──► modelo ──► mean pooling ──► normalização L2 ──► FAISS
  (24 artigos)     (46 chunks)   (ids)           (1 vetor    (1 vetor por      (norma = 1)        (índice em
                                                  por token)  chunk)                               disco)

BUSCA (GET /api/v1/search?q=...&k=5)
  consulta ──► tokenização ──► modelo ──► mean pooling ──► L2 ──► FAISS (produto interno) ──► top-k documentos
```

| Etapa | Onde | O que acontece |
|---|---|---|
| Dataset | [`data/articles/articles.json`](../services/semantic_search/data/articles/articles.json) | 24 artigos curtos em português (Python, culinária, finanças, esportes, viagem, saúde), com `id`, `title`, `content`. |
| Chunking | [`app/chunking.py`](../services/semantic_search/app/chunking.py) | Textos são divididos em pedaços de ~500 caracteres com sobreposição de 50, sem cortar palavras. O modelo só lê 128 tokens; sem isso, o excedente seria descartado. 24 artigos → 46 chunks. |
| Tokenização | `AutoTokenizer` | Quebra o texto em sub-palavras e converte em ids numéricos; `padding` iguala o tamanho no lote e `attention_mask` marca o que é preenchimento. |
| Embedding | [`app/embeddings.py`](../services/semantic_search/app/embeddings.py) | `AutoModel` (`paraphrase-multilingual-MiniLM-L12-v2`) gera um vetor de 384 dimensões **por token**. |
| Mean pooling | `mean_pooling()` | Média dos vetores dos tokens **ignorando o padding**, resultando em um vetor por texto. |
| Normalização L2 | `F.normalize` | Cada vetor passa a ter norma 1. Assim, produto interno = similaridade de cosseno. |
| Vector store | [`app/vector_store.py`](../services/semantic_search/app/vector_store.py) | `faiss.IndexFlatIP` (busca exata por produto interno). O índice vai para `articles.faiss` e os metadados (posição → documento) para `articles_metadata.json`. |
| Busca | [`app/search.py`](../services/semantic_search/app/search.py) | Embedding da consulta → FAISS → mantém o melhor chunk de cada documento → top-k documentos com score (cosseno). |

O título do artigo é concatenado ao texto de cada chunk antes de gerar o embedding
(`"{título}. {chunk}"`), para que chunks do meio do artigo continuem "sabendo" o assunto.

## Exemplos reais de consulta

Resultados reais do índice construído com os 24 artigos (score = cosseno; 1.0 = idêntico):

| Consulta | Top-1 (score) | Top-2 (score) |
|---|---|---|
| `como fazer bolo` | Receita de bolo de cenoura… (0.744) | Como fazer pão caseiro sem sova (0.563) |
| `como criar uma lista em python` | Como criar e manipular listas em Python (0.833) | Testes automatizados com pytest (0.500) |
| `onde investir meu dinheiro com segurança` | Tesouro Direto para iniciantes (0.551) | Diversificação de carteira de investimentos (0.501) |
| `dívidas no cartão` | Como sair das dívidas do cartão de crédito (0.716) | Juros compostos explicados (0.671) |
| `dicas para correr mais rápido` | Como melhorar o tempo em corridas de 5 km (0.743) | Treino de musculação para iniciantes (0.434) |
| `dormir melhor` | A importância do sono para a saúde (0.725) | Treino de musculação para iniciantes (0.423) |
| `o que visitar em Portugal` | Roteiro de 5 dias em Lisboa (0.712) | Feijoada completa (0.290) |
| `how to bake a cake` (inglês) | Receita de bolo de cenoura… (0.702) | Como fazer pão caseiro sem sova (0.544) |

Repare que "correr mais rápido" acha o artigo de corrida sem compartilhar as palavras
"correr" ou "rápido" no título, e que a consulta em inglês encontra o texto em português
(o modelo é multilíngue).

## Limitações observadas

Em vez de escolher só os acertos, estes são casos em que a busca é fraca:

| Consulta | Top-1 (score) | Por quê |
|---|---|---|
| `bolo` (uma palavra) | Brigadeiro perfeito (0.418) — o artigo de bolo **não** é o 1º | O modelo foi treinado com frases; consultas de uma palavra geram vetores pouco específicos. Frases naturais (`como fazer bolo`) funcionam bem. |
| `diferença entre concorrência e paralelismo` | Diversificação de carteira (0.431) — errado | O corpus não tem artigo sobre isso (o mais próximo seria o de `asyncio`). O **score baixo (< 0.5)** é o sinal de que não há bom resultado. |

Não há corte mínimo de score na API: ela sempre devolve os `k` mais próximos. Um limiar
(`min_score`) seria o próximo passo natural.

## Determinismo numérico (achado durante o desenvolvimento)

No ambiente de desenvolvimento (Ryzen 5 3600, WSL2, torch 2.14 CPU), a inferência com o
backend oneDNN (`mkldnn`) ou com várias threads produzia vetores **diferentes para a mesma
entrada** (desvio de até ~5e-2 por componente, de forma intermitente). O impacto medido no
cosseno foi ≤ 0,2% — irrelevante para o ranking —, mas atrapalhava testes e reprodutibilidade.
Mitigação em `TransformersEmbedder`: `mkldnn` desligado e 1 thread (custo desprezível para um
modelo pequeno). Ainda restou ruído numérico raro (~0,5% das chamadas), por isso os testes
comparam por cosseno e não por igualdade exata. Vetores conferidos contra float64.

## Trocar o vector store (FAISS → Milvus)

O serviço de busca depende do `Protocol` `VectorStore` (`add`, `search`, `save`, `__len__`),
não do FAISS. Usar Milvus (ou pgvector) é escrever uma nova classe com esses métodos e
trocá-la em `app/api/deps.py` e `app/indexing.py` — o restante não muda.
