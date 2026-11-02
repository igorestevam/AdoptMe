from .routes import parceiros_bp


def init_app(app):
    app.register_blueprint(parceiros_bp, url_prefix="/api/parceiros")
