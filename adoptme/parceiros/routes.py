from flask import Blueprint, jsonify, request, redirect, abort

from . import services

parceiros_bp = Blueprint("parceiros", __name__)


@parceiros_bp.get("/anuncios")
def listar_anuncios():
    return jsonify(services.listar_anuncios())


@parceiros_bp.get("/anuncios/<int:anuncio_id>/clique")
def registrar_clique(anuncio_id):
    """Registra o clique (base da cobranca CPC) e redireciona para o destino."""
    destino = services.registrar_clique(anuncio_id, sessao=request.args.get("sessao"))
    if not destino:
        abort(404, description="Anuncio nao encontrado")
    return redirect(destino)
