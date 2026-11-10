"""Testes do painel do anunciante: cadastrar, editar, remover e mudar a situacao dos animais."""
import io

import pytest

from adoptme.animais.models import Animal
from adoptme.seed import seed

NOVO = {"nome": "Pipoca", "especie": "gato", "porte": "pequeno", "sexo": "femea", "idade": "2",
        "descricao": "Calma", "fotos": ["https://ex.com/1.jpg", "https://ex.com/2.jpg"]}


@pytest.fixture
def ong(client, session):
    """Entra como o Abrigo Patinhas (anunciante 1, dono de Nina, Mel e Luna)."""
    seed()
    client.post("/api/auth/login", json={"email": "ong@adoptme.dev", "senha": "senha123"})
    return client


def test_painel_exige_login_de_anunciante(client, session):
    seed()
    assert client.get("/api/animais/meus").status_code == 401
    client.post("/api/auth/login", json={"email": "carlos@adoptme.dev", "senha": "senha123"})
    assert client.get("/api/animais/meus").status_code == 403
    assert client.post("/api/animais", json=NOVO).status_code == 403


def test_lista_so_os_animais_do_anunciante(ong):
    # pela ordem do seed, os animais da ONG recebem os ids 1, 2 e 3
    nomes = {a["nome"] for a in ong.get("/api/animais/meus").get_json()}
    assert nomes == {"Nina", "Mel", "Luna"}


def test_cadastrar_animal(ong, session):
    animal = ong.post("/api/animais", json=NOVO).get_json()
    salvo = session.get(Animal, animal["id"])
    assert salvo.nome == "Pipoca" and salvo.idade == 2 and salvo.situacao == "disponivel"
    assert salvo.anunciante.usuario.email == "ong@adoptme.dev"
    assert [f.url for f in salvo.fotos] == NOVO["fotos"]


@pytest.mark.parametrize("campo, valor", [
    ("nome", ""), ("especie", "peixe"), ("porte", "gigante"), ("sexo", "x"),
    ("idade", "dois"), ("fotos", ["ftp://ex.com/a.jpg"]), ("fotos", ["https://ex.com/a.jpg"] * 6),
])
def test_cadastro_de_animal_invalido(ong, campo, valor):
    assert ong.post("/api/animais", json={**NOVO, campo: valor}).status_code == 400


def test_editar_animal_troca_dados_e_fotos(ong, session):
    animal = ong.put("/api/animais/1", json={**NOVO, "nome": "Nina", "fotos": ["https://ex.com/nova.jpg"]}).get_json()
    assert animal["especie"] == "gato" and animal["fotos"] == ["https://ex.com/nova.jpg"]


def test_alterar_situacao(ong):
    assert ong.patch("/api/animais/1/situacao", json={"situacao": "adotado"}).get_json()["situacao"] == "adotado"
    assert ong.patch("/api/animais/1/situacao", json={"situacao": "reservado"}).status_code == 400


def test_remover_animal(ong, session):
    assert ong.delete("/api/animais/3").status_code == 204
    assert session.get(Animal, 3) is None
    assert ong.delete("/api/animais/3").status_code == 404


def test_nao_mexe_em_animal_de_outro_anunciante(ong, session):
    thor = session.query(Animal).filter_by(nome="Thor").one()  # e da Ana Souza
    url = f"/api/animais/{thor.id}"
    assert ong.put(url, json=NOVO).status_code == 403
    assert ong.patch(f"{url}/situacao", json={"situacao": "adotado"}).status_code == 403
    assert ong.delete(url).status_code == 403
    assert ong.get(f"{url}/interesses").status_code == 403
    session.expire_all()
    assert session.get(Animal, thor.id).nome == "Thor"


def test_ver_interessados(ong):
    interesses = ong.get("/api/animais/1/interesses").get_json()
    assert [i["nome"] for i in interesses] == ["Carlos Lima"]
    assert interesses[0]["email"] == "carlos@adoptme.dev"


# Envio de fotos

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64


@pytest.fixture
def pasta_fotos(app, tmp_path):
    app.config["UPLOAD_FOLDER"] = str(tmp_path)
    return tmp_path


def enviar(cliente, conteudo, nome="foto.png"):
    return cliente.post("/api/animais/fotos", data={"foto": (io.BytesIO(conteudo), nome)},
                        content_type="multipart/form-data")


def test_enviar_foto_e_usar_no_animal(ong, pasta_fotos, session):
    resposta = enviar(ong, PNG)
    assert resposta.status_code == 201
    url = resposta.get_json()["url"]
    assert url.startswith("/api/animais/fotos/") and url.endswith(".png")
    assert ong.get(url).data == PNG

    animal = ong.post("/api/animais", json={**NOVO, "fotos": [url]}).get_json()
    assert animal["fotos"] == [url]


def test_foto_tem_que_ser_imagem(ong, pasta_fotos):
    resposta = enviar(ong, b"%PDF-1.4 nao sou imagem", "foto.png")
    assert resposta.status_code == 400
    assert resposta.get_json()["erro"] == "Envie uma imagem JPG, PNG, WEBP ou GIF"
    assert list(pasta_fotos.iterdir()) == []


def test_foto_maior_que_5_mb_e_recusada(ong, pasta_fotos):
    resposta = enviar(ong, PNG + b"\x00" * (5 * 1024 * 1024))
    assert resposta.status_code == 413
    assert resposta.get_json()["erro"] == "A foto pode ter no maximo 5 MB"


def test_so_anunciante_envia_foto(client, session, pasta_fotos):
    assert enviar(client, PNG).status_code == 401


def test_animal_nao_aceita_caminho_de_foto_inventado(ong):
    for foto in ["/api/animais/fotos/../../app.py", "/etc/passwd", r"C:\foto.png"]:
        assert ong.post("/api/animais", json={**NOVO, "fotos": [foto]}).status_code == 400


def test_foto_retirada_ou_animal_removido_apaga_o_arquivo(ong, pasta_fotos):
    url1, url2 = (enviar(ong, PNG).get_json()["url"] for _ in range(2))
    animal = ong.post("/api/animais", json={**NOVO, "fotos": [url1, url2]}).get_json()

    ong.put(f"/api/animais/{animal['id']}", json={**NOVO, "fotos": [url2]})
    assert sorted(p.name for p in pasta_fotos.iterdir()) == [url2.rsplit("/", 1)[1]]

    ong.delete(f"/api/animais/{animal['id']}")
    assert list(pasta_fotos.iterdir()) == []


def test_fotos_por_link_continuam_aceitas(ong):
    animal = ong.put("/api/animais/1", json={**NOVO, "fotos": ["https://ex.com/antiga.jpg"]}).get_json()
    assert animal["fotos"] == ["https://ex.com/antiga.jpg"]
