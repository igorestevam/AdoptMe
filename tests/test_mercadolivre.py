"""Testes da integracao com o Mercado Livre, com a API simulada (sem internet)."""
import pytest
import requests

from adoptme.mercadolivre import services


class RespostaFalsa:
    def __init__(self, dados, status=200):
        self.dados = dados
        self.status_code = status
        self.ok = status < 400

    def json(self):
        return self.dados

    def raise_for_status(self):
        if not self.ok:
            raise requests.HTTPError(f"status {self.status_code}")


def api_falsa(url, params=None, **kwargs):
    """Imita as rotas usadas. Em cada categoria do ML, o produto 1 nao tem anuncio
    a venda (404 nos anuncios) e o produto 2 esta inativo."""
    caminho = url.removeprefix(services.BASE_URL)
    if caminho.startswith("/highlights/MLB/category/"):
        categoria = caminho.rsplit("/", 1)[1]
        conteudo = [{"id": f"{categoria}-{i}", "type": "PRODUCT"} for i in range(10)]
        return RespostaFalsa({"content": conteudo + [{"id": "MLB999", "type": "ITEM"}]})
    if caminho == "/sites/MLB/domain_discovery/search":
        return RespostaFalsa([
            {"category_id": "MLB85861", "domain_id": "MLB-CAT_SCRATCHERS"},
            {"category_id": "MLB3843", "domain_id": "MLB-SPEAKERS"},
        ] if params["q"] == "arranhador" else [{"category_id": "MLB1074", "domain_id": "MLB-DOG_TOYS"}]
            if params["q"] == "bolinha pet" else [{"category_id": "MLB3843", "domain_id": "MLB-SPEAKERS"}])
    if caminho == "/products/search":
        return RespostaFalsa({"results": [
            {"id": "MLB-busca-0", "status": "active", "domain_id": "MLB-PET_TOYS", "pictures": [{}]},
            {"id": "MLB-busca-9", "status": "active", "domain_id": "MLB-CHARMS", "pictures": [{}]},
        ]})
    if caminho.endswith("/items"):
        if caminho.split("/")[2].endswith("-1"):
            return RespostaFalsa({"message": "not found"}, status=404)
        return RespostaFalsa({"results": [{"price": 89.9}, {"price": 59.9}, {"price": 120}]})
    pid = caminho.split("/")[2]
    return RespostaFalsa({"id": pid, "name": f"Produto {pid}", "status": "inactive" if pid.endswith("-2") else "active",
                          "pictures": [{"url": f"https://ex.com/{pid}.jpg"}]})


@pytest.fixture
def ml(app, monkeypatch):
    """Configura credenciais falsas e simula as respostas da API do ML."""
    app.config.update(ML_CLIENT_ID="id", ML_CLIENT_SECRET="segredo")
    services.limpar_cache()
    chamadas = {"token": 0, "get": []}

    def post(url, **kwargs):
        chamadas["token"] += 1
        return RespostaFalsa({"access_token": "abc", "expires_in": 21600})

    def get(url, **kwargs):
        chamadas["get"].append(url)
        return api_falsa(url, **kwargs)

    monkeypatch.setattr(services.requests, "post", post)
    monkeypatch.setattr(services.requests, "get", get)
    yield chamadas
    services.limpar_cache()


def test_banner_traz_um_mais_vendido_de_cada_categoria_basica(client, ml):
    itens = client.get("/api/mercadolivre/destaques").get_json()
    assert [i["categoria"] for i in itens] == ["Ração", "Banho e higiene", "Camas e casinhas", "Brinquedos"]
    assert itens[0]["id"] == "MLB1077-0"
    assert itens[0]["nome"] == "Produto MLB1077-0"
    assert itens[0]["link"] == "https://www.mercadolivre.com.br/p/MLB1077-0"
    assert itens[0]["foto"] == "https://ex.com/MLB1077-0.jpg"


def test_preco_e_o_menor_entre_os_anuncios(client, ml):
    itens = client.get("/api/mercadolivre/destaques").get_json()
    assert all(i["preco"] == 59.9 for i in itens)


