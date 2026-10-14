"""Publica en Instagram el siguiente carrusel pendiente de carruseles/carruseles.json.

Las imágenes se sirven por GitHub Pages: <BASE_URL>/carruseles/cXX/01.jpg … 10.jpg
DRY_RUN=1 : comprueba todo sin publicar.
"""
import os
import sys
from comun import ErrorAPI, accesible, ahora, base_url, escribir, esperar, leer, llamar, yo

COLA = "carruseles/carruseles.json"


def main():
    datos = leer(COLA)
    pend = [c for c in datos["carruseles"] if not c.get("publicado")]
    if not pend:
        sys.exit("No queda ningún carrusel pendiente: hay que añadir el lote siguiente.")
    c = pend[0]
    from datetime import datetime
    from zoneinfo import ZoneInfo
    hoy = datetime.now(ZoneInfo("America/Chicago")).strftime("%Y-%m-%d")
    if c.get("no_antes") and hoy < c["no_antes"]:
        print(f"{c['id']} no se publica antes del {c['no_antes']} (hoy es {hoy} en Chicago). Nada que hacer.")
        return
    urls = [f"{base_url()}/{s}" for s in c["slides"]]
    print(f"Siguiente: {c['id']} – {c['titulo']} ({len(pend)} pendientes)")
    malas = [u for u in urls if not accesible(u)]
    if malas:
        sys.exit("Estas imágenes no son accesibles (¿GitHub Pages activado? ¿subida terminada?):\n" + "\n".join(malas))
    print("Las 10 imágenes son accesibles ✔")
    if os.environ.get("DRY_RUN") == "1":
        print("DRY_RUN: no se publica nada.\nLeyenda:\n" + c["caption"])
        return

    token = os.environ["IG_TOKEN"]
    ig_id, usuario = yo(token)
    # anti-duplicado
    for m in llamar("GET", f"{ig_id}/media", fields="id,caption", limit=5, access_token=token).get("data", []):
        if (m.get("caption") or "").strip() == c["caption"].strip():
            print("Ya estaba publicado (anti-duplicado).")
            c["publicado"], c["media_id"] = ahora(), m["id"]
            escribir(COLA, datos)
            return
    hijos = []
    for u in urls:
        h = llamar("POST", f"{ig_id}/media", image_url=u, is_carousel_item="true", access_token=token)
        esperar(h["id"], token, intentos=30)
        hijos.append(h["id"])
    cont = llamar("POST", f"{ig_id}/media", media_type="CAROUSEL", children=",".join(hijos),
                  caption=c["caption"], access_token=token)
    esperar(cont["id"], token)
    pub = llamar("POST", f"{ig_id}/media_publish", creation_id=cont["id"], access_token=token)
    c["publicado"], c["media_id"] = ahora(), pub["id"]
    escribir(COLA, datos)
    print(f"Carrusel publicado en @{usuario}: {pub['id']}")
    if len(pend) - 1 < 4:
        print(f"::warning::Quedan {len(pend) - 1} carruseles en la cola.")


if __name__ == "__main__":
    try:
        main()
    except ErrorAPI as e:
        sys.exit(f"ERROR API {e}")
