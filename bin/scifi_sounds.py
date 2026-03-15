#!/usr/bin/env python3
"""
60s sci-fi computer noise generator.
Produces 10 seconds of classic beeps, warbles, blips, and electronic chirps.
Output: scifi_computer.wav
"""

import wave
import struct
import random
import math
import os

SAMPLE_RATE = 44100
DURATION = 10  # seconds
NUM_SAMPLES = SAMPLE_RATE * DURATION

# --- Oscillator primitives ---

def sine(t, freq):
    return math.sin(2 * math.pi * freq * t)

def square(t, freq, duty=0.5):
    phase = (freq * t) % 1.0
    return 1.0 if phase < duty else -1.0

def noise():
    return random.uniform(-1.0, 1.0)

# --- Sound generators (each returns a list of float samples) ---

def beep(duration_s, freq, amplitude=0.6, shape="sine"):
    """Simple tone with fast attack/release envelope."""
    n = int(SAMPLE_RATE * duration_s)
    attack = int(SAMPLE_RATE * 0.005)
    release = int(SAMPLE_RATE * 0.015)
    samples = []
    for i in range(n):
        t = i / SAMPLE_RATE
        if shape == "sine":
            s = sine(t, freq)
        elif shape == "square":
            s = square(t, freq, duty=0.4)
        else:
            s = sine(t, freq)
        # envelope
        if i < attack:
            env = i / attack
        elif i > n - release:
            env = (n - i) / release
        else:
            env = 1.0
        samples.append(s * env * amplitude)
    return samples

def warble(duration_s, center_freq, mod_freq, mod_depth=0.4, amplitude=0.55):
    """FM warble: carrier frequency oscillates up and down."""
    n = int(SAMPLE_RATE * duration_s)
    samples = []
    phase = 0.0
    for i in range(n):
        t = i / SAMPLE_RATE
        freq = center_freq * (1.0 + mod_depth * sine(t, mod_freq))
        phase += 2 * math.pi * freq / SAMPLE_RATE
        s = math.sin(phase)
        samples.append(s * amplitude)
    return samples

def chirp(duration_s, start_freq, end_freq, amplitude=0.55):
    """Linear frequency sweep (rising or falling)."""
    n = int(SAMPLE_RATE * duration_s)
    attack = int(SAMPLE_RATE * 0.005)
    release = int(SAMPLE_RATE * 0.015)
    samples = []
    phase = 0.0
    for i in range(n):
        t = i / n  # 0..1
        freq = start_freq + (end_freq - start_freq) * t
        phase += 2 * math.pi * freq / SAMPLE_RATE
        s = math.sin(phase)
        if i < attack:
            env = i / attack
        elif i > n - release:
            env = (n - i) / release
        else:
            env = 1.0
        samples.append(s * env * amplitude)
    return samples

def blip_sequence(total_duration_s, freqs, blip_dur=0.04, gap=0.03, amplitude=0.5):
    """Rapid sequence of short beeps at given frequencies."""
    total_n = int(SAMPLE_RATE * total_duration_s)
    buf = [0.0] * total_n
    t = 0.0
    idx = 0
    while t + blip_dur < total_duration_s and idx < len(freqs):
        b = beep(blip_dur, freqs[idx % len(freqs)], amplitude)
        start = int(t * SAMPLE_RATE)
        for j, s in enumerate(b):
            if start + j < total_n:
                buf[start + j] += s
        t += blip_dur + gap
        idx += 1
    return buf

def static_burst(duration_s, amplitude=0.08):
    """Low-level white noise blip."""
    n = int(SAMPLE_RATE * duration_s)
    return [noise() * amplitude for _ in range(n)]

def overlay(base, patch, offset_samples):
    """Mix patch into base starting at offset_samples."""
    for i, s in enumerate(patch):
        idx = offset_samples + i
        if idx < len(base):
            base[idx] += s
        else:
            base.append(s)

# --- Compose 10 seconds ---

