from adoptme.ext.db import db
from .models import Anuncio, CliqueAnuncio


def _serialize_anuncio(a: Anuncio) -> dict:
    return {
        "id": a.id,
        "conteudo": a.conteudo,
        "link_destino": a.link_destino,
        "empresa_parceira_id": a.empresa_parceira_id,
    }


def listar_anuncios() -> list[dict]:
    return [_serialize_anuncio(a) for a in Anuncio.query.all()]


def registrar_clique(anuncio_id: int, sessao: str | None = None) -> str | None:
    """Registra um clique e devolve o link de destino do anuncio (ou None)."""
    anuncio = db.session.get(Anuncio, anuncio_id)
    if not anuncio:
        return None
    # TODO: deduplicar cliques por sessao/intervalo para evitar contagem fraudulenta
    db.session.add(CliqueAnuncio(anuncio_id=anuncio.id, sessao=sessao))
    db.session.commit()
    return anuncio.link_destino
