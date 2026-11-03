from datetime import datetime
from typing import List, Optional, TYPE_CHECKING

from sqlalchemy.orm import Mapped, mapped_column, relationship

from adoptme.ext.db import db

if TYPE_CHECKING:
    from adoptme.auth.models import Usuario
    from adoptme.anunciantes.models import Anunciante


# Animal
class Animal(db.Model):
    __tablename__ = "animais"
    __table_args__ = (
        db.CheckConstraint("situacao IN ('disponivel', 'adotado')", name="ck_animais_situacao"),
    )

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    nome: Mapped[str] = mapped_column(db.String(100), nullable=False)
    especie: Mapped[str] = mapped_column(db.String(50), nullable=False)
    idade: Mapped[Optional[int]] = mapped_column(db.Integer)
    porte: Mapped[str] = mapped_column(db.String(30), nullable=False)
    sexo: Mapped[str] = mapped_column(db.String(10), nullable=False)
    descricao: Mapped[Optional[str]] = mapped_column(db.String(1000))
    situacao: Mapped[str] = mapped_column(db.String(20), nullable=False, default="disponivel")
    anunciante_id: Mapped[int] = mapped_column(
        db.Integer, db.ForeignKey("anunciantes.id"), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(db.DateTime, nullable=False, server_default=db.func.now())
    updated_at: Mapped[datetime] = mapped_column(db.DateTime, nullable=False, server_default=db.func.now(), onupdate=db.func.now())

    anunciante: Mapped["Anunciante"] = relationship("Anunciante", back_populates="animais")
    fotos: Mapped[List["FotoAnimal"]] = relationship(
        "FotoAnimal", back_populates="animal", cascade="all, delete-orphan")
    interesses: Mapped[List["InteresseAdocao"]] = relationship(
        "InteresseAdocao", back_populates="animal", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Animal id={self.id} nome='{self.nome}' situacao='{self.situacao}'>"


# FotoAnimal (um animal pode ter varias fotos)
class FotoAnimal(db.Model):
    __tablename__ = "fotos_animal"

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    url: Mapped[str] = mapped_column(db.String(255), nullable=False)
    animal_id: Mapped[int] = mapped_column(
        db.Integer, db.ForeignKey("animais.id"), nullable=False, index=True)

    animal: Mapped["Animal"] = relationship("Animal", back_populates="fotos")

    def __repr__(self) -> str:
        return f"<FotoAnimal id={self.id} animal_id={self.animal_id}>"


# InteresseAdocao (manifestacao de interesse: liga Animal e Usuario)
class InteresseAdocao(db.Model):
    __tablename__ = "interesses_adocao"

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    data_hora: Mapped[datetime] = mapped_column(db.DateTime, nullable=False, server_default=db.func.now())
    mensagem: Mapped[Optional[str]] = mapped_column(db.String(500))
    animal_id: Mapped[int] = mapped_column(
        db.Integer, db.ForeignKey("animais.id"), nullable=False, index=True)
    usuario_id: Mapped[int] = mapped_column(
        db.Integer, db.ForeignKey("usuarios.id"), nullable=False, index=True)

    animal: Mapped["Animal"] = relationship("Animal", back_populates="interesses")
    usuario: Mapped["Usuario"] = relationship("Usuario", back_populates="interesses")

    def __repr__(self) -> str:
        return f"<InteresseAdocao id={self.id} animal_id={self.animal_id} usuario_id={self.usuario_id}>"
