"""
ArdaQuenta — Ptolemy Supermath Calculator

Entry point.

Usage:
    python main.py

VCDS-inspired diagnostic viewer for the Ptolemy ValaQuenta.
The derivation engine IS a TDI engine. This viewer IS VCDS for it.
"""

import sys
import os

# Engine is a sibling package — add repo root to path
sys.path.insert(0, os.path.dirname(__file__))

from viewer.main_window import run

if __name__ == '__main__':
    sys.exit(run())
