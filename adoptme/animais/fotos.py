"""Fotos de animais enviadas pelo anunciante (guardadas em instance/uploads)."""
import os
import uuid

from flask import current_app

URL_FOTOS = "/api/animais/fotos/"

# os primeiros bytes de cada formato aceito
ASSINATURAS = {
    b"\xff\xd8\xff": "jpg",
    b"\x89PNG\r\n\x1a\n": "png",
    b"GIF87a": "gif",
    b"GIF89a": "gif",
}


def pasta() -> str:
    caminho = current_app.config["UPLOAD_FOLDER"]
    os.makedirs(caminho, exist_ok=True)
    return caminho


def _formato(inicio: bytes) -> str | None:
    if inicio[:4] == b"RIFF" and inicio[8:12] == b"WEBP":
        return "webp"
    for assinatura, extensao in ASSINATURAS.items():
        if inicio.startswith(assinatura):
            return extensao
    return None


def salvar_foto(arquivo) -> str:
    """Grava a imagem com um nome aleatorio e devolve a URL publica dela."""
    extensao = _formato(arquivo.stream.read(12))
    if not extensao:
        raise ValueError("Envie uma imagem JPG, PNG, WEBP ou GIF")
    arquivo.stream.seek(0)
    nome = f"{uuid.uuid4().hex}.{extensao}"
    arquivo.save(os.path.join(pasta(), nome))
    return URL_FOTOS + nome


def apagar_fotos(urls):
    """Apaga do disco as fotos enviadas (as fotos por link nao sao tocadas)."""
    for url in urls:
        if url.startswith(URL_FOTOS):
            caminho = os.path.join(pasta(), os.path.basename(url))
            if os.path.isfile(caminho):
                os.remove(caminho)
