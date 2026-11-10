from flask import Blueprint, jsonify, request, abort, send_from_directory
from werkzeug.exceptions import RequestEntityTooLarge

from adoptme.auth.services import usuario_logado
from . import fotos, services

animais_bp = Blueprint("animais", __name__)


@animais_bp.errorhandler(services.SemPermissao)
def sem_permissao(e):
    return jsonify({"erro": str(e)}), 403


def _anunciante_id() -> int:
    """Id do anunciante logado; interrompe com 401/403 se nao houver."""
    usuario = usuario_logado()
    if not usuario:
        abort(401, description="Entre na sua conta para continuar")
    if not usuario.anunciante:
        abort(403, description="Apenas anunciantes podem gerenciar animais")
    return usuario.anunciante.id


@animais_bp.get("")
def listar():
    a = request.args
    return jsonify(services.listar_animais(
        especie=a.get("especie"), situacao=a.get("situacao"), q=a.get("q", "").strip(),
        porte=a.get("porte"), sexo=a.get("sexo"),
    ))


@animais_bp.get("/<int:animal_id>")
def obter(animal_id):
    animal = services.obter_animal(animal_id)
    if not animal:
        abort(404, description="Animal nao encontrado")
    return jsonify(animal)


@animais_bp.post("/<int:animal_id>/interesses")
def manifestar_interesse(animal_id):
    usuario = usuario_logado()
    if not usuario:
        abort(401, description="Entre na sua conta para manifestar interesse")
    mensagem = str((request.get_json(silent=True) or {}).get("mensagem") or "")[:500]
    interesse = services.registrar_interesse(animal_id, usuario.id, mensagem.strip())
    if not interesse:
        abort(404, description="Animal nao encontrado")
    return jsonify(interesse), 201


# Rotas do painel do anunciante (exigem login com perfil de anunciante)

@animais_bp.get("/meus")
def meus():
    return jsonify(services.meus_animais(_anunciante_id()))


@animais_bp.post("")
def cadastrar():
    anunciante_id = _anunciante_id()
    try:
        animal = services.cadastrar_animal(anunciante_id, request.get_json(silent=True) or {})
    except ValueError as e:
        abort(400, description=str(e))
    return jsonify(animal), 201


@animais_bp.put("/<int:animal_id>")
def editar(animal_id):
    anunciante_id = _anunciante_id()
    try:
        animal = services.editar_animal(animal_id, anunciante_id, request.get_json(silent=True) or {})
    except ValueError as e:
        abort(400, description=str(e))
    if not animal:
        abort(404, description="Animal nao encontrado")
    return jsonify(animal)


@animais_bp.patch("/<int:animal_id>/situacao")
def alterar_situacao(animal_id):
    anunciante_id = _anunciante_id()
    situacao = (request.get_json(silent=True) or {}).get("situacao")
    try:
        animal = services.alterar_situacao(animal_id, anunciante_id, situacao)
    except ValueError as e:
        abort(400, description=str(e))
    if not animal:
        abort(404, description="Animal nao encontrado")
    return jsonify(animal)


@animais_bp.delete("/<int:animal_id>")
def remover(animal_id):
    if not services.remover_animal(animal_id, _anunciante_id()):
        abort(404, description="Animal nao encontrado")
    return "", 204


@animais_bp.post("/fotos")
def enviar_foto():
    _anunciante_id()
    try:
        arquivo = request.files.get("foto")
    except RequestEntityTooLarge:
        abort(413, description="A foto pode ter no maximo 5 MB")
    if not arquivo or not arquivo.filename:
        abort(400, description="Escolha uma foto")
    try:
        url = fotos.salvar_foto(arquivo)
    except ValueError as e:
        abort(400, description=str(e))
    return jsonify({"url": url}), 201


@animais_bp.get("/fotos/<nome>")
def ver_foto(nome):
    return send_from_directory(fotos.pasta(), nome, max_age=60 * 60 * 24 * 30)


@animais_bp.get("/<int:animal_id>/interesses")
def interesses(animal_id):
    lista = services.interesses_do_animal(animal_id, _anunciante_id())
    if lista is None:
        abort(404, description="Animal nao encontrado")
    return jsonify(lista)
