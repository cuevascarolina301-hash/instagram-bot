"""Prueba las músicas de musica/ contra Content ID de YouTube.

MODO=probar   sube en PRIVADO un Short de prueba por cada música distinta todavía no probada.
              Luego, en YouTube Studio → Contenido, se mira la columna «Restricciones».
MODO=validar  RECLAMADAS = números de las músicas con reclamación («2,5»), o «ninguna».
              Las demás músicas probadas pasan a «ok»; solo esas se usan en YouTube.
"""
import os
import sys

from youtube_comun import (COLA, MUSICA, RAIZ, ErrorYT, ahora, escribir, leer, md5, subir,
                           token_acceso)


def grupos_actuales(m):
    """Agrupa los archivos de musica/ idénticos (mismo contenido) y numera los grupos nuevos."""
    por_md5 = {}
    carpeta = os.path.join(RAIZ, "musica")
    for nombre in sorted(os.listdir(carpeta)):
        if nombre.lower().endswith((".mp3", ".m4a", ".wav", ".aac")):
            por_md5.setdefault(md5(os.path.join(carpeta, nombre)), []).append(nombre)
    conocidos = {g["md5"]: g for g in m["grupos"]}
    for h, nombres in por_md5.items():
        if h in conocidos:
            conocidos[h]["archivos"] = sorted(set(conocidos[h]["archivos"]) | set(nombres))
        else:
            m["grupos"].append({"n": len(m["grupos"]) + 1, "md5": h, "archivos": nombres,
                                "estado": "sin_probar"})
    return m


def probar(m):
    cola = leer(COLA, [])
    token = None
    for g in m["grupos"]:
        if g["estado"] != "sin_probar":
            continue
        post = next((p for p in cola if p.get("musica") in g["archivos"]
                     and os.path.exists(os.path.join(RAIZ, "posts", p["archivo"]))), None)
        if not post:
            print(f"Música {g['n']} ({g['archivos'][0]}): ningún Reel la usa todavía, se deja para más tarde.")
            continue
        token = token or token_acceso()
        titulo = f"PRUEBA música {g['n']}"
        v = subir(token, os.path.join(RAIZ, "posts", post["archivo"]), titulo,
                  f"Prueba privada de Content ID: {g['archivos'][0]}", [], "private")
        g.update(estado="en_prueba", video_prueba=v["id"], probado=ahora())
        print(f"Música {g['n']} ({g['archivos'][0]}) → vídeo privado {v['id']}")
        escribir(MUSICA, m)


def validar(m, reclamadas):
    txt = reclamadas.strip().lower()
    numeros = set() if txt in ("", "ninguna", "0", "no") else {int(x) for x in txt.replace(" ", "").split(",") if x}
    for g in m["grupos"]:
        if g["n"] in numeros:
            g["estado"] = "reclamada"
        elif g["estado"] == "en_prueba":
            g["estado"] = "ok"
    for g in m["grupos"]:
        print(f"Música {g['n']}: {g['estado']:<10} {', '.join(g['archivos'])}")


def main():
    m = grupos_actuales(leer(MUSICA, {"grupos": []}))
    modo = os.environ.get("MODO", "probar")
    if modo == "probar":
        probar(m)
    elif modo == "validar":
        validar(m, os.environ.get("RECLAMADAS", "ninguna"))
    else:
        sys.exit(f"Modo desconocido: {modo}")
    escribir(MUSICA, m)


if __name__ == "__main__":
    try:
        main()
    except ErrorYT as e:
        sys.exit(f"ERROR YouTube: {e}")
