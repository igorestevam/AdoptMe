from typing import List, Optional, TYPE_CHECKING

from sqlalchemy.orm import Mapped, mapped_column, relationship

from adoptme.ext.db import db

if TYPE_CHECKING:
    from adoptme.auth.models import Usuario
    from adoptme.animais.models import Animal


# Anunciante (perfil de quem divulga animais; vinculado a um Usuario)
class Anunciante(db.Model):
    __tablename__ = "anunciantes"
    __table_args__ = (
        db.CheckConstraint("tipo IN ('organizacao', 'pessoa_fisica')", name="ck_anunciantes_tipo"),
    )

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    tipo: Mapped[str] = mapped_column(db.String(20), nullable=False)  # organizacao | pessoa_fisica
    descricao: Mapped[Optional[str]] = mapped_column(db.String(500))
    usuario_id: Mapped[int] = mapped_column(
        db.Integer, db.ForeignKey("usuarios.id"), nullable=False, unique=True)

    usuario: Mapped["Usuario"] = relationship("Usuario", back_populates="anunciante")
    animais: Mapped[List["Animal"]] = relationship(
        "Animal", back_populates="anunciante", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Anunciante id={self.id} tipo='{self.tipo}'>"
