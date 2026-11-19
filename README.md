# AdoptMe

Plataforma web para divulgacao de animais para adocao. Reune animais de ONGs, abrigos e
protetores, mostra quem cuida de cada um e permite manifestar interesse. Tambem exibe
produtos para pets do Mercado Livre e anuncios de empresas parceiras (cobranca por clique).

- **Backend:** Python + Flask (API REST em `/api`), SQLAlchemy 2.0, SQLite
- **Frontend:** Vue 3 + Vite + Vue Router, com CSS proprio e responsivo
- **Testes:** pytest (backend)

## Como rodar (passo a passo)

Pre-requisitos: Python 3.10+ e Node.js 18+.

### 1. Backend

```bash
# na pasta do projeto
python -m venv .venv
.venv\Scripts\activate            # Linux/macOS: source .venv/bin/activate
pip install -e ".[test]"          # ou: pip install -r requirements.txt

copy .env.example .env            # Linux/macOS: cp .env.example .env
# (opcional) preencha ML_CLIENT_ID e ML_CLIENT_SECRET no .env para ver os produtos do Mercado Livre

flask --app app.py seed-db        # cria as tabelas e os dados de demonstracao
flask --app app.py run --debug    # API em http://localhost:5000/api
```

### 2. Frontend (em outro terminal)

```bash
cd frontend
npm install
npm run dev                       # site em http://localhost:5173
```

O Vite encaminha as chamadas `/api` para o backend em `http://localhost:5000`
(para outro endereco: `API_URL=http://localhost:5001 npm run dev`).

### 3. Contas de demonstracao (senha de todas: `senha123`)

| Email | Perfil |
|---|---|
| `ong@adoptme.dev` | Anunciante (organizacao) |
| `ana@adoptme.dev` | Anunciante (pessoa fisica) |
| `carlos@adoptme.dev` | Adotante |

### 4. Testes

```bash
pytest -v                         # todos os testes
pytest --cov=adoptme              # com cobertura
```

Os testes usam SQLite em memoria (`TestConfig`) e simulam a API do Mercado Livre; nao
precisam de internet nem tocam no banco `instance/adoptme.db`.

## Variaveis de ambiente (`.env`)

Veja `.env.example`. Todas sao opcionais em desenvolvimento.

| Variavel | Uso |
|---|---|
| `ML_CLIENT_ID=8091084609428812`, `ML_CLIENT_SECRET=DhHNQblMKRdMZmsy7AcxvCccN1yXmjlc` | Credenciais da aplicacao no Mercado Livre (sem elas, o site informa que as sugestoes estao indisponiveis) |
| `SECRET_KEY` | Chave que assina o cookie de sessao |
| `FLASK_DEBUG` | `1` para modo de desenvolvimento |
| `LOG_LEVEL` | Nivel do log (`INFO` por padrao) |
| `DATABASE_URL` | Banco de dados (padrao: SQLite em `instance/adoptme.db`) |
| `UPLOAD_FOLDER` | Pasta das fotos enviadas (padrao: `instance/uploads`) |

O `.env` nao vai para o git.

## Estrutura

```
app.py                  # cria o app: create_app()
adoptme/
  __init__.py           # fabrica da aplicacao (config, extensoes, blueprints, erros, comandos)
  config.py             # Config e TestConfig (le o .env)
  extensions.py         # CORS e Migrate
  ext/db/               # SQLAlchemy e registro dos models
  logs.py               # logging (terminal e instance/logs/adoptme.log)
  seed.py               # dados de demonstracao
  auth/                 # usuarios, enderecos, login/sessao e validacoes (CPF/CNPJ, CEP, email)
  anunciantes/          # perfil de quem divulga animais
  animais/              # animais, fotos, interesses e painel do anunciante
  parceiros/            # empresas parceiras, anuncios e cliques (CPC)
  mercadolivre/         # integracao com a API do Mercado Livre (sem tabelas)
tests/                  # testes pytest
frontend/src/
  views/                # telas (inicio, animal, perfil, sugestoes, entrar, cadastro, minha conta, painel)
  components/           # cards de animal e produto, banner, anuncio
  services/             # chamadas a API, sessao, consultas de CEP/CNPJ
```

Cada dominio do backend tem `models.py`, `routes.py` (Blueprint com rotas finas) e
`services.py` (regras de negocio), e se registra no `create_app()` pelo seu `init_app(app)`.

## Comandos uteis

```bash
flask --app app.py init-db                 # so cria as tabelas
flask --app app.py seed-db                 # tabelas + dados de demonstracao
flask --app app.py ml-teste "racao gato"   # testa as credenciais e a busca no Mercado Livre

# anuncios das empresas parceiras (cadastrados pela equipe da plataforma)
flask --app app.py nova-empresa "PetShop Amigo" "27 3333-0000" --email contato@petshop.com
flask --app app.py novo-anuncio 1 "10% de desconto na primeira racao" https://petshop.com/promo
flask --app app.py anuncios
flask --app app.py relatorio-cliques --de 2026-11-01 --ate 2026-11-30
```

O site sorteia um anuncio na pagina inicial, na de cada animal e na de sugestoes. O clique
passa por `/api/parceiros/anuncios/<id>/clique`, que registra e redireciona; cliques
repetidos do mesmo visitante no mesmo anuncio, em 30 minutos, nao contam.

## Logs

As principais operacoes (cadastros, logins recusados, alteracoes de animais, fotos, cliques
e falhas do Mercado Livre) e os erros inesperados sao registrados no terminal e em
`instance/logs/adoptme.log`. Erros inesperados devolvem 500 com mensagem generica em JSON.
