"""Funciones comunes de los robots de carruseles (API de Instagram con inicio de sesión de Instagram)."""
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

API = "https://graph.instagram.com"
RAIZ = os.path.dirname(os.path.abspath(__file__))


class ErrorAPI(Exception):
    pass


def llamar(metodo, ruta, **params):
    url = f"{API}/{ruta}"
    datos = urllib.parse.urlencode(params).encode()
    req = (urllib.request.Request(url + "?" + datos.decode()) if metodo == "GET"
           else urllib.request.Request(url, data=datos, method="POST"))
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        raise ErrorAPI(f"{metodo} {ruta}: {e.code} {e.read().decode(errors='replace')}")


def base_url():
    if os.environ.get("BASE_URL"):
        return os.environ["BASE_URL"].rstrip("/")
    repo = os.environ.get("GITHUB_REPOSITORY")
    if not repo:
        sys.exit("Falta BASE_URL (o ejecutar dentro de GitHub Actions).")
    usuario, nombre = repo.split("/")
    return f"https://{usuario.lower()}.github.io/{nombre}"


def accesible(url):
    try:
        with urllib.request.urlopen(urllib.request.Request(url, method="HEAD"), timeout=30) as r:
            return r.status == 200
    except Exception:
        return False


def yo(token):
    r = llamar("GET", "me", fields="user_id,username", access_token=token)
    return r.get("user_id") or r["id"], r.get("username")


def esperar(cid, token, intentos=60):
    for _ in range(intentos):
        e = llamar("GET", cid, fields="status_code,status", access_token=token)
        if e.get("status_code") == "FINISHED":
            return
        if e.get("status_code") in ("ERROR", "EXPIRED"):
            raise ErrorAPI(f"Instagram no pudo procesar {cid}: {e}")
        time.sleep(10)
    raise ErrorAPI(f"{cid} no terminó de procesarse a tiempo.")


def leer(ruta, defecto=None):
    p = os.path.join(RAIZ, ruta)
    if not os.path.exists(p):
        return defecto
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def escribir(ruta, datos):
    with open(os.path.join(RAIZ, ruta), "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=2)


def ahora():
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
