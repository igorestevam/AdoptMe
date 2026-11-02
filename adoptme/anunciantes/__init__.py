from .routes import anunciantes_bp


def init_app(app):
    app.register_blueprint(anunciantes_bp, url_prefix="/api/anunciantes")
