import click

from .routes import mercadolivre_bp


def init_app(app):
    app.register_blueprint(mercadolivre_bp, url_prefix="/api/mercadolivre")

    @app.cli.command("ml-teste")
    @click.argument("termo", default="racao pet")
    def ml_teste(termo):
        """Testa as credenciais e a busca no Mercado Livre."""
        from . import services

        try:
            services._get_token()
            print("Token obtido com sucesso.")
            produtos = services.buscar_produtos(termo, limit=5)
        except services.MercadoLivreIndisponivel as e:
            causa = e.__cause__
            detalhe = getattr(getattr(causa, "response", None), "text", "") or causa or ""
            print(f"Falhou: {e}\n{detalhe}")
            return
        print(f"Busca por '{termo}': {len(produtos)} produto(s)")
        for p in produtos:
            preco = f"R$ {p['preco']:.2f}" if p["preco"] is not None else "sem preco"
            print(f"- {p['nome']} ({preco})\n  {p['link']}")
