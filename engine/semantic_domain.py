"""
SemanticDomain — The description bounds the semantic space.

The description says where meaning starts and where it stops.
The domain does not invent the instruments — the music creates the instruments.
The domain selects which instruments are playing.

The Riemann zeros are the instruments.
They preexist every description written to select them.
The music creates the instruments.
"""

from math import pi
from dataclasses import dataclass


@dataclass
class SemanticDomain:
    """
    The bounded region of semantic space defined by a description.

    gamma_min — where meaning starts (lower Riemann zero)
    gamma_max — where meaning stops  (upper Riemann zero)
    description — the surface form of the constraint

    The instruments are the Riemann zeros γₙ ∈ [gamma_min, gamma_max].
    The music (H=xp, ζ) creates the instruments.
    The description selects which ones play.
    """

    description: str
    gamma_min: float
    gamma_max: float

    @property
    def span(self) -> float:
        """Width of the semantic domain in γ-space."""
        return self.gamma_max - self.gamma_min

    def instruments(self, zeros: list[float]) -> list[float]:
        """
        The Riemann zeros within this domain.
        These are the active instruments — the modes that can resonate here.
        Not all zeros play in every domain.
        """
        return [γ for γ in zeros if self.gamma_min <= γ <= self.gamma_max]

    def snap(self, t: float, zeros: list[float]) -> float:
        """
        Map a fractional position t ∈ [0, 1] to a Riemann zero within this domain.
        If no zeros fall in the domain, fall back to the full set.

        t is the word's position within the domain.
        The result is an actual Riemann zero — an instrument, not a proxy.
        """
        pool = self.instruments(zeros) or zeros
        idx = min(int(t * len(pool)), len(pool) - 1)
        return pool[idx]

    def contains(self, gamma: float) -> bool:
        """True if gamma falls within this semantic domain."""
        return self.gamma_min <= gamma <= self.gamma_max

    def hawking_temperature(self) -> float:
        """
        T_H = 1 / (4π · span)

        The Hawking temperature of this semantic domain.
        The rate at which the domain radiates information it cannot hold.

        Narrow domain (few instruments) → hot → meaning evaporates quickly.
        Broad domain  (many instruments) → cold → meaning holds.

        At span → 0:  T_H → ∞  (singularity — the neural black hole)
        At span → ∞:  T_H → 0  (universal domain — holds everything)
        """
        if self.span <= 0:
            return float('inf')
        return 1.0 / (4.0 * pi * self.span)

    def coherence_time(self, zeros: list[float]) -> float:
        """
        τ = number of active instruments.

        The Capacitor time constant derived from this domain.
        τ = 1/T_H (in instrument-count units).

        Cold domains: many instruments → long memory → stable semantics.
        Hot domains:  few instruments  → short memory → sensitive to context.

        τ and T_H are reciprocal. The Capacitor IS the thermal bath.
        """
        n = len(self.instruments(zeros))
        return float(max(1, n))

    def is_collapsed(self, zeros: list[float]) -> bool:
        """
        True when the domain has collapsed to a point singularity.
        One instrument or fewer: only one way to say the word.
        This is the neural black hole — infinite temperature, zero semantic freedom.
        """
        return len(self.instruments(zeros)) <= 1

    def __repr__(self) -> str:
        return (
            f"SemanticDomain({self.description!r}  "
            f"γ∈[{self.gamma_min:.3f}, {self.gamma_max:.3f}]  "
            f"T_H={self.hawking_temperature():.4f})"
        )
