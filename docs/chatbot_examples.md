# Exemplos de uso do chatbot (Questão 2)

> **De onde vêm estas respostas.** São saídas **reais**, geradas pela própria aplicação (cadeia
> LangChain em [`app/chain.py`](../services/chatbot/app/chain.py), mesmo prompt de sistema, mesma
> memória por sessão), transcritas sem edição. Porém **não são do GPT-4 nem da OpenAI**:
> não havia chave de API disponível, então foram geradas com o provedor local
> **`LLM_PROVIDER=ollama`** e o modelo **`qwen2.5:3b`** (3 bilhões de parâmetros, rodando em CPU).
>
> Um modelo pequeno é menos preciso que o GPT-4; há imprecisões técnicas apontadas nas
> observações abaixo. Com `LLM_PROVIDER=openai` (padrão) ou `gemini` o fluxo é o mesmo e as
> respostas tendem a ser melhores. Isso **não foi exercitado**: a chave é o que falta.

## Como reproduzir

```bash
cp .env.example .env
# edite o .env: LLM_PROVIDER=ollama
make up-local        # sobe os serviços + o Ollama
make pull-model      # baixa o qwen2.5:3b (~2 GB, uma vez)
make chat            # conversa pelo terminal (input de texto)
# ou pela API:
curl -X POST localhost:8002/api/v1/chat -H 'Content-Type: application/json' \
  -d '{"session_id":"demo","message":"Como criar uma lista em Python?"}'
```

