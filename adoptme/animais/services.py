import re

from sqlalchemy import or_

from adoptme.ext.db import db
from .fotos import URL_FOTOS, apagar_fotos
from .models import Animal, FotoAnimal, InteresseAdocao

ESPECIES = ("cachorro", "gato")
PORTES = ("pequeno", "medio", "grande")
SEXOS = ("macho", "femea")
SITUACOES = ("disponivel", "adotado")
MAX_FOTOS = 5
FOTO_ENVIADA = re.compile(re.escape(URL_FOTOS) + r"[0-9a-f]{32}\.(jpg|png|gif|webp)$")


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


def _responsavel(a: Animal) -> dict:
    u = a.anunciante.usuario
    return {
        "id": a.anunciante.id,
        "nome": u.nome,
        "tipo": a.anunciante.tipo,
        "telefone": u.telefone,
        "email": u.email,
        "cidade": u.endereco.cidade if u.endereco else None,
        "estado": u.endereco.estado if u.endereco else None,
    }


def listar_animais(especie: str | None = None, situacao: str | None = None, q: str | None = None,
                   porte: str | None = None, sexo: str | None = None) -> list[dict]:
    query = Animal.query
    if especie:
        query = query.filter_by(especie=especie)
    if situacao:
        query = query.filter_by(situacao=situacao)
    if porte:
        query = query.filter_by(porte=porte)
    if sexo:
        query = query.filter_by(sexo=sexo)
    if q:
        termo = f"%{q}%"
        query = query.filter(or_(Animal.nome.ilike(termo), Animal.descricao.ilike(termo)))
    return [_serialize(a) for a in query.order_by(Animal.id).all()]


def obter_animal(animal_id: int) -> dict | None:
    a = db.session.get(Animal, animal_id)
    if not a:
        return None
    return {**_serialize(a), "responsavel": _responsavel(a)}


def registrar_interesse(animal_id: int, usuario_id: int, mensagem: str | None = None) -> dict | None:
    animal = db.session.get(Animal, animal_id)
    if not animal:
        return None
    interesse = InteresseAdocao(animal=animal, usuario_id=usuario_id, mensagem=mensagem or None)
    db.session.add(interesse)
    db.session.commit()
    return {"id": interesse.id, "animal_id": animal.id, "mensagem": interesse.mensagem}


# Painel do anunciante

class SemPermissao(Exception):
    pass


def _do_anunciante(animal_id: int, anunciante_id: int) -> Animal | None:
    animal = db.session.get(Animal, animal_id)
    if animal and animal.anunciante_id != anunciante_id:
        raise SemPermissao("Este animal pertence a outro anunciante")
    return animal


def _validar(dados: dict) -> dict:
    nome = str(dados.get("nome") or "").strip()
    if not nome or len(nome) > 100:
        raise ValueError("Informe o nome (ate 100 caracteres)")
    if dados.get("especie") not in ESPECIES:
        raise ValueError("Especie invalida")
    if dados.get("porte") not in PORTES:
        raise ValueError("Porte invalido")
    if dados.get("sexo") not in SEXOS:
        raise ValueError("Sexo invalido")

    idade = dados.get("idade")
    if idade in ("", None):
        idade = None
    else:
        try:
            idade = int(idade)
        except (TypeError, ValueError):
            raise ValueError("Idade invalida")
        if not 0 <= idade <= 40:
            raise ValueError("Idade invalida")

    descricao = str(dados.get("descricao") or "").strip()
    if len(descricao) > 1000:
        raise ValueError("A descricao pode ter ate 1000 caracteres")

    fotos = [str(f).strip() for f in dados.get("fotos") or [] if str(f).strip()]
    if len(fotos) > MAX_FOTOS:
        raise ValueError(f"Envie no maximo {MAX_FOTOS} fotos")
    # fotos enviadas pelo site ou links que ja estavam cadastrados
    if any(not (FOTO_ENVIADA.match(f) or f.startswith(("http://", "https://"))) or len(f) > 255 for f in fotos):
        raise ValueError("Foto invalida")

    return {"nome": nome, "especie": dados["especie"], "porte": dados["porte"], "sexo": dados["sexo"],
            "idade": idade, "descricao": descricao or None, "fotos": fotos}


def meus_animais(anunciante_id: int) -> list[dict]:
    animais = Animal.query.filter_by(anunciante_id=anunciante_id).order_by(Animal.id.desc()).all()
    return [{**_serialize(a), "interesses": len(a.interesses)} for a in animais]


def cadastrar_animal(anunciante_id: int, dados: dict) -> dict:
    campos = _validar(dados)
    fotos = campos.pop("fotos")
    animal = Animal(anunciante_id=anunciante_id, **campos)
    animal.fotos = [FotoAnimal(url=f) for f in fotos]
    db.session.add(animal)
    db.session.commit()
    return _serialize(animal)


def editar_animal(animal_id: int, anunciante_id: int, dados: dict) -> dict | None:
    animal = _do_anunciante(animal_id, anunciante_id)
    if not animal:
        return None
    campos = _validar(dados)
    fotos = campos.pop("fotos")
    retiradas = [f.url for f in animal.fotos if f.url not in fotos]
    for campo, valor in campos.items():
        setattr(animal, campo, valor)
    animal.fotos = [FotoAnimal(url=f) for f in fotos]
    db.session.commit()
    apagar_fotos(retiradas)
    return _serialize(animal)


def alterar_situacao(animal_id: int, anunciante_id: int, situacao: str) -> dict | None:
    if situacao not in SITUACOES:
        raise ValueError("Situacao invalida")
    animal = _do_anunciante(animal_id, anunciante_id)
    if not animal:
        return None
    animal.situacao = situacao
    db.session.commit()
    return _serialize(animal)


def remover_animal(animal_id: int, anunciante_id: int) -> bool:
    animal = _do_anunciante(animal_id, anunciante_id)
    if not animal:
        return False
    urls = [f.url for f in animal.fotos]
    db.session.delete(animal)
    db.session.commit()
    apagar_fotos(urls)
    return True


def interesses_do_animal(animal_id: int, anunciante_id: int) -> list[dict] | None:
    animal = _do_anunciante(animal_id, anunciante_id)
    if not animal:
        return None
    interesses = sorted(animal.interesses, key=lambda i: i.data_hora, reverse=True)
    return [{
        "id": i.id,
        "data_hora": i.data_hora.isoformat(),
        "mensagem": i.mensagem,
        "nome": i.usuario.nome,
        "email": i.usuario.email,
        "telefone": i.usuario.telefone,
    } for i in interesses]
