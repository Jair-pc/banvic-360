"""
BanVic 360 -- Projeto 2 -- Orquestrador do Pipeline
Executa Bronze -> Silver -> Gold em sequencia, com timing por etapa.
"""
import time

from .conexao import get_engine
from .gold_dims import popular_dims
from .gold_fatos import popular_fatos
from .silver import transformar_silver

ETAPAS = ["silver", "gold_dims", "gold_fatos"]


def _cronometrar(nome: str, fn, *args, **kwargs):
    inicio = time.time()
    resultado = fn(*args, **kwargs)
    elapsed = time.time() - inicio
    print(f"[{nome}] concluido em {elapsed:.1f}s")
    return resultado


def run_pipeline(etapas: list[str] | None = None, engine=None):
    if engine is None:
        engine = get_engine()

    if etapas is None:
        etapas = ETAPAS

    print("=" * 55)
    print("BanVic 360 -- Projeto 2: Python + PostgreSQL")
    print("=" * 55)

    inicio_total = time.time()

    if "silver" in etapas:
        print("\n[1/3] Transformando Silver (pandas)...")
        _cronometrar("silver", transformar_silver, engine)

    if "gold_dims" in etapas:
        print("\n[2/3] Populando Gold Dims (pandas + SQLAlchemy)...")
        _cronometrar("gold_dims", popular_dims, engine)

    if "gold_fatos" in etapas:
        print("\n[3/3] Populando Gold Fatos (pandas + merge)...")
        _cronometrar("gold_fatos", popular_fatos, engine)

    total = time.time() - inicio_total
    print(f"\nPipeline completo em {total:.1f}s")
    print("Execute 'python scripts/validar_gabarito_pg.py' para validar os KPIs.")
    print("=" * 55)
