"""Fábrica de Reels para @carolina.cuevas.libros.

Página de papel Canson beige, escritura a bolígrafo Bic azul que aparece como si se escribiera.
Marcado de la frase:  texto normal  y  *texto subrayado*.  Saltos de línea con "\n".
"""
import math
import os
import random
import re
import subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

AQUI = os.path.dirname(os.path.abspath(__file__))
FONT = os.path.join(AQUI, "squarepeg.ttf")

W, H = 1080, 1920            # Reel 9:16
CENTRO_Y = 860               # centro del bloque de texto (por encima del centro: abajo están los botones y la leyenda)
ANCHO_MAX = 820              # el texto no llega a la columna de botones de la derecha
SS = 2                       # supermuestreo
FPS = 30

PAPEL = np.array([241, 229, 207], dtype=np.float32)
TINTA = np.array([34, 62, 158], dtype=np.float32)
FIRMA = "@carolina.cuevas.libros"


# ---------------------------------------------------------------- papel
def _suave(rng, escala, w, h):
    pw, ph = max(2, w // escala), max(2, h // escala)
    r = (rng.random((ph, pw)) * 255).astype(np.uint8)
    return np.asarray(Image.fromarray(r).resize((w, h), Image.BICUBIC), dtype=np.float32) / 255.0


def papel(seed):
    rng = np.random.default_rng(seed)
    fino = (rng.random((H, W)) * 255).astype(np.uint8)
    fino = np.asarray(Image.fromarray(fino).filter(ImageFilter.GaussianBlur(1.3)), dtype=np.float32) / 255.0
    relieve = 0.7 * fino + 0.3 * _suave(rng, 6, W, H)
    gy, gx = np.gradient(relieve)
    luz = -gx * 0.7 - gy * 0.7
    luz /= np.abs(luz).max() + 1e-6
    nubes = 0.6 * _suave(rng, 160, W, H) + 0.4 * _suave(rng, 60, W, H)
    nubes -= nubes.mean()
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    grad = 1.0 - 0.035 * ((xx / W) * 0.5 + (yy / H) * 0.8)
    dist = np.sqrt((xx / W + 0.1) ** 2 + (yy / H + 0.1) ** 2)
    sol = np.clip(1.0 - dist / 0.9, 0, 1) ** 2
    base = PAPEL * grad[..., None] * (1 + 0.03 * nubes[..., None]) + 8.0 * luz[..., None]
    base = base + sol[..., None] * np.array([10, 7, 0], dtype=np.float32)
    relieve = (relieve - relieve.min()) / (relieve.max() - relieve.min())
    return np.clip(base, 0, 255), relieve


# ---------------------------------------------------------------- texto
def normalizar(texto):
    """Un subrayado que cruza un salto de línea se cierra y se reabre en cada línea."""
    out, abierto = [], False
    for linea in texto.split("\n"):
        impares = linea.count("*") % 2 == 1
        nuevo = ("*" + linea) if (abierto and linea) else linea
        final = abierto != impares
        if final and linea:
            nuevo += "*"
        out.append(nuevo)
        abierto = final
    return "\n".join(out)


def segmentos(linea):
    out = []
    for p in re.split(r"(\*[^*]+\*)", linea):
        if p:
            out.append((p[1:-1], True) if p.startswith("*") and p.endswith("*") else (p, False))
    return out


def elegir_tam(texto):
    f = ImageFont.truetype(FONT, 100)
    d = ImageDraw.Draw(Image.new("L", (1, 1)))
    esp = d.textlength(" ", font=f) * 1.47
    lineas = texto.replace("*", "").split("\n")
    ancho = max(sum(d.textlength(p, font=f) for p in l.split()) + esp * max(0, len(l.split()) - 1)
                for l in lineas)
    por_ancho = 100 * ANCHO_MAX / ancho
    por_alto = 1000 / (1.25 * (len(lineas) - 1) + 1.6)
    return int(max(56, min(130, por_ancho, por_alto)))


def subrayado(d, x0, x1, y, rnd, grosor):
    x0 += rnd.uniform(-12, 2) * SS
    x1 += rnd.uniform(4, 18) * SS
    inclin = rnd.uniform(-7, -2) * SS
    curva = rnd.uniform(1.5, 4) * SS
    n = 220
    for i in range(n + 1):
        t = i / n
        x = x0 + (x1 - x0) * t
        yy = y + inclin * t + curva * math.sin(math.pi * t) + 0.6 * SS * math.sin(t * 11 + rnd.random())
        r = grosor / 2 * min(1.0, t / 0.08, (1 - t) / 0.12 + 0.25)
        d.ellipse([x - r, yy - r, x + r, yy + r], fill=255)


def corazon(d, cx, cy, rnd, tam_px, grosor):
    """Corazón de un solo trazo. Devuelve la lista de puntos en orden de dibujo."""
    giro = math.radians(rnd.uniform(-12, 12))
    n = 400
    t0, t1 = rnd.uniform(0.02, 0.06), rnd.uniform(0.96, 1.04)
    pts = []
    for i in range(n + 1):
        t = (t0 + (t1 - t0) * i / n) * 2 * math.pi
        x = 16 * math.sin(t) ** 3
        y = -(13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t))
        x, y = x * tam_px / 32, y * tam_px / 32
        x, y = x * math.cos(giro) - y * math.sin(giro), x * math.sin(giro) + y * math.cos(giro)
        x += 0.8 * SS * math.sin(i * 0.07)
        r = grosor / 2 * min(1.0, i / 25 + 0.3, (n - i) / 25 + 0.3)
        d.ellipse([cx + x - r, cy + y - r, cx + x + r, cy + y + r], fill=255)
        pts.append((cx + x, cy + y))
    return pts


