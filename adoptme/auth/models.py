from datetime import datetime, date
from typing import List, Optional, TYPE_CHECKING

from sqlalchemy.orm import Mapped, mapped_column, relationship

from adoptme.ext.db import db

if TYPE_CHECKING:
    from adoptme.anunciantes.models import Anunciante
    from adoptme.animais.models import InteresseAdocao


# Usuario (conta + dados pessoais, comuns a adotantes e anunciantes)
class Usuario(db.Model):
    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    nome: Mapped[str] = mapped_column(db.String(150), nullable=False)
    cpf_cnpj: Mapped[str] = mapped_column(db.String(18), nullable=False, unique=True)
    telefone: Mapped[str] = mapped_column(db.String(20), nullable=False)
    data_nascimento: Mapped[Optional[date]] = mapped_column(db.Date)
    email: Mapped[str] = mapped_column(db.String(150), nullable=False, unique=True, index=True)
    senha_hash: Mapped[str] = mapped_column(db.String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(db.DateTime, nullable=False, server_default=db.func.now())
    updated_at: Mapped[datetime] = mapped_column(db.DateTime, nullable=False, server_default=db.func.now(), onupdate=db.func.now())

    endereco: Mapped[Optional["Endereco"]] = relationship(
        "Endereco", back_populates="usuario", uselist=False, cascade="all, delete-orphan")
    anunciante: Mapped[Optional["Anunciante"]] = relationship(
        "Anunciante", back_populates="usuario", uselist=False, cascade="all, delete-orphan")
    interesses: Mapped[List["InteresseAdocao"]] = relationship(
        "InteresseAdocao", back_populates="usuario", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Usuario id={self.id} email='{self.email}'>"


# Endereco (1:1 com Usuario)
class Endereco(db.Model):
    __tablename__ = "enderecos"

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    estado: Mapped[str] = mapped_column(db.String(2), nullable=False)
    cidade: Mapped[str] = mapped_column(db.String(100), nullable=False)
    bairro: Mapped[str] = mapped_column(db.String(100), nullable=False)
    rua: Mapped[str] = mapped_column(db.String(150), nullable=False)
    numero: Mapped[str] = mapped_column(db.String(10), nullable=False)
    cep: Mapped[str] = mapped_column(db.String(9), nullable=False)
    complemento: Mapped[Optional[str]] = mapped_column(db.String(100))
    usuario_id: Mapped[int] = mapped_column(
        db.Integer, db.ForeignKey("usuarios.id"), nullable=False, unique=True)

    usuario: Mapped["Usuario"] = relationship("Usuario", back_populates="endereco")

    def __repr__(self) -> str:
        return f"<Endereco id={self.id} cidade='{self.cidade}/{self.estado}'>"
