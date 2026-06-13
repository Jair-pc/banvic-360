"""
BanVic 360 - Projeto 8 - n8n
Automacao completa: build, Bronze, owner setup, workflows, execucao e validacao.

Uso (da raiz do projeto):
    python projetos/08-n8n/run_automacao.py
"""
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import requests

ROOT        = Path(__file__).parent.parent.parent
COMPOSE_F   = str(ROOT / "projetos/08-n8n/docker-compose.yml")
N8N_URL     = "http://localhost:5678"
BASIC_AUTH  = ("admin", "banvic2024")
CRED_NAME   = "BanVic PostgreSQL"

# Credenciais do dono n8n (user management interno)
OWNER_EMAIL = "admin@banvic.com"
OWNER_PASS  = "Banvic2024!"
OWNER_FIRST = "Admin"
OWNER_LAST  = "BanVic"


def log(msg):
    print(msg, flush=True)


def run_cmd(args, env_extra=None, **kwargs):
    env = os.environ.copy()
    if env_extra:
        env.update(env_extra)
    return subprocess.run(args, shell=True, env=env, **kwargs)


# ── Helpers n8n healthcheck ───────────────────────────────────────────────────

def wait_n8n(timeout=240):
    log("  Aguardando n8n inicializar...")
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            r = requests.get(f"{N8N_URL}/healthz", timeout=3)
            if r.status_code == 200:
                log("  n8n OK!")
                return True
        except Exception:
            pass
        time.sleep(5)
    return False


# ── Autenticacao n8n 1.x (owner setup + session cookie) ──────────────────────

def setup_n8n_session() -> requests.Session | None:
    """
    Configura owner n8n se necessario, faz login e retorna Session autenticada.
    Usa /rest/ interno com basic auth + session cookie.
    """
    s = requests.Session()
    s.auth = BASIC_AUTH

    # 1. Verificar se owner ja esta configurado
    try:
        r = s.get(f"{N8N_URL}/rest/settings", timeout=5)
        show_setup = r.json().get("data", {}).get("userManagement", {}).get("showSetupOnFirstLoad", True)
    except Exception:
        show_setup = True

    # 2. Configurar owner se necessario
    if show_setup:
        log("  Configurando owner n8n...")
        r = s.post(f"{N8N_URL}/rest/owner/setup", json={
            "email":     OWNER_EMAIL,
            "firstName": OWNER_FIRST,
            "lastName":  OWNER_LAST,
            "password":  OWNER_PASS,
        })
        if r.status_code in (200, 201):
            log("  Owner criado.")
        else:
            log(f"  Owner setup: {r.status_code} (pode ja existir) — continuando...")

    # 3. Login para obter session cookie
    r = s.post(f"{N8N_URL}/rest/login", json={
        "email":    OWNER_EMAIL,
        "password": OWNER_PASS,
    })
    if r.status_code != 200:
        log(f"  ERRO login n8n: {r.status_code} — {r.text[:200]}")
        return None

    # n8n 1.x define o cookie n8n-auth com Secure=True mesmo em HTTP.
    # Python nao envia cookies Secure em conexoes HTTP — forcar sem Secure.
    for cookie in r.cookies:
        if cookie.name == "n8n-auth":
            s.cookies.set("n8n-auth", cookie.value,
                          domain="localhost", path="/", secure=False)
    log("  Login n8n OK.")
    return s


# ── Helpers n8n REST (/rest/ interno, aceita basic auth + session cookie) ─────

def get_or_create_credential(s: requests.Session) -> str | None:
    # Verificar se ja existe
    r = s.get(f"{N8N_URL}/rest/credentials")
    if r.status_code == 200:
        for c in r.json().get("data", []):
            if c.get("name") == CRED_NAME:
                log(f"  Credencial ja existe: id={c['id']}")
                return str(c["id"])

    payload = {
        "name": CRED_NAME,
        "type": "postgres",
        "data": {
            "host":     "postgres",
            "port":     5432,
            "database": "banvic",
            "user":     "banvic_user",
            "password": "banvic_pass",
            "ssl":      "disable",
        },
        "nodesAccess": [],
    }
    r = s.post(f"{N8N_URL}/rest/credentials", json=payload)
    if r.status_code in (200, 201):
        cred_id = str(r.json().get("id") or r.json().get("data", {}).get("id"))
        log(f"  Credencial criada: id={cred_id}")
        return cred_id
    log(f"  ERRO criar credencial: {r.status_code} — {r.text[:300]}")
    return None


