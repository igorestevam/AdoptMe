from flask import Blueprint, jsonify, request, abort

from . import services

auth_bp = Blueprint("auth", __name__)


@auth_bp.get("/usuarios")
def listar_usuarios():
    return jsonify(services.listar_usuarios())


@auth_bp.post("/register")
def register():
    dados = request.get_json() or {}
    # TODO: validacao completa dos campos obrigatorios
    usuario = services.criar_usuario(dados)
    return jsonify(usuario), 201


@auth_bp.post("/login")
def login():
    dados = request.get_json() or {}
    usuario = services.autenticar(dados.get("email", ""), dados.get("senha", ""))
    if not usuario:
        abort(401, description="Credenciais invalidas")
    # TODO: emitir sessao / JWT
    return jsonify(usuario)
