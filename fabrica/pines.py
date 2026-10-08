"""Fabrica las imágenes de Pinterest (pines/NNNN.jpg) y los ficheros CSV para la importación
masiva de Pinterest (Crear → Crear Pines en bloque).

Uso:  python3 pines.py --tablero "Frases de amor propio" --inicio 2026-10-10 --base https://usuario.github.io/repo
      (--prueba  -> solo 3 pines y un CSV de prueba)
"""
import argparse
import csv
import os
import re
import sys
from datetime import date, datetime, timedelta
from multiprocessing import Pool

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
from frases import FRASES          # noqa: E402
from pin import generar_pin        # noqa: E402

RAIZ = os.path.dirname(AQUI)
CARPETA = os.path.join(RAIZ, "pines")
ENLACE = "https://www.amazon.com/dp/B0HJ564B3W"
LIBRO = "«No estás rota, estás cansada», de Carolina Cuevas"
HORAS_UTC = ["15:30:00", "01:30:00"]      # 10:30 y 20:30 en Chicago (horario de verano)
POR_CSV = 60                                # 2 pines al día → un CSV por mes

TEMAS = [
    ("Frases de amor propio", "frases de amor propio, autoestima mujer, amor propio"),
    ("Frases sobre la autoexigencia", "autoexigencia, perfeccionismo, ser suficiente"),
    ("Frases para mujeres cansadas", "cansancio emocional, mujeres, descanso sin culpa"),
    ("Frases de crecimiento personal", "crecimiento personal, salud emocional, frases para reflexionar"),
]


def limpiar(texto):
    t = texto.replace("*", "").replace("\n", " ")
    return re.sub(r"\s+", " ", t).strip()


def titulo(texto, i):
    pref = TEMAS[i % len(TEMAS)][0]
    frase = limpiar(texto)
    corte = re.split(r"(?<=[.?!])\s", frase)[0].rstrip(".")
    k = next((j for j, c in enumerate(corte) if c.isalpha()), 0)
    t = f"{pref}: {corte[:k]}{corte[k].lower()}{corte[k + 1:]}"
    if len(t) > 100:
        t = t[:97].rsplit(" ", 1)[0] + "…"
    return t


def descripcion(texto, leyenda, i):
    claves = TEMAS[i % len(TEMAS)][1]
    d = (f"{limpiar(texto)} {leyenda.strip()} "
         f"Una frase del libro {LIBRO}, para las que llevan años sintiéndose insuficientes. "
         f"Guárdala para cuando la necesites.")
    return d[:500], claves


def tarea(args):
    i, texto, corazon = args
    generar_pin(texto, os.path.join(CARPETA, f"{i + 1:04d}.jpg"), seed=1000 + i, adorno=corazon)
    return i


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tablero", default="Frases de amor propio")
    ap.add_argument("--inicio", default=(date.today() + timedelta(days=1)).isoformat())
    ap.add_argument("--base", required=True)
    ap.add_argument("--prueba", action="store_true")
    a = ap.parse_args()

    os.makedirs(CARPETA, exist_ok=True)
    indices = list(range(3)) if a.prueba else list(range(len(FRASES)))
    trabajos = [(i, FRASES[i][0], FRASES[i][2]) for i in indices
                if a.prueba or not os.path.exists(os.path.join(CARPETA, f"{i + 1:04d}.jpg"))]
    with Pool(os.cpu_count() or 2) as p:
        for i in p.imap_unordered(tarea, trabajos):
            print(f"pin {i + 1:04d}", flush=True)

    inicio = datetime.fromisoformat(a.inicio)
    filas = []
    for n, i in enumerate(indices):
        dia = inicio + timedelta(days=n // len(HORAS_UTC))
        hora = HORAS_UTC[n % len(HORAS_UTC)]
        if hora < "12":                     # 01:30 UTC = la noche del día anterior en EE. UU.
            dia += timedelta(days=1)
        texto, leyenda, _ = FRASES[i]
        desc, claves = descripcion(texto, leyenda, i)
        filas.append({
            "Title": titulo(texto, i),
            "Media URL": f"{a.base.rstrip('/')}/pines/{i + 1:04d}.jpg",
            "Pinterest board": a.tablero,
            "Thumbnail": "",
            "Description": desc,
            "Link": ENLACE,
            "Publish date": f"{dia.date().isoformat()}T{hora}",
            "Keywords": claves,
        })

    grupos = [filas] if a.prueba else [filas[k:k + POR_CSV] for k in range(0, len(filas), POR_CSV)]
    for g_i, grupo in enumerate(grupos, start=1):
        nombre = "pinterest_prueba.csv" if a.prueba else f"pinterest_mes{g_i}.csv"
        with open(os.path.join(RAIZ, nombre), "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(grupo[0].keys()))
            w.writeheader()
            w.writerows(grupo)
        print(nombre, len(grupo), "pines, del", grupo[0]["Publish date"], "al", grupo[-1]["Publish date"])


if __name__ == "__main__":
    main()
