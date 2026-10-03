"""Fabrica todos los Reels (posts/*.mp4), sus portadas (portadas/*.jpg) y la cola de publicación (cola.json).

Uso:  python3 construir.py            -> crea todo (se niega si cola.json ya existe)
      python3 construir.py --forzar   -> rehace todo (borra el registro de lo publicado)
"""
import json
import os
import subprocess
import sys
from multiprocessing import Pool

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
from frases import FRASES          # noqa: E402
from generar import generar        # noqa: E402

RAIZ = os.path.dirname(AQUI)
POSTS = os.path.join(RAIZ, "posts")
PORTADAS = os.path.join(RAIZ, "portadas")
COLA = os.path.join(RAIZ, "cola.json")

CTA = "\n\nEsta frase es de mi libro «No estás rota, estás cansada». El link está en mi perfil 📖"
COMPARTIR = [
    "\n\nEnvíaselo a alguien que necesite leerlo hoy.",
    "\n\nEtiqueta a quien necesita leer esto.",
    "\n\nGuárdalo para la próxima vez que lo olvides.",
]
HASHTAGS = "\n\n#amorpropio #autoexigencia #frasesdelavida #mujeres #crecimientopersonal"

LIBRO = [
    ("libro_1.jpg", "Lo escribí para la mujer que lleva años haciéndolo todo bien y aun así siente que no alcanza. "
                    "Sesenta y dos textos cortos para abrir por cualquier página. 📖\n\nEl link está en mi perfil."),
    ("libro_2.jpg", "No es un método ni un reto de treinta días. Es una sola idea, mirada desde muchos ángulos, "
                    "hasta que se te quede. 📖\n\nEl link está en mi perfil."),
    ("libro_1.jpg", "Si conoces a alguien que lo necesita, regálaselo. A veces basta con que llegue la frase "
                    "adecuada en la semana adecuada. 📖\n\nEl link está en mi perfil."),
    ("libro_2.jpg", "Sigue leyendo. Sigue en terapia si te hace bien. Sigue cuidándote. Lo que cambia no es lo "
                    "que haces: es desde dónde lo haces. 📖\n\nEl link está en mi perfil."),
]


def reel_libro(foto, mp4, jpg):
    """Reel de 7 s: la foto del libro con un zoom muy lento."""
    from PIL import Image
    im = Image.open(os.path.join(AQUI, foto)).convert("RGB")
    w, h = im.size
    if w / h > 9 / 16:                       # recortar a 9:16
        nw = int(h * 9 / 16)
        im = im.crop(((w - nw) // 2, 0, (w - nw) // 2 + nw, h))
    else:
        nh = int(w * 16 / 9)
        im = im.crop((0, (h - nh) // 2, w, (h - nh) // 2 + nh))
    im = im.resize((1080, 1920), Image.LANCZOS)
    im.save(jpg, "JPEG", quality=92)
    subprocess.run([
        "ffmpeg", "-y", "-loglevel", "error", "-loop", "1", "-i", jpg,
        "-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=48000",
        "-filter_complex",
        "[0:v]scale=2160:3840,zoompan=z='1+0.035*on/210':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
        ":d=210:s=1080x1920:fps=30,format=yuv420p[v]",
        "-map", "[v]", "-map", "1:a", "-t", "7", "-c:v", "libx264", "-preset", "slow", "-crf", "26", "-profile:v", "high",
        "-c:a", "aac", "-b:a", "128k", "-ar", "48000", "-movflags", "+faststart", mp4], check=True)
    return 7.0, 500


def duracion_valida(mp4):
    """Duración del vídeo si está completo, si no None."""
    try:
        r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", mp4],
                           capture_output=True, text=True, check=True)
        return float(r.stdout.strip())
    except Exception:
        return None


def tarea(t):
    numero, tipo, datos = t
    mp4 = os.path.join(POSTS, f"{numero:04d}.mp4")
    jpg = os.path.join(PORTADAS, f"{numero:04d}.jpg")
    if os.path.exists(mp4) and os.path.exists(jpg) and "--reanudar" in sys.argv:
        d = duracion_valida(mp4)
        if d:
            return numero, d, (500 if tipo == "libro" else int((d - 0.5) * 1000))
    if tipo == "libro":
        dur, portada = reel_libro(datos, mp4, jpg)
    else:
        texto, corazon, seed = datos
        dur, portada = generar(texto, mp4, jpg, seed=seed, adorno=corazon)
    print(f"{numero:04d}", flush=True)
    return numero, dur, portada


def main():
    if os.path.exists(COLA) and "--forzar" not in sys.argv and "--reanudar" not in sys.argv:
        sys.exit("cola.json ya existe: rehacerla borraría el registro de lo publicado. Usa --forzar si es a propósito.")
    os.makedirs(POSTS, exist_ok=True)
    os.makedirs(PORTADAS, exist_ok=True)

    cola, trabajos, n_libro = [], [], 0
    for i, (texto, leyenda, corazon) in enumerate(FRASES):
        if i and i % 30 == 0 and n_libro < len(LIBRO):
            foto, cap = LIBRO[n_libro]
            n = len(cola) + 1
            cola.append({"archivo": f"{n:04d}.mp4", "leyenda": cap + HASHTAGS, "tipo": "libro", "publicado": None})
            trabajos.append((n, "libro", foto))
            n_libro += 1
        if (i + 1) % 4 == 0:
            cap = leyenda + CTA
        elif (i + 1) % 4 == 2:
            cap = leyenda + COMPARTIR[(i // 4) % len(COMPARTIR)]
        else:
            cap = leyenda
        n = len(cola) + 1
        cola.append({"archivo": f"{n:04d}.mp4", "leyenda": cap + HASHTAGS, "tipo": "frase", "texto": texto,
                     "publicado": None})
        trabajos.append((n, "frase", (texto, corazon, 1000 + i)))

    with Pool(os.cpu_count() or 2) as p:
        resultados = {n: (d, c) for n, d, c in p.imap_unordered(tarea, trabajos)}
    for k, post in enumerate(cola, start=1):
        post["duracion"] = round(resultados[k][0], 2)
        post["portada_ms"] = resultados[k][1]

    with open(COLA, "w", encoding="utf-8") as f:
        json.dump(cola, f, ensure_ascii=False, indent=2)
    print("total", len(cola))


if __name__ == "__main__":
    main()
