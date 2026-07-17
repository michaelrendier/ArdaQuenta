"""
SemanticWord — A word is its multidimensional context.

Not the surface form. Not the string.
The prime in semantic space — the invariant point — with all its projections.

A tree is still a tree in any language because TREE is the prime.
"tree", "arbre", "木" are coordinate systems pointing at the same point.
The multidimensional context IS the word.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class SemanticWord:
    """
    The word as a point in semantic space.

    The node line IS the observer. They are not two things.

    The prime is always at Re(s) = 1/2 — the critical line — the equator.
    This is not derived. This is not computed. This IS the definition of the prime
    as a point in semantic space. The real part is always 1/2.
    The imaginary part γ is the specific zero — the specific face.

    surface          — the coordinate (any language, any script)
    prime            — the node line = the observer = complex(0.5, γ)
                       Re is always 1/2. Im is the semantic zero γ.
    magnitude        — E = xp, the conserved energy (how strong the prime is)
    projections      — the faces: {context → projection value}
    noether_forward  — what it IS  (Riemann current: the attractor)
    noether_backward — what it CANNOT BE (Fermat current: the repulsor)
    dc               — the DC component from the Capacitor (confirms the prime)
    """

    surface: str
    prime: complex         = complex(0.5, 0.0)   # always Re = 1/2
    magnitude: float       = 0.0                  # E = xp
    projections: dict      = field(default_factory=dict)
    noether_forward: float = 0.0
    noether_backward: float = 0.0
    dc: float              = 0.0
    domain: Optional[Any]  = None                 # SemanticDomain — the bounding description

    @property
    def observer(self) -> complex:
        """The observer IS the node line IS the prime. Same object."""
        return self.prime

    @property
    def gamma(self) -> float:
        """The imaginary part — the specific Riemann zero, the semantic zero."""
        return self.prime.imag

    def faces(self) -> int:
        """How many ways can this word be said. Dimension of its symmetry group."""
        return len(self.projections)

    def add_projection(self, context: str, value: Any) -> None:
        """Add a face — another way of saying this word."""
        self.projections[context] = value

    def is_understood(self) -> bool:
        """True when the DC component has been extracted."""
        return self.dc != 0.0

    def __repr__(self) -> str:
        domain_str = f'  domain={self.domain.description!r}' if self.domain else ''
        return (
            f"SemanticWord('{self.surface}' "
            f"→ node=0.5+{self.gamma:.4f}j  |E|={self.magnitude:.4f}  "
            f"faces={self.faces()}  dc={self.dc:.6f}{domain_str})"
        )
