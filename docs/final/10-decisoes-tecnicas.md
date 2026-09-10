# 10 — Decisões Técnicas

Registro no estilo *Architecture Decision Record* (ADR) resumido: cada decisão relevante do
projeto, as alternativas consideradas, a opção escolhida, o motivo e o trade-off aceito. O objetivo
é demonstrar que as escolhas foram **intencionais**, não a ausência de escolha.

## D1 — FastAPI como framework de API

- **Alternativas consideradas:** Flask, Django (com Django REST Framework).
- **Escolha:** FastAPI 0.115.
- **Motivo:** exigência do enunciado. Além disso, FastAPI gera OpenAPI/Swagger automaticamente a
  partir dos schemas Pydantic (`RNF06`), tem injeção de dependência nativa via `Depends()` — o
  suficiente para este projeto sem precisar de um framework de DI separado (ver D11) — e validação
  de corpo/tipo integrada, que é o que sustenta `extra="forbid"` nos schemas de entrada
  (`app/adapters/inbound/api/schemas.py`).
- **Trade-off:** Flask exigiria escolher e configurar manualmente validação (ex.: Marshmallow) e
  geração de OpenAPI; Django traria um ORM e um admin embutidos que competiriam com a escolha
  explícita de SQLAlchemy (D3) e tornariam a separação Controller/Service menos didática (o padrão
  Django é *fat models*, o oposto do que o enunciado pede).

## D2 — SQLite como banco de dados

- **Alternativas consideradas:** PostgreSQL, MySQL.
- **Escolha:** SQLite, arquivo único `bank.db`.
- **Motivo:** exigência do enunciado (`RNF03`: executável localmente sem infraestrutura externa).
  Sem servidor de banco separado, sem Docker, sem credenciais de conexão — `git clone` +
  `pip install` + `alembic upgrade head` é suficiente para rodar o projeto em qualquer máquina.
- **Trade-off:** SQLite permite apenas um *writer* ativo por vez (lock a nível de arquivo) e não tem
  tipos de dado tão ricos quanto Postgres (ex.: sem `NUMERIC` com precisão configurável nativa) — mas
  nenhuma dessas limitações importa para o volume e a concorrência de um projeto acadêmico avaliado
  localmente. Ver D4 e a nota de concorrência em `05-banco-de-dados.md`.

## D3 — SQLAlchemy 2.x (estilo `Mapped`/`mapped_column`) como ORM

- **Alternativas consideradas:** SQL puro (`sqlite3` da stdlib), SQLAlchemy no estilo legado
  (`Column` declarativo 1.x), outro ORM (ex.: Tortoise ORM, SQLModel).
- **Escolha:** SQLAlchemy 2.0, com a sintaxe tipada `Mapped[...]`/`mapped_column(...)`.
- **Motivo:** SQL puro exigiria escrever e manter manualmente todo o mapeamento
  linha-de-resultado ⇄ objeto Python, sem ganho para este projeto. A sintaxe 2.0 traz tipagem
  estática nas colunas (`Mapped[int]`, `Mapped[str | None]`), o que ajuda tanto a leitura do código
  quanto o `black`/`ruff` a pegar erros cedo. As migrações versionadas (Alembic, ver `README.md` da
  raiz do projeto) já assumem SQLAlchemy como fonte de verdade do schema via `Base.metadata`.
- **Trade-off:** SQLAlchemy tem uma curva de aprendizado real (sessão, identity map, `flush` vs
  `commit`) — mas é exatamente esse aprendizado que o enunciado quer demonstrar.

## D4 — SQLAlchemy síncrono (não `asyncio`)

- **Alternativas consideradas:** SQLAlchemy assíncrono (`AsyncSession`, `create_async_engine`) com
  driver `aiosqlite`, combinado a rotas `async def` no FastAPI.
- **Escolha:** `Session` síncrona (`sqlalchemy.orm.Session`), rotas `def` (síncronas) nos
  Controllers.
