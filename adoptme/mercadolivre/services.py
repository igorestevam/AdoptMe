"""Integracao com a API de produtos (catalogo) do Mercado Livre.

Requer uma aplicacao registrada no portal de desenvolvedores do Mercado Livre
(ML_CLIENT_ID / ML_CLIENT_SECRET). As chamadas exigem OAuth 2.0 (Bearer token).
As credenciais e o token ficam SEMPRE no backend.

Os produtos aparecem em dois lugares do site: um banner com poucos itens no topo da
pagina principal e a aba "Sugestoes de compras", com mais produtos por categoria.

A busca comum do catalogo traz muitos produtos sem nenhum anuncio a venda. Por isso
as categorias usam os mais vendidos de cada categoria do Pet Shop do Mercado Livre
(GET /highlights), que estao a venda e tem preco.
"""
import time
from concurrent.futures import ThreadPoolExecutor
from itertools import zip_longest

import requests
from flask import current_app

BASE_URL = "https://api.mercadolibre.com"
CACHE_SEGUNDOS = 30 * 60
PRODUTOS_POR_CATEGORIA = 8
CANDIDATOS_POR_CATEGORIA_ML = 8  # dos mais vendidos de cada categoria do ML, quantos consultamos
CONEXOES_SIMULTANEAS = 16

# (chave, nome exibido, categorias do Pet Shop do Mercado Livre: de caes e de gatos).
# Ids conferidos na API em 2026-11 (GET /categories/MLB1071 e filhas).
CATEGORIAS = [
    ("racao", "Ração", ("MLB1077", "MLB85870")),
    ("banho", "Banho e higiene", ("MLB434767", "MLB434791")),
    ("cama", "Camas e casinhas", ("MLB437585", "MLB434788")),
    ("brinquedos", "Brinquedos", ("MLB1074", "MLB85860")),
    ("petiscos", "Petiscos", ("MLB270533", "MLB377252")),
    ("coleiras", "Coleiras e guias", ("MLB1075",)),
    ("comedouros", "Comedouros e bebedouros", ("MLB32277", "MLB85881")),
    ("tapetes", "Tapetes higiênicos e areia", ("MLB434766", "MLB434790")),
]
CATEGORIAS_BANNER = ("racao", "banho", "cama", "brinquedos")

# domain_id dos produtos para pets (ex.: MLB-CAT_AND_DOG_FOODS, MLB-PET_COLLARS).
# Deixa de fora joias, brinquedos infantis, moldes de cozinha etc. que tambem aparecem na busca.
PALAVRAS_PET = {"PET", "PETS", "DOG", "DOGS", "CAT", "CATS"}

_token = {"valor": None, "expira": 0.0}
_cache: dict[tuple, tuple[float, object]] = {}


class MercadoLivreIndisponivel(Exception):
    pass


def limpar_cache():
    _token.update(valor=None, expira=0.0)
    _cache.clear()


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


def _requisitar(caminho: str, token: str, params: dict | None = None) -> requests.Response:
    """GET na API do ML sem depender do contexto do Flask (pode rodar em threads)."""
    return requests.get(f"{BASE_URL}{caminho}", params=params,
                        headers={"Authorization": f"Bearer {token}"}, timeout=10)


def _do_cache(chave):
    guardado = _cache.get(chave)
    return guardado[1] if guardado and time.time() < guardado[0] else None


def _cache_valido(chave) -> bool:
    guardado = _cache.get(chave)
    return bool(guardado) and time.time() < guardado[0]


def _guardar(chave, valor):
    _cache[chave] = (time.time() + CACHE_SEGUNDOS, valor)


def _em_paralelo(funcao, itens):
    with ThreadPoolExecutor(max_workers=CONEXOES_SIMULTANEAS) as pool:
        return list(pool.map(funcao, itens))


def _eh_pet(domain_id: str) -> bool:
    return bool(set(str(domain_id or "").replace("-", "_").split("_")) & PALAVRAS_PET)


def _resumo(p: dict, preco: float | None = None) -> dict:
    fotos = p.get("pictures") or [{}]
    return {
        "id": p.get("id"),
        "nome": p.get("name"),
        "foto": fotos[0].get("url"),
        # 'permalink' e a URL para onde o usuario e redirecionado
        "link": p.get("permalink") or f"https://www.mercadolivre.com.br/p/{p.get('id')}",
        "preco": preco,
    }


def _mais_vendidos(categorias: list[str]) -> dict[str, list[str]]:
    """Ids dos produtos mais vendidos de cada categoria do ML (GET /highlights)."""
    faltam = [c for c in dict.fromkeys(categorias) if not _cache_valido(("vendidos", c))]
    if faltam:
        token = _get_token()

        def buscar(categoria):
            resp = _requisitar(f"/highlights/MLB/category/{categoria}", token)
            if resp.status_code == 404:  # categoria sem ranking
                return categoria, []
            resp.raise_for_status()
            return categoria, [x["id"] for x in resp.json().get("content", []) if x.get("type") == "PRODUCT"]

        try:
            for categoria, ids in _em_paralelo(buscar, faltam):
                _guardar(("vendidos", categoria), ids)
        except requests.RequestException as e:
            raise MercadoLivreIndisponivel("Mercado Livre indisponivel no momento.") from e
    return {c: _do_cache(("vendidos", c)) for c in categorias}


