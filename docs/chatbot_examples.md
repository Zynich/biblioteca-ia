# Exemplos de uso do chatbot (Questão 2)

> **Importante — leia antes de usar este arquivo na entrega:** os exemplos abaixo foram
> escritos manualmente para ilustrar o comportamento esperado (regras do prompt de
> sistema em [app/chain.py](../services/chatbot/app/chain.py): responder em português,
> sempre com explicação + código, recusar fora do escopo). **Não são transcrições reais
> da API da OpenAI** — a implementação não foi validada contra a API de verdade porque
> nenhuma `OPENAI_API_KEY` estava disponível neste ambiente de desenvolvimento.
>
> Antes de entregar o teste, rode os exemplos de verdade e substitua as respostas
> abaixo pelas reais:
>
> ```bash
> cp .env.example .env      # preencha OPENAI_API_KEY
> make up
> make chat                 # ou: curl no /api/v1/chat, ver services/chatbot/README.md
> ```
>
> Se `LANGSMITH_TRACING=true` estiver configurado, tire também um print do trace em
> https://smith.langchain.com e cole aqui.

## 1. Pergunta básica

**Pergunta:** Como criar uma lista em Python?

**Resposta esperada:**

> Em Python, uma lista é criada com colchetes `[]`, e pode conter qualquer tipo de
> valor, inclusive misturados.
>
> ```python
> numeros = [1, 2, 3, 4]
> frutas = ["maçã", "banana", "laranja"]
> lista_vazia = []
>
> # também é possível criar com a função list()
> outra_lista = list((1, 2, 3))  # a partir de uma tupla
> ```
>
> Você pode adicionar itens com `.append()`, acessar por índice (`frutas[0]`) e fatiar
> com `frutas[1:3]`.

## 2. Pergunta conceitual

**Pergunta:** Qual a diferença entre lista e tupla em Python?

**Resposta esperada:**

> A principal diferença é a **mutabilidade**: listas podem ser alteradas depois de
> criadas (adicionar, remover, modificar itens); tuplas não podem.
>
> ```python
> lista = [1, 2, 3]
> lista.append(4)       # funciona: [1, 2, 3, 4]
>
> tupla = (1, 2, 3)
> tupla.append(4)        # AttributeError: 'tuple' object has no attribute 'append'
> ```
>
> Por serem imutáveis, tuplas são um pouco mais rápidas e podem ser usadas como chave
> de dicionário — listas não podem, porque dicionários exigem chaves *hashable*.

## 3. Pergunta de follow-up (demonstra a memória por `session_id`)

**Pergunta 1:** Como eu ordeno uma lista em Python?

**Resposta esperada:**

> Use o método `.sort()` (ordena a lista original, no lugar) ou a função `sorted()`
> (retorna uma lista nova, sem alterar a original).
>
> ```python
> numeros = [5, 2, 4, 1, 3]
> numeros.sort()              # numeros agora é [1, 2, 3, 4, 5]
>
> outra = [5, 2, 4, 1, 3]
> ordenada = sorted(outra)    # outra continua [5, 2, 4, 1, 3]; ordenada é [1, 2, 3, 4, 5]
> ```

**Pergunta 2 (mesma `session_id`, sem repetir contexto):** E se eu quiser em ordem
decrescente?

**Resposta esperada** (o chatbot entende que "em ordem decrescente" se refere à
ordenação da pergunta anterior, graças ao histórico da conversa):

> Basta passar `reverse=True` para `.sort()` ou `sorted()`:
>
> ```python
> numeros = [5, 2, 4, 1, 3]
> numeros.sort(reverse=True)          # [5, 4, 3, 2, 1]
> ordenada = sorted(numeros, reverse=True)
> ```

## 4. Pergunta fora do escopo (deve ser recusada)

**Pergunta:** Qual a melhor receita de brigadeiro?

**Resposta esperada:**

> Desculpe, meu escopo é apenas dúvidas sobre programação em Python — não consigo
> ajudar com receitas culinárias. Se tiver alguma pergunta sobre Python, fico à
> disposição!

## 5. Pergunta um pouco mais avançada

**Pergunta:** O que é uma list comprehension?

**Resposta esperada:**

> É uma forma concisa de criar listas a partir de uma sequência existente, combinando
> um laço `for` (e opcionalmente um `if`) em uma única linha.
>
> ```python
> numeros = [1, 2, 3, 4, 5, 6]
>
> # forma tradicional
> pares = []
> for n in numeros:
>     if n % 2 == 0:
>         pares.append(n)
>
> # com list comprehension
> pares = [n for n in numeros if n % 2 == 0]   # [2, 4, 6]
>
> # também funciona para transformar valores
> quadrados = [n ** 2 for n in numeros]         # [1, 4, 9, 16, 25, 36]
> ```