- **Motivo:** FastAPI já executa rotas síncronas em um *threadpool* automaticamente, então não há
  ganho de throughput perceptível para o volume deste projeto. SQLAlchemy síncrono é mais direto de
  ler e depurar — sem `await` espalhado por Service, Port e Adapter — o que favorece a clareza
  didática sobre performance, coerente com o resto das escolhas do projeto.
- **Trade-off:** numa API de produção com alto volume de I/O concorrente, `asyncio` teria vantagem
  real de escalabilidade. Aqui, essa vantagem não existe (SQLite tem um único *writer* de qualquer
  forma — ver D2) e o custo de complexidade adicional não se paga.

## D5 — Dinheiro como `int` em centavos

- **Alternativas consideradas:** `float`, `decimal.Decimal`, tipo `NUMERIC` do banco com
  `TypeDecorator` customizado no SQLAlchemy.
- **Escolha:** `int` em centavos (`balance_cents`, `amount_cents`) em todas as camadas do backend.
- **Motivo:** `float` introduz erro de arredondamento binário, inaceitável em operações financeiras
  repetidas; `Decimal` resolveria a precisão, mas exigiria serialização cuidadosa em JSON e um
  `TypeDecorator` para mapear no SQLite (que não tem tipo decimal nativo). `int` em centavos resolve
  a precisão com o tipo mais simples possível, sem configuração extra. A explicação técnica completa
  (com o exemplo de `0.1 + 0.2 != 0.3`) está em `05-banco-de-dados.md`.
- **Trade-off:** exige disciplina — todo campo `*_cents` deve permanecer inteiro em todas as
  camadas, e a conversão para `"R$ 10,50"` só pode acontecer em exibição (frontend), nunca em cálculo
  (ver `04-modelo-de-dominio.md` e `08-frontend.md`). É uma regra simples de seguir, mas que precisa
  ser lembrada conscientemente — não há um tipo `Money` do Python que imponha isso automaticamente.

## D6 — Arquitetura hexagonal simplificada

- **Alternativas consideradas:** MVC simples (Controller chamando o ORM direto, sem Service
  separado); arquitetura hexagonal "pura" (com Unit of Work genérico, DTOs de camada em camada,
  mapeadores explícitos em todo lugar).
- **Escolha:** Controller → Service → Domínio/Port → Adapter → SQLAlchemy → SQLite, sem Unit of Work
  genérico, sem DTO próprio por camada (os DTOs de API já são os schemas Pydantic).
- **Motivo:** MVC simples não atenderia a exigência central do enunciado (Controller e Service
  precisam ser módulos claramente distintos, com a regra de negócio fora do Controller). Hexagonal
  pura, por outro lado, introduziria abstrações (Unit of Work, mapeadores em camadas adicionais) que
  não têm público — este projeto tem 4 conceitos de domínio e um único mecanismo de persistência
  (SQLite); a interface de repositório já é suficiente para mostrar inversão de dependência sem
  precisar generalizar mais.
- **Trade-off:** duas concessões conscientes resultam disso — `Transaction` sem entidade de domínio
  própria, e checagens de autorização lendo o repositório direto em alguns pontos, sem passar pelo
  Service. Ambas são detalhadas e justificadas em `03-arquitetura.md`.

## D7 — Repository Ports como `typing.Protocol`

- **Alternativas consideradas:** classe abstrata (`abc.ABC` + `@abstractmethod`); nenhuma interface
  (Service recebendo a classe concreta `*RepositorySqlAlchemy` diretamente).
- **Escolha:** `Protocol` (tipagem estrutural, sem herança).
- **Motivo:** `Protocol` expressa exatamente o contrato necessário (quais métodos um Service espera)
  sem exigir que `AccountRepositorySqlAlchemy` herde explicitamente de uma classe base — reduz
  acoplamento textual entre o Adapter e a definição da porta, e permite que um repositório de teste
  (ver `BrokenTransactionRepo` em `test_pix_transfer_service.py`, `09-testes.md`) satisfaça a
  interface sem herdar de nada, só implementando os métodos certos.