def _carregar_produtos(ids: list[str]):
    """Busca nome, foto e preco dos produtos que ainda nao estao no cache.

    O preco e o menor entre os anuncios do produto (GET /products/{id}/items). Produto
    inativo, sem foto ou sem nenhum anuncio a venda (404) fica guardado como None.
    """
    faltam = [i for i in dict.fromkeys(ids) if not _cache_valido(("produto", i))]
    if not faltam:
        return
    token = _get_token()

    def carregar(pid):
        try:
            detalhe = _requisitar(f"/products/{pid}", token)
            if not detalhe.ok:
                return pid, None, detalhe.status_code == 404
            p = detalhe.json()
            if p.get("status") != "active" or not p.get("pictures"):
                return pid, None, True
            anuncios = _requisitar(f"/products/{pid}/items", token)
        except requests.RequestException:
            return pid, None, False
        if anuncios.status_code == 404:
            return pid, None, True
        if not anuncios.ok:
            # nao deu para saber o preco agora: mostra sem preco e tenta de novo depois
            return pid, _resumo(p), False
        precos = [a["price"] for a in anuncios.json().get("results", []) if a.get("price")]
        return pid, (_resumo(p, min(precos)) if precos else None), True

    for pid, produto, guardar in _em_paralelo(carregar, faltam):
        if guardar:
            _guardar(("produto", pid), produto)
        elif produto:
            _cache[("produto", pid)] = (time.time() + 60, produto)


def _produtos(ids: list[str]) -> list[dict]:
    """Os produtos que estao a venda, na ordem dos ids."""
    _carregar_produtos(ids)
    return [_do_cache(("produto", i)) for i in dict.fromkeys(ids) if _do_cache(("produto", i))]


def _intercalar(listas: list[list[dict]], limite: int) -> list[dict]:
    """Junta os resultados alternando caes e gatos, sem repetir produto."""
    juntos, vistos = [], set()
    for grupo in zip_longest(*listas):
        for p in grupo:
            if p and p["id"] not in vistos and len(juntos) < limite:
                vistos.add(p["id"])
                juntos.append(p)
    return juntos


def destaques() -> list[dict]:
    """Banner da pagina principal: um produto de cada categoria basica."""
    banner = [(nome, cats[0]) for chave, nome, cats in CATEGORIAS if chave in CATEGORIAS_BANNER]
    vendidos = _mais_vendidos([c for _, c in banner])
    candidatos = {c: vendidos[c][:4] for _, c in banner}
    _carregar_produtos([i for ids in candidatos.values() for i in ids])

    itens, usados = [], set()
    for nome, categoria in banner:
        produto = next((p for p in _produtos(candidatos[categoria]) if p["id"] not in usados), None)
        if produto:
            usados.add(produto["id"])
            itens.append({**produto, "categoria": nome})
    return itens


def sugestoes(categoria: str | None = None) -> list[dict] | None:
    """Aba de sugestoes de compras. Retorna None se a categoria nao existir."""
    escolhidas = [c for c in CATEGORIAS if categoria is None or c[0] == categoria]
    if not escolhidas:
        return None

    vendidos = _mais_vendidos([c for _, _, cats in escolhidas for c in cats])
    candidatos = {c: ids[:CANDIDATOS_POR_CATEGORIA_ML] for c, ids in vendidos.items()}
    _carregar_produtos([i for ids in candidatos.values() for i in ids])

    return [
        {"categoria": chave, "nome": nome,
         "produtos": _intercalar([_produtos(candidatos[c]) for c in cats], PRODUTOS_POR_CATEGORIA)}
        for chave, nome, cats in escolhidas
    ]


def _categorias_do_termo(q: str) -> list[str]:
    """Categorias de pet do ML que combinam com o termo (ex.: 'arranhador' -> Arranhadores).

    Palavras soltas como 'bolinha' nao sao reconhecidas como de pet; nesse caso tenta 'bolinha pet'.
    """
    for termo in (q, f"{q} pet"):
        resp = _requisitar("/sites/MLB/domain_discovery/search", _get_token(), {"q": termo, "limit": 4})
        resp.raise_for_status()
        categorias = [d["category_id"] for d in resp.json() if _eh_pet(d.get("domain_id"))][:2]
        if categorias:
            return categorias
    return []


def _busca_no_catalogo(q: str) -> list[str]:
    site = current_app.config.get("ML_SITE_ID", "MLB")
    resp = _requisitar("/products/search", _get_token(), {"site_id": site, "q": q, "limit": 50})
    resp.raise_for_status()
    return [p["id"] for p in resp.json().get("results", [])
            if p.get("status") == "active" and p.get("pictures") and _eh_pet(p.get("domain_id"))]


def buscar_produtos(q: str, limit: int = 10) -> list[dict]:
    """Busca livre da aba de sugestoes: mais vendidos da categoria do termo ou, se nao houver, a busca do catalogo."""
    chave = ("busca", q.strip().lower())
    ids = _do_cache(chave)
    if ids is None:
        try:
            categorias = _categorias_do_termo(q)
            vendidos = _mais_vendidos(categorias) if categorias else {}
            ids = [i for c in categorias for i in vendidos[c]]
            if not ids:
                ids = _busca_no_catalogo(q)
        except requests.RequestException as e:
            raise MercadoLivreIndisponivel("Mercado Livre indisponivel no momento.") from e
        _guardar(chave, ids)
    return _produtos(ids[:limit + 6])[:limit]


def obter_produto(product_id: str) -> dict | None:
    produtos = _produtos([product_id])
    return produtos[0] if produtos else None
