"""Testes dos anuncios das empresas parceiras: comandos, cliques e relatorio de cobranca."""
from datetime import datetime, timedelta

import pytest

from adoptme.parceiros import services
from adoptme.parceiros.models import CliqueAnuncio


@pytest.fixture
def terminal(app, session):
    runner = app.test_cli_runner()
    return lambda *args: runner.invoke(args=list(args))


@pytest.fixture
def anuncio(terminal):
    terminal("nova-empresa", "PetShop Amigo", "2733330000", "--email", "contato@petshop.com")
    terminal("novo-anuncio", "1", "10% de desconto na primeira ração", "https://petshop.com/promo")
    return 1


def test_cadastrar_empresa_e_anuncio_pelo_terminal(terminal, anuncio):
    saida = terminal("anuncios").output
    assert "[1] PetShop Amigo - 2733330000 - contato@petshop.com" in saida
    assert "anuncio 1: 10% de desconto na primeira ração -> https://petshop.com/promo (0 cliques)" in saida


def test_terminal_recusa_dados_invalidos(terminal, anuncio):
    assert "Empresa 9 nao encontrada" in terminal("novo-anuncio", "9", "Promo", "https://ex.com").output
    assert "http://" in terminal("novo-anuncio", "1", "Promo", "petshop.com").output
    assert terminal("nova-empresa", " ", "27").exit_code != 0


def test_lista_publica_de_anuncios_nao_expoe_o_link(client, anuncio):
    anuncios = client.get("/api/parceiros/anuncios").get_json()
    assert anuncios == [{"id": 1, "conteudo": "10% de desconto na primeira ração", "empresa": "PetShop Amigo",
                         "empresa_parceira_id": 1}]


def test_clique_redireciona_e_e_registrado(client, anuncio, session):
    resposta = client.get("/api/parceiros/anuncios/1/clique")
    assert resposta.status_code == 302
    assert resposta.headers["Location"] == "https://petshop.com/promo"
    assert session.query(CliqueAnuncio).count() == 1
    assert client.get("/api/parceiros/anuncios/99/clique").status_code == 404


def test_clique_repetido_da_mesma_sessao_nao_conta(client, app, anuncio, session):
    client.get("/api/parceiros/anuncios/1/clique")
    client.get("/api/parceiros/anuncios/1/clique")
    assert session.query(CliqueAnuncio).count() == 1

    outro_visitante = app.test_client()
    outro_visitante.get("/api/parceiros/anuncios/1/clique")
    assert session.query(CliqueAnuncio).count() == 2


def test_clique_volta_a_contar_depois_do_intervalo(client, anuncio, session):
    client.get("/api/parceiros/anuncios/1/clique")
    clique = session.query(CliqueAnuncio).one()
    clique.data_hora -= services.INTERVALO_CLIQUE_REPETIDO + timedelta(minutes=1)
    session.commit()

    client.get("/api/parceiros/anuncios/1/clique")
    assert session.query(CliqueAnuncio).count() == 2


def test_visitante_nao_escolhe_a_propria_sessao(client, anuncio, session):
    client.get("/api/parceiros/anuncios/1/clique?sessao=a")
    client.get("/api/parceiros/anuncios/1/clique?sessao=b")
    assert session.query(CliqueAnuncio).count() == 1


def test_relatorio_de_cliques_por_periodo(terminal, anuncio, session):
    terminal("novo-anuncio", "1", "Banho e tosa", "https://petshop.com/banho")
    session.add_all([
        CliqueAnuncio(anuncio_id=1, sessao="a", data_hora=datetime(2026, 10, 31, 23, 0)),
        CliqueAnuncio(anuncio_id=1, sessao="b", data_hora=datetime(2026, 11, 1, 10, 0)),
        CliqueAnuncio(anuncio_id=2, sessao="c", data_hora=datetime(2026, 11, 30, 23, 59)),
        CliqueAnuncio(anuncio_id=2, sessao="d", data_hora=datetime(2026, 12, 1, 0, 0)),
    ])
    session.commit()

    linhas = services.relatorio_cliques(datetime(2026, 11, 1), datetime(2026, 12, 1))
    assert [(l["anuncio_id"], l["cliques"]) for l in linhas] == [(1, 1), (2, 1)]

    saida = terminal("relatorio-cliques", "--de", "2026-11-01", "--ate", "2026-11-30").output
    assert "Cliques de 01/11/2026 a 30/11/2026" in saida
    assert "PetShop Amigo: 2" in saida
