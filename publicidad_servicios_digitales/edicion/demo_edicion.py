"""Demo de edición profesional de 10 s (1080x1920, 30 fps) a partir de tomas reales de drone (CC BY 3.0).

Técnicas: reencuadre vertical con cámara virtual, speed ramping con interpolación por flujo óptico,
motion blur por acumulación de subcuadros, corrección de color por plano, bloom, viñeta, grano,
tilt-shift, transiciones (zoom blur, whip pan, flash, glitch RGB, dip con light leak) y tipografía animada.

Uso: python3 edicion/demo_edicion.py <carpeta_fuentes> <salida_frames> [<salida_frames_sin_editar>]
"""
import math, os, subprocess, sys
from pathlib import Path
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1080, 1920, 30
BASE = Path(__file__).resolve().parent.parent
FUENTES = BASE / "web/_fuentes"
SRC = Path(sys.argv[1]); OUT = Path(sys.argv[2]); RAW = Path(sys.argv[3]) if len(sys.argv) > 3 else None
OUT.mkdir(parents=True, exist_ok=True)
if RAW: RAW.mkdir(parents=True, exist_ok=True)
RNG = np.random.default_rng(3)

# ------------------------------------------------------------------ planos
# t0: segundo de inicio en la fuente; vel: [(tiempo relativo del plano, velocidad)]; zoom/cx: (inicio, fin)
PLANOS = [
    dict(src="fjord.webm", fps=25, a=0.0, b=1.5, t0=175.2, vel=[(0, .9), (1.5, 1.1)], zoom=(1.0, 1.16), cx=(.62, .55), look="frio"),
    dict(src="fpv.webm", fps=59.94, a=1.5, b=3.0, t0=81.0, vel=[(0, 3.2), (.7, 1.0), (1.5, 1.6)], zoom=(1.18, 1.0), cx=(.5, .45), look="calido"),
    dict(src="fpv.webm", fps=59.94, a=3.0, b=4.5, t0=86.6, vel=[(0, 2.4), (.6, .55), (1.5, .8)], zoom=(1.05, 1.2), cx=(.45, .55), look="calido", tilt=True),
    dict(src="diving.webm", fps=50, a=4.5, b=7.0, t0=27.7, vel=[(0, 1.3), (.7, .28), (1.35, .28), (1.75, 2.6), (2.5, 2.2)], zoom=(1.0, 1.1), cx=(.5, .42), look="esmeralda", shake=True),
    dict(src="fjord.webm", fps=25, a=7.0, b=8.5, t0=157.5, vel=[(0, 1.8), (1.5, 1.2)], zoom=(1.1, 1.0), cx=(.40, .60), look="frio"),
    dict(src="diving.webm", fps=50, a=8.5, b=10.0, t0=31.2, vel=[(0, .5), (1.5, .35)], zoom=(1.0, 1.14), cx=(.62, .58), look="esmeralda"),
]

# ------------------------------------------------------------------ utilidades
def interp(keys, x):
    xs, ys = zip(*keys)
    return float(np.interp(x, xs, ys))

def ease(x):
    x = min(1, max(0, x)); return x * x * (3 - 2 * x)

def eoc(x):
    x = min(1, max(0, x)); return 1 - (1 - x) ** 3

def leer(src, t_ini, dur, fps):
    """Decodifica un tramo de la fuente a cuadros BGR (resolución nativa)."""
    cmd = ["ffmpeg", "-v", "error", "-ss", f"{max(0, t_ini):.3f}", "-t", f"{dur:.3f}", "-i", str(SRC / src),
           "-f", "rawvideo", "-pix_fmt", "bgr24", "-"]
    data = subprocess.run(cmd, capture_output=True, check=True).stdout
    n = len(data) // (1920 * 1080 * 3)
    return np.frombuffer(data[:n * 1920 * 1080 * 3], np.uint8).reshape(n, 1080, 1920, 3), max(0, t_ini)

DIS = cv2.DISOpticalFlow_create(cv2.DISOPTICAL_FLOW_PRESET_MEDIUM)
_cache_flujo = {}

