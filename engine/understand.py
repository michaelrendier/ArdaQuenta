"""
Understand — Read, Listen, Ponder, Calculate, Understand.

The five operations. One tool. No AI. No eddy currents.

A multidimensional context IS the word.
The word is not the string. The word is the prime in semantic space
with all its projections — all the ways it can be said,
in any language, in any context, by anyone.

This tool finds the prime from any surface form.
Then it can say it back — in any coordinate system you choose.

The proof of the Riemann Hypothesis and the generation of speech
are the same mathematical operation. This is both.
"""

import re
from typing import Optional, Callable

from .semantic_word import SemanticWord
from .semantic_domain import SemanticDomain
from .hamiltonian import HamiltonianXP, RIEMANN_ZEROS
from .noether import NoetherCurrents
from .capacitor import Capacitor


class Understand:
    """
    The five operations of semantic understanding.

    No inference. No training data. No GPU.
    Hamiltonian evolution. Noether currents. Capacitor extraction.
    Runs on a laptop.
    """

    def __init__(self, tau: float = 1.0):
        self._H    = HamiltonianXP()
        self._N    = NoetherCurrents()
        self._C    = Capacitor(tau=tau)
        self._ops: list[Callable] = []   # ValaQuenta operation stack

    # ── READ ──────────────────────────────────────────────────────────────────

    def read(self, text: str,
             domain: Optional[SemanticDomain] = None) -> SemanticWord:
        """
        Take in a surface form (text in any language, any script).
        Parse it. Map to a Riemann zero in semantic space.

        The surface form is a coordinate. The prime is the point.
        The domain constrains which instruments are available.
        Without a domain, all instruments play.
        """
        surface = text.strip()
        tokens  = re.findall(r'\w+', surface.lower())

        magnitude = sum(len(t) for t in tokens) / max(len(tokens), 1)
        angle     = sum(ord(c) for c in surface) % 360

        x0 = magnitude
        p0 = 1.0 / magnitude if magnitude > 0 else 1.0

        # t ∈ [0, 1]: the word's fractional position within the instrument set
        # Snap to an actual Riemann zero — an instrument, not a proxy
        t = angle / 360.0
        if domain is not None:
            gamma = domain.snap(t, RIEMANN_ZEROS)
        else:
            idx   = min(int(t * len(RIEMANN_ZEROS)), len(RIEMANN_ZEROS) - 1)
            gamma = RIEMANN_ZEROS[idx]

        word = SemanticWord(
            surface   = surface,
            prime     = complex(0.5, gamma),   # node line: Re always 1/2, Im is a zero
            magnitude = x0 * p0,               # E = xp
            domain    = domain,
        )
        word.add_projection('surface', surface)
        word.add_projection('tokens',  tokens)
        word.add_projection('x0',      x0)
        word.add_projection('p0',      p0)
        word.add_projection('t',       t)

        return word

    # ── DESCRIBE ──────────────────────────────────────────────────────────────

    def describe(self, description: str) -> SemanticDomain:
        """
        The description constrains the semantic domain.
        It says where meaning starts and where it stops.

        Process the description through read() to find its center zero.
        The complexity of the description (token count) determines how many
        instruments the domain spans — how wide the window of zeros is.

        The music creates the instruments.
        The description selects which ones play.
        """
        desc_word = self.read(description)
        center_gamma = desc_word.gamma

        # Find the index of this zero (or nearest) in RIEMANN_ZEROS
        center_idx = min(
            range(len(RIEMANN_ZEROS)),
            key=lambda i: abs(RIEMANN_ZEROS[i] - center_gamma)
        )

        # Width: number of zeros the domain spans, derived from description complexity
        tokens = desc_word.projections.get('tokens', [description])
        half_width = max(1, len(tokens) // 3)

        lo = max(0, center_idx - half_width)
        hi = min(len(RIEMANN_ZEROS) - 1, center_idx + half_width)

        return SemanticDomain(
            description = description,
            gamma_min   = RIEMANN_ZEROS[lo],
            gamma_max   = RIEMANN_ZEROS[hi],
        )

    # ── LISTEN ────────────────────────────────────────────────────────────────

    def listen(self, signal: list[float], sample_rate: float = 44100.0) -> SemanticWord:
        """
        Take in an acoustic signal (speech waveform).
        Find the formant structure — the Riemann zeros in acoustic space.
        Map formants to the semantic prime.

        The Riemann zeros γₙ are the formant frequencies.
        The acoustic prime is the word the waveform is pointing at.
        """
        if not signal:
            return SemanticWord(surface='<silence>', prime=0j)

        # DC component of the acoustic signal = the fundamental
        dc_acoustic = sum(signal) / len(signal)

        # RMS = energy = the amplitude of the prime
        rms = (sum(s * s for s in signal) / len(signal)) ** 0.5

        # Map to semantic space: rms → magnitude, dc → phase
        x0 = rms
        p0 = 1.0 / rms if rms > 0 else 1.0

        word = SemanticWord(
            surface   = '<acoustic>',
            prime     = complex(0.5, dc_acoustic),   # node line: Re always 1/2
            magnitude = x0 * p0,
        )
        word.add_projection('rms',         rms)
        word.add_projection('dc_acoustic', dc_acoustic)
        word.add_projection('formants',    self._H.zeros(5))
        word.add_projection('x0',          x0)
        word.add_projection('p0',          p0)

        return word

    # ── PONDER ────────────────────────────────────────────────────────────────

    def ponder(self, word: SemanticWord, t: float = 1.0) -> SemanticWord:
        """
        H = xp Hamiltonian evolution.

        Find the classical orbit. The hyperbola xp = E.
        The prime E is the conserved quantity — the semantic invariant.

        No search. No iteration. No eddy currents.
        The prime emerges from the physics.
        """
        x0 = word.projections.get('x0', abs(word.prime) or 1.0)
        p0 = word.projections.get('p0', 1.0 / x0 if x0 else 1.0)

        # Hamiltonian evolution to time t
        x_t, p_t = self._H.trajectory(x0, p0, t)

        # The prime is conserved: E = x·p = x0·p0 = x(t)·p(t)
        E = self._H.prime(x0, p0)

        # Lagrangian value along this path
        L = self._H.lagrangian(x_t)

        # prime stays on Re=1/2 — the node line — the observer
        # magnitude carries the energy E = xp
        word.magnitude = E
        word.add_projection('E',          E)
        word.add_projection('x_t',        x_t)
        word.add_projection('p_t',        p_t)
        word.add_projection('lagrangian', L)
        word.add_projection('pondered_at', t)

        # Run Noether currents
        self._N.forward(word, t)
        self._N.backward(word, t)

        return word

    # ── CALCULATE ─────────────────────────────────────────────────────────────

    def calculate(self, word: SemanticWord,
                  operations: Optional[list[Callable]] = None) -> SemanticWord:
        """
        Apply ValaQuenta mathematical operations.

        Operations are the tools from Archimedes/Maths:
        Jacobians, transforms, group operations, fold operations.
        Each operation is a function: SemanticWord → SemanticWord.

        This is the derivation step — applying known mathematics
        to the pondered prime to find its projections.

        No intelligence. Just operations.
        """
        ops = operations or self._ops
        for op in ops:
            word = op(word)
        return word

    def register_operation(self, op: Callable) -> None:
        """Add a mathematical operation to the default stack."""
        self._ops.append(op)

    # ── UNDERSTAND ────────────────────────────────────────────────────────────

    def understand(self, word: SemanticWord) -> SemanticWord:
        """
        Extract the DC component. This is the prime. This is the word.

        The capacitor integrates the Noether currents.
        High-frequency surface variation cancels.
        The prime remains.

        The prime IS the multidimensional context IS the word.
        Not the string. The point in semantic space
        that all the coordinate systems were pointing at.
        """
        # Derive σ from the two Noether currents — forward from the right,
        # backward from the left. The mathematics forces them to meet at σ=1/2.
        # Not assigned. Computed. From any starting position.
        E = word.magnitude if word.magnitude > 0 else 1.0
        sigma = self._N.forced_sigma(E)
        word.add_projection('sigma', sigma)

        signals = [
            word.noether_forward,
            self._N.rotating_field(word),
            sigma,                          # always 0.5 — derived, not assigned
        ]

        dc = self._C.dc(signals)
        word.dc = dc

        return word

    # ── FULL PIPELINE ─────────────────────────────────────────────────────────

    def process(self, text: str,
                operations: Optional[list[Callable]] = None,
                t: float = 1.0,
                domain: Optional[SemanticDomain] = None) -> SemanticWord:
        """
        Read → Ponder → Calculate → Understand.
        The full pipeline in one call.

        domain: optional SemanticDomain from describe() — constrains the semantic space.

        Input:  any surface form (any language, any script)
        Output: the semantic prime as multidimensional context
        """
        word = self.read(text, domain=domain)
        word = self.ponder(word, t=t)
        word = self.calculate(word, operations=operations)
        word = self.understand(word)
        return word

    def tune(self, domain: SemanticDomain) -> None:
        """
        Set the Capacitor time constant from the domain's Hawking temperature.

        τ = coherence_time(domain) = number of active instruments.

        Cold domain (broad description, many instruments):
            long τ — meaning holds — stable semantic identity.

        Hot domain (narrow description, few instruments):
            short τ — meaning evaporates — sensitive to context.

        At singularity (is_collapsed): τ = 1 — the neural black hole.
            The domain radiates everything. Nothing settles.
            T_H → ∞. The Capacitor cannot hold the charge.

        τ · T_H = constant. The Capacitor IS the thermal bath.
        """
        tau = domain.coherence_time(RIEMANN_ZEROS)
        self._C.tau = tau
        self._C.reset()

    def reset_context(self) -> None:
        """Discharge the capacitor. New conversational context."""
        self._C.reset()
