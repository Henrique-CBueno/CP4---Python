# Documentação Final — Banco Digital Acadêmico

Este conjunto de documentos descreve o sistema **como ele foi efetivamente implementado**,
verificado diretamente contra o código-fonte deste repositório e contra o grafo de conhecimento
gerado pelo Graphify sobre ele. Onde a implementação diverge do design original em
`docs/specs/`, a diferença é apontada explicitamente em vez de omitida — ver, em especial,
`03-arquitetura.md` e `07-fluxos-principais.md`.

## Índice

| Documento | Conteúdo |
|---|---|
| [`01-visao-geral.md`](01-visao-geral.md) | Contexto do projeto, objetivo acadêmico, escopo, tecnologias e um diagrama de alto nível do fluxo do sistema. |
| [`02-requisitos.md`](02-requisitos.md) | Requisitos funcionais e não funcionais implementados, matriz de rastreabilidade do enunciado e a lista explícita do que é exigência mínima versus funcionalidade extra. |
| [`03-arquitetura.md`](03-arquitetura.md) | A arquitetura hexagonal simplificada real — camadas, diagramas de componentes e de dependência, estrutura de diretórios, e as simplificações conscientes verificadas no código. |
| [`04-modelo-de-dominio.md`](04-modelo-de-dominio.md) | `Customer`, `Account`, `PixKey` e `Transaction`: atributos, regras de negócio, invariantes, exceções e o diagrama de classes do domínio. |
| [`05-banco-de-dados.md`](05-banco-de-dados.md) | Schema real do SQLite (4 tabelas), constraints, índices, diagrama ER e a justificativa de dinheiro em centavos. |
| [`06-api.md`](06-api.md) | Todos os endpoints implementados, agrupados por recurso, com exemplos de request/response, códigos HTTP e a matriz de autorização. |
| [`07-fluxos-principais.md`](07-fluxos-principais.md) | O caminho ponta a ponta (Frontend → Controller → Service → Domínio → Port → Adapter → SQLite) de cada caso de uso principal, com diagramas de sequência para depósito, saque e transferência Pix. |
| [`08-frontend.md`](08-frontend.md) | As 6 páginas da interface web, seus módulos JavaScript, e como cada uma consome a API exclusivamente via `fetch()`. |
| [`09-testes.md`](09-testes.md) | A estratégia de testes em três camadas (unit/service/API), com a tabela completa de requisito/regra → arquivo de teste → cenário. |
| [`10-decisoes-tecnicas.md`](10-decisoes-tecnicas.md) | Registro no estilo ADR de cada decisão técnica relevante — alternativas consideradas, escolha, motivo e trade-off. |
| [`11-rastreabilidade.md`](11-rastreabilidade.md) | Matriz completa conectando requisito acadêmico → funcionalidade → endpoint → Service → persistência → frontend → teste. |
| [`12-guia-de-apresentacao.md`](12-guia-de-apresentacao.md) | Roteiro de apresentação oral de 7–10 minutos, com os arquivos a abrir em cada momento e respostas curtas para perguntas prováveis do professor. |

## Como navegar

Para uma leitura sequencial completa, siga a ordem numérica acima — cada documento assume o
vocabulário e as referências de código já introduzidos nos anteriores. Para preparar uma
apresentação, comece por `12-guia-de-apresentacao.md`, que aponta de volta para os demais quando
necessário.
