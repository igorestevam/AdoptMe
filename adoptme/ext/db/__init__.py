import sqlite3

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import event
from sqlalchemy.engine import Engine

db = SQLAlchemy()


@event.listens_for(Engine, "connect")
def _ativar_foreign_keys_sqlite(dbapi_connection, connection_record):
    """O SQLite ignora chaves estrangeiras por padrao; ativa em cada conexao."""
    if isinstance(dbapi_connection, sqlite3.Connection):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


def init_app(app):
    db.init_app(app)


def register_models():
    """Importa os modulos de modelos para registra-los no metadata do SQLAlchemy."""
    import adoptme.auth.models            # noqa: F401
    import adoptme.anunciantes.models     # noqa: F401
    import adoptme.animais.models         # noqa: F401
    import adoptme.parceiros.models       # noqa: F401
