"""Testes de persistencia do banco SQLite (models do DER do AdoptMe)."""
import pytest
from sqlalchemy import inspect, select, func, text
from sqlalchemy.exc import IntegrityError

from adoptme import create_app
from adoptme.config import TestConfig
from adoptme.ext.db import db
from adoptme.auth.models import Usuario, Endereco
from adoptme.anunciantes.models import Anunciante
from adoptme.animais.models import Animal, FotoAnimal, InteresseAdocao
from adoptme.parceiros.models import EmpresaParceira, Anuncio, CliqueAnuncio
from adoptme.auth import services as auth_services
from adoptme.parceiros import services as parceiros_services
from adoptme.seed import seed


def recarregar(session, model, id_):
    """Descarta o cache da sessao para garantir que o dado vem do banco."""
    session.expunge_all()
    return session.get(model, id_)


def contar(session, model) -> int:
    return session.scalar(select(func.count()).select_from(model))


# Estrutura do banco

def test_cria_as_9_tabelas_do_der(app):
    tabelas = set(inspect(db.engine).get_table_names())
    assert tabelas == {
        "usuarios", "enderecos", "anunciantes", "animais", "fotos_animal",
        "interesses_adocao", "empresas_parceiras", "anuncios", "cliques_anuncio",
    }


def test_foreign_keys_ativadas_no_sqlite(session):
    assert session.execute(text("PRAGMA foreign_keys")).scalar() == 1


# Usuario / Endereco

def test_salva_e_recupera_usuario(session, criar_usuario):
    u = criar_usuario(nome="Maria", email="maria@teste.com")
    salvo = recarregar(session, Usuario, u.id)
    assert salvo.nome == "Maria"
    assert salvo.email == "maria@teste.com"
    assert salvo.data_nascimento is None
    assert salvo.created_at is not None and salvo.updated_at is not None


def test_email_de_usuario_e_unico(session, criar_usuario):
    criar_usuario(email="repetido@teste.com")
    with pytest.raises(IntegrityError):
        criar_usuario(email="repetido@teste.com")


def test_campo_obrigatorio_nulo_e_rejeitado(session):
    session.add(Usuario(nome="Sem email", cpf_cnpj="1", telefone="1", senha_hash="x"))
    with pytest.raises(IntegrityError):
        session.commit()


def dados_cadastro(**campos):
    dados = {
        "nome": "Joao", "cpf_cnpj": "111.222.333-44", "telefone": "27988887777",
        "email": "joao@teste.com", "senha": "minhasenha",
        "endereco": {
            "estado": "ES", "cidade": "Vitoria", "bairro": "Centro",
            "rua": "Rua A", "numero": "s/n", "cep": "29000-000",
        },
    }
    dados.update(campos)
    return dados


def test_senha_e_armazenada_com_hash(session):
    criado = auth_services.criar_usuario(dados_cadastro())
    u = recarregar(session, Usuario, criado["id"])
    assert u.senha_hash != "minhasenha"
    assert auth_services.autenticar("joao@teste.com", "minhasenha")["id"] == u.id
    assert auth_services.autenticar("joao@teste.com", "errada") is None


def test_cadastro_salva_o_endereco_do_usuario(session):
    criado = auth_services.criar_usuario(dados_cadastro())
    assert recarregar(session, Usuario, criado["id"]).endereco.numero == "s/n"


def test_cadastro_sem_endereco_e_rejeitado(client, session):
    dados = dados_cadastro()
    del dados["endereco"]
    assert client.post("/api/auth/register", json=dados).status_code == 400
    assert contar(session, Usuario) == 0


def test_cadastro_com_endereco_incompleto_e_rejeitado(client, session):
    resposta = client.post("/api/auth/register", json=dados_cadastro(endereco={"estado": "ES"}))
    assert resposta.status_code == 400
    assert contar(session, Usuario) == 0


def test_endereco_um_para_um_com_usuario(session, criar_usuario, criar_endereco):
    u = criar_usuario()
    criar_endereco(u, cidade="Vila Velha", complemento="Apto 101")
    salvo = recarregar(session, Usuario, u.id)
    assert salvo.endereco.cidade == "Vila Velha"
    assert salvo.endereco.complemento == "Apto 101"


