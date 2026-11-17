"""Configuracao de logging da aplicacao.

Todos os modulos usam logging.getLogger(__name__); como os nomes comecam com
"adoptme", as mensagens chegam aos handlers configurados aqui.
"""
import logging
import os
from logging.handlers import RotatingFileHandler

FORMATO = "%(asctime)s %(levelname)s [%(name)s] %(message)s"


def configurar_logging(app):
    logger = logging.getLogger("adoptme")
    logger.setLevel(app.config.get("LOG_LEVEL", "INFO"))
    logger.handlers.clear()

    # nos testes as mensagens seguem para o pytest (caplog), sem arquivo
    if app.testing:
        logger.propagate = True
        return logger

    formato = logging.Formatter(FORMATO)
    terminal = logging.StreamHandler()
    terminal.setFormatter(formato)
    logger.addHandler(terminal)

    pasta = os.path.join(app.instance_path, "logs")
    os.makedirs(pasta, exist_ok=True)
    arquivo = RotatingFileHandler(os.path.join(pasta, "adoptme.log"), maxBytes=1_000_000,
                                  backupCount=3, encoding="utf-8")
    arquivo.setFormatter(formato)
    logger.addHandler(arquivo)

    logger.propagate = False
    return logger
