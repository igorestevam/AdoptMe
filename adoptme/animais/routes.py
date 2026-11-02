from flask import Blueprint, jsonify, request, abort

from . import services

animais_bp = Blueprint("animais", __name__)


@animais_bp.get("")
def listar():
    especie = request.args.get("especie")
    situacao = request.args.get("situacao")
    return jsonify(services.listar_animais(especie=especie, situacao=situacao))


@animais_bp.get("/<int:animal_id>")
def obter(animal_id):
    animal = services.obter_animal(animal_id)
    if not animal:
        abort(404, description="Animal nao encontrado")
    return jsonify(animal)


# TODO: rotas protegidas do anunciante:
#   POST   ""                      -> cadastrar animal
#   PUT    "/<int:animal_id>"      -> editar
#   DELETE "/<int:animal_id>"      -> remover
#   PATCH  "/<int:animal_id>/situacao" -> alterar situacao (disponivel/adotado)
