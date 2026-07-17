"""
ValaQuenta

The mathematical derivation engine for Ptolemy.
Built on H = xp (Berry-Keating, 1999).

A multidimensional context IS the word.
The prime preexists every alphabet invented to point at it.

Five operations:
    Read       — surface form → candidate prime
    Listen     — acoustic signal → formant prime
    Ponder     — H = xp evolution → conserved prime
    Calculate  — ValaQuenta operations → projections
    Understand — Capacitor extraction → DC prime

No inference. No training data. No GPU. No eddy currents.
Runs on a laptop.

Usage:
    from ValaQuenta import Understand

    engine = Understand(tau=1.0)
    word   = engine.process("tree")
    print(word)
    # SemanticWord('tree' → prime=..., faces=4, dc=...)
"""

from .semantic_word import SemanticWord
from .semantic_domain import SemanticDomain
from .hamiltonian import HamiltonianXP, FermatEllipticHamiltonian, RedBlueHamiltonian, RIEMANN_ZEROS
from .noether import NoetherCurrents
from .capacitor import Capacitor
from .understand import Understand
from .lexicon import Lexicon
from .corpus import CorpusProcessor

__all__ = [
    'SemanticWord',
    'SemanticDomain',
    'HamiltonianXP',
    'FermatEllipticHamiltonian',
    'RedBlueHamiltonian',
    'RIEMANN_ZEROS',
    'NoetherCurrents',
    'Capacitor',
    'Understand',
    'Lexicon',
    'CorpusProcessor',
]

__version__ = '0.1.0'
__author__  = 'Cody Michael Allison'
