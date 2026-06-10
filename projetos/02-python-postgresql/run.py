"""
BanVic 360 -- Projeto 2 -- Ponto de entrada CLI

Uso:
    python projetos/02-python-postgresql/run.py
    python projetos/02-python-postgresql/run.py --etapa silver
    python projetos/02-python-postgresql/run.py --etapa gold_dims gold_fatos
"""
import argparse
import sys
from pathlib import Path

# Permite importar o modulo etl independente de onde o script e chamado
sys.path.insert(0, str(Path(__file__).parent))

from etl.pipeline import ETAPAS, run_pipeline  # noqa: E402


def main():
    parser = argparse.ArgumentParser(
        description="BanVic 360 -- Projeto 2: Python + PostgreSQL"
    )
    parser.add_argument(
        "--etapa",
        nargs="+",
        choices=ETAPAS,
        default=None,
        metavar="ETAPA",
        help=f"Etapas a executar: {ETAPAS}. Padrao: todas.",
    )
    args = parser.parse_args()
    run_pipeline(etapas=args.etapa)


if __name__ == "__main__":
    main()
