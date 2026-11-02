"""Integracao com a API de produtos do Mercado Livre.

Requer uma aplicacao registrada no portal de desenvolvedores do Mercado Livre
(ML_CLIENT_ID / ML_CLIENT_SECRET). As chamadas exigem OAuth 2.0 (Bearer token).
As credenciais e o token ficam SEMPRE no backend.
"""
import requests
from flask import current_app

BASE_URL = "https://api.mercadolibre.com"


def _get_token() -> str | None:
    cid = current_app.config.get("ML_CLIENT_ID")
    secret = current_app.config.get("ML_CLIENT_SECRET")
    if not cid or not secret:
        return None
    resp = requests.post(
        f"{BASE_URL}/oauth/token",
        data={
            "grant_type": "client_credentials",
            "client_id": cid,
            "client_secret": secret,
        },
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json().get("access_token")
    # TODO: cachear/renovar o token em vez de gerar a cada chamada


def buscar_produtos(q: str, limit: int = 10, offset: int = 0) -> dict:
    token = _get_token()
    if not token:
        return {"erro": "Configure ML_CLIENT_ID e ML_CLIENT_SECRET."}
    site = current_app.config.get("ML_SITE_ID", "MLB")
    resp = requests.get(
        f"{BASE_URL}/products/search",
        params={"site_id": site, "q": q, "limit": limit, "offset": offset},
        headers={"Authorization": f"Bearer {token}"},
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()


def obter_produto(product_id: str) -> dict:
    token = _get_token()
    if not token:
        return {"erro": "Configure ML_CLIENT_ID e ML_CLIENT_SECRET."}
    resp = requests.get(
        f"{BASE_URL}/products/{product_id}",
        headers={"Authorization": f"Bearer {token}"},
        timeout=10,
    )
    resp.raise_for_status()
    # o campo 'permalink' e a URL para redirecionar o usuario ao Mercado Livre
    return resp.json()
