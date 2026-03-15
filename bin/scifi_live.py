#!/usr/bin/env python3
"""
COGITRON — 60s sci-fi computer noise generator.
Streams constant intense beeps, chirps, and warbles to speakers.

Dependencies: sounddevice numpy
    pip install sounddevice numpy
"""

import math
import random
import threading
import time

import numpy as np
import sounddevice as sd

SAMPLE_RATE = 44100   # Hz — increase to 48000 for some DACs, but 44100 is universally safe
BLOCK_SIZE  = 512     # samples per audio callback — lower = less latency, higher = more stable
MAX_VOICES  = 16      # polyphony cap — raise for denser texture, lower to reduce CPU load

# ---------------------------------------------------------------------------
# Global sound character — the two most impactful knobs
# ---------------------------------------------------------------------------

AMP      = 0.60   # master amplitude 0.0–1.0; above ~0.8 the tanh saturator kicks in hard
MIN_GAP  = 0.07   # minimum seconds between spawn bursts — lower = more frantic
MAX_GAP  = 0.22   # maximum seconds between spawn bursts — raise for a calmer, sparser feel

# ---------------------------------------------------------------------------
# Voice definitions
# ---------------------------------------------------------------------------

class Voice:
    """A single synthesised sound event with its own phase/state."""
    __slots__ = ("kind", "freq", "freq_end", "mod_freq", "mod_depth",
                 "phase", "mod_phase", "amp", "samples_left", "total_samples",
                 "done")

    def __init__(self, kind, freq, amp, duration_s,
                 freq_end=None, mod_freq=0.0, mod_depth=0.0):
        self.kind         = kind
        self.freq         = freq
        self.freq_end     = freq_end if freq_end is not None else freq
        self.mod_freq     = mod_freq
        self.mod_depth    = mod_depth
        self.phase        = 0.0
        self.mod_phase    = 0.0
        self.amp          = amp
        self.total_samples = max(1, int(SAMPLE_RATE * duration_s))
        self.samples_left  = self.total_samples
        self.done          = False

    def render(self, n):
        out = np.zeros(n, dtype=np.float32)
        for i in range(n):
            if self.samples_left <= 0:
                self.done = True
                break

            # Envelope: 5ms attack, 20ms release — increase attack for softer onset, release for longer fade
            attack  = min(1.0, self.samples_left / max(1, SAMPLE_RATE * 0.005))
            release = 1.0 - max(0.0, (self.total_samples - self.samples_left
                                       - (self.total_samples - SAMPLE_RATE * 0.02))
                                      / max(1, SAMPLE_RATE * 0.02))
            env = min(attack, max(0.0, release))

            t_norm = 1.0 - self.samples_left / self.total_samples

            if self.kind == "sine":
                s = math.sin(self.phase)
            elif self.kind == "square":
                s = 1.0 if (self.phase % (2 * math.pi)) < math.pi * 0.8 else -1.0
            elif self.kind == "chirp":
                s    = math.sin(self.phase)
                freq = self.freq + (self.freq_end - self.freq) * t_norm
                self.phase += 2 * math.pi * freq / SAMPLE_RATE
                self.samples_left -= 1
                out[i] = s * env * self.amp
                continue
            elif self.kind == "warble":
                inst_freq = self.freq * (1.0 + self.mod_depth * math.sin(self.mod_phase))
                self.mod_phase += 2 * math.pi * self.mod_freq / SAMPLE_RATE
                s = math.sin(self.phase)
                self.phase += 2 * math.pi * inst_freq / SAMPLE_RATE
                self.samples_left -= 1
                out[i] = s * env * self.amp
                continue
            else:
                s = 0.0

            self.phase += 2 * math.pi * self.freq / SAMPLE_RATE
            self.samples_left -= 1
            out[i] = s * env * self.amp

        if self.samples_left <= 0:
            self.done = True
        return out


# ---------------------------------------------------------------------------
# Voice pool
# ---------------------------------------------------------------------------

voices: list[Voice] = []
voices_lock = threading.Lock()


def add_voice(v: Voice):
    with voices_lock:
        if len(voices) < MAX_VOICES:
            voices.append(v)


# ---------------------------------------------------------------------------
# Voice spawner — constant intense activity
# ---------------------------------------------------------------------------

# Musical frequencies for sine beeps (Hz) — these are C major scale notes across 3 octaves.
# Remove high values (>1000) for a mellower tone, or add sub-bass (<200) for a rumblier feel.
BEEP_FREQS = [523, 587, 659, 698, 784, 880, 988, 1047,
              1175, 1319, 1397, 1568, 1760, 1976]

def spawner():
    rng = random.Random()

    while True:
        # Burst size: how many voices fire at once. Raise the upper bound for denser blasts.
        n_burst = rng.randint(1, 2)
        for _ in range(n_burst):
            roll = rng.random()

            # Voice-type mix — thresholds are cumulative:
            #   0.00–0.50 → sine beep  (50%)
            #   0.50–0.85 → chirp      (35%)
            #   0.85–1.00 → warble     (15%)
            # Shift these numbers to change the character of the mix.

            if roll < 0.50:
                # Sine beep — pure tones; short duration keeps them punchy
                freq = rng.choice(BEEP_FREQS)
                add_voice(Voice("sine", freq, AMP * 0.8,
                                rng.uniform(0.03, 0.10)))  # duration range (s)
            elif roll < 0.85:
                # Chirp — linear frequency sweep; wide range = more dramatic swoops
                f0 = rng.uniform(200, 1200)   # sweep start frequency (Hz)
                f1 = rng.uniform(600, 2400)   # sweep end frequency (Hz)
                if rng.random() < 0.5:
                    f0, f1 = f1, f0           # 50% chance of falling instead of rising
                add_voice(Voice("chirp", f0, AMP * 0.75,
                                rng.uniform(0.08, 0.30), freq_end=f1))  # duration range (s)
            else:
                # Warble — FM-modulated tone; mod_freq controls wobble rate, mod_depth controls width
                freq = rng.choice([330, 440, 550, 660, 770, 880])  # carrier frequencies (Hz)
                add_voice(Voice("warble", freq, AMP * 0.65,
                                rng.uniform(0.2, 0.6),              # duration range (s)
                                mod_freq=rng.uniform(4, 12),        # wobble rate (Hz); higher = faster
                                mod_depth=rng.uniform(0.2, 0.5)))   # wobble width; 0=none, 1=very wide

        time.sleep(rng.uniform(MIN_GAP, MAX_GAP))


# ---------------------------------------------------------------------------
# Audio callback
# ---------------------------------------------------------------------------

def audio_callback(outdata: np.ndarray, frames: int, time_info, status):
    if status:
        print(f"[audio status] {status}")

    mix = np.zeros(frames, dtype=np.float32)

    with voices_lock:
        for v in voices:
            if not v.done:
                mix += v.render(frames)
        voices[:] = [v for v in voices if not v.done]

    np.clip(mix, -1.0, 1.0, out=mix)
    mix = np.tanh(mix * 0.9)  # soft saturation — lower the 0.9 coefficient for less compression/drive

    outdata[:, 0] = mix


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("COGITRON online. Press Ctrl+C to stop.\n")

    t_spawn = threading.Thread(target=spawner, daemon=True)
    t_spawn.start()

    with sd.OutputStream(samplerate=SAMPLE_RATE,
                         blocksize=BLOCK_SIZE,
                         channels=1,
                         dtype="float32",
                         callback=audio_callback):
        try:
            while True:
                with voices_lock:
                    n = len(voices)
                print(f"\r{n:3d} voices", end="", flush=True)
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("\nCOGITRON offline.")
