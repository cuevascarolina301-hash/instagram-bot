"""Funciones comunes del robot de YouTube Shorts (API de datos de YouTube v3, OAuth con refresh token)."""
import hashlib
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

RAIZ = os.path.dirname(os.path.abspath(__file__))
API = "https://www.googleapis.com/youtube/v3"
SUBIDA = "https://www.googleapis.com/upload/youtube/v3/videos"
ESTADO = os.path.join(RAIZ, "youtube_estado.json")
MUSICA = os.path.join(RAIZ, "youtube_musica.json")
COLA = os.path.join(RAIZ, "cola.json")
LIBRO = "https://www.amazon.com/dp/B0HJ564B3W"


class ErrorYT(Exception):
    pass


def leer(ruta, defecto):
    if not os.path.exists(ruta):
        return defecto
    with open(ruta, encoding="utf-8") as f:
        return json.load(f)


def escribir(ruta, datos):
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=2)
        f.write("\n")


def ahora():
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _peticion(req, intentos=3):
    for i in range(intentos):
        try:
            with urllib.request.urlopen(req, timeout=300) as r:
                cuerpo = r.read()
                return r, (json.loads(cuerpo) if cuerpo else {})
        except urllib.error.HTTPError as e:
            texto = e.read().decode(errors="replace")
            if e.code >= 500 and i < intentos - 1:
                time.sleep(10 * (i + 1))
                continue
            raise ErrorYT(f"{req.get_method()} {req.full_url.split('?')[0]}: {e.code} {texto}")
        except urllib.error.URLError as e:
            if i < intentos - 1:
                time.sleep(10 * (i + 1))
                continue
            raise ErrorYT(f"Red: {e}")


def token_acceso():
    faltan = [k for k in ("YT_CLIENT_ID", "YT_CLIENT_SECRET", "YT_REFRESH_TOKEN") if not os.environ.get(k)]
    if faltan:
        raise ErrorYT("Faltan los secretos de GitHub: " + ", ".join(faltan))
    datos = urllib.parse.urlencode({
        "client_id": os.environ["YT_CLIENT_ID"].strip(),
        "client_secret": os.environ["YT_CLIENT_SECRET"].strip(),
        "refresh_token": os.environ["YT_REFRESH_TOKEN"].strip(),
        "grant_type": "refresh_token",
    }).encode()
    req = urllib.request.Request("https://oauth2.googleapis.com/token", data=datos, method="POST")
    _, r = _peticion(req)
    return r["access_token"]


def api(token, metodo, ruta, **params):
    url = f"{API}/{ruta}?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, method=metodo, headers={"Authorization": f"Bearer {token}"})
    _, r = _peticion(req)
    return r


def subir(token, mp4, titulo, descripcion, etiquetas, privacidad):
    """Subida reanudable (resumable). Devuelve el recurso vídeo que devuelve YouTube."""
    meta = {
        "snippet": {
            "title": titulo,
            "description": descripcion,
            "tags": etiquetas,
            "categoryId": "22",
            "defaultLanguage": "es",
            "defaultAudioLanguage": "es",
        },
        "status": {
            "privacyStatus": privacidad,
            "selfDeclaredMadeForKids": False,
            "containsSyntheticMedia": False,
            "embeddable": True,
        },
    }
    tam = os.path.getsize(mp4)
    req = urllib.request.Request(
        SUBIDA + "?uploadType=resumable&part=snippet,status",
        data=json.dumps(meta).encode(), method="POST",
        headers={"Authorization": f"Bearer {token}",
                 "Content-Type": "application/json; charset=UTF-8",
                 "X-Upload-Content-Length": str(tam),
                 "X-Upload-Content-Type": "video/mp4"})
    resp, _ = _peticion(req)
    destino = resp.headers.get("Location")
    if not destino:
        raise ErrorYT("YouTube no devolvió la dirección de subida.")
    with open(mp4, "rb") as f:
        contenido = f.read()
    req = urllib.request.Request(destino, data=contenido, method="PUT",
                                 headers={"Authorization": f"Bearer {token}",
                                          "Content-Type": "video/mp4",
                                          "Content-Length": str(tam)})
    _, video = _peticion(req)
    return video


def titulos_recientes(token, n=15):
    canal = api(token, "GET", "channels", part="contentDetails", mine="true")
    items = canal.get("items") or []
    if not items:
        raise ErrorYT("Esta cuenta de Google no tiene canal de YouTube.")
    lista = items[0]["contentDetails"]["relatedPlaylists"]["uploads"]
    try:
        r = api(token, "GET", "playlistItems", part="snippet", playlistId=lista, maxResults=n)
    except ErrorYT as e:
        if " 404 " in str(e):      # canal sin vídeos todavía
            return {}
        raise
    return {i["snippet"]["title"].strip(): i["snippet"]["resourceId"]["videoId"] for i in r.get("items", [])}


def estado_video(token, video_id):
    r = api(token, "GET", "videos", part="status", id=video_id)
    items = r.get("items") or []
    return items[0]["status"] if items else {}


def md5(ruta):
    h = hashlib.md5()
    with open(ruta, "rb") as f:
        for bloque in iter(lambda: f.read(1 << 20), b""):
            h.update(bloque)
    return h.hexdigest()


def pistas_validas():
    """Nombres de las pistas de música aprobadas (sin reclamación de Content ID)."""
    m = leer(MUSICA, {"grupos": []})
    return {nombre for g in m["grupos"] if g.get("estado") == "ok" for nombre in g["archivos"]}