Para usar um modelo de nuvem em vez do local: `LLM_PROVIDER=openai` + `OPENAI_API_KEY`, ou
`LLM_PROVIDER=gemini` + `GOOGLE_API_KEY` (chave gratuita em https://aistudio.google.com/apikey).
As respostas variam a cada execução (o LLM não é determinístico).

## 1. Pergunta do enunciado

**Pergunta:** Como criar uma lista em Python?

**Resposta** (gerada em 16s):

> Em Python, você pode criar uma lista usando colchetes []. Aqui está um exemplo simples de como fazer isso:
>
> ```python
> minha_lista = [1, 2, 3, 4, 5]
> print(minha_lista)
> ```
>
> Neste exemplo, estamos criando uma lista chamada `minha_lista` que contém cinco números inteiros. Quando você executa este código, a saída será `[1, 2, 3, 4, 5]`.
>
> Você também pode adicionar itens à lista ou remover itens dela. Aqui está um exemplo de como adicionar um item à lista:
>
> ```python
> minha_lista.append(6)
> print(minha_lista)
> ```
>
> E aqui está um exemplo de como remover um item da lista:
>
> ```python
> minha_lista.remove(3)
> print(minha_lista)
> ```
>
> Lembre-se de que as listas em Python são mutáveis, o que significa que você pode alterar seus elementos.

**Observação:** a mesma pergunta também foi feita pela CLI (`make chat`, loop de `input()`) e obteve resposta equivalente.

## 2. Pergunta conceitual

**Pergunta:** Qual a diferença entre lista e tupla em Python?

**Resposta** (gerada em 24s):

> Em Python, tanto listas quanto tuplas são estruturas de dados utilizadas para armazenar coleções de itens. No entanto, existem algumas diferenças entre elas:
>
> 1. Mutabilidade: Uma das principais diferenças entre listas e tuplas é que listas são mutáveis, ou seja, você pode alterar, adicionar ou remover itens após a criação da lista. Já as tuplas são imutáveis, ou seja, você não pode alterar, adicionar ou remover itens após a criação da tupla.
>
> 2. Criação: As listas são criadas usando colchetes [], enquanto as tuplas são criadas usando parênteses ().
>
> Vamos ver um exemplo de cada:
>
> Lista:
> ```python
> minha_lista = [1, 2, 3, 4]
> print(minha_lista)
> minha_lista.append(5)  # Adicionando um elemento à lista
> print(minha_lista)
> ```
>
> Tupla:
> ```python
> minha_tupla = (1, 2, 3, 4)
> print(minha_tupla)
> # minha_tupla.append(5)  # Não podemos adicionar elementos a uma tupla
> ```
>
> Em Python, listas são geralmente mais flexíveis e úteis para manipulações de dados, enquanto tuplas são mais rápidas e são úteis para quando você precisa garantir que os dados não serão alterados.

## 3. Follow-up (memória por `session_id`)

**Pergunta 1:** Como eu ordeno uma lista em Python?

**Resposta** (gerada em 57s):

> Em Python, você pode ordenar uma lista de várias maneiras. A função mais comumente usada para isso é a `sorted()` para obter uma nova lista ordenada, ou a função `list.sort()` para ordenar a lista original em sua versão de lista.
>
> 1. Para obter uma nova lista ordenada, você pode usar a função `sorted()`. Essa função retorna uma nova lista que é a versão ordenada da lista original. Aqui está um exemplo:
>
> ```python
> # Lista original
> minha_lista = [3, 1, 4, 1, 5, 9, 2, 6, 5, 3, 5]
>
> # Usando sorted() para obter uma nova lista ordenada
> nova_lista = sorted(minha_lista)
>
> print(nova_lista)  # Saída: [1, 1, 2, 3, 3, 4, 5, 5, 5, 6, 9]
> ```
>
> 2. Para ordenar a lista original, você pode usar a função `list.sort()`. Essa função ordena a lista original em seu próprio lugar. Note que `list.sort()` ordena a lista em ordem crescente por padrão. Se você quiser ordenar em ordem decrescente, você pode usar a função `reverse=True`:
>
> ```python
> # Lista original
> minha_lista = [3, 1, 4, 1, 5, 9, 2, 6, 5, 3, 5]
>
> # Usando list.sort() para ordenar a lista original
> minha_lista.sort()
>
> print(minha_lista)  # Saída: [1, 1, 2, 3, 3, 4, 5, 5, 5, 6, 9]
>
> # Para ordenar em ordem decrescente
> minha_lista.sort(reverse=True)
>
> print(minha_lista)  # Saída: [9, 6, 5, 5, 5, 4, 3, 3, 2, 1, 1]
> ```
>
> Se você precisar de uma ordenação personalizada, como por exemplo, baseada em um valor de cada elemento, você pode fornecer uma função de comparação para a função `sort()` ou `sorted()`.
>
> Por exemplo, se você quiser ordenar uma lista de dicionários por um valor específico, você pode fazer isso da seguinte maneira:
>
> ```python
> # Lista de dicionários
> dicionarios = [
>     {'nome': 'João', 'idade': 30},
>     {'nome': 'Maria', 'idade': 25},
>     {'nome': 'Pedro', 'idade': 35},
> ]
>
> # Ordenando por 'idade'
> dicionarios.sort(key=lambda d: d['idade'])
>
> print(dicionarios)  # Saída: [{'nome': 'Maria', 'idade': 25}, {'nome': 'João', 'idade': 30}, {'nome': 'Pedro', 'idade': 35}]
> ```
>
> Lembre-se de que `sorted()` retorna uma lista ordenada, enquanto `list.sort()` ordena a lista original. Se você não precisa de uma lista ordenada e está apenas interessado em alterar a lista original, use `list.sort()`. Se você precisa de uma lista ordenada e não quer alterar a lista original, use `sorted()`.

**Pergunta 2:** E se eu quiser em ordem decrescente?

**Resposta** (gerada em 31s):

> Para ordenar uma lista em ordem decrescente em Python, você pode usar a função `sorted()` com o parâmetro `reverse=True`, ou você pode usar a função `list.sort()` com o parâmetro `reverse=True`. Ambas as abordagens retornam uma lista ordenada, mas com a diferença que `list.sort()` modifica a lista original, enquanto `sorted()` retorna uma nova lista.
>
> Vamos ver ambos os métodos:
>
> ### Usando `sorted()` com `reverse=True`
> ```python
> minha_lista = [3, 1, 4, 1, 5, 9, 2, 6, 5, 3, 5]
> nova_lista = sorted(minha_lista, reverse=True)
> print(nova_lista)  # Saída: [9, 6, 5, 5, 5, 4, 3, 3, 2, 1, 1]
> ```
>
> ### Usando `list.sort()` com `reverse=True`
> ```python
> minha_lista = [3, 1, 4, 1, 5, 9, 2, 6, 5, 3, 5]
> minha_lista.sort(reverse=True)
> print(minha_lista)  # Saída: [9, 6, 5, 5, 5, 4, 3, 3, 2, 1, 1]
> ```
>
> Ambas as abordagens retornam uma nova lista ordenada em ordem decrescente. Se você deseja alterar a lista original, use `list.sort()` com `reverse=True`. Se você não deseja alterar a lista original, use `sorted()` com `reverse=True`.

**Observação:** a segunda pergunta não repete o assunto e o bot a entendeu como "ordem decrescente da lista": é o histórico da sessão funcionando. **Imprecisões do modelo:** na resposta 1 ele diz "função de comparação" onde o correto é uma função de *chave* (`key=`), e chama `reverse=True` de "função" (é um parâmetro); na resposta 2 afirma que ambas as abordagens "retornam uma nova lista", mas `list.sort()` retorna `None` e altera a lista original (o exemplo de código, porém, está correto).

## 4. Pergunta fora do escopo (deve ser recusada)

**Pergunta:** Qual a melhor receita de brigadeiro?

**Resposta** (gerada em 6s):

> Desculpe, mas eu não posso ajudar com isso. Meu escopo é fornecer assistência com perguntas relacionadas a programação em Python. Sobre brigadeiros, você poderia me perguntar sobre como fazer uma receita de brigadeiro em Python, como calcular a quantidade de ingredientes ou como criar um programa que gere receitas de brigadeiro?

**Observação:** recusou e manteve o escopo, mas a sugestão final ("receita de brigadeiro em Python") é desnecessária; um modelo maior costuma ser mais conciso.

## 5. Pergunta um pouco mais avançada

**Pergunta:** O que é uma list comprehension?

**Resposta** (gerada em 27s):

> List comprehension é uma maneira concisa de criar listas em Python. Ela consiste em escrever uma nova lista baseada em uma sequência existente, usando uma expressão de lista e um ou mais loops condicionais ou de iteração.
>
> A sintaxe básica de list comprehension é:
>
> ```python
> [expressão for item in lista]
> ```
>
> Ou com uma condição:
>
> ```python
> [expressão for item in lista if condição]
> ```
>
> Vamos ver um exemplo para entender melhor:
>
> ```python
> # Exemplo 1: Criando uma lista com list comprehension
> numeros = [1, 2, 3, 4, 5]
> pares = [n for n in numeros if n % 2 == 0]
> print(pares)  # Saída: [2, 4]
> ```
>
> Neste exemplo, estamos criando uma nova lista chamada `pares` que contém apenas os números pares da lista `numeros`.
>
> ```python
> # Exemplo 2: Criando uma lista com list comprehension usando uma condição
> numeros = [1, 2, 3, 4, 5]
> impares = [n for n in numeros if n % 2 != 0]
> print(impares)  # Saída: [1, 3, 5]
> ```
>
> Neste segundo exemplo, estamos criando uma nova lista chamada `impares` que contém apenas os números ímpares da lista `numeros`.
>
> List comprehension é uma forma concisa e rápida de criar listas, e é muito útil quando você precisa criar listas a partir de outras sequências.

## Rastreamento com LangSmith

A integração é feita só por variáveis (`LANGSMITH_TRACING`, `LANGSMITH_API_KEY`,
`LANGSMITH_PROJECT`) e **não foi validada** (exige conta e chave do LangSmith); nenhum trace
foi anexado aqui.