- **Trade-off:** `Protocol` não é verificado em runtime — só ferramentas de tipagem estática (mypy,
  ou o próprio editor) pegam um Adapter que não implementa o contrato corretamente. Numa base de
  código maior isso pesaria mais; aqui, com 4 portas e 4 adapters, o risco é baixo.

## D8 — `Transaction` sem entidade de domínio própria (domínio/ORM parcialmente separados)

- **Alternativas consideradas:** criar uma entidade de domínio `Transaction` pura, simétrica a
  `Customer`/`Account`/`PixKey`, com mapeamento explícito ORM ⇄ domínio no repositório.
- **Escolha:** `Transaction` existe só como modelo SQLAlchemy
  (`adapters/outbound/persistence/models.py`), complementada por uma função pura de validação
  (`domain/transaction_rules.py::validate_transaction_shape()`).
- **Motivo:** `Transaction` é um registro de ledger *create-only* — nunca é atualizada nem tem
  comportamento além de existir. Uma entidade de domínio separada geraria código de mapeamento
  (`_to_domain()`/construção do modelo) sem nenhuma regra de negócio adicional para justificá-lo —
  puro boilerplate.
- **Trade-off:** é a concessão mais visível da arquitetura — a porta `TransactionRepository` e os
  Services `AccountService`/`PixTransferService` importam `Transaction` diretamente da camada de
  persistência (`app.adapters.outbound.persistence.models`), uma inversão real, ainda que pequena e
  isolada, da direção de dependência pretendida. Documentada e assumida conscientemente, não
  escondida — ver `03-arquitetura.md`.

## D9 — Autenticação simples por sessão (não JWT/OAuth)

- **Alternativas consideradas:** JWT em header `Authorization`, OAuth2 (`fastapi.security.OAuth2`),
  nenhuma autenticação (endpoints abertos).
- **Escolha:** sessão via cookie assinado (`starlette.middleware.sessions.SessionMiddleware` +
  `itsdangerous`), com `customer_id` guardado na sessão após `POST /api/auth/login`.
- **Motivo:** o enunciado não exige autenticação, mas sem ela as regras "cliente só opera a própria
  conta" e "não é permitido transferir para a própria conta, mas é permitido transferir para a de
  outro cliente" perdem sentido prático — não haveria como distinguir "outro cliente" de "eu mesmo".
  Sessão via cookie assinado é suficiente para demonstrar controle de acesso sem a complexidade de
  emitir, renovar e validar tokens JWT.
- **Trade-off:** cookies de sessão não escalam horizontalmente sem um *store* de sessão
  compartilhado (Redis, banco) — irrelevante aqui, com um único processo `uvicorn`. Não há
  refresh token, expiração configurável, nem revogação individual de sessão — fora do escopo
  proposital (ver `02-requisitos.md`, "Fora do escopo").

## D10 — Sem integração real com o Pix / Banco Central

- **Alternativas consideradas:** nenhuma — integração real nunca foi cogitada como viável para o
  escopo do trabalho.
- **Escolha:** "chave Pix" e "transferência Pix" são conceitos inteiramente simulados dentro do
  próprio banco de dados do projeto.
- **Motivo:** integração real exigiria credenciamento junto ao Banco Central (DICT), certificados,
  ambiente de homologação — infraestrutura totalmente fora do alcance e do objetivo de um trabalho
  acadêmico. O valor pedagógico está em modelar corretamente a *forma* da transferência (chave →
  conta de destino, débito/crédito atômico), não em processá-la de verdade.
- **Trade-off:** nenhum "Pix" cadastrado aqui funciona fora deste sistema — é uma simulação, e o
  `README.md` e `01-visao-geral.md` deixam isso explícito para quem avaliar o projeto.

## D11 — Sem framework de injeção de dependência

- **Alternativas consideradas:** `dependency-injector`, `punq`, container de DI customizado.
- **Escolha:** só `Depends()` nativo do FastAPI, com funções `get_*_service()` por Controller.
- **Motivo:** o próprio FastAPI já resolve o problema real deste projeto — "montar um Service com os
  Repository Adapters certos, usando a `Session` da requisição" — sem precisar de um container
  configurável, registro de bindings, nem *lifetime scopes*. Um framework de DI resolveria um
  problema que este projeto não tem (muitas implementações alternativas de uma mesma porta,
  registradas dinamicamente).
