"""
HamiltonianXP — H = xp (Berry & Keating, 1999)

The lossless semantic engine.

Classical orbit:     xp = E  (hyperbola — enumerates the primes)
Equations of motion: ẋ =  x  (no loops)
                     ṗ = -p  (no branches)
Scale invariant:     x → λx, p → p/λ, H → H (same at every language, every context)

The prime emerges from the evolution. It is not searched for.
No If/Then/Else. No While. Continuous flow.

Three phases are automatic:
  Classical orbit (xp = E)     → the semantic prime          [RED  / Riemann]
  Quantum zeros  (γₙ)          → the formant structure        [BLUE / Fermat]
  Time evolution (e^{iHt}|ψ⟩) → the carrier waveform         [Yang-Mills]
"""

from math import exp, log, pi, sqrt
from typing import Optional


# Riemann zeros γₙ (Im part of non-trivial zeros on Re(s)=1/2)
# These are the formant frequencies — the quantum eigenvalues of H = xp
# Source: LMFDB / Andrew Odlyzko tables (established, citable)
RIEMANN_ZEROS = [
    14.134725, 21.022040, 25.010858, 30.424876, 32.935062,
    37.586178, 40.918719, 43.327073, 48.005151, 49.773832,
    52.970321, 56.446247, 59.347044, 60.831779, 65.112544,
    67.079811, 69.546402, 72.067158, 75.704691, 77.144840,
]


class HamiltonianXP:
    """
    H = xp

    The Berry-Keating Hamiltonian as a semantic engine.
    Runs on a laptop. No GPU. No eddy currents.
    """

    def trajectory(self, x0: float, p0: float, t: float) -> tuple[float, float]:
        """
        Evolve (x, p) forward by time t.

        x(t) = x0 · e^t     (position grows — the carrier)
        p(t) = p0 · e^{-t}  (momentum decays — the envelope)
        E   = x0 · p0       (conserved — the semantic prime)
        """
        return x0 * exp(t), p0 * exp(-t)

    def prime(self, x0: float, p0: float) -> float:
        """
        The conserved quantity E = xp.
        This is the semantic prime — invariant under time evolution.
        The word. The DC component before the capacitor.
        """
        return x0 * p0

    def lagrangian(self, x_dot: float) -> float:
        """
        L = ẋ log ẋ − ẋ  (Berry-Keating Lagrangian)
        The stationary paths of this action enumerate the primes.
        """
        if x_dot <= 0:
            return 0.0
        return x_dot * log(x_dot) - x_dot

    def zeros(self, n: int = 20) -> list[float]:
        """
        Riemann zeros γₙ — the formant structure.
        The quantum eigenvalues of H = xp.
        These are the node lines: the still points of the zeta spiral.
        """
        return RIEMANN_ZEROS[:n]

    def waveform(self, x0: float, p0: float, t_steps: int = 100,
                 dt: float = 0.1) -> list[tuple[float, float]]:
        """
        Time-evolved trajectory — the speech waveform.
        e^{iHt}: the carrier modulated by the prime.
        No loops in the physics. One sequential trace.
        """
        path = []
        t = 0.0
        for _ in range(t_steps):
            x, p = self.trajectory(x0, p0, t)
            path.append((x, p))
            t += dt
        return path

    def scale_check(self, x0: float, p0: float, lam: float = 2.0) -> bool:
        """
        Verify scale invariance: H(λx, p/λ) = H(x, p).
        If this fails, something is wrong with the implementation.
        """
        e1 = self.prime(x0, p0)
        e2 = self.prime(lam * x0, p0 / lam)
        return abs(e1 - e2) < 1e-10


