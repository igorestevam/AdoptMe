"""Testes da integracao com o Mercado Livre, com a API simulada (sem internet)."""
import pytest
import requests

from adoptme.mercadolivre import services


class RespostaFalsa:
    def __init__(self, dados, status=200):
        self.dados = dados
        self.status = status

    def json(self):
        return self.dados

    def raise_for_status(self):
        if self.status >= 400:
            raise requests.HTTPError(f"status {self.status}")


@pytest.fixture
def ml(app, monkeypatch):
    """Configura credenciais falsas e simula as respostas da API do ML."""
    app.config.update(ML_CLIENT_ID="id", ML_CLIENT_SECRET="segredo")
    services.limpar_cache()
    chamadas = {"token": 0, "busca": []}

    def post(url, **kwargs):
        chamadas["token"] += 1
        return RespostaFalsa({"access_token": "abc", "expires_in": 21600})

    def get(url, params=None, **kwargs):
        if url.endswith("/products/search"):
            chamadas["busca"].append(params["q"])
            n = params["limit"]
            return RespostaFalsa({"results": [
                {"id": f"MLB{i}", "name": f"{params['q']} {i}",
                 "pictures": [{"url": f"https://ex.com/{i}.jpg"}],
                 "permalink": f"https://www.mercadolivre.com.br/p/MLB{i}"}
                for i in range(n)
            ]})
        return RespostaFalsa({"id": "MLB9", "name": "Cama media"})

    monkeypatch.setattr(services.requests, "post", post)
    monkeypatch.setattr(services.requests, "get", get)
    yield chamadas
    services.limpar_cache()


def test_banner_traz_um_produto_de_cada_categoria_basica(client, ml):
    itens = client.get("/api/mercadolivre/destaques").get_json()
    assert [i["categoria"] for i in itens] == ["Ração", "Banho e higiene", "Camas e casinhas", "Brinquedos"]
    assert itens[0]["link"] == "https://www.mercadolivre.com.br/p/MLB0"
    assert itens[0]["foto"] == "https://ex.com/0.jpg"


def test_sugestoes_traz_todas_as_categorias(client, ml):
    grupos = client.get("/api/mercadolivre/sugestoes").get_json()
    assert len(grupos) == len(services.CATEGORIAS)
    assert all(len(g["produtos"]) == services.PRODUTOS_POR_CATEGORIA for g in grupos)


def test_sugestoes_de_uma_categoria(client, ml):
    grupos = client.get("/api/mercadolivre/sugestoes?categoria=petiscos").get_json()
    assert [g["nome"] for g in grupos] == ["Petiscos"]
    assert client.get("/api/mercadolivre/sugestoes?categoria=xyz").status_code == 404


def test_token_e_buscas_sao_reaproveitados(client, ml):
    client.get("/api/mercadolivre/destaques")
    client.get("/api/mercadolivre/destaques")
    assert ml["token"] == 1
    assert len(ml["busca"]) == len(services.CATEGORIAS_BANNER)


def test_produto_sem_permalink_usa_link_do_catalogo(client, ml):
    produto = client.get("/api/mercadolivre/produtos/MLB9").get_json()
    assert produto == {"id": "MLB9", "nome": "Cama media", "foto": None,
                       "link": "https://www.mercadolivre.com.br/p/MLB9"}


def test_busca_sem_termo_e_rejeitada(client, ml):
    assert client.get("/api/mercadolivre/produtos?q=").status_code == 400


def test_sem_credenciais_responde_503(client, app):
    services.limpar_cache()
    app.config.update(ML_CLIENT_ID="", ML_CLIENT_SECRET="")
    resposta = client.get("/api/mercadolivre/destaques")
    assert resposta.status_code == 503
    assert "ML_CLIENT_ID" in resposta.get_json()["erro"]


def test_falha_na_api_responde_503(client, ml, monkeypatch):
    monkeypatch.setattr(services.requests, "get", lambda *a, **k: RespostaFalsa({}, status=403))
    assert client.get("/api/mercadolivre/destaques").status_code == 503
