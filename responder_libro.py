"""ENSAYO: responde por mensaje privado a quien comenta «LIBRO» en un post de los últimos 7 días.

Instagram solo permite 1 mensaje privado por comentario, dentro de los 7 días.
Si la API lo rechaza (permiso, app en modo desarrollo…), el robot NO insiste: lo apunta en
respuestas/estado.json y lista los comentarios para responder a mano.
"""
import json
import os
import re
import sys
from datetime import datetime, timedelta, timezone
from comun import ErrorAPI, ahora, escribir, leer, llamar, yo

ENLACE = os.environ.get("ENLACE_LIBRO", "https://www.amazon.com/dp/B0HJ564B3W")
MENSAJE = ("¡Hola! 🧡 Gracias por tu comentario. Aquí tienes el libro "
           "«No estás rota, estás cansada»: " + ENLACE)
PALABRA = re.compile(r"\blibro\b", re.I)


def main():
    token = os.environ["IG_TOKEN"]
    ig_id, _ = yo(token)
    estado = leer("respuestas/estado.json", {"respondidos": [], "pendientes_a_mano": [], "api_ok": None})
    hace7 = datetime.now(timezone.utc) - timedelta(days=7)
    medios = llamar("GET", f"{ig_id}/media", fields="id,timestamp,permalink", limit=25, access_token=token)["data"]
    nuevos = []
    for m in medios:
        if datetime.strptime(m["timestamp"][:19], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc) < hace7:
            continue
        coms = llamar("GET", f"{m['id']}/comments", fields="id,text,username,timestamp", limit=50, access_token=token)
        for c in coms.get("data", []):
            if PALABRA.search(c.get("text", "")) and c["id"] not in estado["respondidos"] \
                    and c["id"] not in [p["id"] for p in estado["pendientes_a_mano"]]:
                nuevos.append({**c, "post": m.get("permalink")})
    print(f"{len(nuevos)} comentario(s) nuevo(s) con «LIBRO».")
    for c in nuevos:
        if estado["api_ok"] is False:
            estado["pendientes_a_mano"].append(c); continue
        try:
            llamar("POST", f"{ig_id}/messages", recipient=json.dumps({"comment_id": c["id"]}),
                   message=json.dumps({"text": MENSAJE}), access_token=token)
            estado["respondidos"].append(c["id"]); estado["api_ok"] = True
            print(f"✔ enviado a @{c.get('username')}")
        except ErrorAPI as e:
            estado["api_ok"] = False; estado["error"] = str(e)[:500]; estado["pendientes_a_mano"].append(c)
            print(f"✘ La API no deja enviar el mensaje: {e}\n→ Responder a mano.")
    estado["ultima_revision"] = ahora()
    os.makedirs("respuestas", exist_ok=True)
    escribir("respuestas/estado.json", estado)
    if estado["pendientes_a_mano"]:
        print("\nPARA RESPONDER A MANO:")
        for c in estado["pendientes_a_mano"]:
            print(f"  @{c.get('username')}: «{c.get('text')}» – {c.get('post')}")


if __name__ == "__main__":
    try:
        main()
    except ErrorAPI as e:
        sys.exit(f"ERROR API {e}")
