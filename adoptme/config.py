import os


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-adoptme")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///adoptme.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DEBUG = True

    # Integracao Mercado Livre (registrar aplicacao no portal de desenvolvedores)
    ML_CLIENT_ID = os.getenv("ML_CLIENT_ID", "")
    ML_CLIENT_SECRET = os.getenv("ML_CLIENT_SECRET", "")
    ML_SITE_ID = os.getenv("ML_SITE_ID", "MLB")  # Brasil


class TestConfig(Config):
    TESTING = True
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = "sqlite://"  # banco em memoria, recriado a cada teste