def tinta(seed, texto, tam, adorno):
    """Devuelve (máscara de tinta 0..1, mapa de tiempos de aparición en segundos, duración de escritura)."""
    rnd = random.Random(seed)
    w, h = W * SS, H * SS
    mask = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(mask)
    font = ImageFont.truetype(FONT, tam * SS)
    lineas = texto.split("\n")
    interlinea = tam * 1.25 * SS
    alto = interlinea * (len(lineas) - 1) + (tam * 0.9 * SS if adorno else 0)
    y0 = CENTRO_Y * SS - alto / 2 + tam * 0.35 * SS
    espacio = d.textlength(" ", font=font)
    grosor_raya = max(2, tam * 0.03) * SS

    renglones = []        # (y_base, x_ini, x_fin) en píxeles finales
    for i, linea in enumerate(lineas):
        palabras = [(p, m) for t, m in segmentos(linea) for p in t.split(" ") if p]
        y = y0 + i * interlinea
        if not palabras:
            renglones.append((y / SS, None, None))
            continue
        anchos = [d.textlength(p, font=font) for p, _ in palabras]
        total = sum(anchos) + espacio * 1.47 * (len(palabras) - 1)
        x = (w - total) / 2 + rnd.uniform(-8, 8) * SS
        x_ini = x
        deriva = math.radians(rnd.uniform(-0.8, 0.8))
        tramo = None
        for (pal, marca), aw in zip(palabras, anchos):
            dy = (x - w / 2) * math.tan(deriva) + rnd.uniform(-2.5, 2.5) * SS
            f = ImageFont.truetype(FONT, int(tam * SS * rnd.uniform(0.97, 1.03)))
            capa = Image.new("L", (int(aw * 1.2) + 40 * SS, int(tam * 2.2 * SS)), 0)
            ImageDraw.Draw(capa).text((20 * SS, tam * 1.5 * SS), pal, font=f, fill=255, anchor="ls")
            capa = capa.rotate(rnd.uniform(-1.2, 1.2), resample=Image.BICUBIC, center=(20 * SS, tam * 1.5 * SS))
            mask.paste(255, (int(x - 20 * SS), int(y + dy - tam * 1.5 * SS)), capa)
            if marca:
                tramo = [x, x + aw, y + dy] if tramo is None else [tramo[0], x + aw, tramo[2]]
            elif tramo:
                subrayado(d, tramo[0], tramo[1], tramo[2] + tam * 0.21 * SS, rnd, grosor_raya)
                tramo = None
            x += aw + espacio * rnd.uniform(1.35, 1.6)
        if tramo:
            subrayado(d, tramo[0], tramo[1], tramo[2] + tam * 0.21 * SS, rnd, grosor_raya)
        renglones.append((y / SS, x_ini / SS - 15, x / SS + 25))

    cor = None
    if adorno:
        cy = y0 + (len(lineas) - 1) * interlinea + tam * 0.95 * SS
        pts = corazon(d, w / 2 + rnd.uniform(-6, 6) * SS, cy, rnd, tam * 0.42 * SS, grosor_raya)
        cor = [(px / SS, py / SS) for px, py in pts]
        y_fin = cy / SS + tam * 0.6
    else:
        y_fin = renglones[-1][0] + tam * 0.6

    # firma, debajo del bloque
    y_firma = min(y_fin + 80, 1520)
    ff = ImageFont.truetype(FONT, 46 * SS)
    firma = Image.new("L", (w, h), 0)
    ImageDraw.Draw(firma).text((w / 2, y_firma * SS), FIRMA, font=ff, fill=150, anchor="ms")
    mask = Image.fromarray(np.maximum(np.asarray(mask), np.asarray(firma)))
    mask = mask.filter(ImageFilter.MaxFilter(3))
    m = np.asarray(mask.resize((W, H), Image.LANCZOS), dtype=np.float32) / 255.0

    # ------------------------------------------------ mapa de tiempos (cuándo aparece cada píxel)
    VEL = 620.0                                    # píxeles por segundo de escritura
    T = np.full((H, W), np.inf, dtype=np.float32)
    xx = np.arange(W, dtype=np.float32)[None, :]
    yy = np.arange(H, dtype=np.float32)[:, None]
    bases = [r[0] for r in renglones]
    # cada píxel pertenece al renglón cuya zona (de -0.95·tam a +0.45·tam alrededor de la base) lo contiene
    t = 0.35                                       # pequeña pausa antes de empezar
    inicios = []                                   # (y_base, t_inicio, x_ini) de cada renglón escrito
    for (yb, xa, xb) in renglones:
        if xa is None:
            t += 0.35
            continue
        banda = (yy >= yb - tam * 0.95) & (yy < yb + tam * 0.30)
        tiempos = t + np.clip(xx - xa, 0, None) / VEL
        T = np.where(banda & np.isinf(T), np.broadcast_to(tiempos, (H, W)), T)
        inicios.append((yb, t, xa))
        t += (xb - xa) / VEL + 0.18                # pausa al cambiar de renglón
    # tinta fuera de las bandas (descendentes largos, subrayados bajos): aparece con el renglón de arriba
    sin = np.isinf(T) & (m > 0.01) & (np.broadcast_to(yy, (H, W)) < inicios[-1][0] + tam * 0.75)
    if sin.any():
        ys, xs = np.nonzero(sin)
        bases = np.array([i[0] for i in inicios])
        k = np.clip(np.searchsorted(bases, ys) - 1, 0, len(inicios) - 1)
        t0 = np.array([i[1] for i in inicios])[k]
        x0 = np.array([i[2] for i in inicios])[k]
        T[ys, xs] = t0 + np.clip(xs - x0, 0, None) / VEL
    # corazón: se dibuja siguiendo su trazo
    if cor:
        t_cor0 = t + 0.1
        dur_cor = 0.7
        cy_min = min(p[1] for p in cor) - 12
        cy_max = max(p[1] for p in cor) + 12
        zona = (yy >= cy_min) & (yy <= cy_max)
        P = np.array(cor, dtype=np.float32)
        # para cada píxel de la zona, el índice del punto del trazo más cercano
        ys, xs = np.nonzero(zona & (m > 0.02) & np.broadcast_to(xx >= P[:, 0].min() - 12, (H, W))
                            & np.broadcast_to(xx <= P[:, 0].max() + 12, (H, W)))
        if len(ys):
            dx = xs[:, None] - P[None, ::4, 0]
            dy = ys[:, None] - P[None, ::4, 1]
            k = np.argmin(dx * dx + dy * dy, axis=1) / (len(P[::4]) - 1)
            T[ys, xs] = t_cor0 + k * dur_cor
        t = t_cor0 + dur_cor
    # firma: aparece al final
    zona_firma = (yy >= y_firma - 45) & (yy <= y_firma + 20)
    T = np.where(np.broadcast_to(zona_firma, (H, W)) & (m > 0.0), t + 0.2, T)
    T[np.isinf(T)] = t
    return m, T, t + 0.6


