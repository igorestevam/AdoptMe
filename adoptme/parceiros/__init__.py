from datetime import datetime, timedelta

import click

from .routes import parceiros_bp


def init_app(app):
    app.register_blueprint(parceiros_bp, url_prefix="/api/parceiros")

    # A equipe da plataforma cadastra empresas e anuncios pelo terminal, ex.:
    #   flask --app app.py nova-empresa "PetShop Amigo" "27 3333-0000" --email contato@petshop.com
    #   flask --app app.py novo-anuncio 1 "10% de desconto na primeira racao" https://petshop.com/promo
    #   flask --app app.py anuncios
    #   flask --app app.py relatorio-cliques --de 2026-11-01 --ate 2026-11-30

    @app.cli.command("nova-empresa")
    @click.argument("nome")
    @click.argument("telefone")
    @click.option("--email", default=None)
    def nova_empresa(nome, telefone, email):
        """Cadastra uma empresa parceira."""
        from . import services

        try:
            empresa = services.cadastrar_empresa(nome, telefone, email)
        except ValueError as e:
            raise click.ClickException(str(e))
        click.echo(f"Empresa {empresa.id} cadastrada: {empresa.nome}")

    @app.cli.command("novo-anuncio")
    @click.argument("empresa_id", type=int)
    @click.argument("conteudo")
    @click.argument("link")
    def novo_anuncio(empresa_id, conteudo, link):
        """Cadastra um anuncio de uma empresa parceira."""
        from . import services

        try:
            anuncio = services.cadastrar_anuncio(empresa_id, conteudo, link)
        except ValueError as e:
            raise click.ClickException(str(e))
        click.echo(f"Anuncio {anuncio.id} cadastrado para {anuncio.empresa.nome}")

    @app.cli.command("anuncios")
    def anuncios():
        """Lista as empresas parceiras e seus anuncios."""
        from adoptme.ext.db import db
        from .models import EmpresaParceira

        empresas = db.session.query(EmpresaParceira).order_by(EmpresaParceira.id).all()
        if not empresas:
            click.echo("Nenhuma empresa parceira cadastrada.")
        for e in empresas:
            click.echo(f"[{e.id}] {e.nome} - {e.telefone}" + (f" - {e.email}" if e.email else ""))
            for a in e.anuncios:
                click.echo(f"    anuncio {a.id}: {a.conteudo} -> {a.link_destino} ({len(a.cliques)} cliques)")

    @app.cli.command("relatorio-cliques")
    @click.option("--de", "inicio", type=click.DateTime(["%Y-%m-%d"]), help="Data inicial (AAAA-MM-DD)")
    @click.option("--ate", "fim", type=click.DateTime(["%Y-%m-%d"]), help="Data final, inclusive (AAAA-MM-DD)")
    def relatorio_cliques(inicio, fim):
        """Mostra os cliques por anuncio e por empresa (base da cobranca por clique)."""
        from . import services

        linhas = services.relatorio_cliques(inicio, fim + timedelta(days=1) if fim else None)
        periodo = f"{inicio:%d/%m/%Y}" if inicio else "inicio"
        periodo += f" a {fim:%d/%m/%Y}" if fim else " ate hoje"
        click.echo(f"Cliques de {periodo} (horario UTC):")
        total_empresa = {}
        for l in linhas:
            total_empresa[l["empresa"]] = total_empresa.get(l["empresa"], 0) + l["cliques"]
            click.echo(f"  {l['empresa']} - anuncio {l['anuncio_id']} ({l['conteudo'][:40]}): {l['cliques']}")
        click.echo("Total por empresa:")
        for empresa, total in total_empresa.items():
            click.echo(f"  {empresa}: {total}")
