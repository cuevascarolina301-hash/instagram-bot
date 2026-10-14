"""Publica el siguiente Reel-versión de carrusel, en orden A1, B1, A2, B2…

TRIAL=1 : como Trial Reel (solo a partir de 1 000 seguidores). Si no, Reel normal.

Instagram lo enseña después a tus seguidoras si funciona bien (graduation_strategy = SS_PERFORMANCE).
Orden: A y B del mismo carrusel salen el mismo día (mañana y tarde) para compararlas en igualdad.
DRY_RUN=1 : comprueba sin publicar.
"""
import json
import os
import sys
from comun import ErrorAPI, accesible, ahora, base_url, escribir, esperar, leer, llamar, yo


def main():
    cola = leer("trial/trial_cola.json", [])
    pend = [t for t in cola if not t.get("publicado")]
    if not pend:
        sys.exit("No hay Trial Reels pendientes: lanza «Fabricar Trial Reels».")
    t = pend[0]
    url = f"{base_url()}/{t['archivo']}"
    print(f"Siguiente: {t['id']} (gancho {t['gancho']}) – {len(pend)} pendientes\n{url}")
    if not accesible(url):
        sys.exit("El vídeo no es accesible por GitHub Pages.")
    if os.environ.get("DRY_RUN") == "1":
        print("DRY_RUN: no se publica nada.")
        return
    token = os.environ["IG_TOKEN"]
    ig_id, usuario = yo(token)
    extra = {}
    if os.environ.get("TRIAL") == "1":      # solo a partir de 1 000 seguidores
        extra["trial_params"] = json.dumps({"graduation_strategy": "SS_PERFORMANCE"})
    else:
        extra["share_to_feed"] = "true"
    cont = llamar("POST", f"{ig_id}/media", media_type="REELS", video_url=url, caption=t["caption"],
                  access_token=token, **extra)
    esperar(cont["id"], token)
    pub = llamar("POST", f"{ig_id}/media_publish", creation_id=cont["id"], access_token=token)
    t["publicado"], t["media_id"] = ahora(), pub["id"]
    escribir("trial/trial_cola.json", cola)
    print(f"Reel {t['id']} publicado en @{usuario}: {pub['id']}")


if __name__ == "__main__":
    try:
        main()
    except ErrorAPI as e:
        sys.exit(f"ERROR API {e}")
