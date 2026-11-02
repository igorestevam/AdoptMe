# AdoptMe

Plataforma web para divulgacao de animais para adocao. Backend em Flask (API REST)
e frontend em Vue 3 + Vite. Estrutura modular baseada no padrao TaskFlow.
Contexto completo do projeto no arquivo `CLAUDE.md`.

## Backend

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e .

# criar as tabelas (desenvolvimento rapido)
flask --app app.py init-db

# ou usando migrations
flask --app app.py db init
flask --app app.py db migrate -m "init"
flask --app app.py db upgrade

flask --app app.py run --debug   # ou: python app.py
```

API em http://localhost:5000/api  (health: /api/health)

### Banco de dados (SQLite) e dados de demonstracao

O banco fica em `instance/adoptme.db`. As chaves estrangeiras do SQLite sao ativadas
em toda conexao (`adoptme/ext/db/__init__.py`).

```bash
flask --app app.py seed-db   # cria as tabelas e insere dados de exemplo (senha: senha123)
```

### Testes de persistencia

```bash
pip install -e ".[test]"
pytest -v
```

Os testes usam SQLite em memoria (`TestConfig`) e nao tocam no `instance/adoptme.db`.

### Variaveis de ambiente (opcionais)
- `SECRET_KEY`, `DATABASE_URL`
- `ML_CLIENT_ID`, `ML_CLIENT_SECRET`, `ML_SITE_ID` (integracao Mercado Livre)

## Frontend

```bash
cd frontend
npm install
npm run dev     # http://localhost:5173 (proxy /api -> :5000)
```

## Modulos (dominios)
- `auth`        -> Usuario, Endereco
- `anunciantes` -> Anunciante
- `animais`     -> Animal, FotoAnimal, InteresseAdocao
- `parceiros`   -> EmpresaParceira, Anuncio, CliqueAnuncio
- `mercadolivre`-> integracao com a API do Mercado Livre (sem tabelas)
