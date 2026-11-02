"""Dados de demonstracao para desenvolvimento (comando: flask --app app.py seed-db)."""
from datetime import date

from werkzeug.security import generate_password_hash

from adoptme.ext.db import db
from adoptme.auth.models import Usuario, Endereco
from adoptme.anunciantes.models import Anunciante
from adoptme.animais.models import Animal, FotoAnimal, InteresseAdocao
from adoptme.parceiros.models import EmpresaParceira, Anuncio

SENHA_DEMO = "senha123"

ANIMAIS_DEMO = [
    ("Nina", "cachorro", 2, "medio", "femea",
     "Docil e brincalhona, adora colo e passeios tranquilos.",
     "https://images.unsplash.com/photo-1552053831-71594a27632d?auto=format&fit=crop&w=1000&q=85"),
    ("Thor", "cachorro", 4, "grande", "macho",
     "Companheiro leal e cheio de energia, ideal para atividades ao ar livre.",
     "https://images.unsplash.com/photo-1551717743-49959800b1f6?auto=format&fit=crop&w=1000&q=85"),
    ("Mel", "gato", 1, "pequeno", "femea",
     "Curiosa e carinhosa, procura um lar calmo com janelas seguras.",
     "https://images.unsplash.com/photo-1518791841217-8f162f1e1131?auto=format&fit=crop&w=1000&q=85"),
    ("Bidu", "cachorro", 6, "pequeno", "macho",
     "Tranquilo e sociavel, perfeito para apartamento.",
     "https://images.unsplash.com/photo-1543466835-00a7907e9de1?auto=format&fit=crop&w=1000&q=85"),
    ("Luna", "cachorro", 3, "medio", "femea",
     "Muito inteligente e afetuosa, adora brincar com criancas.",
     "https://images.unsplash.com/photo-1517849845537-4d257902454a?auto=format&fit=crop&w=1000&q=85"),
    ("Simba", "gato", 2, "pequeno", "macho",
     "Gatinho curioso que adora explorar e tirar longas sonecas.",
     "https://images.unsplash.com/photo-1573865526739-10659fec78a5?auto=format&fit=crop&w=1000&q=85"),
]


def _usuario(nome, cpf_cnpj, email, cidade, data_nascimento=None) -> Usuario:
    u = Usuario(
        nome=nome,
        cpf_cnpj=cpf_cnpj,
        telefone="27999990000",
        data_nascimento=data_nascimento,
        email=email,
        senha_hash=generate_password_hash(SENHA_DEMO),
    )
    u.endereco = Endereco(
        estado="ES", cidade=cidade, bairro="Centro", rua="Rua das Flores",
        numero="100", cep="29100-000",
    )
    return u


def seed() -> bool:
    """Insere os dados de demonstracao. Retorna False se o banco ja tiver usuarios."""
    if db.session.query(Usuario.id).first():
        return False

    ong = _usuario("Abrigo Patinhas", "12.345.678/0001-90", "ong@adoptme.dev", "Vila Velha")
    ong.anunciante = Anunciante(tipo="organizacao", descricao="ONG de resgate e adocao responsavel.")

    tutora = _usuario("Ana Souza", "123.456.789-09", "ana@adoptme.dev", "Vitoria", date(1995, 5, 20))
    tutora.anunciante = Anunciante(tipo="pessoa_fisica", descricao="Protetora independente.")

    adotante = _usuario("Carlos Lima", "987.654.321-00", "carlos@adoptme.dev", "Serra", date(1990, 1, 10))

    for i, (nome, especie, idade, porte, sexo, descricao, foto) in enumerate(ANIMAIS_DEMO):
        dono = ong.anunciante if i % 2 == 0 else tutora.anunciante
        animal = Animal(nome=nome, especie=especie, idade=idade, porte=porte, sexo=sexo, descricao=descricao)
        animal.fotos.append(FotoAnimal(url=foto))
        dono.animais.append(animal)

    nina = ong.anunciante.animais[0]
    nina.interesses.append(InteresseAdocao(usuario=adotante, mensagem="Tenho quintal e experiencia com caes."))

    empresa = EmpresaParceira(nome="PetShop Amigo", telefone="2733330000", email="contato@petshopamigo.dev")
    empresa.anuncios.append(Anuncio(conteudo="10% de desconto na primeira racao!", link_destino="https://example.com/petshop"))

    db.session.add_all([ong, tutora, adotante, empresa])
    db.session.commit()
    return True
