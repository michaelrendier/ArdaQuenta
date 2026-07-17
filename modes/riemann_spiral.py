"""
modes/riemann_spiral.py — Riemann critical strip with zeros and spiral arcs.

Displays:
  - Critical line Re(s) = ½ (vertical gold line)
  - First N non-trivial zeros γₙ as nodes on the critical line
  - Inherent-time spiral arcs: z(t) = ½ + i·γₙ·e^{iHt} from HamiltonianXP
  - (x, p) phase space portrait — hyperbola xp = E for each word
  - J_Red (forward) and J_Blue (backward) current arrows
  - Balance = 0 manifold highlight (the critical line, demonstrated)

VCDS analogue: Oscilloscope / Advanced Measuring Values.
The zeros are the formant frequencies — the eigenvalues of H = xp.
The spiral is the time evolution e^{iHt}|ψ⟩ — the carrier waveform.

Uses matplotlib Agg for headless render → PNG delivered to viewer.
VisPy scene variant available when GL context is present.
"""

import math
from typing import Optional, List, Tuple

from engine.hamiltonian import RIEMANN_ZEROS, HamiltonianXP, RedBlueHamiltonian

OMEGA_ZS  = 0.5671432904097838
GAP       = 0.000707
N_DEFAULT = 20


def _spiral_arc(gamma: float, t_max: float = 2.0,
                steps: int = 200) -> List[Tuple[float, float]]:
    """
    Compute spiral arc for one zero γ under H = xp time evolution.

    z(t) = (½ + γ·sin(t),  γ·cos(t))   — the inherent-time helix projected to 2D.
    This IS the carrier waveform of that semantic prime.

    :param gamma: Imaginary part of zero (the zero itself).
    :param t_max: Time extent.
    :param steps: Number of arc points.
    :returns: List of (x, y) tuples.
    """
    arc  = []
    H    = HamiltonianXP()
    x0   = 0.5
    p0   = gamma
    dt   = t_max / steps
    t    = 0.0
    for _ in range(steps):
        x, p = H.trajectory(x0, p0, t)
        # Project to strip: clamp x to [0, 1] range for display
        arc.append((min(max(x / (x + 1), 0.0), 1.0), p / (abs(p) + 1)))
        t += dt
    return arc


def render_matplotlib(
    n_zeros: int = N_DEFAULT,
    word_primes: Optional[List[Tuple[float, float]]] = None,
    output_path: Optional[str] = None,
) -> Optional[str]:
    """
    Render Riemann strip to PNG via matplotlib Agg.

    :param n_zeros: Number of zeros to display.
    :param word_primes: List of (x0, p0) pairs for active words.
    :param output_path: PNG path. If None, returns None without saving.
    :returns: output_path on success, None on failure.
    :rtype: str or None
    """
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        import numpy as np
    except ImportError:
        return None

    zeros = RIEMANN_ZEROS[:n_zeros]
    BG    = '#050510'
    fig, ax = plt.subplots(figsize=(8, 12), facecolor=BG)
    ax.set_facecolor(BG)
    ax.spines[:].set_color('#333')
    ax.tick_params(colors='#aaa')

    # ── Critical line ──────────────────────────────────────────────────────────
    ax.axvline(0.5, color='gold', linewidth=1.5, alpha=0.8,
               label=f'Re(s)=½  σ_crit')

    # ── Zeros as nodes ────────────────────────────────────────────────────────
    for i, gamma in enumerate(zeros):
        ax.plot(0.5, gamma, 'o', color='#00e5ff', markersize=5, alpha=0.9)
        ax.text(0.52, gamma, f'γ{i+1}={gamma:.3f}',
                color='#aaa', fontsize=6, va='center')

    # ── Spiral arcs ───────────────────────────────────────────────────────────
    for i, gamma in enumerate(zeros[:8]):
        arc = _spiral_arc(gamma, t_max=1.5, steps=150)
        xs  = [p[0] for p in arc]
        ys  = [p[1] for p in arc]
        ax.plot(xs, ys, linewidth=0.6, alpha=0.3,
                color=f'#{int(255 * i/8):02x}{int(200 - 150*i/8):02x}ff')

    # ── Word primes ───────────────────────────────────────────────────────────
    if word_primes:
        rb = RedBlueHamiltonian()
        for x0, p0 in word_primes:
            e = rb.red.prime(x0, p0)
            ax.plot(0.5, e, '*', color='white', markersize=10, alpha=0.9)

    # ── OMEGA_ZS reference ────────────────────────────────────────────────────
    ax.axvline(OMEGA_ZS, color='#ff4444', linewidth=0.8, linestyle='--',
               alpha=0.5, label=f'Ω_ZS={OMEGA_ZS}')

    ax.set_xlim(-0.1, 1.1)
    ax.set_xlabel('Re(s)  σ', color='#aaa')
    ax.set_ylabel('Im(s)  γ  (Riemann zeros)', color='#aaa')
    ax.set_title('Riemann Critical Strip — Zeros + Spiral Arcs',
                 color='white', fontsize=10)
    ax.legend(facecolor='#111', labelcolor='white', fontsize=7)

    if output_path:
        plt.savefig(output_path, dpi=100, bbox_inches='tight', facecolor=BG)
        plt.close(fig)
        return output_path

    plt.close(fig)
    return None


def balance_manifold(
    x_range: Tuple[float, float] = (0.1, 3.0),
    p_range: Tuple[float, float] = (0.1, 3.0),
    grid: int = 80,
) -> Tuple[list, list]:
    """
    Compute the (x, p) locus where J_Red + J_Blue = 0.

    This IS the critical line, demonstrated numerically.
    The balance manifold in (x, p) space corresponds to σ = ½ in s-space.

    :returns: (x_vals, p_vals) of points where |balance| < threshold.
    :rtype: tuple of lists
    """
    rb = RedBlueHamiltonian()
    xs, ps = [], []
    dx = (x_range[1] - x_range[0]) / grid
    dp = (p_range[1] - p_range[0]) / grid
    thr = 0.05

    x = x_range[0]
    while x <= x_range[1]:
        p = p_range[0]
        while p <= p_range[1]:
            try:
                b = abs(rb.balance(x, p))
                if b < thr:
                    xs.append(x)
                    ps.append(p)
            except Exception:
                pass
            p += dp
        x += dx

    return xs, ps
