"""Música de fondo original para la invitación web (vals suave tipo caja de música). Uso: python3 audio/musica_invitacion.py salida.wav"""
import sys
import numpy as np
from sintes import SR, campana, pad, poner, reverb, guardar_wav, sub

BPM = 84; B = 60 / BPM
prog = [(62, 66, 69), (59, 62, 66), (55, 59, 62), (57, 61, 64)]  # D Bm G A
mel = [74, 73, 71, 69, 71, 73, 74, 76, 78, 76, 74, 73, 71, 69, 66, 69]
bars = 16
dur = bars * 3 * B
L = np.zeros(int(SR * (dur + 3)))
for b in range(bars):
    ch = prog[b % 4]; st = b * 3 * B
    poner(L, st, pad([n - 12 for n in ch], 3 * B + .6, 1400, .09, .5, .6))
    poner(L, st, sub(ch[0] - 24, B * .9, .18))
    for k in (1, 2):
        poner(L, st + k * B, campana(ch[k % 3] + 12, 1.2, .07))
    poner(L, st, campana(mel[b], 2.2, .16))
    if b % 2: poner(L, st + 1.5 * B, campana(mel[b] - 3 + 12, 1.0, .05))
L = reverb(L, 3.0, .35)
# cola cruzada para que el loop sea continuo
cola = L[int(SR * dur):]
L = L[:int(SR * dur)]; L[:len(cola)] += cola
L = L / np.max(np.abs(L)) * .7
guardar_wav(sys.argv[1], np.stack([L, np.roll(L, 30)], 1))
