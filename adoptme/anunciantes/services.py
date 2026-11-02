from adoptme.ext.db import db
from .models import Anunciante


def _serialize(a: Anunciante) -> dict:
    return {
        "id": a.id,
        "tipo": a.tipo,
        "descricao": a.descricao,
        "usuario_id": a.usuario_id,
    }


def listar_anunciantes() -> list[dict]:
    return [_serialize(a) for a in Anunciante.query.all()]


def obter_anunciante(anunciante_id: int) -> dict | None:
    a = db.session.get(Anunciante, anunciante_id)
    return _serialize(a) if a else None
