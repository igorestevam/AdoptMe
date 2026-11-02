from werkzeug.security import generate_password_hash, check_password_hash

from adoptme.ext.db import db
from .models import Usuario


def _serialize(u: Usuario) -> dict:
    return {
        "id": u.id,
        "nome": u.nome,
        "cpf_cnpj": u.cpf_cnpj,
        "telefone": u.telefone,
        "email": u.email,
    }


def listar_usuarios() -> list[dict]:
    return [_serialize(u) for u in Usuario.query.all()]


def obter_usuario(usuario_id: int) -> dict | None:
    u = db.session.get(Usuario, usuario_id)
    return _serialize(u) if u else None


def criar_usuario(dados: dict) -> dict:
    # TODO: validar dados (email unico, formato de CPF/CNPJ, etc.)
    u = Usuario(
        nome=dados["nome"],
        cpf_cnpj=dados["cpf_cnpj"],
        telefone=dados["telefone"],
        data_nascimento=dados.get("data_nascimento"),
        email=dados["email"],
        senha_hash=generate_password_hash(dados["senha"]),
    )
    db.session.add(u)
    db.session.commit()
    return _serialize(u)


def autenticar(email: str, senha: str) -> dict | None:
    u = Usuario.query.filter_by(email=email).first()
    if u and check_password_hash(u.senha_hash, senha):
        return _serialize(u)
    return None
