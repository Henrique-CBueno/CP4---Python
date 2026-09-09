# Banco Digital Acadêmico

Simulação acadêmica de um banco digital (clientes, contas, chaves Pix, depósitos, saques e
transferências Pix internas), construída com FastAPI, SQLAlchemy e SQLite, com frontend em
HTML/CSS/JavaScript consumindo a própria API.

Não é um banco real: não há integração com o Banco Central, com o sistema Pix real ou com qualquer
processamento financeiro verdadeiro.

A documentação de design completa (requisitos, modelo de domínio, casos de uso, especificação da
API, esquema do banco, arquitetura, especificação do frontend, plano de testes e plano de
implementação) está em [`docs/specs/`](docs/specs/).

## Requisitos

- Python 3.12+

## Instalação

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Inicializar o banco de dados

Duas formas equivalentes de criar o schema num banco novo:

```bash
python -m scripts.init_db        # cria as tabelas direto do metadata do SQLAlchemy
# ou, recomendado a partir de agora (fica com histórico de versão):
alembic upgrade head
```

`scripts.init_db` roda `Base.metadata.create_all()` — rápido, sem histórico, e é o que a própria
aplicação usa automaticamente ao subir se o banco ainda não existir. `alembic upgrade head` aplica
as migrações versionadas em `alembic/versions/` e é o caminho recomendado quando o schema precisar
evoluir depois (nova coluna, novo índice etc.): gere a alteração no `app/adapters/outbound/persistence/models.py`,
depois `alembic revision --autogenerate -m "descrição"` e revise o arquivo gerado antes de aplicar.

Se você já tem um `bank.db` criado antes do Alembic existir (via `create_all`, sem a tabela
`alembic_version`), marque-o como já estando na revisão atual em vez de recriar as tabelas:

```bash
alembic stamp head
```

## Login e usuário admin

A aplicação exige login (sessão via cookie). Como criar clientes é uma operação restrita a admin,
é preciso criar o primeiro admin diretamente (sem passar pela API):

```bash
python -m scripts.create_admin
```

Cria o admin `admin@example.com` / senha `admin123` (personalizável com `--name`, `--email`, `--cpf`
e `--password`). Faça login em `/login` com essas credenciais para cadastrar clientes (com senha) e
abrir contas para eles. Um cliente logado só vê e opera as próprias contas; o admin vê e opera
tudo, incluindo depósito em conta de qualquer cliente.

> Se você já tinha um `bank.db` de antes da autenticação existir, apague-o e recrie
> (`rm bank.db && python -m scripts.init_db`) — as novas colunas de login em `customers` são
> `NOT NULL`. **Cuidado:** nunca apague/recrie o `bank.db` enquanto um `uvicorn` estiver rodando
> contra ele — o processo fica com um handle para o arquivo antigo e passa a falhar com
> "readonly database"; reinicie o servidor depois de trocar o arquivo.

## Executar a aplicação

```bash
uvicorn app.main:app --reload
```

- Interface web: http://127.0.0.1:8000/
- Documentação interativa da API (Swagger): http://127.0.0.1:8000/docs

## Rodar os testes

```bash
pytest
```

Os testes usam um banco SQLite temporário por teste — não afetam o `bank.db` usado pela aplicação
em execução normal.

## Qualidade de código

```bash
black app scripts tests          # formata
ruff check app scripts tests     # lint (use --fix para autocorrigir o que for possível)
```

Configuração em [`pyproject.toml`](pyproject.toml) (linha de 100 colunas para os dois). O hook de
geração de migração do Alembic já roda `black`/`ruff` automaticamente no arquivo gerado.

## Migrações (Alembic)

```bash
alembic revision --autogenerate -m "descrição da alteração"   # gera uma migração a partir do diff
alembic upgrade head                                            # aplica até a mais recente
alembic downgrade -1                                             # desfaz a última
```

`alembic/env.py` usa a mesma `DATABASE_URL` da aplicação (`app/infrastructure/config.py`) e conhece
todas as entidades via `app.adapters.outbound.persistence.models`. Para gerar/testar uma migração
sem tocar no `bank.db` real, aponte para outro arquivo temporariamente:
`ALEMBIC_DATABASE_URL="sqlite:///teste.db" alembic upgrade head`.

## Estrutura do projeto

```
app/
  domain/            # entidades de domínio, exceções, validadores, regras de transação
  application/        # services (casos de uso) e ports (interfaces de repositório)
  adapters/
    inbound/api/       # controllers REST
    inbound/web/        # rotas que servem as páginas HTML
    outbound/persistence/ # modelos SQLAlchemy e repositórios concretos
  infrastructure/      # configuração e sessão do banco
  templates/            # páginas Jinja2
  static/                # CSS e JavaScript
scripts/
  init_db.py             # inicialização rápida do schema (create_all, fora da API pública)
  create_admin.py         # bootstrap do primeiro usuário admin
alembic/
  versions/                # migrações versionadas
  env.py                     # aponta para Base.metadata e DATABASE_URL da aplicação
tests/
  unit/                   # domínio puro
  service/                 # services contra SQLite temporário
  api/                      # endpoints via TestClient
docs/specs/                 # documentação de design do projeto
pyproject.toml               # configuração do black e do ruff
```

Veja [`docs/specs/06-architecture.md`](docs/specs/06-architecture.md) para a explicação completa da
arquitetura (Controller → Service → Repository Port → Adapter SQLite).
