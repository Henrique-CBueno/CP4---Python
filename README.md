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

```bash
python -m scripts.init_db
```

Cria o arquivo `bank.db` na raiz do projeto com as 4 tabelas (`customers`, `accounts`, `pix_keys`,
`transactions`). Este passo é opcional: a aplicação também cria o schema automaticamente ao subir,
se ele ainda não existir.

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
  init_db.py             # inicialização do schema (fora da API pública)
tests/
  unit/                   # domínio puro
  service/                 # services contra SQLite temporário
  api/                      # endpoints via TestClient
docs/specs/                 # documentação de design do projeto
```

Veja [`docs/specs/06-architecture.md`](docs/specs/06-architecture.md) para a explicação completa da
arquitetura (Controller → Service → Repository Port → Adapter SQLite).
