"""Integracao com a API de produtos (catalogo) do Mercado Livre.

Requer uma aplicacao registrada no portal de desenvolvedores do Mercado Livre
(ML_CLIENT_ID / ML_CLIENT_SECRET). As chamadas exigem OAuth 2.0 (Bearer token).
As credenciais e o token ficam SEMPRE no backend.

Os produtos aparecem em dois lugares do site: um banner com poucos itens no topo da
pagina principal e a aba "Sugestoes de compras", com mais produtos por categoria.
"""
import time

import requests
from flask import current_app

BASE_URL = "https://api.mercadolibre.com"
CACHE_SEGUNDOS = 30 * 60
PRODUTOS_POR_CATEGORIA = 8

# (chave, nome exibido, termo buscado no Mercado Livre)
CATEGORIAS = [
    ("racao", "Ração", "racao pet"),
    ("banho", "Banho e higiene", "shampoo pet"),
    ("cama", "Camas e casinhas", "cama pet"),
    ("brinquedos", "Brinquedos", "brinquedo pet"),
    ("petiscos", "Petiscos", "petisco pet"),
    ("coleiras", "Coleiras e guias", "coleira pet"),
    ("comedouros", "Comedouros e bebedouros", "comedouro pet"),
    ("tapetes", "Tapetes higiênicos e areia", "tapete higienico pet"),
]
CATEGORIAS_BANNER = ("racao", "banho", "cama", "brinquedos")

_token = {"valor": None, "expira": 0.0}
_buscas: dict[tuple, tuple[float, list[dict]]] = {}


class MercadoLivreIndisponivel(Exception):
    pass


def limpar_cache():
    _token.update(valor=None, expira=0.0)
    _buscas.clear()


def _get_token() -> str:
    if _token["valor"] and time.time() < _token["expira"]:
        return _token["valor"]

    cid = current_app.config.get("ML_CLIENT_ID")
    secret = current_app.config.get("ML_CLIENT_SECRET")
    if not cid or not secret:
        raise MercadoLivreIndisponivel("Configure ML_CLIENT_ID e ML_CLIENT_SECRET.")
    try:
        resp = requests.post(
            f"{BASE_URL}/oauth/token",
            data={"grant_type": "client_credentials", "client_id": cid, "client_secret": secret},
            timeout=10,
        )
        resp.raise_for_status()
    except requests.RequestException as e:
        raise MercadoLivreIndisponivel("Nao foi possivel autenticar no Mercado Livre.") from e

    dados = resp.json()
    # renova um minuto antes de expirar
    _token.update(valor=dados["access_token"], expira=time.time() + dados.get("expires_in", 21600) - 60)
    return _token["valor"]


def _get(caminho: str, params: dict | None = None) -> dict:
    try:
        resp = requests.get(
            f"{BASE_URL}{caminho}",
            params=params,
            headers={"Authorization": f"Bearer {_get_token()}"},
            timeout=10,
        )
        resp.raise_for_status()
    except requests.RequestException as e:
        raise MercadoLivreIndisponivel("Mercado Livre indisponivel no momento.") from e
    return resp.json()


def _resumo(p: dict) -> dict:
    fotos = p.get("pictures") or [{}]
    return {
        "id": p.get("id"),
        "nome": p.get("name"),
        "foto": fotos[0].get("url"),
        # 'permalink' e a URL para onde o usuario e redirecionado
        "link": p.get("permalink") or f"https://www.mercadolivre.com.br/p/{p.get('id')}",
    }


def buscar_produtos(q: str, limit: int = 10, offset: int = 0) -> list[dict]:
    chave = (q, limit, offset)
    guardado = _buscas.get(chave)
    if guardado and time.time() < guardado[0]:
        return guardado[1]

    site = current_app.config.get("ML_SITE_ID", "MLB")
    dados = _get("/products/search", {"site_id": site, "q": q, "limit": limit, "offset": offset})
    produtos = [_resumo(p) for p in dados.get("results", [])]
    _buscas[chave] = (time.time() + CACHE_SEGUNDOS, produtos)
    return produtos


def obter_produto(product_id: str) -> dict:
    return _resumo(_get(f"/products/{product_id}"))


def destaques() -> list[dict]:
    """Banner da pagina principal: um produto de cada categoria basica."""
    itens = []
    for chave, nome, termo in CATEGORIAS:
        if chave in CATEGORIAS_BANNER:
            produtos = buscar_produtos(termo, limit=1)
            if produtos:
                itens.append({**produtos[0], "categoria": nome})
    return itens


def sugestoes(categoria: str | None = None) -> list[dict] | None:
    """Aba de sugestoes de compras. Retorna None se a categoria nao existir."""
    escolhidas = [c for c in CATEGORIAS if categoria is None or c[0] == categoria]
    if not escolhidas:
        return None
    return [
        {"categoria": chave, "nome": nome, "produtos": buscar_produtos(termo, limit=PRODUTOS_POR_CATEGORIA)}
        for chave, nome, termo in escolhidas
    ]