def test_usuario_nao_pode_ter_dois_enderecos(session, criar_usuario, criar_endereco):
    u = criar_usuario()
    criar_endereco(u)
    session.add(Endereco(usuario_id=u.id, estado="ES", cidade="Serra", bairro="B",
                         rua="R", numero="s/n", cep="29000-000"))
    with pytest.raises(IntegrityError):
        session.commit()


def test_excluir_usuario_remove_endereco_e_anunciante(session, criar_usuario, criar_endereco, criar_anunciante):
    u = criar_usuario()
    criar_endereco(u)
    criar_anunciante(usuario=u)
    session.delete(u)
    session.commit()
    assert contar(session, Endereco) == 0
    assert contar(session, Anunciante) == 0


# Anunciante

def test_adotante_e_usuario_sem_perfil_de_anunciante(session, criar_usuario):
    u = criar_usuario()
    assert recarregar(session, Usuario, u.id).anunciante is None


def test_anunciante_vinculado_ao_usuario(session, criar_usuario, criar_anunciante):
    u = criar_usuario(nome="Abrigo")
    a = criar_anunciante(usuario=u, tipo="pessoa_fisica", descricao="Protetora")
    salvo = recarregar(session, Anunciante, a.id)
    assert salvo.usuario.nome == "Abrigo"
    assert salvo.tipo == "pessoa_fisica"


def test_tipo_de_anunciante_invalido_e_rejeitado(session, criar_anunciante):
    with pytest.raises(IntegrityError):
        criar_anunciante(tipo="empresa")


def test_usuario_nao_pode_ter_dois_perfis_de_anunciante(session, criar_usuario, criar_anunciante):
    u = criar_usuario()
    criar_anunciante(usuario=u)
    session.add(Anunciante(usuario_id=u.id, tipo="pessoa_fisica"))
    with pytest.raises(IntegrityError):
        session.commit()


# Animal / FotoAnimal / InteresseAdocao

def test_animal_nasce_disponivel(session, criar_animal):
    a = criar_animal()
    salvo = recarregar(session, Animal, a.id)
    assert salvo.situacao == "disponivel"
    assert salvo.idade is None and salvo.descricao is None


def test_alterar_situacao_para_adotado(session, criar_animal):
    a = criar_animal()
    a.situacao = "adotado"
    session.commit()
    assert recarregar(session, Animal, a.id).situacao == "adotado"


def test_situacao_invalida_e_rejeitada(session, criar_animal):
    with pytest.raises(IntegrityError):
        criar_animal(situacao="reservado")


def test_animal_com_anunciante_inexistente_e_rejeitado(session):
    session.add(Animal(nome="X", especie="gato", porte="pequeno", sexo="macho", anunciante_id=999))
    with pytest.raises(IntegrityError):
        session.commit()


def test_anunciante_com_varios_animais(session, criar_anunciante, criar_animal):
    dono = criar_anunciante()
    criar_animal(anunciante=dono, nome="Nina")
    criar_animal(anunciante=dono, nome="Thor")
    salvo = recarregar(session, Anunciante, dono.id)
    assert sorted(a.nome for a in salvo.animais) == ["Nina", "Thor"]


def test_animal_com_varias_fotos(session, criar_animal):
    a = criar_animal()
    a.fotos.extend([FotoAnimal(url="https://ex.com/1.jpg"), FotoAnimal(url="https://ex.com/2.jpg")])
    session.commit()
    assert len(recarregar(session, Animal, a.id).fotos) == 2


def test_interesse_liga_animal_e_usuario(session, criar_animal, criar_usuario):
    animal = criar_animal()
    adotante = criar_usuario(nome="Carlos")
    session.add(InteresseAdocao(animal=animal, usuario=adotante, mensagem="Tenho quintal"))
    session.commit()
    adotante_id = adotante.id

    salvo = recarregar(session, Animal, animal.id)
    interesse = salvo.interesses[0]
    assert interesse.usuario.nome == "Carlos"
    assert interesse.mensagem == "Tenho quintal"
    assert interesse.data_hora is not None
    assert len(session.get(Usuario, adotante_id).interesses) == 1


