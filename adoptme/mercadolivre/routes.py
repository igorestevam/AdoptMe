from flask import Blueprint, jsonify, request, abort

from . import services

mercadolivre_bp = Blueprint("mercadolivre", __name__)


@mercadolivre_bp.errorhandler(services.MercadoLivreIndisponivel)
def ml_indisponivel(e):
    return jsonify({"erro": str(e)}), 503


@mercadolivre_bp.get("/destaques")
def destaques():
    """Poucos produtos para o banner do topo da pagina principal."""
    return jsonify(services.destaques())


@mercadolivre_bp.get("/sugestoes")
def sugestoes():
    """Aba de sugestoes de compras: produtos agrupados por categoria."""
    grupos = services.sugestoes(request.args.get("categoria"))
    if grupos is None:
        abort(404, description="Categoria nao encontrada")
    return jsonify(grupos)


@mercadolivre_bp.get("/produtos")
def buscar_produtos():
    q = request.args.get("q", "").strip()
    if not q:
        abort(400, description="Informe o termo de busca (q)")
    limit = request.args.get("limit", 10, type=int)
    return jsonify(services.buscar_produtos(q, limit=min(limit, 24)))


@mercadolivre_bp.get("/produtos/<product_id>")
def obter_produto(product_id):
    produto = services.obter_produto(product_id)
    if not produto:
        abort(404, description="Produto nao encontrado ou sem anuncio a venda")
    return jsonify(produto)
