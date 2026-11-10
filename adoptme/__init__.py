import os

from flask import Flask, jsonify
from werkzeug.exceptions import HTTPException

from .config import Config
from .extensions import cors, migrate
from .ext.db import db, init_app as init_db, register_models


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    if not app.config.get("UPLOAD_FOLDER"):
        app.config["UPLOAD_FOLDER"] = os.path.join(app.instance_path, "uploads")

    # extensoes / banco
    init_db(app)
    register_models()
    migrate.init_app(app, db)
    cors.init_app(app, resources={r"/api/*": {"origins": "*"}})

    # registro dos dominios (cada modulo se registra)
    from .auth import init_app as init_auth
    from .anunciantes import init_app as init_anunciantes
    from .animais import init_app as init_animais
    from .parceiros import init_app as init_parceiros
    from .mercadolivre import init_app as init_mercadolivre

    init_auth(app)
    init_anunciantes(app)
    init_animais(app)
    init_parceiros(app)
    init_mercadolivre(app)

    # erros da API em JSON, para o frontend mostrar a mensagem
    @app.errorhandler(HTTPException)
    def erro_http(e):
        return jsonify({"erro": e.description}), e.code

    @app.get("/api/health")
    def health():
        return {"status": "ok", "message": "AdoptMe API is running"}

    @app.cli.command("init-db")
    def init_db_command():
        """Cria todas as tabelas no banco (uso em desenvolvimento)."""
        db.create_all()
        print("Tabelas criadas.")

    @app.cli.command("seed-db")
    def seed_db_command():
        """Cria as tabelas e insere dados de demonstracao (se o banco estiver vazio)."""
        from .seed import seed

        db.create_all()
        print("Dados de demonstracao inseridos." if seed() else "Banco ja possui dados; nada foi inserido.")

    return app
