from adoptme.ext.db import db
from .models import Animal


def _serialize(a: Animal) -> dict:
    return {
        "id": a.id,
        "nome": a.nome,
        "especie": a.especie,
        "idade": a.idade,
        "porte": a.porte,
        "sexo": a.sexo,
        "descricao": a.descricao,
        "situacao": a.situacao,
        "anunciante_id": a.anunciante_id,
        "fotos": [f.url for f in a.fotos],
    }


def listar_animais(especie: str | None = None, situacao: str | None = None) -> list[dict]:
    query = Animal.query
    if especie:
        query = query.filter_by(especie=especie)
    if situacao:
        query = query.filter_by(situacao=situacao)
    return [_serialize(a) for a in query.all()]


def obter_animal(animal_id: int) -> dict | None:
    a = db.session.get(Animal, animal_id)
    return _serialize(a) if a else None