def intermedio(f0, f1, a, key):
    """Cuadro intermedio por flujo óptico (cámara lenta suave)."""
    if a < 1e-3: return f0
    if a > 1 - 1e-3: return f1
    if key not in _cache_flujo:
        g0 = cv2.cvtColor(cv2.resize(f0, (960, 540)), cv2.COLOR_BGR2GRAY)
        g1 = cv2.cvtColor(cv2.resize(f1, (960, 540)), cv2.COLOR_BGR2GRAY)
        fw = cv2.resize(DIS.calc(g0, g1, None), (1920, 1080)) * 2
        bw = cv2.resize(DIS.calc(g1, g0, None), (1920, 1080)) * 2
        _cache_flujo.clear(); _cache_flujo[key] = (fw, bw)
    fw, bw = _cache_flujo[key]
    gx, gy = np.meshgrid(np.arange(1920, dtype=np.float32), np.arange(1080, dtype=np.float32))
    w0 = cv2.remap(f0, gx - fw[..., 0] * a, gy - fw[..., 1] * a, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    w1 = cv2.remap(f1, gx - bw[..., 0] * (1 - a), gy - bw[..., 1] * (1 - a), cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    return cv2.addWeighted(w0, 1 - a, w1, a, 0)

def cuadro_fuente(frames, base_t, fps, s, lento):
    x = (s - base_t) * fps
    i = int(math.floor(x)); a = x - i
    i = max(0, min(len(frames) - 2, i))
    if lento:
        return intermedio(frames[i], frames[i + 1], a, i)
    return frames[i] if a < .5 else frames[i + 1]

def reencuadre(img, zoom, cx, shake=(0, 0, 0)):
    """Cámara virtual: recorte vertical 9:16 dentro del cuadro 16:9 con zoom, paneo y vibración."""
    ch = 1080 / zoom; cw = ch * 9 / 16
    cxp = np.clip(cx * 1920, cw / 2, 1920 - cw / 2) + shake[0]
    cyp = 540 + shake[1]
    s = H / ch
    M = cv2.getRotationMatrix2D((float(cxp), float(cyp)), shake[2], s)
    M[0, 2] += W / 2 - cxp; M[1, 2] += H / 2 - cyp
    return cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_LANCZOS4, borderMode=cv2.BORDER_REFLECT)

# ------------------------------------------------------------------ color
LOOKS = {
    "frio": dict(lift=(.035, .03, .015), gamma=(1.0, .98, .92), gain=(1.02, 1.04, 1.1), sat=.82, con=.55, ts=(.0, .05, .09), th=(.06, .03, -.02)),
    "calido": dict(lift=(.02, .025, .03), gamma=(.95, .98, 1.04), gain=(1.1, 1.03, .92), sat=1.12, con=.5, ts=(-.02, .04, .07), th=(.09, .04, -.04)),
    "esmeralda": dict(lift=(.02, .03, .03), gamma=(1.0, .95, .98), gain=(1.04, 1.06, 1.0), sat=1.18, con=.6, ts=(.0, .05, .06), th=(.07, .03, -.03)),
}
VIN = None

def graduar(img, look):
    global VIN
    p = LOOKS[look]
    x = img.astype(np.float32) / 255.0
    x = x[..., ::-1]  # BGR -> RGB
    lift = np.array(p["lift"], np.float32); gain = np.array(p["gain"], np.float32); gam = np.array(p["gamma"], np.float32)
    x = np.clip(lift + x * (gain - lift), 0, 1) ** gam
    l = (x @ np.array([.2126, .7152, .0722], np.float32))[..., None]
    s = x * x * (3 - 2 * x)
    x = x + (s - x) * p["con"]
    l = (x @ np.array([.2126, .7152, .0722], np.float32))[..., None]
    x = l + (x - l) * p["sat"]
    x = x + (1 - l) ** 2 * np.array(p["ts"], np.float32) + l ** 2 * np.array(p["th"], np.float32)
    # bloom en altas luces
    hi = np.clip((x - .72) * 3.5, 0, 1)
    small = cv2.resize(hi, (W // 8, H // 8), interpolation=cv2.INTER_AREA)
    bloom = cv2.resize(cv2.GaussianBlur(small, (0, 0), 9), (W, H))
    x = 1 - (1 - x) * (1 - bloom * .35)
    if VIN is None:
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        d = np.sqrt(((xx - W / 2) / (W * .62)) ** 2 + ((yy - H / 2) / (H * .62)) ** 2)
        VIN = np.clip(1 - .5 * np.clip(d - .55, 0, 1) ** 1.6, 0, 1)[..., None]
    x = x * VIN
    return np.clip(x, 0, 1)

def tilt_shift(x):
    small = cv2.resize(x, (W // 3, H // 3), interpolation=cv2.INTER_AREA)
    bl = cv2.resize(cv2.GaussianBlur(small, (0, 0), 5), (W, H))
    yy = np.linspace(0, 1, H, dtype=np.float32)[:, None, None]
    m = np.clip((np.abs(yy - .52) - .14) / .2, 0, 1)
    return x * (1 - m) + bl * m

def grano(x, k=.035):
    n = RNG.standard_normal((H // 2, W // 2, 1)).astype(np.float32)
    n = cv2.resize(n, (W, H))[..., None]
    return np.clip(x + n * k * (.4 + .6 * (1 - x.mean(axis=2, keepdims=True))), 0, 1)

def nitidez(x):
    b = cv2.GaussianBlur(x, (0, 0), 1.4)
    return np.clip(x + (x - b) * .6, 0, 1)

# ------------------------------------------------------------------ transiciones
def zoom_blur(x, k, escala_base=1.0):
    acc = np.zeros_like(x)
    n = 9
    for i in range(n):
        s = escala_base * (1 + k * i / n)
        M = cv2.getRotationMatrix2D((W / 2, H / 2), 0, s)
        acc += cv2.warpAffine(x, M, (W, H), borderMode=cv2.BORDER_REFLECT)
    return acc / n

def whip(x, dx, blur):
    M = np.float32([[1, 0, dx], [0, 1, 0]])
    y = cv2.warpAffine(x, M, (W, H), borderMode=cv2.BORDER_WRAP)
    if blur > 2:
        k = np.zeros((1, int(blur) | 1), np.float32); k[:] = 1 / k.size
        y = cv2.filter2D(y, -1, k)
    return y

def glitch(x, k, rng):
    y = x.copy()
    s = int(26 * k)
    y[..., 0] = np.roll(x[..., 0], s, axis=1); y[..., 2] = np.roll(x[..., 2], -s, axis=1)
    for _ in range(int(10 * k)):
        a = rng.integers(0, H - 60); h = rng.integers(10, 90); off = rng.integers(-120, 120)
        y[a:a + h] = np.roll(y[a:a + h], off, axis=1)
    return y

def light_leak(t, fuerza):
    yy, xx = np.mgrid[0:H // 8, 0:W // 8].astype(np.float32)
    cx = W / 8 * (.2 + .6 * (t % 1)); cy = H / 8 * .35
    d = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2) / (W / 8)
    m = np.exp(-d * d * 3)[..., None] * np.array([1.0, .55, .25], np.float32)
    return cv2.resize(m, (W, H)) * fuerza

# ------------------------------------------------------------------ tipografía
def fuente(nombre, tam):
    f = ImageFont.truetype(str(FUENTES / nombre), tam)
    return f

def var(f, peso):
    try:
        f.set_variation_by_axes([peso])
    except Exception:
        pass
    return f

F_TIT = var(fuente("Unbounded.ttf", 158), 800)
F_SUB = var(fuente("Syne.ttf", 34), 700)
F_GR = var(fuente("Unbounded.ttf", 120), 800)
F_CH = var(fuente("Syne.ttf", 28), 700)

def texto_espaciado(draw, xy_centro, txt, f, espaciado, fill):
    anchos = [draw.textlength(c, font=f) for c in txt]
    total = sum(anchos) + espaciado * (len(txt) - 1)
    x = xy_centro[0] - total / 2
    for c, a in zip(txt, anchos):
        draw.text((x, xy_centro[1]), c, font=f, fill=fill, anchor="lm")
        x += a + espaciado

def capa_titulo(t):
    """Devuelve una capa RGBA (float) con la tipografía del cuadro t, o None."""
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    hay = False
    # 1) NORTE: aparece con tracking que se cierra y revelado por máscara
    if .15 <= t < 1.55:
        k = eoc((t - .15) / .9); sal = ease((t - 1.3) / .25)
        esp = 70 * (1 - k) + 8
        capa = Image.new("RGBA", (W, H), (0, 0, 0, 0)); dc = ImageDraw.Draw(capa)
        texto_espaciado(dc, (W / 2, H * .44), "NORTE", F_TIT, esp, (255, 255, 255, int(255 * (1 - sal))))
        m = Image.new("L", (W, H), 0); dm = ImageDraw.Draw(m)
        top = H * .44 + 130 - 260 * k
        dm.rectangle([0, top, W, H * .44 + 130], fill=255)
        im.paste(capa, (0, 0), Image.composite(capa, Image.new("RGBA", (W, H)), m).getchannel("A"))
        a2 = ease((t - .55) / .4) * (1 - sal)
        texto_espaciado(d, (W / 2, H * .44 + 160), "UNA HISTORIA EN MOVIMIENTO", F_SUB, 9, (255, 255, 255, int(220 * a2)))
        d.line([(W / 2 - 150 * a2, H * .44 + 210), (W / 2 + 150 * a2, H * .44 + 210)], fill=(255, 255, 255, int(160 * a2)), width=2)
        hay = True
    # 2) SIN LÍMITES: palabras cinéticas en la caída
    if 5.05 <= t < 6.95:
        for j, (pal, t0, y) in enumerate((("SIN", 5.05, .40), ("LÍMITES", 5.35, .47))):
            k = eoc((t - t0) / .35); sal = ease((t - 6.7) / .25)
            if t < t0: continue
            esc = 1.25 - .25 * k
            capa = Image.new("RGBA", (W, H), (0, 0, 0, 0)); dc = ImageDraw.Draw(capa)
            dc.text((W / 2, H * y), pal, font=F_GR, fill=(255, 255, 255, int(255 * k * (1 - sal))), anchor="mm")
            if abs(esc - 1) > .01:
                capa = capa.resize((int(W * esc), int(H * esc)), Image.BICUBIC)
                ox, oy = (capa.width - W) // 2, (capa.height - H) // 2
                capa = capa.crop((ox, oy, ox + W, oy + H))
            if k < .9:
                capa = capa.filter(ImageFilter.GaussianBlur(10 * (1 - k)))
            im.alpha_composite(capa); hay = True
    # 3) chip lateral
    if 7.15 <= t < 8.4:
        k = eoc((t - 7.15) / .4); sal = ease((t - 8.15) / .25)
        x = 70 - 80 * (1 - k)
        a = int(255 * k * (1 - sal))
        d.rectangle([x, H * .78, x + 6, H * .78 + 70], fill=(255, 255, 255, a))
        d.text((x + 26, H * .78 + 8), "SENTÍ", font=F_CH, fill=(255, 255, 255, a))
        d.text((x + 26, H * .78 + 40), "EL VIAJE", font=F_CH, fill=(255, 255, 255, a))
        hay = True
    # 4) cierre
    if t >= 8.75:
        k = eoc((t - 8.75) / .6)
        texto_espaciado(d, (W / 2, H * .5), "NORTE", F_TIT, 8 + 40 * (1 - k), (255, 255, 255, int(255 * k)))
        a2 = ease((t - 9.1) / .4)
        texto_espaciado(d, (W / 2, H * .5 + 150), "DEMO DE EDICIÓN", F_SUB, 10, (255, 255, 255, int(200 * a2)))
        hay = True
    if not hay:
        return None
    return np.asarray(im).astype(np.float32) / 255.0

def destello_titulo(x, t):
    """Barrido de luz sobre el título final."""
    if not (9.0 <= t <= 9.8): return x
    k = (t - 9.0) / .8
    cx = -200 + 1500 * k
    xx = np.arange(W, dtype=np.float32)[None, :, None]
    yy = np.arange(H, dtype=np.float32)[:, None, None]
    banda = np.exp(-(((xx - cx) + (yy - H * .5) * .35) / 70) ** 2) * np.exp(-((yy - H * .5) / 240) ** 2)
    return np.clip(x + banda * .35, 0, 1)

# ------------------------------------------------------------------ render
def velocidad_integrada(vel, dur):
    ts = np.linspace(0, dur, 2001)
    v = np.array([interp(vel, u) for u in ts])
    acc = np.concatenate([[0], np.cumsum((v[1:] + v[:-1]) / 2 * np.diff(ts))])
    return ts, acc, v

def main():
    total = int(10 * FPS)
    cortes = [p["a"] for p in PLANOS[1:]]
    trans = {1.5: "zoom", 3.0: "whip", 4.5: "flash", 7.0: "glitch", 8.5: "dip"}
    grng = np.random.default_rng(5)
    for pi, p in enumerate(PLANOS):
        dur = p["b"] - p["a"]
        ts, acc, v = velocidad_integrada(p["vel"], dur)
        s_max = p["t0"] + acc[-1] + .3
        frames, base = leer(p["src"], p["t0"] - .2, s_max - p["t0"] + .5, p["fps"])
        f0, f1 = int(round(p["a"] * FPS)), int(round(p["b"] * FPS))
        print(f"plano {pi}: {p['src']} {p['t0']}s +{acc[-1]:.2f}s fuente, {len(frames)} cuadros", flush=True)
        for f in range(f0, f1):
            t = f / FPS; u = t - p["a"]
            vel = interp(p["vel"], u)
            s = p["t0"] + float(np.interp(u, ts, acc))
            lento = vel < .85
            # motion blur: acumula subcuadros en el intervalo de obturación cuando la velocidad es alta
            if vel > 1.25:
                n = min(7, int(vel * 2))
                span = vel / FPS * .6
                img = np.mean([cuadro_fuente(frames, base, p["fps"], s + span * (i / (n - 1) - .5), False).astype(np.float32) for i in range(n)], axis=0).astype(np.uint8)
            else:
                img = cuadro_fuente(frames, base, p["fps"], s, lento)
            k = ease(u / dur)
            zoom = p["zoom"][0] + (p["zoom"][1] - p["zoom"][0]) * k
            cx = p["cx"][0] + (p["cx"][1] - p["cx"][0]) * k
            sh = (0, 0, 0)
            if p.get("shake"):
                amp = 6 + 10 * max(0, vel - 1)
                sh = (amp * math.sin(t * 37.0), amp * math.sin(t * 29.0 + 1), .25 * math.sin(t * 23.0))
            enc = reencuadre(img, zoom, cx, sh)
            if RAW is not None:
                cv2.imwrite(str(RAW / f"f{f:04d}.jpg"), enc, [cv2.IMWRITE_JPEG_QUALITY, 90])
            x = graduar(enc, p["look"])
            if p.get("tilt"): x = tilt_shift(x)
            x = nitidez(x)
            # transiciones alrededor de cada corte
            for c, tipo in trans.items():
                d = t - c  # negativo: antes del corte
                if abs(d) > .2: continue
                q = 1 - abs(d) / .2
                if tipo == "zoom":
                    x = zoom_blur(x, .35 * q, 1 + (.25 * q if d < 0 else .2 * q))
                    x = np.clip(x + q ** 4 * .35, 0, 1)
                elif tipo == "whip":
                    dx = (-1 if d < 0 else 1) * 520 * q ** 2
                    x = whip(x, dx, 260 * q)
                elif tipo == "flash":
                    x = np.clip(x + (q ** 3) * (.85 if d >= 0 else .45), 0, 1)
                elif tipo == "glitch":
                    if abs(d) < .12: x = glitch(x, q, grng)
                elif tipo == "dip":
                    x = np.clip(x * (1 - .85 * q ** 2) + light_leak(t, .8 * q), 0, 1)
            # light leak suave al inicio y en la caída
            if t < .8: x = np.clip(x + light_leak(t * .7, .35 * (1 - t / .8)), 0, 1)
            if 5.6 < t < 6.4: x = np.clip(x + light_leak(t, .18 * math.sin((t - 5.6) / .8 * math.pi)), 0, 1)
            x = grano(x)
            capa = capa_titulo(t)
            if capa is not None:
                a = capa[..., 3:4]
                # sombra suave para legibilidad
                sombra = cv2.GaussianBlur(a, (0, 0), 18)[..., None] if a.ndim == 3 else None
                x = x * (1 - .45 * sombra) if sombra is not None else x
                x = x * (1 - a) + capa[..., :3] * a
            if t > 8.6: x = x * (1 - .38 * ease((t - 8.6) / .4))
            x = destello_titulo(x, t)
            # entrada desde negro y salida a negro
            if t < .25: x = x * ease(t / .25)
            if t > 9.7: x = x * (1 - ease((t - 9.7) / .3))
            cv2.imwrite(str(OUT / f"f{f:04d}.jpg"), (x[..., ::-1] * 255).astype(np.uint8), [cv2.IMWRITE_JPEG_QUALITY, 93])
        del frames
    print("listo", total)

if __name__ == "__main__":
    main()
