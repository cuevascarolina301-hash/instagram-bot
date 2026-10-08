"""Imagen para Pinterest (1000x1500, 2:3): arriba la frase a boli en el papel Canson, grande;
abajo la foto con el libro entero.

Uso de prueba:  python3 pin.py salida.jpg
"""
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFont

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import generar as g                      # noqa: E402

PW, PH = 1000, 1500
ALTO_FOTO = 840                          # la foto se recorta a 1080x907: cabe el libro entero
SERIF = os.path.join(AQUI, "ebgaramond.ttf")
SERIF_M = os.path.join(AQUI, "ebgaramond-500.ttf")
TITULO = "No estás rota, estás cansada"
AUTORA = "CAROLINA CUEVAS"
TERRACOTA = (176, 66, 38)


def frase_en_papel(texto, seed, adorno):
    texto = g.normalizar(texto)
    tam = g.elegir_tam(texto)
    firma = g.FIRMA
    g.FIRMA = ""                         # en el pin la firma va aparte
    try:
        base, relieve = g.papel(seed)
        m, _, _ = g.tinta(seed, texto, tam, adorno)
    finally:
        g.FIRMA = firma
    pintar = g.componer(base, relieve, m, np.random.default_rng(seed + 100))
    liso = Image.fromarray(np.clip(base, 0, 255).astype(np.uint8))
    return Image.fromarray(pintar(np.ones_like(m))), m, liso


def generar_pin(texto, destino, seed=1, adorno=True, foto="libro_1.jpg"):
    marco, m, liso = frase_en_papel(texto, seed, adorno)
    alto_papel = PH - ALTO_FOTO
    # encuadre ajustado a la tinta, para que la frase salga lo más grande posible
    ys, xs = np.nonzero(m > 0.05)
    x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max()
    zona_alto = alto_papel - 140                      # sitio para el título del libro
    ratio = PW / zona_alto
    w = max((x1 - x0) * 1.10, (y1 - y0) * 1.10 * ratio)
    h = w / ratio
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    # lienzo de papel más grande que el marco, por si el encuadre se sale
    esc = w / PW                                       # px del marco por px del pin
    pad = int(max(w, alto_papel * esc)) + 10
    ext = Image.new("RGB", (g.W + 2 * pad, g.H + 2 * pad))
    ox, oy = pad, pad
    kx, ky = pad // g.W + 1, pad // g.H + 1
    for i in range(-kx, kx + 1):                       # mosaico en espejo: textura continua y a la misma escala
        for j in range(-ky, ky + 1):
            t = liso
            if i % 2:
                t = t.transpose(Image.FLIP_LEFT_RIGHT)
            if j % 2:
                t = t.transpose(Image.FLIP_TOP_BOTTOM)
            ext.paste(t, (ox + i * g.W, oy + j * g.H))
    ext.paste(marco, (ox, oy))
    top = cy - (30 + zona_alto / 2) * esc
    caja = (cx - w / 2 + ox, top + oy, cx + w / 2 + ox, top + alto_papel * esc + oy)
    frase = ext.resize((PW, alto_papel), Image.LANCZOS, box=caja)

    # papel liso (del mismo marco) para el resto de la parte de arriba
    pin = liso.resize((PW, int(PW * g.H / g.W)), Image.LANCZOS).crop((0, 0, PW, PH))
    papel_pin = pin.copy()
    pin.paste(frase, (0, 0))
    papel_pin.paste(liso.resize((PW, alto_papel), Image.LANCZOS, box=(0, 0, g.W, alto_papel * g.W / PW)), (0, 0))

    d = ImageDraw.Draw(pin)
    f1 = ImageFont.truetype(SERIF_M, 36)
    f2 = ImageFont.truetype(SERIF_M, 21)
    l1 = f"Del libro «{TITULO}»"
    l2 = " ".join(AUTORA)
    yt = alto_papel - 108
    d.text(((PW - d.textlength(l1, font=f1)) / 2, yt), l1, font=f1, fill=(56, 42, 34))
    d.text(((PW - d.textlength(l2, font=f2)) / 2, yt + 50), l2, font=f2, fill=TERRACOTA)

    # foto con el libro entero
    im = Image.open(os.path.join(AQUI, foto)).convert("RGB")
    fw, fh = im.size
    alto_rec = int(fw * ALTO_FOTO / PW)
    cyf = int(fh * 0.565)
    top = max(0, min(cyf - alto_rec // 2, fh - alto_rec))
    franja = im.crop((0, top, fw, top + alto_rec)).resize((PW, ALTO_FOTO), Image.LANCZOS)
    franja = ImageEnhance.Contrast(ImageEnhance.Color(franja).enhance(1.08)).enhance(1.05)
    pin.paste(franja, (0, alto_papel))
    # transición papel -> foto
    deg = Image.linear_gradient("L").resize((PW, 70)).transpose(Image.FLIP_TOP_BOTTOM)
    borde = papel_pin.crop((0, alto_papel - 70, PW, alto_papel)).transpose(Image.FLIP_TOP_BOTTOM)
    pin.paste(borde, (0, alto_papel), deg)
    pin.save(destino, "JPEG", quality=92)


if __name__ == "__main__":
    from frases import FRASES
    destino = sys.argv[1] if len(sys.argv) > 1 else "pin.jpg"
    i = int(sys.argv[2]) if len(sys.argv) > 2 else 3
    texto, _, corazon = FRASES[i]
    generar_pin(texto, destino, seed=1000 + i, adorno=corazon)
    print(destino)
