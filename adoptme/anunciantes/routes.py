from flask import Blueprint, jsonify, abort

from . import services

anunciantes_bp = Blueprint("anunciantes", __name__)


@anunciantes_bp.get("")
def listar():
    return jsonify(services.listar_anunciantes())


@anunciantes_bp.get("/<int:anunciante_id>")
def obter(anunciante_id):
    anunciante = services.obter_anunciante(anunciante_id)
    if not anunciante:
        abort(404, description="Anunciante nao encontrado")
    return jsonify(anunciante)
