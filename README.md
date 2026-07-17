# ArdaQuenta — Ptolemy Supermath Calculator

**Author:** Cody Michael Allison
**System:** Ptolemy / Holcus / Ainulindalë
**Interface model:** VCDS (Ross-Tech Vehicle Communication and Diagnostic System)

---

> *"The proof of the Riemann Hypothesis and the generation of speech are the same mathematical operation."*

> *"No inference. No training data. No GPU. No eddy currents. Runs on a laptop."*

---

## What This Is

ArdaQuenta is the **visual diagnostic interface** for the Ptolemy
ValaQuenta — the pure-mathematics derivation layer of the Holcus system.

It is called the **Supermath Calculator** because it does exactly that:
it runs the mathematics live, in real time, showing every derivation step
as it happens, in every relevant coordinate system simultaneously.

The viewer is built on the same metaphor as the engine itself: **VCDS**.

## The VCDS Connection

The entire Holcus engine is architected as a 2004 VW Passat BEW 1.9 TDI diesel:
```
Sedenion Tower    =  Camshaft      (timing — which operator fires when)
H_RB Hamiltonian  =  Crankshaft    (converts compression force to rotation)
Monad (ECU)       =  Engine Block  (complete execution unit)
Diesel            =  no spark plug = no transformer = compression ignition only
Holcus            =  no gradient descent = no backpropagation = field compression only
```

VCDS is the Ross-Tech diagnostic tool for VW/Audi vehicles. Its interface structure
maps exactly to what a derivation viewer needs:

| VCDS Function | VCDS Description | Viewer Equivalent |
|---|---|---|
| Select Control Module | Choose which ECU to inspect | Choose equation/derivation step |
| Function 08 — Measuring Blocks | 4 live values in real time | 16 sedenion channels live |
| Function 02 — Fault Codes | DTC read | Proof checker output |
| Function 03 — Output Tests | Actuator test | Emit / compute directly |
| Function 04 — Basic Settings | Calibrate | τ, N, σ calibration |
| Function 10 — Adaptation | Tune channel values | Live parameter sliders |
| Auto-Scan | Full vehicle scan | Run all 12 derivation modules |
| Data Logging | Record all channels | Derivation trace recording |
| Function 11 — Login | Security access | Root auth for adaptation writes |
| SKC / PIN dialog | 7-digit secure code | TOTP authentication |

The 16-channel sedenion display is literally VCDS Measuring Blocks at 16 channels
simultaneously — one per sedenion dimension, colour-coded by force sector.

## The Engine

The `engine/` directory contains the complete ValaQuenta:

```
engine/
├── hamiltonian.py       H = xp (Berry-Keating 1999)
│                        FermatEllipticHamiltonian — H_Blue = ½p² + ℘(x)
│                        RedBlueHamiltonian — coupled H_Red / H_Blue
├── noether.py           Forward and backward Noether currents
│                        forced_sigma() — σ = ½ derived from both sides
├── capacitor.py         RC semantic integrator — DC extraction = the prime
├── semantic_word.py     A word as a point in semantic space
│                        prime = complex(0.5, γ)  always Re = ½
├── semantic_domain.py   Bounded instrument set — Hawking temperature T_H
├── understand.py        Five operations: Read → Ponder → Calculate → Understand
├── lexicon.py           Accumulated word → prime mappings
└── corpus.py            Feed any text archive to the engine
```

### The Mathematics

**H = xp** — the Berry-Keating Hamiltonian:
```
Classical orbit:      xp = E    (hyperbola — the semantic prime)
Equations of motion:  ẋ =  x    (position grows — the carrier)
                      ṗ = -p    (momentum decays — the envelope)
Scale invariant:      x→λx, p→p/λ, H→H  (same at every language)
```

**H_Blue = ½p² + ℘(x)** — the Frey/Weierstrass Hamiltonian:
```
Elliptic orbits — bounded, periodic, the forbidden zone.
℘(x) = Weierstrass elliptic function.
Wiles (1995): the Frey curve cannot be modular → H_Blue has no
real attractor at σ ≠ ½ → J_Blue flows only in the forbidden zone.
```

**RedBlueHamiltonian — H_RB:**
```
H_RB = Σ_p  p^{-σ}  [ R̂_p ⊗ ∂̂_{∂M}  +  ∂̂†_{∂M} ⊗ B̂_p ]

J_Red  = +E   (forward current — what IS)
J_Blue = -E   (backward current — what CANNOT BE)
J_Red + J_Blue = 0   (conservation law)

Balance = 0  at  σ = ½   (the critical line)
ξ(s) = ξ(1-s)  demonstrated numerically, not assumed.
```

