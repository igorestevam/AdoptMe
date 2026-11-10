from adoptme.ext.db import db
from .models import Anunciante


def _serialize(a: Anunciante) -> dict:
    u = a.usuario
    return {
        "id": a.id,
        "tipo": a.tipo,
        "descricao": a.descricao,
        "usuario_id": a.usuario_id,
        "nome": u.nome,
        "telefone": u.telefone,
        "email": u.email,
        "cidade": u.endereco.cidade if u.endereco else None,
        "estado": u.endereco.estado if u.endereco else None,
    }


def listar_anunciantes() -> list[dict]:
    return [_serialize(a) for a in Anunciante.query.all()]


def obter_anunciante(anunciante_id: int) -> dict | None:
    a = db.session.get(Anunciante, anunciante_id)
    if not a:
        return None
    animais = [{"id": x.id, "nome": x.nome, "especie": x.especie, "situacao": x.situacao,
                "foto": x.fotos[0].url if x.fotos else None} for x in a.animais]
    return {**_serialize(a), "animais": animais}
