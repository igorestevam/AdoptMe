"""Testes da tela "Minha conta": ver e editar os dados e trocar a senha."""
from adoptme.auth.models import Endereco, Usuario
from tests.test_api import cadastro


def dados_da_conta(**campos):
    dados = {
        "nome": "Joao Silva", "telefone": "27911112222", "data_nascimento": "2000-05-10",
        "endereco": {"estado": "es", "cidade": "Vila Velha", "bairro": "Praia da Costa",
                     "rua": "Rua B", "numero": "20", "cep": "29101000", "complemento": "Apto 3"},
    }
    dados.update(campos)
    return dados


def test_conta_exige_login(client, session):
    assert client.get("/api/auth/conta").status_code == 401
    assert client.put("/api/auth/conta", json=dados_da_conta()).status_code == 401
    assert client.put("/api/auth/senha", json={"senha_atual": "x", "nova_senha": "y"}).status_code == 401


def test_conta_traz_endereco_e_perfil(client, session):
    client.post("/api/auth/register", json=cadastro(data_nascimento="1999-01-02"))
    conta = client.get("/api/auth/conta").get_json()
    assert conta["email"] == "joao@teste.com"
    assert conta["data_nascimento"] == "1999-01-02"
    assert conta["endereco"]["cidade"] == "Vitoria"
    assert conta["anunciante"] is None


def test_atualiza_dados_e_endereco(client, session):
    client.post("/api/auth/register", json=cadastro())
    resposta = client.put("/api/auth/conta", json=dados_da_conta())
    assert resposta.status_code == 200
    conta = resposta.get_json()
    assert conta["nome"] == "Joao Silva" and conta["telefone"] == "27911112222"
    assert conta["data_nascimento"] == "2000-05-10"
    assert conta["endereco"]["cep"] == "29101-000" and conta["endereco"]["estado"] == "ES"

    # continua com um unico endereco, atualizado no lugar
    assert session.query(Endereco).count() == 1
    assert client.get("/api/auth/me").get_json()["nome"] == "Joao Silva"


def test_email_e_documento_nao_mudam(client, session):
    client.post("/api/auth/register", json=cadastro())
    conta = client.put("/api/auth/conta", json=dados_da_conta(
        email="outro@teste.com", cpf_cnpj="12345678000195")).get_json()
    assert conta["email"] == "joao@teste.com"
    assert conta["cpf_cnpj"] == "529.982.247-25"


def test_atualizacao_valida_os_campos(client, session):
    client.post("/api/auth/register", json=cadastro())

    def erro(**campos):
        resposta = client.put("/api/auth/conta", json=dados_da_conta(**campos))
        assert resposta.status_code == 400
        return resposta.get_json()["erro"]

    endereco = dados_da_conta()["endereco"]
    assert erro(nome="  ") == "Campos obrigatorios: nome"
    assert erro(endereco={**endereco, "cep": "123"}) == "CEP invalido"
    assert erro(endereco={**endereco, "estado": "XX"}) == "UF invalida"
    assert erro(endereco={**endereco, "rua": ""}) == "Endereco incompleto: rua"
    assert erro(data_nascimento="10/05/2000") == "Data de nascimento invalida"
    assert erro(anunciante="sim") == "Dados de anunciante invalidos"

    # nada foi gravado pelas tentativas com erro
    assert client.get("/api/auth/conta").get_json()["nome"] == "Joao"


def test_anunciante_edita_a_apresentacao(client, session):
    client.post("/api/auth/register", json=cadastro(
        cpf_cnpj="12345678000195", anunciante={"tipo": "organizacao", "descricao": "Abrigo"}))
    conta = client.put("/api/auth/conta", json=dados_da_conta(
        anunciante={"descricao": "Abrigo com 40 animais"})).get_json()
    assert conta["anunciante"] == {"tipo": "organizacao", "descricao": "Abrigo com 40 animais"}


def test_adotante_pode_passar_a_divulgar(client, session):
    usuario = client.post("/api/auth/register", json=cadastro()).get_json()
    assert usuario["anunciante_id"] is None

    conta = client.put("/api/auth/conta", json=dados_da_conta(anunciante={"descricao": "Protetora"})).get_json()
    assert conta["anunciante"]["tipo"] == "pessoa_fisica"
    assert conta["anunciante_id"] is not None
    assert client.get("/api/animais/meus").status_code == 200


def test_sem_anunciante_no_corpo_mantem_o_perfil(client, session):
    client.post("/api/auth/register", json=cadastro(anunciante={"tipo": "pessoa_fisica", "descricao": "Protetora"}))
    conta = client.put("/api/auth/conta", json=dados_da_conta()).get_json()
    assert conta["anunciante"]["descricao"] == "Protetora"


def test_cria_endereco_se_a_conta_nao_tinha(client, session, criar_usuario):
    usuario = criar_usuario(email="semendereco@teste.com")
    client.post("/api/auth/login", json={"email": "semendereco@teste.com", "senha": "senha123"})
    assert client.get("/api/auth/conta").get_json()["endereco"] is None

    client.put("/api/auth/conta", json=dados_da_conta())
    assert session.get(Usuario, usuario.id).endereco.cidade == "Vila Velha"


def test_troca_de_senha(client, session):
    client.post("/api/auth/register", json=cadastro())

    errada = client.put("/api/auth/senha", json={"senha_atual": "errada", "nova_senha": "novasenha"})
    assert errada.status_code == 400 and errada.get_json()["erro"] == "Senha atual incorreta"
    curta = client.put("/api/auth/senha", json={"senha_atual": "minhasenha", "nova_senha": "123"})
    assert curta.status_code == 400

    assert client.put("/api/auth/senha", json={"senha_atual": "minhasenha", "nova_senha": "novasenha"}).status_code == 204
    client.post("/api/auth/logout")
    assert client.post("/api/auth/login", json={"email": "joao@teste.com", "senha": "minhasenha"}).status_code == 401
    assert client.post("/api/auth/login", json={"email": "joao@teste.com", "senha": "novasenha"}).status_code == 200
