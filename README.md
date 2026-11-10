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

### Anuncios das empresas parceiras (cobranca por clique)

As empresas e os anuncios sao cadastrados pela equipe da plataforma, pelo terminal:

```bash
flask --app app.py nova-empresa "PetShop Amigo" "27 3333-0000" --email contato@petshop.com
flask --app app.py novo-anuncio 1 "10% de desconto na primeira racao" https://petshop.com/promo
flask --app app.py anuncios                                      # lista empresas, anuncios e cliques
flask --app app.py relatorio-cliques --de 2026-11-01 --ate 2026-11-30   # base da cobranca
```

O site sorteia um anuncio na pagina inicial e na pagina de cada animal. O clique passa por
`/api/parceiros/anuncios/<id>/clique`, que registra e redireciona; cliques repetidos do mesmo
visitante no mesmo anuncio, dentro de 30 minutos, nao contam.

### Testes de persistencia

```bash
pip install -e ".[test]"
pytest -v
```

Os testes usam SQLite em memoria (`TestConfig`) e nao tocam no `instance/adoptme.db`.

### Variaveis de ambiente (opcionais)
- `SECRET_KEY`, `DATABASE_URL`
- `ML_CLIENT_ID`, `ML_CLIENT_SECRET`, `ML_SITE_ID` (integracao Mercado Livre)

Copie `.env.example` para `.env` e preencha; o `flask run` le o `.env` sozinho
(`python-dotenv`). O `.env` nao vai para o git.

## Frontend

```bash
cd frontend
npm install
npm run dev     # http://localhost:5173 (proxy /api -> :5000)
```

Para apontar o proxy para outro backend: `API_URL=http://localhost:5001 npm run dev`.

Telas (`frontend/src/views`): inicio com o banner do Mercado Livre e a lista de animais,
detalhes do animal (com contato do responsavel e manifestacao de interesse), perfil do
responsavel, sugestoes de compras, entrar e cadastro (endereco pelo CEP e dados pelo CNPJ).
O login usa a sessao do Flask (cookie), que passa pelo proxy do Vite.

As fotos enviadas pelos anunciantes ficam em `instance/uploads` (fora do git). Para usar
outra pasta, defina `UPLOAD_FOLDER`.

## Modulos (dominios)
- `auth`        -> Usuario, Endereco
- `anunciantes` -> Anunciante
- `animais`     -> Animal, FotoAnimal, InteresseAdocao
- `parceiros`   -> EmpresaParceira, Anuncio, CliqueAnuncio
- `mercadolivre`-> integracao com a API do Mercado Livre (sem tabelas)
