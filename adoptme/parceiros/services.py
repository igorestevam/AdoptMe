from datetime import datetime, timedelta, timezone

from sqlalchemy import func

from adoptme.ext.db import db
from .models import EmpresaParceira, Anuncio, CliqueAnuncio

# cliques repetidos da mesma sessao no mesmo anuncio, dentro deste intervalo, nao contam
INTERVALO_CLIQUE_REPETIDO = timedelta(minutes=30)


def _agora() -> datetime:
    # o SQLite grava CURRENT_TIMESTAMP em UTC, sem fuso
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _serialize_anuncio(a: Anuncio) -> dict:
    return {
        "id": a.id,
        "conteudo": a.conteudo,
        "empresa": a.empresa.nome,
        "empresa_parceira_id": a.empresa_parceira_id,
    }


def listar_anuncios() -> list[dict]:
    return [_serialize_anuncio(a) for a in Anuncio.query.order_by(Anuncio.id).all()]


def registrar_clique(anuncio_id: int, sessao: str | None = None) -> str | None:
    """Registra um clique e devolve o link de destino do anuncio (ou None).

    Um novo clique da mesma sessao no mesmo anuncio so conta depois do intervalo,
    para a empresa nao pagar por cliques repetidos.
    """
    anuncio = db.session.get(Anuncio, anuncio_id)
    if not anuncio:
        return None
    repetido = sessao and CliqueAnuncio.query.filter(
        CliqueAnuncio.anuncio_id == anuncio.id,
        CliqueAnuncio.sessao == sessao,
        CliqueAnuncio.data_hora >= _agora() - INTERVALO_CLIQUE_REPETIDO,
    ).first()
    if not repetido:
        db.session.add(CliqueAnuncio(anuncio_id=anuncio.id, sessao=sessao))
        db.session.commit()
    return anuncio.link_destino


# Usadas pelos comandos de terminal (cadastro feito pela equipe da plataforma)

def cadastrar_empresa(nome: str, telefone: str, email: str | None = None) -> EmpresaParceira:
    nome, telefone = nome.strip(), telefone.strip()
    if not nome or not telefone:
        raise ValueError("Nome e telefone sao obrigatorios")
    empresa = EmpresaParceira(nome=nome, telefone=telefone, email=(email or "").strip() or None)
    db.session.add(empresa)
    db.session.commit()
    return empresa


def cadastrar_anuncio(empresa_id: int, conteudo: str, link_destino: str) -> Anuncio:
    if not db.session.get(EmpresaParceira, empresa_id):
        raise ValueError(f"Empresa {empresa_id} nao encontrada")
    conteudo, link_destino = conteudo.strip(), link_destino.strip()
    if not conteudo or len(conteudo) > 500:
        raise ValueError("O texto do anuncio deve ter entre 1 e 500 caracteres")
    if not link_destino.startswith(("http://", "https://")) or len(link_destino) > 255:
        raise ValueError("O link deve comecar com http:// ou https:// e ter ate 255 caracteres")
    anuncio = Anuncio(empresa_parceira_id=empresa_id, conteudo=conteudo, link_destino=link_destino)
    db.session.add(anuncio)
    db.session.commit()
    return anuncio


def relatorio_cliques(inicio: datetime | None = None, fim: datetime | None = None) -> list[dict]:
    """Cliques por anuncio no periodo (fim exclusivo), base da cobranca de cada empresa."""
    cliques = func.count(CliqueAnuncio.id)
    consulta = (db.session.query(EmpresaParceira, Anuncio, cliques)
                .join(Anuncio, Anuncio.empresa_parceira_id == EmpresaParceira.id)
                .outerjoin(CliqueAnuncio, (CliqueAnuncio.anuncio_id == Anuncio.id)
                           & (CliqueAnuncio.data_hora >= (inicio or datetime.min))
                           & (CliqueAnuncio.data_hora < (fim or datetime.max)))
                .group_by(EmpresaParceira.id, Anuncio.id)
                .order_by(EmpresaParceira.nome, Anuncio.id))
    return [{"empresa": e.nome, "anuncio_id": a.id, "conteudo": a.conteudo, "cliques": n}
            for e, a, n in consulta.all()]
