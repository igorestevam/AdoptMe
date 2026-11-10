import pytest
from werkzeug.security import generate_password_hash

from adoptme import create_app
from adoptme.config import TestConfig
from adoptme.ext.db import db
from adoptme.auth.models import Usuario, Endereco
from adoptme.anunciantes.models import Anunciante
from adoptme.animais.models import Animal
from adoptme.auth.validacao import _digito, formatar_documento


@pytest.fixture
def app():
    """App com SQLite em memoria; as tabelas sao criadas e destruidas a cada teste."""
    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def session(app):
    return db.session


def gerar_cpf(n: int) -> str:
    """CPF valido e diferente para cada n (o CPF/CNPJ e unico no banco)."""
    base = f"{n:09d}"
    dv1 = _digito(base, range(10, 1, -1))
    dv2 = _digito(base + str(dv1), range(11, 1, -1))
    return formatar_documento(f"{base}{dv1}{dv2}")


# fabricas: cada uma devolve uma funcao que cria e persiste o registro

@pytest.fixture
def criar_usuario(session):
    contador = {"n": 0}

    def _criar(**campos):
        contador["n"] += 1
        dados = {
            "nome": f"Usuario {contador['n']}",
            "cpf_cnpj": gerar_cpf(100 + contador["n"]),
            "telefone": "27999990000",
            "email": f"usuario{contador['n']}@teste.com",
            "senha_hash": generate_password_hash("senha123"),
        }
        dados.update(campos)
        u = Usuario(**dados)
        session.add(u)
        session.commit()
        return u

    return _criar


@pytest.fixture
def criar_endereco(session):
    def _criar(usuario, **campos):
        dados = {
            "estado": "ES", "cidade": "Vitoria", "bairro": "Centro",
            "rua": "Rua A", "numero": "10", "cep": "29000-000",
        }
        dados.update(campos)
        e = Endereco(usuario=usuario, **dados)
        session.add(e)
        session.commit()
        return e

    return _criar


@pytest.fixture
def criar_anunciante(session, criar_usuario):
    def _criar(usuario=None, tipo="organizacao", **campos):
        a = Anunciante(usuario=usuario or criar_usuario(), tipo=tipo, **campos)
        session.add(a)
        session.commit()
        return a

    return _criar


@pytest.fixture
def criar_animal(session, criar_anunciante):
    def _criar(anunciante=None, **campos):
        dados = {"nome": "Nina", "especie": "cachorro", "porte": "medio", "sexo": "femea"}
        dados.update(campos)
        a = Animal(anunciante=anunciante or criar_anunciante(), **dados)
        session.add(a)
        session.commit()
        return a

    return _criar
