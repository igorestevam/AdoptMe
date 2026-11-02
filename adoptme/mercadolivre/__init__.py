from .routes import mercadolivre_bp


def init_app(app):
    app.register_blueprint(mercadolivre_bp, url_prefix="/api/mercadolivre")