def import_workflow(path: Path, cred_id: str, s: requests.Session) -> str | None:
    raw = path.read_text(encoding="utf-8")
    raw = raw.replace('"id": "banvic-pg-cred"', f'"id": "{cred_id}"')
    wf  = json.loads(raw)

    # Se ja existe, deletar para reimportar (garante versao atualizada)
    r = s.get(f"{N8N_URL}/rest/workflows")
    if r.status_code == 200:
        for existing in r.json().get("data", []):
            if existing.get("name") == wf.get("name"):
                old_id = str(existing["id"])
                s.delete(f"{N8N_URL}/rest/workflows/{old_id}")
                log(f"  '{wf['name']}': removido id={old_id} para reimportar")

    # Importar — sem ID fixo (deixa n8n gerar)
    wf.pop("id", None)
    wf.setdefault("settings", {})
    wf.setdefault("staticData", None)
    wf["active"] = False

    r = s.post(f"{N8N_URL}/rest/workflows", json=wf)
    if r.status_code in (200, 201):
        resp  = r.json()
        wf_id = str(resp.get("id") or resp.get("data", {}).get("id"))
        log(f"  '{wf['name']}': importado (id={wf_id})")
        return wf_id
    log(f"  ERRO importar {path.name}: {r.status_code} — {r.text[:300]}")
    return None


def run_workflow_cli(wf_id: str, label: str, timeout=300) -> bool:
    """Executa workflow via n8n CLI (docker exec). Mais confiavel que REST /run."""
    import subprocess as _sp
    log(f"  Executando {label} via CLI (id={wf_id})...")
    try:
        result = run_cmd(
            f"docker exec banvic-p08-n8n n8n execute --id={wf_id}",
            capture_output=True, text=True, timeout=timeout,
        )
    except _sp.TimeoutExpired:
        log(f"  {label}: TIMEOUT ({timeout}s)")
        return False
    output = (result.stdout or "") + (result.stderr or "")
    if "Error executing workflow" in output or result.returncode != 0:
        for line in output.splitlines()[-6:]:
            if line.strip() and not line.startswith("{"):
                log(f"    {line}")
        log(f"  {label}: status=error")
        return False
    log(f"  {label}: status=success")
    return True


# ── Bronze loader ─────────────────────────────────────────────────────────────

def load_bronze():
    """Carrega Bronze no postgres do P08 (porta 5434) diretamente do host."""
    log("  Rodando carga_bronze.py apontando para porta 5434...")
    result = run_cmd(
        f'"{sys.executable}" scripts/carga_bronze.py',
        env_extra={
            "PG_HOST":     "localhost",
            "PG_PORT":     "5434",
            "PG_DB":       "banvic",
            "PG_USER":     "banvic_user",
            "PG_PASSWORD": "banvic_pass",
        },
        cwd=str(ROOT),
        capture_output=True, text=True,
    )
    if result.returncode == 0:
        log("  Bronze: OK")
        return True
    log(f"  Bronze ERRO:\n{result.stderr[-400:]}")
    return False


# ── main ─────────────────────────────────────────────────────────────────────

def main():
    log("=" * 60)
    log("BanVic 360 - Projeto 8: n8n (postgres isolado)")
    log("=" * 60)

    # 1. Build + start
    log("\n[1/6] Build + start (postgres + n8n)...")
    r = run_cmd(f'docker compose -f "{COMPOSE_F}" up -d --build', cwd=str(ROOT))
    if r.returncode != 0:
        log("ERRO: falha ao subir containers")
        sys.exit(1)

    # 2. Aguardar n8n
    log("\n[2/6] Aguardando n8n...")
    if not wait_n8n():
        log("ERRO: n8n nao respondeu. Verifique os logs abaixo:")
        run_cmd(f'docker compose -f "{COMPOSE_F}" logs n8n --tail 30', cwd=str(ROOT))
        sys.exit(1)
    time.sleep(5)

    # 3. Carregar Bronze (porta 5434)
    log("\n[3/6] Carregando Bronze no postgres do P08...")
    if not load_bronze():
        log("  Continuando mesmo com erro no Bronze (pode ja estar carregado)")

    # 4. Autenticar na API n8n
    log("\n[4/6] Autenticando na API n8n (owner setup + session)...")
    session = setup_n8n_session()
    if not session:
        sys.exit(1)

    # 5. Criar credencial + importar workflows
    log("\n[5/6] Configurando credencial e importando workflows...")
    cred_id = get_or_create_credential(session)
    if not cred_id:
        sys.exit(1)

    wf_dir  = ROOT / "projetos/08-n8n/workflows"
    wf1_id  = import_workflow(wf_dir / "01_pipeline_banvic.json", cred_id, session)
    wf2_id  = import_workflow(wf_dir / "02_validar_kpis.json",    cred_id, session)

    # 6. Executar via CLI
    log("\n[6/6] Executando workflows via n8n CLI...")

    if wf1_id:
        log("\n  >> Pipeline ETL Completo (Bronze -> Silver -> Gold -> KPI1)...")
        ok1 = run_workflow_cli(wf1_id, "Pipeline ETL", timeout=300)
        if not ok1:
            log("  Verifique os logs: http://localhost:5678")

    if wf2_id:
        log("\n  >> Validacao KPIs standalone...")
        run_workflow_cli(wf2_id, "Validacao KPIs", timeout=120)

    log("\n" + "=" * 60)
    log("n8n ativo em:  http://localhost:5678")
    log("Login:         admin@banvic.com / Banvic2024!")
    log("=" * 60)
    log("\nPara parar:")
    log(f'  docker compose -f projetos/08-n8n/docker-compose.yml down')


if __name__ == "__main__":
    main()
