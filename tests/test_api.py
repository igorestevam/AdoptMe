"""Testes das rotas usadas pela interface (sessao, busca, detalhes e interesse)."""
from adoptme.animais.models import InteresseAdocao
from adoptme.seed import seed


def cadastro(**campos):
    dados = {
        "nome": "Joao", "cpf_cnpj": "529.982.247-25", "telefone": "27988887777",
        "email": "joao@teste.com", "senha": "minhasenha",
        "endereco": {"estado": "ES", "cidade": "Vitoria", "bairro": "Centro",
                     "rua": "Rua A", "numero": "10", "cep": "29000-000"},
    }
    dados.update(campos)
    return dados


def test_login_mantem_a_sessao_ate_o_logout(client, session):
    client.post("/api/auth/register", json=cadastro())
    client.post("/api/auth/logout")
    assert client.get("/api/auth/me").status_code == 401

    assert client.post("/api/auth/login", json={"email": "joao@teste.com", "senha": "minhasenha"}).status_code == 200
    assert client.get("/api/auth/me").get_json()["email"] == "joao@teste.com"

    client.post("/api/auth/logout")
    assert client.get("/api/auth/me").status_code == 401


def test_login_com_senha_errada_devolve_erro_em_json(client, session):
    client.post("/api/auth/register", json=cadastro())
    resposta = client.post("/api/auth/login", json={"email": "joao@teste.com", "senha": "errada"})
    assert resposta.status_code == 401
    assert resposta.get_json()["erro"] == "Email ou senha invalidos"


def test_cadastro_ja_entra_na_conta(client, session):
    client.post("/api/auth/register", json=cadastro())
    assert client.get("/api/auth/me").status_code == 200


def test_cadastro_de_anunciante_cria_o_perfil(client, session):
    usuario = client.post("/api/auth/register", json=cadastro(
        cpf_cnpj="12345678000195", anunciante={"tipo": "organizacao", "descricao": "Abrigo"})).get_json()
    assert usuario["anunciante_id"] is not None
    perfil = client.get(f"/api/anunciantes/{usuario['anunciante_id']}").get_json()
    assert perfil["nome"] == "Joao" and perfil["cidade"] == "Vitoria"


def test_cadastro_com_campo_faltando_e_tipo_invalido(client, session):
    assert client.post("/api/auth/register", json=cadastro(senha="")).status_code == 400
    assert client.post("/api/auth/register", json=cadastro(anunciante={"tipo": "empresa"})).status_code == 400


def test_cadastro_valida_documento_email_cep_e_uf(client, session):
    def erro(**campos):
        resposta = client.post("/api/auth/register", json=cadastro(**campos))
        assert resposta.status_code == 400
        return resposta.get_json()["erro"]

    endereco = cadastro()["endereco"]
    assert erro(cpf_cnpj="111.222.333-44") == "CPF ou CNPJ invalido"
    assert erro(cpf_cnpj="11111111111") == "CPF ou CNPJ invalido"
    assert erro(email="joao@") == "Email invalido"
    assert erro(endereco={**endereco, "cep": "2900"}) == "CEP invalido"
    assert erro(endereco={**endereco, "estado": "XX"}) == "UF invalida"
    assert erro(anunciante={"tipo": "organizacao"}) == "Organizacoes devem informar um CNPJ"
    assert erro(cpf_cnpj="12345678000195", anunciante={"tipo": "pessoa_fisica"}) == "Pessoas fisicas devem informar um CPF"


def test_cadastro_guarda_documento_e_cep_formatados(client, session):
    usuario = client.post("/api/auth/register", json=cadastro(
        cpf_cnpj="52998224725", email="Joao@Teste.com",
        endereco={**cadastro()["endereco"], "cep": "29000000", "estado": "es"})).get_json()
    assert usuario["cpf_cnpj"] == "529.982.247-25"
    assert usuario["email"] == "joao@teste.com"
    assert client.post("/api/auth/login", json={"email": "JOAO@teste.com", "senha": "minhasenha"}).status_code == 200


def test_cpf_cnpj_e_unico_mesmo_com_outra_formatacao(client, session):
    client.post("/api/auth/register", json=cadastro())
    resposta = client.post("/api/auth/register", json=cadastro(email="outro@teste.com", cpf_cnpj="52998224725"))
    assert resposta.status_code == 409
    assert resposta.get_json()["erro"] == "Ja existe um usuario com este CPF/CNPJ"


def test_lista_de_usuarios_nao_e_publica(client, session):
    assert client.get("/api/auth/usuarios").status_code == 404


def test_busca_por_nome_ou_descricao(client, session):
    seed()
    assert [a["nome"] for a in client.get("/api/animais?q=nin").get_json()] == ["Nina"]
    assert [a["nome"] for a in client.get("/api/animais?q=apartamento").get_json()] == ["Bidu"]
    assert len(client.get("/api/animais?porte=pequeno").get_json()) == 3


def test_detalhe_traz_o_responsavel(client, session):
    seed()
    animal = client.get("/api/animais/1").get_json()
    assert animal["responsavel"]["nome"] == "Abrigo Patinhas"
    assert animal["responsavel"]["telefone"] and animal["responsavel"]["cidade"] == "Vila Velha"


def test_interesse_exige_login(client, session):
    seed()
    assert client.post("/api/animais/1/interesses", json={"mensagem": "Oi"}).status_code == 401

    client.post("/api/auth/login", json={"email": "carlos@adoptme.dev", "senha": "senha123"})
    antes = session.query(InteresseAdocao).count()
    resposta = client.post("/api/animais/2/interesses", json={"mensagem": "Tenho quintal"})
    assert resposta.status_code == 201
    assert session.query(InteresseAdocao).count() == antes + 1
    assert client.post("/api/animais/999/interesses", json={}).status_code == 404
