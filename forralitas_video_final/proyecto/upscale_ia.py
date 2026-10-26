"""Upscaler con IA (Real-ESRGAN realesr-general-x4v3, arquitectura SRVGGNetCompact) en CPU.

Uso:  python upscale_ia.py entrada.mp4 salida.mp4 [--escala 2.25] [--ss 0 --t 3]
El modelo amplía x4; después se reduce con Lanczos al tamaño final (por defecto 1080x1944 → recorte a 1080x1920).
"""
import argparse
import os
import subprocess

import cv2
import numpy as np
import torch
from torch import nn
from torch.nn import functional as F

MODELO = os.environ.get("REALESRGAN_PTH", os.path.join(os.path.dirname(__file__), "modelos", "realesr-general-x4v3.pth"))


class SRVGGNetCompact(nn.Module):
    def __init__(self, num_feat=64, num_conv=32, upscale=4):
        super().__init__()
        self.upscale = upscale
        body = [nn.Conv2d(3, num_feat, 3, 1, 1), nn.PReLU(num_parameters=num_feat)]
        for _ in range(num_conv):
            body += [nn.Conv2d(num_feat, num_feat, 3, 1, 1), nn.PReLU(num_parameters=num_feat)]
        body += [nn.Conv2d(num_feat, 3 * upscale * upscale, 3, 1, 1)]
        self.body = nn.ModuleList(body)
        self.upsampler = nn.PixelShuffle(upscale)

    def forward(self, x):
        out = x
        for m in self.body:
            out = m(out)
        out = self.upsampler(out)
        return out + F.interpolate(x, scale_factor=self.upscale, mode="nearest")


def cargar_modelo():
    net = SRVGGNetCompact()
    sd = torch.load(MODELO, map_location="cpu")
    sd = sd.get("params_ema", sd.get("params", sd))
    net.load_state_dict(sd, strict=True)
    return net.eval()


@torch.inference_mode()
def ampliar(net, rgb):
    x = torch.from_numpy(rgb).permute(2, 0, 1).float().div(255).unsqueeze(0)
    y = net(x).clamp(0, 1)[0].permute(1, 2, 0).numpy()
    return (y * 255 + 0.5).astype(np.uint8)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("entrada")
    ap.add_argument("salida")
    ap.add_argument("--ancho", type=int, default=1080)
    ap.add_argument("--ss", type=float, default=0)
    ap.add_argument("--t", type=float, default=None)
    a = ap.parse_args()
    torch.set_num_threads(os.cpu_count())
    net = cargar_modelo()
    cap = cv2.VideoCapture(a.entrada)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    cap.set(cv2.CAP_PROP_POS_MSEC, a.ss * 1000)
    n_max = int(a.t * fps) if a.t else 10 ** 9
    w0, h0 = int(cap.get(3)), int(cap.get(4))
    W = a.ancho
    H = int(round(h0 * W / w0 / 2) * 2)
    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(fps),
           "-i", "-", "-c:v", "libx264", "-crf", "10", "-preset", "slow", "-pix_fmt", "yuv420p", a.salida]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    n = 0
    while n < n_max:
        ok, f = cap.read()
        if not ok:
            break
        rgb = cv2.cvtColor(f, cv2.COLOR_BGR2RGB)
        up = ampliar(net, rgb)
        out = cv2.resize(up, (W, H), interpolation=cv2.INTER_AREA)
        p.stdin.write(out.tobytes())
        n += 1
        if n % 30 == 0:
            print(a.salida, n, "cuadros", flush=True)
    p.stdin.close()
    p.wait()
    print("listo", a.salida, n, "cuadros")


if __name__ == "__main__":
    main()
