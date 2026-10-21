"""Publica en YouTube Shorts el siguiente Reel de cola.json.

Elección: primero los Reels publicados en Instagram hace más de 48 h, del que tiene más «me gusta»
al que tiene menos; después, los demás en el orden de la cola. Solo se usan Reels cuya música
está aprobada en youtube_musica.json (sin reclamación de Content ID).

Variables de entorno:
  YT_CLIENT_ID, YT_CLIENT_SECRET, YT_REFRESH_TOKEN   acceso a YouTube
  IG_TOKEN        (opcional) para leer los «me gusta» de Instagram
  DRY_RUN=1       no publica nada, solo muestra lo que haría
"""
import json
import os
import re
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

from youtube_comun import (COLA, ESTADO, LIBRO, RAIZ, ErrorYT, ahora, escribir, estado_video, leer,
                           pistas_validas, subir, titulos_recientes, token_acceso)

ETIQUETAS = ["amor propio", "autoexigencia", "crecimiento personal", "frases de amor propio",
             "libros en español", "No estás rota estás cansada", "Carolina Cuevas"]
AVISO = 6   # aviso cuando quedan menos de 3 días de Shorts


def limpiar(t):
    t = t.replace("*", "").replace("<", "").replace(">", "")
    return re.sub(r"\s+", " ", t).strip()


def titulo_de(post):
    if post.get("texto"):
        base = limpiar(post["texto"])
    else:
        base = limpiar(re.split(r"(?<=[.!?])\s", post["leyenda"].strip(), maxsplit=1)[0])
        base = re.sub(r"[^\w\s.,;:¡!¿?«»'’-]", "", base).strip()
    if len(base) > 95:
        base = base[:95].rsplit(" ", 1)[0].rstrip(",;:") + "…"
    return base


def descripcion_de(post):
    lineas = post["leyenda"].strip().split("\n")
    etiquetas = [l for l in lineas if l.strip().startswith("#")]
    cuerpo = [l for l in lineas if not l.strip().startswith("#")]
    texto = "\n".join(cuerpo)
    texto = re.sub(r"\s*Esta frase es de mi libro «No estás rota, estás cansada»\.?", "", texto)
    texto = re.sub(r"\s*El link está en mi perfil\.?\s*📖?", "", texto)
    texto = re.sub(r"\n{3,}", "\n\n", texto).strip()
    bloque = f"📖 «No estás rota, estás cansada», de Carolina Cuevas, en Amazon:\n{LIBRO}"
    hashtags = (etiquetas[0].strip() + " #shorts") if etiquetas else "#amorpropio #shorts"
    return f"{texto}\n\n{bloque}\n\n{hashtags}"


def me_gusta(media_id, token):
    url = f"https://graph.instagram.com/{media_id}?" + urllib.parse.urlencode(
        {"fields": "like_count", "access_token": token})
    try:
        with urllib.request.urlopen(url, timeout=30) as r:
            return int(json.loads(r.read()).get("like_count") or 0)
    except Exception:
        return None


def elegir(cola, hechos, validas, ig_token):
    candidatos = [p for p in cola if p["leyenda"] not in hechos and p.get("musica") in validas
                  and os.path.exists(os.path.join(RAIZ, "posts", p["archivo"]))]
    if not candidatos:
        return None, 0
    limite = datetime.now(timezone.utc) - timedelta(hours=48)
    maduros = [p for p in candidatos if p.get("publicado") and p.get("media_id")
               and datetime.strptime(p["publicado"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc) <= limite]
    if maduros and ig_token:
        puntos = []
        for i, p in enumerate(maduros):
            n = me_gusta(p["media_id"], ig_token)
            if n is not None:
                puntos.append((-n, i, p))
        if puntos:
            puntos.sort(key=lambda x: (x[0], x[1]))
            n, _, p = puntos[0]
            print(f"Elegido por «me gusta» en Instagram: {p['archivo']} ({-n} me gusta)")
            return p, len(candidatos)
    elegido = maduros[0] if maduros else candidatos[0]
    print(f"Elegido por orden de la cola: {elegido['archivo']}")
    return elegido, len(candidatos)


def main():
    cola = leer(COLA, [])
    estado = leer(ESTADO, {})
    validas = pistas_validas()
    if not validas:
        sys.exit("Ninguna música aprobada todavía: lanza el modo «probar_musica» y luego «validar_musica».")
    post, quedan = elegir(cola, estado, validas, os.environ.get("IG_TOKEN"))
    if not post:
        sys.exit("No queda ningún Reel para YouTube (o ninguno con música aprobada).")
    titulo, desc = titulo_de(post), descripcion_de(post)
    mp4 = os.path.join(RAIZ, "posts", post["archivo"])
    print(f"Vídeo: {post['archivo']} – {quedan} disponibles\nTítulo: {titulo}\nDescripción:\n{desc}\n")
    if os.environ.get("DRY_RUN") == "1":
        token = token_acceso()
        titulos_recientes(token)
        print("DRY_RUN: acceso a YouTube correcto ✔. No se publica nada.")
        return

    token = token_acceso()
    recientes = titulos_recientes(token)
    if titulo in recientes:
        print("Ya estaba publicado (anti-duplicado). Se marca y se sale.")
        estado[post["leyenda"]] = {"archivo": post["archivo"], "video_id": recientes[titulo], "publicado": ahora()}
        escribir(ESTADO, estado)
        return

    video = subir(token, mp4, titulo, desc, ETIQUETAS, "public")
    vid = video["id"]
    st = estado_video(token, vid) or video.get("status", {})
    privacidad = st.get("privacyStatus")
    estado[post["leyenda"]] = {"archivo": post["archivo"], "video_id": vid, "publicado": ahora(),
                               "privacidad": privacidad}
    escribir(ESTADO, estado)
    print(f"Subido: https://youtube.com/shorts/{vid} (estado: {privacidad})")
    if privacidad != "public":
        sys.exit("ATENCIÓN: YouTube ha dejado el vídeo en PRIVADO. Es el bloqueo de los proyectos de API "
                 "no auditados. No sigas publicando: avisa a Claude.")
    if quedan - 1 < AVISO:
        print(f"::warning::Quedan {quedan - 1} Reels para YouTube.")


if __name__ == "__main__":
    try:
        main()
    except ErrorYT as e:
        sys.exit(f"ERROR YouTube: {e}")
