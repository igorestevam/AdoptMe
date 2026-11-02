from flask import Blueprint, jsonify, request

from . import services

mercadolivre_bp = Blueprint("mercadolivre", __name__)


@mercadolivre_bp.get("/produtos")
def buscar_produtos():
    q = request.args.get("q", "")
    limit = request.args.get("limit", 10, type=int)
    return jsonify(services.buscar_produtos(q, limit=limit))


@mercadolivre_bp.get("/produtos/<product_id>")
def obter_produto(product_id):
    return jsonify(services.obter_produto(product_id))
