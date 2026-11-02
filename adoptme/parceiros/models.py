from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Mapped, mapped_column, relationship

from adoptme.ext.db import db


# EmpresaParceira (anunciante de produtos)
class EmpresaParceira(db.Model):
    __tablename__ = "empresas_parceiras"

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    nome: Mapped[str] = mapped_column(db.String(150), nullable=False)
    telefone: Mapped[str] = mapped_column(db.String(20), nullable=False)
    email: Mapped[Optional[str]] = mapped_column(db.String(150))

    anuncios: Mapped[List["Anuncio"]] = relationship(
        "Anuncio", back_populates="empresa", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<EmpresaParceira id={self.id} nome='{self.nome}'>"


# Anuncio (de uma empresa parceira)
class Anuncio(db.Model):
    __tablename__ = "anuncios"

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    conteudo: Mapped[str] = mapped_column(db.String(500), nullable=False)
    link_destino: Mapped[str] = mapped_column(db.String(255), nullable=False)
    empresa_parceira_id: Mapped[int] = mapped_column(
        db.Integer, db.ForeignKey("empresas_parceiras.id"), nullable=False, index=True)

    empresa: Mapped["EmpresaParceira"] = relationship("EmpresaParceira", back_populates="anuncios")
    cliques: Mapped[List["CliqueAnuncio"]] = relationship(
        "CliqueAnuncio", back_populates="anuncio", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Anuncio id={self.id} empresa_parceira_id={self.empresa_parceira_id}>"


# CliqueAnuncio (registro de clique - base para a cobranca CPC)
class CliqueAnuncio(db.Model):
    __tablename__ = "cliques_anuncio"

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    data_hora: Mapped[datetime] = mapped_column(db.DateTime, nullable=False, server_default=db.func.now())
    sessao: Mapped[Optional[str]] = mapped_column(db.String(100))
    anuncio_id: Mapped[int] = mapped_column(
        db.Integer, db.ForeignKey("anuncios.id"), nullable=False, index=True)

    anuncio: Mapped["Anuncio"] = relationship("Anuncio", back_populates="cliques")

    def __repr__(self) -> str:
        return f"<CliqueAnuncio id={self.id} anuncio_id={self.anuncio_id}>"
