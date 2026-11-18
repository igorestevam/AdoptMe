import logging
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

logger = logging.getLogger(__name__)


def _mascarar(email: str) -> str:
    """joao@teste.com -> j***@teste.com (o log nao guarda o email inteiro)."""
    nome, _, dominio = (email or "").partition("@")
    return f"{nome[:1]}***@{dominio}"


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


def _ler_endereco(endereco) -> dict:
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
    return {
        "estado": estado,
        "cidade": endereco["cidade"].strip(),
        "bairro": endereco["bairro"].strip(),
        "rua": endereco["rua"].strip(),
        "numero": str(endereco["numero"]).strip(),
        "cep": cep,
        "complemento": (endereco.get("complemento") or "").strip() or None,
    }


def _ler_nascimento(valor) -> date | None:
    try:
        return date.fromisoformat(valor) if valor else None
    except (TypeError, ValueError):
        raise ValueError("Data de nascimento invalida")


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

    endereco = _ler_endereco(dados.get("endereco"))
    nascimento = _ler_nascimento(dados.get("data_nascimento"))

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
    u.endereco = Endereco(**endereco)
    if anunciante:
        u.anunciante = Anunciante(tipo=anunciante["tipo"], descricao=anunciante.get("descricao") or None)
    db.session.add(u)
    db.session.commit()
    logger.info("Usuario %s cadastrado (anunciante: %s)", u.id, u.anunciante.tipo if u.anunciante else "nao")
    return _serialize(u)


def obter_conta(u: Usuario) -> dict:
    """Dados completos da conta, para a tela "Minha conta"."""
    e = u.endereco
    return {
        **_serialize(u),
        "data_nascimento": u.data_nascimento.isoformat() if u.data_nascimento else None,
        "endereco": {c: getattr(e, c) for c in CAMPOS_ENDERECO + ("complemento",)} if e else None,
        "anunciante": {"tipo": u.anunciante.tipo, "descricao": u.anunciante.descricao} if u.anunciante else None,
    }


def atualizar_conta(u: Usuario, dados: dict) -> dict:
    # email e CPF/CNPJ identificam a conta e nao mudam por aqui
    faltando = [c for c in ("nome", "telefone") if not str(dados.get(c) or "").strip()]
    if faltando:
        raise ValueError(f"Campos obrigatorios: {', '.join(faltando)}")
    endereco = _ler_endereco(dados.get("endereco"))
    nascimento = _ler_nascimento(dados.get("data_nascimento"))

    anunciante = dados.get("anunciante")
    if anunciante is not None and not isinstance(anunciante, dict):
        raise ValueError("Dados de anunciante invalidos")

    u.nome = dados["nome"].strip()
    u.telefone = dados["telefone"].strip()
    u.data_nascimento = nascimento
    if u.endereco:
        for campo, valor in endereco.items():
            setattr(u.endereco, campo, valor)
    else:
        u.endereco = Endereco(**endereco)

    if anunciante is not None:
        descricao = (anunciante.get("descricao") or "").strip()[:500] or None
        if u.anunciante:
            u.anunciante.descricao = descricao
        else:
            # quem se cadastrou so para adotar pode passar a divulgar animais;
            # o tipo sai do documento ja cadastrado
            tipo = "organizacao" if len(so_digitos(u.cpf_cnpj)) == 14 else "pessoa_fisica"
            u.anunciante = Anunciante(tipo=tipo, descricao=descricao)
            logger.info("Usuario %s passou a ser anunciante (%s)", u.id, tipo)

    db.session.commit()
    logger.info("Usuario %s atualizou os dados da conta", u.id)
    return obter_conta(u)


def trocar_senha(u: Usuario, atual: str, nova: str):
    if not check_password_hash(u.senha_hash, atual or ""):
        raise ValueError("Senha atual incorreta")
    if len(nova or "") < 6:
        raise ValueError("A nova senha deve ter pelo menos 6 caracteres")
    u.senha_hash = generate_password_hash(nova)
    db.session.commit()
    logger.info("Usuario %s trocou a senha", u.id)


def autenticar(email: str, senha: str) -> dict | None:
    u = Usuario.query.filter_by(email=(email or "").strip().lower()).first()
    if u and check_password_hash(u.senha_hash, senha):
        logger.info("Usuario %s entrou", u.id)
        return _serialize(u)
    logger.warning("Login recusado para %s", _mascarar(email))
    return None


def entrar(usuario: dict):
    session.clear()
    session["usuario_id"] = usuario["id"]


def sair():
    session.clear()


def usuario_logado() -> Usuario | None:
    usuario_id = session.get("usuario_id")
    return db.session.get(Usuario, usuario_id) if usuario_id else None