def test_excluir_animal_remove_fotos_e_interesses(session, criar_animal, criar_usuario):
    animal = criar_animal()
    adotante = criar_usuario()
    animal.fotos.append(FotoAnimal(url="https://ex.com/1.jpg"))
    animal.interesses.append(InteresseAdocao(usuario=adotante))
    session.commit()

    session.delete(animal)
    session.commit()
    assert contar(session, FotoAnimal) == 0
    assert contar(session, InteresseAdocao) == 0
    assert contar(session, Usuario) == 2  # o adotante (e o dono) continuam existindo


def test_excluir_anunciante_remove_seus_animais(session, criar_animal):
    animal = criar_animal()
    session.delete(animal.anunciante)
    session.commit()
    assert contar(session, Animal) == 0


# Parceiros (anuncios CPC)

def test_empresa_anuncio_e_cliques(session):
    empresa = EmpresaParceira(nome="PetShop", telefone="2733330000")
    anuncio = Anuncio(conteudo="Racao em promocao", link_destino="https://ex.com/promo")
    empresa.anuncios.append(anuncio)
    session.add(empresa)
    session.commit()

    assert parceiros_services.registrar_clique(anuncio.id, sessao="abc") == "https://ex.com/promo"
    parceiros_services.registrar_clique(anuncio.id, sessao="def")

    salvo = recarregar(session, Anuncio, anuncio.id)
    assert salvo.empresa.nome == "PetShop"
    assert sorted(c.sessao for c in salvo.cliques) == ["abc", "def"]
    assert all(c.data_hora is not None for c in salvo.cliques)


def test_clique_em_anuncio_inexistente_nao_registra(session):
    assert parceiros_services.registrar_clique(999) is None
    assert contar(session, CliqueAnuncio) == 0


def test_excluir_empresa_remove_anuncios_e_cliques(session):
    empresa = EmpresaParceira(nome="PetShop", telefone="2733330000")
    anuncio = Anuncio(conteudo="Promo", link_destino="https://ex.com")
    anuncio.cliques.append(CliqueAnuncio(sessao="s1"))
    empresa.anuncios.append(anuncio)
    session.add(empresa)
    session.commit()

    session.delete(empresa)
    session.commit()
    assert contar(session, Anuncio) == 0
    assert contar(session, CliqueAnuncio) == 0


# Seed e persistencia em arquivo

def test_seed_popula_e_nao_duplica(session):
    assert seed() is True
    assert contar(session, Animal) == 6
    assert contar(session, Anunciante) == 2
    assert contar(session, Usuario) == 3
    assert seed() is False
    assert contar(session, Animal) == 6


def test_dados_sobrevivem_ao_reiniciar_a_aplicacao(tmp_path):
    """Grava num arquivo .db, "desliga" a app e confere os dados numa nova instancia."""
    class ArquivoConfig(TestConfig):
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{(tmp_path / 'adoptme_teste.db').as_posix()}"

    app1 = create_app(ArquivoConfig)
    with app1.app_context():
        db.create_all()
        seed()
        db.session.remove()
        db.engine.dispose()

    app2 = create_app(ArquivoConfig)
    with app2.app_context():
        nina = db.session.scalar(select(Animal).filter_by(nome="Nina"))
        assert nina is not None
        assert nina.anunciante.usuario.email == "ong@adoptme.dev"
        assert len(nina.interesses) == 1
        db.session.remove()
        db.engine.dispose()


# API lendo do banco

def test_api_lista_e_filtra_animais(client, session):
    seed()
    assert len(client.get("/api/animais").get_json()) == 6
    gatos = client.get("/api/animais?especie=gato").get_json()
    assert {a["nome"] for a in gatos} == {"Mel", "Simba"}
    assert client.get("/api/animais/999").status_code == 404