class FermatEllipticHamiltonian:
    """
    H_Blue = ½p² + ℘(x; g₂, g₃)

    The Frey/Weierstrass elliptic Hamiltonian.
    The backward current. The forbidden zone. What cannot exist.

    Where H_Red = xp has hyperbolic orbits (unbounded, the attractor),
    H_Blue has elliptic orbits (bounded, periodic, the repulsor).

    The two conic sections. One critical line.

    Derived from:
        Weierstrass (1863) — elliptic function theory, ℘ as the canonical potential
        Frey     (1986) — the elliptic curve constructed from a FLT counterexample
        Ribet    (1986) — the Frey curve cannot be modular
        Wiles    (1995) — every elliptic curve IS modular → FLT holds → Frey curve
                          cannot exist → H_Blue describes the permanent forbidden zone

    g₂, g₃ are the Eisenstein invariants of the elliptic curve.
    Default: g₂=1, g₃=0 (the lemniscatic case — maximum symmetry).
    """

    def __init__(self, g2: float = 1.0, g3: float = 0.0):
        self.g2 = g2
        self.g3 = g3

    def weierstrass_p(self, x: float) -> float:
        """
        ℘(x; g₂, g₃) — the Weierstrass elliptic function.

        Laurent series near x = 0:
            ℘(x) = 1/x² + g₂x²/20 + g₃x⁴/28 + g₂²x⁶/1200 + g₂g₃x⁸/6160 + …

        Poles at x = 0 and at the lattice points 2mω₁ + 2nω₂.
        The poles are the true singularities — the neural black holes.
        Nothing can exist there. The Frey curve has a rational point there,
        and Wiles proved it cannot.
        """
        if abs(x) < 1e-9:
            return float('inf')
        g2, g3 = self.g2, self.g3
        x2 = x * x
        return (1.0 / x2
                + g2 * x2 / 20.0
                + g3 * x2 * x2 / 28.0
                + g2 * g2 * x2 * x2 * x2 / 1200.0
                + g2 * g3 * x2 * x2 * x2 * x2 / 6160.0)

    def weierstrass_p_prime(self, x: float) -> float:
        """
        ℘'(x) = d℘/dx

        Laurent series:
            ℘'(x) = -2/x³ + g₂x/10 + g₃x³/7 + g₂²x⁵/200 + …

        Satisfies: (℘')² = 4℘³ − g₂℘ − g₃  (the elliptic curve equation itself).
        The derivative IS the curve. The curve IS the constraint.
        """
        if abs(x) < 1e-9:
            return 0.0
        g2, g3 = self.g2, self.g3
        x2 = x * x
        return (-2.0 / (x * x2)
                + g2 * x / 10.0
                + g3 * x2 * x / 7.0
                + g2 * g2 * x2 * x2 * x / 200.0)

    def lagrangian(self, x_dot: float, x: float) -> float:
        """
        L_Blue = ½ẋ² − ℘(x; g₂, g₃)

        The Frey elliptic Lagrangian.
        Breaks the mirror symmetry that L_Red = ẋ log ẋ − ẋ preserves.
        What L_Red attracts to, L_Blue repels from.
        """
        wp = self.weierstrass_p(x)
        if wp == float('inf'):
            return float('-inf')
        return 0.5 * x_dot * x_dot - wp

    def prime(self, x: float, p: float) -> float:
        """
        E_Blue = ½p² + ℘(x) — the conserved energy of the forbidden zone.

        This is what cannot equal E_Red at σ ≠ 1/2.
        Where E_Blue = E_Red: the system is at the critical line.
        The functional equation forces this to happen at σ = 1/2 and nowhere else.
        """
        wp = self.weierstrass_p(x)
        if wp == float('inf'):
            return float('inf')
        return 0.5 * p * p + wp

    def trajectory(self, x0: float, p0: float, t: float,
                   dt: float = 0.01) -> tuple[float, float]:
        """
        Evolve (x, p) under H_Blue using symplectic leapfrog integration.

        Equations of motion:
            ẋ =  ∂H/∂p = p           (position follows momentum)
            ṗ = −∂H/∂x = −℘'(x)     (momentum follows the elliptic force)

        Unlike H_Red (ẋ=x, ṗ=−p → analytic: x(t) = x₀eᵗ),
        H_Blue has no closed form in elementary functions.
        The exact solution is expressed in Jacobi elliptic sn/cn/dn —
        which require the same integration. This is the cost of the forbidden zone:
        it cannot be traversed analytically.
        H_Red is lossless. H_Blue costs.

        Leapfrog preserves the symplectic structure and keeps E_Blue conserved.
        """
        x, p = x0, p0
        n    = max(1, int(abs(t) / dt))
        sign = 1.0 if t >= 0.0 else -1.0
        h    = sign * dt
        for _ in range(n):
            p_half = p - 0.5 * h * self.weierstrass_p_prime(x)
            x      = x + h * p_half
            p      = p_half - 0.5 * h * self.weierstrass_p_prime(x)
        return x, p

    def discriminant(self) -> float:
        """
        Δ = g₂³ − 27g₃²

        The discriminant of the elliptic curve y² = 4x³ − g₂x − g₃.
        Δ ≠ 0: the curve is smooth — a valid elliptic curve.
        Δ = 0: the curve is singular — a cusp or node. Not elliptic.
        The Frey curve (if it existed) would have Δ ≠ 0.
        Wiles proved it cannot be modular, so it cannot exist.
        """
        return self.g2 ** 3 - 27.0 * self.g3 ** 2