def compose():
    random.seed(42)
    buf = [0.0] * NUM_SAMPLES

    # Classic "computer thinking" blip sequences
    thinking_freqs = [880, 1046, 784, 1174, 659, 987, 523, 1318]
    overlay(buf, blip_sequence(2.5, thinking_freqs, blip_dur=0.045, gap=0.025), 0)

    # Long warble (comm system sound)
    overlay(buf, warble(1.8, center_freq=440, mod_freq=6.5, mod_depth=0.35), int(0.3 * SAMPLE_RATE))

    # Rising chirp (alert)
    overlay(buf, chirp(0.4, 300, 1800, amplitude=0.5), int(2.6 * SAMPLE_RATE))

    # Fast blip burst (data transfer)
    burst_freqs = [1047, 1175, 1319, 1047, 880, 988, 1175, 784, 1047, 1319]
    overlay(buf, blip_sequence(1.2, burst_freqs, blip_dur=0.03, gap=0.015, amplitude=0.45), int(3.1 * SAMPLE_RATE))

    # Warble at different frequency (secondary system)
    overlay(buf, warble(2.0, center_freq=660, mod_freq=4.2, mod_depth=0.5, amplitude=0.4), int(3.5 * SAMPLE_RATE))

    # Short confirmation beep
    overlay(buf, beep(0.12, 1047, amplitude=0.55, shape="sine"), int(4.2 * SAMPLE_RATE))
    overlay(buf, beep(0.12, 1319, amplitude=0.55, shape="sine"), int(4.38 * SAMPLE_RATE))
    overlay(buf, beep(0.25, 1568, amplitude=0.55, shape="sine"), int(4.56 * SAMPLE_RATE))

    # Descending alert sweep
    overlay(buf, chirp(0.5, 2000, 400, amplitude=0.45), int(5.1 * SAMPLE_RATE))

    # Another blip sequence (navigation computer)
    nav_freqs = [523, 587, 659, 698, 784, 880, 988, 1047]
    overlay(buf, blip_sequence(1.5, nav_freqs, blip_dur=0.06, gap=0.04, amplitude=0.4), int(5.7 * SAMPLE_RATE))

    # Square wave buzz (relay switching)
    overlay(buf, beep(0.08, 220, amplitude=0.3, shape="square"), int(6.4 * SAMPLE_RATE))
    overlay(buf, beep(0.08, 220, amplitude=0.3, shape="square"), int(6.52 * SAMPLE_RATE))
    overlay(buf, beep(0.08, 220, amplitude=0.3, shape="square"), int(6.64 * SAMPLE_RATE))

    # Fast warble (incoming transmission)
    overlay(buf, warble(1.5, center_freq=800, mod_freq=12.0, mod_depth=0.6, amplitude=0.4), int(7.0 * SAMPLE_RATE))

    # Scattered random blips in background
    for _ in range(18):
        t_offset = random.uniform(0.5, 9.5)
        freq = random.choice([523, 659, 784, 880, 1047, 1175, 1319, 1568])
        dur = random.uniform(0.02, 0.07)
        amp = random.uniform(0.15, 0.3)
        overlay(buf, beep(dur, freq, amplitude=amp), int(t_offset * SAMPLE_RATE))

    # Light static noise throughout
    static = static_burst(DURATION, amplitude=0.04)
    for i in range(NUM_SAMPLES):
        if i < len(static):
            buf[i] += static[i]

    # Final two-tone sign-off
    overlay(buf, beep(0.3, 880, amplitude=0.5), int(9.2 * SAMPLE_RATE))
    overlay(buf, beep(0.5, 440, amplitude=0.5), int(9.55 * SAMPLE_RATE))

    # Normalize to prevent clipping
    peak = max(abs(s) for s in buf)
    if peak > 0.95:
        scale = 0.95 / peak
        buf = [s * scale for s in buf]

    return buf

# --- Write WAV ---

def write_wav(filename, samples):
    with wave.open(filename, "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)  # 16-bit
        wf.setframerate(SAMPLE_RATE)
        packed = struct.pack(f"<{len(samples)}h",
                             *(int(s * 32767) for s in samples))
        wf.writeframes(packed)

if __name__ == "__main__":
    output = os.path.join(os.path.dirname(__file__), "scifi_computer.wav")
    print("Generating 60s sci-fi computer noises...")
    samples = compose()
    write_wav(output, samples)
    print(f"Done. Written to: {output}")
    print(f"Duration: {len(samples) / SAMPLE_RATE:.1f}s  |  Samples: {len(samples)}")
