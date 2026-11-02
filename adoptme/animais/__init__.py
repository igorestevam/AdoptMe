from .routes import animais_bp


def init_app(app):
    app.register_blueprint(animais_bp, url_prefix="/api/animais")