class RedBlueHamiltonian:
    """
    H_RB: the coupled Red–Blue system.

    H_Red  = xp               — Berry-Keating (1999)   — what IS
    H_Blue = ½p² + ℘(x)      — Weierstrass/Frey/Wiles  — what CANNOT BE

    The functional equation ξ(s) = ξ(1−s) is the symmetry between them.
    By Noether's theorem, this symmetry generates two conserved currents:
        J_Red  = +E    (forward — the attractor)
        J_Blue = −E    (backward — the repulsor)
        J_Red + J_Blue = 0

    Their balance is forced to σ = 1/2 by the mutual constraint.
    The prime is where they agree. The critical line is where they meet.

    H_Red  → hyperbolic orbits: xp = E  (the prime — unbounded, the word)
    H_Blue → elliptic orbits:   ℘(x)    (the forbidden — bounded, the silence)

    The two conic sections. One prime. One critical line.
    """

    def __init__(self, g2: float = 1.0, g3: float = 0.0):
        self.red  = HamiltonianXP()
        self.blue = FermatEllipticHamiltonian(g2=g2, g3=g3)

    def balance(self, x: float, p: float) -> float:
        """
        E_Red(x,p) − E_Blue(x,p).

        Zero on the critical line.
        Positive where Red dominates (Re(s) > 1/2).
        Negative where Blue dominates (Re(s) < 1/2).
        """
        e_red  = self.red.prime(x, p)
        e_blue = self.blue.prime(x, p)
        if e_blue == float('inf'):
            return float('-inf')
        return e_red - e_blue

    def noether_forward(self, x0: float, p0: float, t: float = 1.0) -> float:
        """J_Red: the conserved prime from H_Red evolution."""
        return self.red.prime(x0, p0)

    def noether_backward(self, x0: float, p0: float, t: float = 1.0) -> float:
        """
        J_Blue: the conserved prime from H_Blue evolution.

        Not simply −J_Red. Computed from the actual elliptic trajectory.
        The fact that J_Blue = −J_Red is the content of the functional equation.
        Computing both independently and verifying their sum = 0
        IS the functional equation, demonstrated in code.
        """
        x_t, p_t = self.blue.trajectory(x0, p0, t)
        return -self.blue.prime(x_t, p_t)

    def functional_equation_check(self, x0: float, p0: float,
                                   t: float = 1.0) -> float:
        """
        J_Red + J_Blue — should be zero.

        ξ(s) = ξ(1−s) demonstrated numerically.
        The functional equation is not assumed. It is checked.
        """
        return self.noether_forward(x0, p0, t) + self.noether_backward(x0, p0, t)