def test_produto_sem_anuncio_ou_inativo_fica_de_fora(client, ml):
    grupo = client.get("/api/mercadolivre/sugestoes?categoria=coleiras").get_json()[0]
    # coleiras usa uma categoria so; dos 8 primeiros, o 1 nao esta a venda e o 2 esta inativo
    assert [p["id"] for p in grupo["produtos"]] == ["MLB1075-0", "MLB1075-3", "MLB1075-4", "MLB1075-5",
                                                    "MLB1075-6", "MLB1075-7"]


def test_sugestoes_juntam_caes_e_gatos(client, ml):
    grupo = client.get("/api/mercadolivre/sugestoes?categoria=racao").get_json()[0]
    ids = [p["id"] for p in grupo["produtos"]]
    assert len(ids) == services.PRODUTOS_POR_CATEGORIA
    assert ids[:2] == ["MLB1077-0", "MLB85870-0"]


def test_sugestoes_traz_todas_as_categorias(client, ml):
    grupos = client.get("/api/mercadolivre/sugestoes").get_json()
    assert [g["categoria"] for g in grupos] == [c[0] for c in services.CATEGORIAS]
    assert all(g["produtos"] for g in grupos)


def test_sugestoes_de_categoria_inexistente(client, ml):
    assert client.get("/api/mercadolivre/sugestoes?categoria=xyz").status_code == 404


def test_busca_usa_os_mais_vendidos_da_categoria_de_pet_do_termo(client, ml):
    produtos = client.get("/api/mercadolivre/produtos?q=arranhador&limit=3").get_json()
    assert [p["id"] for p in produtos] == ["MLB85861-0", "MLB85861-3", "MLB85861-4"]
    assert not any("MLB3843" in url for url in ml["get"])  # categoria de caixa de som foi ignorada


def test_busca_tenta_de_novo_com_pet_no_termo(client, ml):
    produtos = client.get("/api/mercadolivre/produtos?q=bolinha&limit=2").get_json()
    assert [p["id"] for p in produtos] == ["MLB1074-0", "MLB1074-3"]


def test_busca_sem_categoria_de_pet_usa_o_catalogo(client, ml):
    produtos = client.get("/api/mercadolivre/produtos?q=caixa de som").get_json()
    assert [p["id"] for p in produtos] == ["MLB-busca-0"]


def test_busca_sem_termo_e_rejeitada(client, ml):
    assert client.get("/api/mercadolivre/produtos?q=").status_code == 400


def test_token_e_resultados_ficam_em_cache(client, ml):
    client.get("/api/mercadolivre/sugestoes")
    antes = len(ml["get"])
    client.get("/api/mercadolivre/sugestoes")
    client.get("/api/mercadolivre/destaques")
    assert ml["token"] == 1
    assert len(ml["get"]) == antes


def test_se_o_preco_falhar_mostra_o_produto_sem_preco(client, ml, monkeypatch):
    monkeypatch.setattr(services.requests, "get", lambda url, **k: RespostaFalsa({}, status=500)
                        if url.endswith("/items") else api_falsa(url, **k))
    itens = client.get("/api/mercadolivre/destaques").get_json()
    assert len(itens) == 4 and all(i["preco"] is None for i in itens)


def test_detalhe_do_produto(client, ml):
    produto = client.get("/api/mercadolivre/produtos/MLB1-0").get_json()
    assert produto["preco"] == 59.9 and produto["nome"] == "Produto MLB1-0"
    assert client.get("/api/mercadolivre/produtos/MLB1-1").status_code == 404


def test_sem_credenciais_responde_503(client, app):
    services.limpar_cache()
    app.config.update(ML_CLIENT_ID="", ML_CLIENT_SECRET="")
    resposta = client.get("/api/mercadolivre/destaques")
    assert resposta.status_code == 503
    assert "ML_CLIENT_ID" in resposta.get_json()["erro"]


def test_falha_na_api_responde_503(client, ml, monkeypatch):
    monkeypatch.setattr(services.requests, "get", lambda *a, **k: RespostaFalsa({}, status=403))
    assert client.get("/api/mercadolivre/destaques").status_code == 503
