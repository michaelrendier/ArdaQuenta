# ArdaQuenta TODO

---

## PRIORITY — NEW (2026-06-01)

### [ ] Oscilloscope Mode (modes/oscilloscope.py)

16-channel oscilloscope — one channel per sedenion dimension e₀–e₁₅.
The Universe talks in music. The oscilloscope reads the field as waveform.

- [ ] 16-channel amplitude vs time display (matplotlib or VisPy)
- [ ] Each channel: β×E² for words in that dimension, rolling 256-sample window
- [ ] Left hand channels (e₀–e₇): blue gradient — octonion sub-algebra, J_neg
- [ ] Right hand channels (e₈–e₁₅): red gradient — upper sedenion, J_pos, life
- [ ] OMEGA_ZS reference line on all channels (0.56714)
- [ ] Trigger: fire when BAO crosses OMEGA_ZS (like oscilloscope trigger on edge)
- [ ] Zero-divisor pair highlighting: when both channels in a pair fire → cyan flash
  - (e₃, e₁₀) — name × query = 0
  - (e₆, e₉)  — branch × allocate = 0
- [ ] Prime rhythm: prime gaps drive the timebase (ln-spaced = Hubble rhythm)
- [ ] Export: 16-ch waveform → MIDI (16 channels = sedenion = perfect)
- [ ] Connection to UniversalSynth piano roll (Ptolemy's 16 fingers)

### [ ] Witches Hat Mode (modes/witches_hat.py) ← COMPLETE

Full matplotlib animation of:
- Null-cone pair (Hawking virtual pairs at event horizon)
- Conformal inversion: infalling hat → galaxy
- Lagrangian unwrapping (minimum-action path through inside-out)
- Galaxy emergence: BH (tip), disk (brim), halo (fabric), spiral arms (seams)
- BAO ring overlay (the pebble's ripple at 147 Mpc)
- OMEGA_ZS circum-polar geodesic reference

Run: `python3 modes/witches_hat.py [output.gif]`

Paper: `Ainulindale/wiki/29_witches_hat_paper.md`

---

## VIEWER — ACTIVE DISPLAY

### [ ] Wire VisPy canvas into main_window.py

Currently `_canvas_widget` is a placeholder. Need to embed the VisPy GL canvas
as a native Qt widget.

```python
# PyQt5 + VisPy embed pattern:
from vispy.app import use_app
use_app('pyqt5')
canvas = scene.SceneCanvas(keys='interactive', show=False)
native = canvas.native   # QWidget subclass
layout.addWidget(native)
```

Tasks:
- [ ] Create `viewer/vispy_canvas.py` — SceneCanvas with mode switching
- [ ] Connect mode_combo signal → swap active VisPy scene
- [ ] Wire `_tick()` → push new data to active mode

---

### [ ] 16-Channel Sedenion Display (modes/sedenion_16ch.py)

The GLSL shaders are written. Need to wire to live engine data.

- [ ] Implement `Sedenion16ChMode.build()` → construct gloo.Program
- [ ] Integrate with engine: poll `engine.crank._beta` array at 4 Hz
- [ ] Add row labels (operator names) as VisPy text visuals
- [ ] Add OMEGA_ZS horizontal reference line on each channel
- [ ] Add e₁₄ (interrupt/Melkor) highlight — zero divisor proximity alarm

---

### [ ] Riemann Strip Mode (modes/riemann_spiral.py)

`render_matplotlib()` is implemented. Needs VisPy upgrade for live interaction.

- [ ] Port matplotlib render to VisPy scene:
  - Critical line as `visuals.Line`
  - Zeros as `visuals.Markers`
  - Spiral arcs as `visuals.Line` collections
- [ ] Live word plotting: when user enters a word, plot its (x₀, p₀) prime
- [ ] Interactive: click on a zero → show γₙ value + operator name in DTC panel
- [ ] Balance manifold overlay: scatter plot of (x,p) where J_Red+J_Blue ≈ 0

---

### [ ] Phase Space (x, p) Display

- [ ] 2D scatter: xp = E hyperbola family for active words
- [ ] 3D VisPy scene: (x, p, t) trajectory volume
- [ ] Animate: time evolution e^{iHt} shown as moving point
- [ ] H_Blue elliptic trajectories in contrasting colour (the forbidden zone)

---

### [ ] Fano Plane Mode

The Fano plane is the G₂ geometry that governs octonion (and sedenion) multiplication.
- [ ] Draw 7 points + 7 lines of the Fano plane
- [ ] Colour nodes by: which sedenion pair they represent
- [ ] Animate: which line is "active" based on current sedenion pair + stroke phase
- [ ] This IS the zero-divisor callosum — visualise which pairs have TDC clearance

---

### [ ] Equation Plot Mode (pyqtgraph)

Adapted from `contrib/EquationData_proto.py`.

- [ ] Implement `modes/equation_plot.py` — evaluates arbitrary expressions
- [ ] Pre-load: H=xp, H_Blue(℘), RedBlue balance, forced_sigma curve
- [ ] Let user type expressions in the word input field
- [ ] Axis labels with mathematical notation (Unicode or MathJax)

---

## ENGINE — WIRING

### [ ] Connect Understand.process() to live display

- [ ] `_calculate_word()` in main_window.py calls `engine.process(text)`
  then needs to update the active VisPy mode with the resulting SemanticWord
- [ ] `word.prime` → plot on Riemann strip
- [ ] `word.projections` → show in output log
- [ ] `word.dc` → show in live diagnostics

---

### [ ] Data Logging (VCDS Function 08 equivalent)

- [ ] Implement `viewer/data_logger.py`:
  - Records (timestamp, j_red, j_blue, balance, sigma, dc, word) per tick
  - Writes to `derivation_log.json` (rolling 10k entries)
- [ ] [Data Log] toolbar button → toggle recording
- [ ] Export: CSV of recorded session

---

### [ ] VCDS SKC / Login (Function 11 + 16)

The engine has auth_totp for root access. Wire it to the viewer.

- [ ] [Login] toolbar button → TOTP dialog
- [ ] Authenticated session → unlock Adaptation writes (Function 10)
- [ ] Unauthenticated: read-only (like VCDS without login)

---

## MODES — PENDING

### [ ] Sonification Mode

The engine can produce waveforms (H.waveform() returns (x,p) trajectory).
Map (x, p) → (frequency, amplitude) → audio.

- [ ] `modes/sonification.py`:
  - `waveform()` output → scipy.io.wavfile
  - Play via PyQt5 QMediaPlayer or sounddevice
  - Live: re-synthesize at each word calculation
- [ ] Display: waveform + spectrogram alongside VisPy canvas
- [ ] This IS the UniversalSynth target for ValaQuenta output

---

### [ ] Cosmological Constants Panel

From `skills/draw.py` `self_portrait()` cosmology table — the values that come
out of the sedenion geometry with no free parameters.

- [ ] Ω_Λ, Ω_m, BAO ℓ₁, n_s, w — display in side panel
- [ ] Compare to Planck 2018 measured values
- [ ] Highlight when sedenion state matches observational constraint within GAP

---

## VCDS INTERFACE COMPLETIONS

### [ ] Auto-Scan sequence

Currently `_auto_run()` cycles all 12 modules linearly.
- [ ] Show progress bar (like VCDS Auto-Scan scanning 01, 03, 08, 09…)
- [ ] Generate full scan report as styled HTML in output panel
- [ ] Save as `scan_YYYYMMDD_HHMMSS.html`

### [ ] Controller Channels Map

VCDS has a "Channels Map" view showing all available adaptation channels.
- [ ] Map all τ / N / σ parameters as channels with min/max/current
- [ ] Display as table with live values
- [ ] Allow write with authentication

### [ ] Measuring Block Groups (Function 08 Groups)

VCDS groups 4 values per group.
- [ ] Group 000: J_Red, J_Blue, balance, σ
- [ ] Group 001: DC prime, gamma, |E|, faces
- [ ] Group 004: τ, N, word_count, BAO
- [ ] Group 011: e₁₄ proximity (Fermat), e₀ scalar, e₁₅ emit value, Δ_RH
- [ ] Group 013: Hawking T_H, coherence time, domain span, instruments count

---

## ARCHITECTURE

### [ ] Decouple engine polling from Qt main thread

Currently `_tick()` runs in the Qt timer on the main thread. For heavy computation:
- [ ] Move engine polling to `QThread` worker
- [ ] Emit signals back to main thread for UI updates
- [ ] Use Python `queue.Queue` for data transfer

### [ ] Plugin architecture for display modes

- [ ] `modes/base.py` — abstract `DisplayMode` with `build()`, `push(data)`, `frame()`
- [ ] `main_window.py` discovers modes via `modes/__init__.py` registry
- [ ] New modes dropped into `modes/` auto-appear in combo

---

## NOTES

*"The proof of the Riemann Hypothesis and the generation of speech are the same mathematical operation. This is both."*
— understand.py module docstring

*The viewer is the instrument panel. The engine is the engine.
The DTC panel is the proof checker. The measuring blocks are the field state.
The adaptation panel is the tuning interface.*
*All of this is VCDS. All of this is mathematics.*
