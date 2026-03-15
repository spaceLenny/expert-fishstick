# COGITRON

> *"The COGITRON is processing your request..."*

COGITRON fills your terminal sessions with authentic 60s B-movie computer sounds — rapid beeps, chirps, and warbles that scale in intensity with your CPU load. Plug it into [Claude Code](https://claude.ai/claude-code) hooks and your AI assistant will sound like it's running on a room-sized mainframe.

```
 17.3%   8 voices  [#####                         ]
 42.1%  14 voices  [#############                 ]
 89.6%  29 voices  [###########################   ]
```

---

## Requirements

- macOS or Linux
- Python 3.9+
- [Claude Code](https://claude.ai/claude-code) (for the hooks integration)

> **macOS note:** `sounddevice` requires PortAudio. Install it with `brew install portaudio` if the installer fails.

Dependencies: `sounddevice`, `numpy` (the installer handles these).

---

## Installation

```sh
git clone https://github.com/spaceLenny/expert-fishstick.git
cd cogitron
./install.sh
source ~/.zshrc
```

That's it. The installer:

1. Creates a `.venv` and installs Python dependencies
2. Registers start/stop hooks in `~/.claude/settings.json`
3. Adds `scifi-on`, `scifi-off`, and `scifi-toggle` aliases to your shell

---

## Usage

```sh
scifi-on      # enable — sounds will play on your next Claude prompt
scifi-off     # disable + kill any running instance
scifi-toggle  # flip current state
```

Once enabled, sounds start automatically when you submit a prompt to Claude Code and stop when Claude finishes responding. No manual babysitting required.

### Run it standalone

```sh
# Live CPU-reactive stream (Ctrl+C to stop)
.venv/bin/python bin/scifi_live.py

# Generate a sample WAV file (no dependencies beyond stdlib)
.venv/bin/python bin/scifi_sounds.py
```

---

## How it works

`scifi_live.py` maintains a pool of up to 32 simultaneous voices, spawning new ones continuously at a rate driven by CPU load.

### Voice types

| Type | Weight | Description |
|------|--------|-------------|
| **sine beep** | 50% | Short pure tone at a musical frequency |
| **chirp** | 35% | Linear frequency sweep (rising or falling) |
| **warble** | 15% | FM-modulated tone — that classic computer-thinking sound |

Events fire in bursts of 1–3, with 40–130ms between bursts. Up to 32 voices play simultaneously.

Each voice has a 5ms attack and 20ms release envelope. The final mix runs through a soft tanh saturator to keep things loud without harsh clipping.

---

## Customization

All tweakable values are in `bin/scifi_live.py`. The most impactful ones:

### Overall character

| Constant | Default | Effect |
|----------|---------|--------|
| `AMP` | `0.60` | Master volume (0.0–1.0). Above ~0.8 the saturator clips hard. |
| `MIN_GAP` | `0.04` | Minimum seconds between bursts. Lower = more frantic. |
| `MAX_GAP` | `0.13` | Maximum seconds between bursts. Raise for a calmer, sparser sound. |
| `MAX_VOICES` | `32` | Polyphony cap. Lower to reduce CPU load; raise for a denser wall of sound. |

### Voice type mix

In `spawner()`, the three `roll < N` thresholds control how often each voice type fires:

```python
if roll < 0.50:     # 50% → sine beep
elif roll < 0.85:   # 35% → chirp
else:               # 15% → warble
```

Change those numbers (they must be ascending and ≤ 1.0) to shift the character — e.g. push chirps to 60% for a more sweepy feel, or warbles to 30% for the classic "thinking computer" effect.

### Per-voice parameters

| Voice | What to tune | Where |
|-------|-------------|-------|
| **Sine beep** | `BEEP_FREQS` list — remove high values for a mellower tone | line ~115 |
| **Sine beep** | Duration `(0.03, 0.10)` — increase for longer sustained tones | `spawner()` |
| **Chirp** | Frequency ranges `(200, 1200)` / `(600, 2400)` — narrow for subtle sweeps | `spawner()` |
| **Chirp** | Duration `(0.08, 0.30)` — longer = more dramatic | `spawner()` |
| **Warble** | `mod_freq (4, 12)` Hz — higher = faster wobble | `spawner()` |
| **Warble** | `mod_depth (0.2, 0.5)` — higher = wider pitch swing | `spawner()` |

### Envelope & saturation

- Attack/release times are in `Voice.render()` — search for `0.005` (5ms attack) and `0.02` (20ms release).
- The tanh saturator coefficient (`0.9` in `audio_callback`) controls drive. Lower it for a cleaner, less compressed mix.

---

## Claude Code hooks

COGITRON wires into two Claude Code hook events:

| Event | Script | Effect |
|-------|--------|--------|
| `UserPromptSubmit` | `start_sounds.sh` | Starts audio (async, if flag file present) |
| `Stop` | `stop_sounds.sh` | Kills the audio process |

The flag file at `~/.claude/scifi_sounds_enabled` acts as the on/off switch. The running process PID is tracked at `/tmp/scifi_sounds.pid`.

The installer merges these hooks into your existing `~/.claude/settings.json` non-destructively — any other hooks you have configured are left untouched.

---

## Inspiration

- [MST3K](https://www.youtube.com/live/B7qOZraAIlw) — the gold standard for 60s sci-fi computer aesthetics
- [Man or Astro-man?](https://www.youtube.com/watch?v=GrhLdjIKsV0) — sonic reference for the beeps and chirps
- [mact.io](https://www.mact.io/) — the original spark for this idea

---

## Uninstall

```sh
./uninstall.sh
source ~/.zshrc
```

This removes the hooks from `~/.claude/settings.json`, removes the shell aliases, stops any running instance, and optionally deletes the `.venv`.

---

## Project structure

```
bin/
  scifi_live.py      # Live CPU-reactive audio stream
  scifi_sounds.py    # Offline WAV generator (no extra deps)
  start_sounds.sh    # Hook: start audio if enabled
  stop_sounds.sh     # Hook: stop audio
install.sh           # One-command setup
uninstall.sh         # Full teardown
requirements.txt     # Python dependencies
```