- **Trade-off:** a função `get_*_service()` é reescrita (com pequenas variações) em cada arquivo de
  controller — uma repetição pequena e aceitável dado o número de Services (4).

## D12 — Sem CQRS ou microserviços

- **Alternativas consideradas:** nenhuma foi implementada; citadas aqui só para deixar explícito que
  foram avaliadas e descartadas, não esquecidas.
- **Escolha:** um único modelo de leitura e escrita por entidade (sem `Command`/`Query` separados
  nem modelo de leitura materializado à parte), um único processo (sem serviços distribuídos).
- **Motivo:** CQRS resolve o problema de um modelo de leitura que diverge estruturalmente do modelo
  de escrita, geralmente com um *read model* persistido separadamente — este projeto lê o saldo
  calculando-o sob demanda (ver D13), sem precisar de um modelo de leitura materializado à parte.
  Microserviços resolveriam um problema de deploy e escala independente entre módulos — inexistente
  aqui, onde todo o sistema roda em um único processo `uvicorn` contra um único arquivo SQLite.
- **Trade-off:** nenhum, para este escopo — essas técnicas adicionariam complexidade sem nenhum
  problema real para resolver, o oposto do que o enunciado pede ("sem introduzir infraestrutura
  desnecessária").

## D13 — Event sourcing para o saldo de conta

- **Alternativas consideradas:** manter `balance_cents` como coluna mutável em `accounts`,
  atualizada via `UPDATE` a cada depósito/saque/transferência (abordagem original do projeto — ainda
  descrita, sem essa evolução, em `docs/specs/`).
- **Escolha:** remover a coluna `balance_cents` de `accounts`; `transactions` passa a ser a única
  fonte de verdade sobre movimentações financeiras, e o saldo é sempre recalculado somando os
  eventos daquela conta (`AccountRepositorySqlAlchemy._compute_balance()`). Depositar, sacar e
  transferir passam a ser só um `INSERT` em `transactions` — nunca mais um `UPDATE` em `accounts`.
  Ver `04-modelo-de-dominio.md` e `05-banco-de-dados.md` para o detalhamento, e
  `07-fluxos-principais.md` para os diagramas de sequência atualizados.
- **Motivo:** `transactions` já era, na prática, um log completo de todo evento financeiro da conta
  — manter `balance_cents` como coluna era guardar o mesmo fato duas vezes (estado e histórico), com
  risco real de os dois divergirem se algum caminho de código esquecesse de atualizar um dos dois.
  Derivar o saldo elimina essa redundância: não existe estado para ficar inconsistente com o
  histórico, porque o "estado" é sempre calculado a partir dele.
- **Trade-off:** cada leitura de saldo passa a exigir somar todo o histórico de transações da conta
  (duas queries `SUM`), em vez de ler um único campo — mais caro por leitura, mas sem custo real no
  volume de um projeto acadêmico. Não é event sourcing "completo" no sentido de arquitetura de
  produção: não há *event store* dedicado, *snapshotting* incremental, nem projeção
  materializada/cache — se o volume de transações por conta crescesse muito, seria o próximo passo
  natural (ver D12, que documenta por que isso não foi necessário aqui).

## Resumo

Cada decisão acima resolve um requisito real do projeto (ou o requisito explícito do enunciado, ou
uma necessidade didática concreta, como distinguir "minha conta" de "conta de outro cliente"). Onde
uma técnica mais sofisticada foi deliberadamente deixada de fora (D9 sem JWT, D10 sem Pix real, D12
sem CQRS/microserviços), a ausência é uma escolha registrada, não uma lacuna — e onde uma técnica
mais sofisticada *foi* adotada de forma proposital e escopada (D13, event sourcing só para o saldo),
isso também está registrado, com o trade-off explícito em vez de omitido.