# ---------------------------------------------------------------- composición
def componer(base, relieve, m, rng):
    """Devuelve funciones para pintar la tinta con un alpha dado."""
    salteado = np.clip(0.55 + 0.75 * relieve, 0, 1)
    presion = 0.80 + 0.20 * _suave(rng, 90, W, H)
    granulo = 0.88 + 0.12 * rng.random((H, W)).astype(np.float32)
    factor = salteado * presion * granulo * 1.08
    tinta_rgb = TINTA * (0.92 + 0.16 * relieve[..., None])
    mult = base * tinta_rgb / 255.0
    destino = mult * 0.65 + tinta_rgb * 0.35        # color donde la tinta es plena

    def pintar(alpha):
        a = np.clip(m * alpha * factor, 0, 1)[..., None]
        return np.clip(base * (1 - a) + destino * a, 0, 255).astype(np.uint8)
    return pintar


def generar(texto, destino_mp4, destino_jpg, seed=1, adorno=True, espera=4.0):
    """Crea el Reel (mp4) y su portada (jpg). Devuelve la duración y el instante de portada en ms."""
    texto = normalizar(texto)
    tam = elegir_tam(texto)
    base, relieve = papel(seed)
    m, T, fin_escritura = tinta(seed, texto, tam, adorno)
    pintar = componer(base, relieve, m, np.random.default_rng(seed + 100))

    duracion = max(7.0, fin_escritura + espera)
    n = int(round(duracion * FPS))
    BORDE = 0.12                                   # suavidad del avance de la tinta, en segundos

    final = pintar(np.ones_like(m))
    Image.fromarray(final).save(destino_jpg, "JPEG", quality=92)

    cmd = ["ffmpeg", "-y", "-loglevel", "error",
           "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=48000",
           "-shortest", "-map", "0:v", "-map", "1:a",
           "-c:v", "libx264", "-preset", "slow", "-crf", "28", "-pix_fmt", "yuv420p",
           "-g", str(FPS * 2), "-profile:v", "high",
           "-c:a", "aac", "-b:a", "128k", "-ar", "48000",
           "-movflags", "+faststart", destino_mp4]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    ultimo = None
    for i in range(n):
        tt = i / FPS
        if tt >= fin_escritura + BORDE:
            frame = final
        else:
            alpha = np.clip((tt - T) / BORDE + 1.0, 0, 1)
            frame = pintar(alpha)
        if frame is final and ultimo is final:
            p.stdin.write(final_bytes)
        else:
            if frame is final:
                final_bytes = final.tobytes()
                p.stdin.write(final_bytes)
            else:
                p.stdin.write(frame.tobytes())
        ultimo = frame
    p.stdin.close()
    if p.wait():
        raise RuntimeError("ffmpeg falló")
    return duracion, int((duracion - 0.5) * 1000)


if __name__ == "__main__":
    t = ("No vas tarde.\nNo estás rota.\n*Estás cansada,*\nque es otra cosa\n"
         "completamente distinta.\nY de eso *sí se sale.*")
    print(generar(t, os.path.join(AQUI, "prueba.mp4"), os.path.join(AQUI, "prueba.jpg"), seed=3))
