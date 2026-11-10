from flask import Blueprint, jsonify, request, abort

from . import services

auth_bp = Blueprint("auth", __name__)


@auth_bp.post("/register")
def register():
    dados = request.get_json(silent=True) or {}
    try:
        usuario = services.criar_usuario(dados)
    except ValueError as e:
        abort(400, description=str(e))
    except services.JaCadastrado as e:
        abort(409, description=str(e))
    services.entrar(usuario)
    return jsonify(usuario), 201


@auth_bp.post("/login")
def login():
    dados = request.get_json(silent=True) or {}
    usuario = services.autenticar(dados.get("email", ""), dados.get("senha", ""))
    if not usuario:
        abort(401, description="Email ou senha invalidos")
    services.entrar(usuario)
    return jsonify(usuario)


@auth_bp.post("/logout")
def logout():
    services.sair()
    return "", 204


@auth_bp.get("/me")
def me():
    usuario = services.usuario_logado()
    if not usuario:
        abort(401, description="Nao autenticado")
    return jsonify(services.obter_usuario(usuario.id))