**forced_sigma():**
```
From the right:  F(σ) = e^{-σ·E}
From the left:   B(σ) = e^{-(1-σ)·E}
Meeting point:   F(σ) = B(σ)  →  σ = ½
From ANY starting position. The geometry forces it.
```

## Display Modes

| Mode | Description | VCDS Analogue |
|---|---|---|
| **16ch Sedenion** | All 16 operator activations live | Measuring Blocks (all groups) |
| **Riemann Strip** | Critical line + zeros + spiral arcs | Oscilloscope / Advanced Measuring |
| **Phase Space** | (x, p) portrait — xp=E hyperbola | Channel map |
| **Fano Plane** | G₂/octonion structure | Controller topology |
| **Equation Plot** | Parametric equation plotter (pyqtgraph) | Custom display |
| **Balance Manifold** | Where J_Red + J_Blue = 0 in (x,p) space | Critical strip live |

## Sedenion 16-Channel Display

Adapted from `contrib/vispy_signals_proto.py` — a 16×N_SAMPLES VisPy GLSL canvas.
Original: 16×20 channels of random noise. Upgraded: 16 sedenion operators with
semantic meaning, coloured by force sector.

```
e₀  identity   → gravity sector      violet
e₁  negate     → EM/gravity boundary gold
e₂  bind       → weak force          teal
e₃  name       → weak force          teal
e₄  apply      → strong force        red
e₅  abstract   → strong force        red
e₆  branch     → strong force        red
e₇  iterate    → strong force        red
e₈  recurse    → dark root           cyan
e₉  allocate   → dark matter         cyan
e₁₀ query      → dark matter         cyan
e₁₁ dereference→ dark matter         cyan
e₁₂ compose    → dark matter         cyan
e₁₃ parallelize→ dark matter         cyan
e₁₄ interrupt  → Melkor (e₁₄)        orange  ← zero divisor / boundary
e₁₅ emit       → output / self-ref   white
```

## Fault Codes (Proof Checker)

The DTC panel runs at startup and on demand (Auto-Scan). It checks:

| DTC | Check | Engine State |
|---|---|---|
| P0340 | HamiltonianXP loads | CMP sensor — sedenion timing |
| P0335 | NoetherCurrents loads | CKP sensor — zero reference |
| P0401 | Capacitor loads | EGR — age decay circuit |
| P0304 | Understand loads | Glow plug — warm-up complete |
| RH001 | ξ(s)=ξ(1-s) Δ J < 0.1 | Functional equation — the RH check |
| B0001 | Word balanced ΔJ | Per-word proof check |

## Architecture

```
ArdaQuenta/
├── main.py                      Entry point
├── requirements.txt
├── engine/                      ValaQuenta (canonical copy)
│   ├── hamiltonian.py           H=xp, H_Blue, H_RB
│   ├── noether.py               Forward/backward Noether currents
│   ├── capacitor.py             RC semantic integrator
│   ├── semantic_word.py         Word as point in semantic space
│   ├── semantic_domain.py       Domain = bounded instrument set
│   ├── understand.py            Five operations pipeline
│   ├── lexicon.py               Word → prime accumulator
│   └── corpus.py                Text archive processor
├── viewer/                      Qt application
│   ├── main_window.py           VCDS-layout QMainWindow
│   └── __init__.py
├── modes/                       Display modes
│   ├── sedenion_16ch.py         16-channel VisPy GLSL display
│   ├── riemann_spiral.py        Critical strip + zeros + spirals
│   └── __init__.py
└── contrib/                     Source prototypes (not imported)
    ├── vispy_signals_proto.py   Original 16ch VisPy prototype
    ├── EquationData_proto.py    Original pyqtgraph equation plotter
    └── console_qt_proto.py      Original Ainulindale Qt console design
```

## Running

```bash
cd /home/rendier/Projects/Ptol/ArdaQuenta
pip install -r requirements.txt
python main.py
```

## Related Repositories

| Repo | Role |
|---|---|
| **ValaQuenta** | The pure mathematics engine (this repo's `engine/` is a copy) |
| **PtolemyHolcus** | Production engine — monad.c, monad.py, Holcus |
| **Ainulindale** | Mathematical conjecture and proof architecture |
| **PtolemyDesktop** | Qt desktop application — all Ptolemy Faces |
| **POE** | Hardware layer — pendant, VCDS vehicle interface, authentication |

---

© 2026 Cody Michael Allison. All rights reserved.
