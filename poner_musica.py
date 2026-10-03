"""Añade música a los Reels que aún no se han publicado.

Coge los archivos .mp3 / .m4a / .wav de la carpeta musica/ y los reparte por turnos entre los Reels
pendientes, con entrada y salida suaves. Los Reels ya publicados no se tocan.
"""
import glob
import json
import os
import subprocess
import sys

RAIZ = os.path.dirname(os.path.abspath(__file__))
COLA = os.path.join(RAIZ, "cola.json")
VOLUMEN = 0.6   # la música acompaña, no tapa


def main():
    pistas = sorted(p for ext in ("mp3", "m4a", "wav", "aac")
                    for p in glob.glob(os.path.join(RAIZ, "musica", f"*.{ext}")))
    if not pistas:
        sys.exit("No hay música en la carpeta musica/. Nada que hacer.")
    with open(COLA, encoding="utf-8") as f:
        cola = json.load(f)

    hechos = 0
    pendientes = [p for p in cola if not p.get("publicado")]
    for i, post in enumerate(pendientes):
        pista = pistas[i % len(pistas)]
        nombre_pista = os.path.basename(pista)
        if post.get("musica") == nombre_pista:
            continue
        mp4 = os.path.join(RAIZ, "posts", post["archivo"])
        dur = float(post.get("duracion") or 10)
        tmp = mp4 + ".tmp.mp4"
        filtro = (f"[1:a]atrim=0:{dur},asetpts=N/SR/TB,afade=t=in:d=1,"
                  f"afade=t=out:st={max(0.5, dur - 1.5)}:d=1.5,volume={VOLUMEN},"
                  f"aresample=48000,aformat=channel_layouts=stereo[a]")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", mp4, "-stream_loop", "-1", "-i", pista,
                        "-filter_complex", filtro, "-map", "0:v", "-map", "[a]", "-c:v", "copy",
                        "-c:a", "aac", "-b:a", "128k", "-ar", "48000", "-t", str(dur),
                        "-movflags", "+faststart", tmp], check=True)
        os.replace(tmp, mp4)
        post["musica"] = nombre_pista
        hechos += 1
        print(f"{post['archivo']} ← {nombre_pista}", flush=True)

    with open(COLA, "w", encoding="utf-8") as f:
        json.dump(cola, f, ensure_ascii=False, indent=2)
    print(f"Música añadida a {hechos} Reels.")


if __name__ == "__main__":
    main()
