"""Fabrica 2 Trial Reels (variantes A y B) por carrusel a partir de sus slides.

A = slides en orden (gancho original).   B = abre con la «slide_golpe» (otro gancho), luego el resto.
Formato 1080x1920: slide cuadrada en el centro (fuera de las zonas tapadas por la interfaz),
fondo = la misma slide ampliada y desenfocada. Música: carpeta musica/, por turnos.
Salida: trial/cXX_A.mp4, trial/cXX_B.mp4 y trial/trial_cola.json
"""
import glob
import os
import subprocess
from PIL import Image, ImageFilter, ImageEnhance
from comun import RAIZ, escribir, leer

W, H, Y0 = 1080, 1920, 380          # la slide ocupa y 380 → 1460
SEG, SEG_GOLPE, FADE = 2.6, 3.2, 0.35
FIN = "carruseles/c02/10.jpg"       # slide del libro con «Comenta LIBRO» (común a todos)


def lienzo(slide, salida):
    sq = Image.open(slide).convert("RGB").resize((W, W), Image.LANCZOS)
    fondo = sq.resize((H, H)).crop(((H - W) // 2, 0, (H - W) // 2 + W, H)).filter(ImageFilter.GaussianBlur(40))
    fondo = ImageEnhance.Brightness(fondo).enhance(0.55)
    fondo.paste(sq, (0, Y0))
    fondo.save(salida, quality=92)


def video(slides, duraciones, musica, salida, tmp):
    entradas, filtros = [], []
    for i, (s, d) in enumerate(zip(slides, duraciones)):
        png = os.path.join(tmp, f"f{i:02d}.jpg"); lienzo(s, png)
        entradas += ["-loop", "1", "-t", str(d), "-i", png]
        filtros.append(f"[{i}:v]scale={W}:{H},setsar=1,fps=30,format=yuv420p,"
                       f"fade=t=in:st=0:d={FADE}[v{i}]")
    n = len(slides); total = sum(duraciones)
    filtros.append("".join(f"[v{i}]" for i in range(n)) + f"concat=n={n}:v=1:a=0[v]")
    entradas += ["-stream_loop", "-1", "-i", musica]
    filtros.append(f"[{n}:a]atrim=0:{total},asetpts=N/SR/TB,afade=t=in:d=1,"
                   f"afade=t=out:st={total - 2}:d=2,volume=0.6,aresample=48000[a]")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *entradas, "-filter_complex", ";".join(filtros),
                    "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-preset", "medium", "-crf", "23",
                    "-c:a", "aac", "-b:a", "128k", "-t", str(total), "-movflags", "+faststart", salida], check=True)


def main():
    datos = leer("carruseles/carruseles.json")
    cola = leer("trial/trial_cola.json", [])
    hechos = {t["id"] for t in cola}
    pistas = sorted(p for e in ("mp3", "m4a", "wav") for p in glob.glob(os.path.join(RAIZ, "musica", f"*.{e}")))
    if not pistas:
        raise SystemExit("No hay música en musica/.")
    os.makedirs(os.path.join(RAIZ, "trial", "tmp"), exist_ok=True)
    k = len(cola)
    for c in datos["carruseles"]:
        base = [os.path.join(RAIZ, s) for s in c["slides"][:9]]
        fin = os.path.join(RAIZ, FIN)
        g = c["slide_golpe"] - 1
        variantes = {
            "A": (base + [fin], [SEG_GOLPE] + [SEG] * 8 + [SEG_GOLPE]),
            "B": ([base[g]] + [s for i, s in enumerate(base) if i != g] + [fin], [SEG_GOLPE] + [SEG] * 8 + [SEG_GOLPE]),
        }
        for v, (slides, durs) in variantes.items():
            tid = f"{c['id']}_{v}"
            if tid in hechos:
                continue
            salida = os.path.join(RAIZ, "trial", f"{tid}.mp4")
            video(slides, durs, pistas[k % len(pistas)], salida, os.path.join(RAIZ, "trial", "tmp"))
            cola.append({"id": tid, "carrusel": c["id"], "variante": v, "archivo": f"trial/{tid}.mp4",
                         "tema": c.get("tema"), "gancho": c.get("gancho") if v == "A" else "Golpe",
                         "caption": c["caption"], "publicado": None, "media_id": None})
            k += 1
            print(f"{tid}.mp4 ✔", flush=True)
    escribir("trial/trial_cola.json", cola)
    for f in glob.glob(os.path.join(RAIZ, "trial", "tmp", "*")):
        os.remove(f)


if __name__ == "__main__":
    main()
