"""Gera o .zip da entrega do projeto (GrupoX_AdoptMe.zip) na pasta acima do projeto.

Uso (na raiz do projeto):
    python scripts/gerar_entrega.py --grupo 3
    python scripts/gerar_entrega.py --grupo 3 --com-env      # inclui o .env (credenciais do Mercado Livre)
    python scripts/gerar_entrega.py --grupo 3 --com-dados    # inclui o banco e as fotos de instance/

Fica de fora o que e gerado ou reinstalado (venv, __pycache__, node_modules, dist, caches).
"""
import argparse
import os
import zipfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
PASTAS_FORA = {".venv", "venv", "__pycache__", "node_modules", "dist", ".pytest_cache", "htmlcov", ".idea", ".vscode"}
ARQUIVOS_FORA = {".coverage", "CLAUDE.md"}


def deve_entrar(caminho: Path, com_env: bool, com_dados: bool) -> bool:
    relativo = caminho.relative_to(RAIZ)
    partes = relativo.parts
    if any(p in PASTAS_FORA or p.endswith(".egg-info") for p in partes):
        return False
    if partes[0] == "instance" and not com_dados:
        return False
    if partes[0] == "instance" and len(partes) > 1 and partes[1] == "logs":
        return False
    if caminho.name in ARQUIVOS_FORA or caminho.suffix == ".pyc":
        return False
    if caminho.name == ".env" and not com_env:
        return False
    return True


def main():
    parser = argparse.ArgumentParser(description="Gera o .zip da entrega do AdoptMe")
    parser.add_argument("--grupo", required=True, help="numero do grupo (ex.: 3)")
    parser.add_argument("--com-env", action="store_true", help="inclui o .env com as credenciais")
    parser.add_argument("--com-dados", action="store_true", help="inclui instance/ (banco e fotos)")
    args = parser.parse_args()

    destino = RAIZ.parent / f"Grupo{args.grupo}_AdoptMe.zip"
    total = 0
    with zipfile.ZipFile(destino, "w", zipfile.ZIP_DEFLATED) as z:
        for pasta, subpastas, arquivos in os.walk(RAIZ):
            subpastas[:] = [s for s in subpastas if s not in PASTAS_FORA]
            for nome in arquivos:
                caminho = Path(pasta) / nome
                if deve_entrar(caminho, args.com_env, args.com_dados):
                    z.write(caminho, Path("AdoptMe") / caminho.relative_to(RAIZ))
                    total += 1

    print(f"{destino} gerado com {total} arquivos ({destino.stat().st_size / 1024 / 1024:.1f} MB)")
    if not args.com_env:
        print("Sem o .env: para ver os produtos do Mercado Livre, quem rodar precisa preencher as credenciais.")


if __name__ == "__main__":
    main()
