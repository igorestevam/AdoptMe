from datetime import date

from flask import session
from werkzeug.security import generate_password_hash, check_password_hash

from adoptme.ext.db import db
from adoptme.anunciantes.models import Anunciante
from .models import Usuario, Endereco
from .validacao import UFS, so_digitos, formatar_documento, formatar_cep, email_valido

CAMPOS_USUARIO = ("nome", "cpf_cnpj", "telefone", "email", "senha")
CAMPOS_ENDERECO = ("estado", "cidade", "bairro", "rua", "numero", "cep")
TIPOS_ANUNCIANTE = ("organizacao", "pessoa_fisica")


def _serialize(u: Usuario) -> dict:
    return {
        "id": u.id,
        "nome": u.nome,
        "cpf_cnpj": u.cpf_cnpj,
        "telefone": u.telefone,
        "email": u.email,
        "anunciante_id": u.anunciante.id if u.anunciante else None,
    }


def obter_usuario(usuario_id: int) -> dict | None:
    u = db.session.get(Usuario, usuario_id)
    return _serialize(u) if u else None


class JaCadastrado(Exception):
    pass


def criar_usuario(dados: dict) -> dict:
    faltando = [c for c in CAMPOS_USUARIO if not str(dados.get(c) or "").strip()]
    if faltando:
        raise ValueError(f"Campos obrigatorios: {', '.join(faltando)}")

    email = dados["email"].strip().lower()
    if not email_valido(email):
        raise ValueError("Email invalido")
    documento = formatar_documento(dados["cpf_cnpj"])
    if not documento:
        raise ValueError("CPF ou CNPJ invalido")

    endereco = dados.get("endereco")
    if not isinstance(endereco, dict):
        endereco = {}
    faltando = [c for c in CAMPOS_ENDERECO if not str(endereco.get(c) or "").strip()]
    if faltando:
        raise ValueError(f"Endereco incompleto: {', '.join(faltando)}")
    cep = formatar_cep(endereco["cep"])
    if not cep:
        raise ValueError("CEP invalido")
    estado = endereco["estado"].strip().upper()
    if estado not in UFS:
        raise ValueError("UF invalida")
    try:
        nascimento = date.fromisoformat(dados["data_nascimento"]) if dados.get("data_nascimento") else None
    except (TypeError, ValueError):
        raise ValueError("Data de nascimento invalida")

    # quem vai divulgar animais manda tambem o perfil de anunciante
    anunciante = dados.get("anunciante")
    if anunciante is not None:
        if not isinstance(anunciante, dict) or anunciante.get("tipo") not in TIPOS_ANUNCIANTE:
            raise ValueError("Tipo de anunciante invalido")
        if anunciante["tipo"] == "organizacao" and len(so_digitos(documento)) != 14:
            raise ValueError("Organizacoes devem informar um CNPJ")
        if anunciante["tipo"] == "pessoa_fisica" and len(so_digitos(documento)) != 11:
            raise ValueError("Pessoas fisicas devem informar um CPF")

    if Usuario.query.filter_by(email=email).first():
        raise JaCadastrado("Ja existe um usuario com este email")
    if Usuario.query.filter_by(cpf_cnpj=documento).first():
        raise JaCadastrado("Ja existe um usuario com este CPF/CNPJ")

    u = Usuario(
        nome=dados["nome"].strip(),
        cpf_cnpj=documento,
        telefone=dados["telefone"].strip(),
        data_nascimento=nascimento,
        email=email,
        senha_hash=generate_password_hash(dados["senha"]),
    )
    u.endereco = Endereco(
        estado=estado,
        cidade=endereco["cidade"].strip(),
        bairro=endereco["bairro"].strip(),
        rua=endereco["rua"].strip(),
        numero=str(endereco["numero"]).strip(),
        cep=cep,
        complemento=(endereco.get("complemento") or "").strip() or None,
    )
    if anunciante:
        u.anunciante = Anunciante(tipo=anunciante["tipo"], descricao=anunciante.get("descricao") or None)
    db.session.add(u)
    db.session.commit()
    return _serialize(u)


def autenticar(email: str, senha: str) -> dict | None:
    u = Usuario.query.filter_by(email=(email or "").strip().lower()).first()
    if u and check_password_hash(u.senha_hash, senha):
        return _serialize(u)
    return None


def entrar(usuario: dict):
    session.clear()
    session["usuario_id"] = usuario["id"]


def sair():
    session.clear()


def usuario_logado() -> Usuario | None:
    usuario_id = session.get("usuario_id")
    return db.session.get(Usuario, usuario_id) if usuario_id else None
