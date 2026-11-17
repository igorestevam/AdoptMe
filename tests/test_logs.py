"""Testes do logging e do tratamento de erros inesperados."""
import logging

from adoptme.seed import seed


def test_erro_inesperado_vira_500_em_json_e_vai_para_o_log(app, client, caplog):
    @app.get("/api/teste-erro")
    def quebra():
        raise RuntimeError("falha de teste")

    with caplog.at_level(logging.ERROR, logger="adoptme"):
        resposta = client.get("/api/teste-erro")
    assert resposta.status_code == 500
    assert resposta.get_json() == {"erro": "Erro interno. Tente novamente mais tarde."}
    assert "Erro inesperado em GET /api/teste-erro" in caplog.text
    assert "falha de teste" in caplog.text


def test_login_recusado_fica_no_log_sem_o_email_completo(client, session, caplog):
    seed()
    with caplog.at_level(logging.WARNING, logger="adoptme"):
        client.post("/api/auth/login", json={"email": "ana@adoptme.dev", "senha": "errada"})
    assert "Login recusado para a***@adoptme.dev" in caplog.text
    assert "ana@adoptme.dev" not in caplog.text


def test_operacoes_principais_ficam_no_log(client, session, caplog):
    seed()
    with caplog.at_level(logging.INFO, logger="adoptme"):
        client.post("/api/auth/login", json={"email": "ong@adoptme.dev", "senha": "senha123"})
        client.patch("/api/animais/1/situacao", json={"situacao": "adotado"})
        client.get("/api/parceiros/anuncios/1/clique")
    assert "Usuario 1 entrou" in caplog.text
    assert "Animal 1 agora esta adotado" in caplog.text
    assert "Clique registrado no anuncio 1" in caplog.text


def test_erro_de_rota_continua_com_a_mensagem_propria(client, session):
    resposta = client.get("/api/animais/999")
    assert resposta.status_code == 404
    assert resposta.get_json() == {"erro": "Animal nao encontrado"}
