"""
modes/sedenion_16ch.py — 16-channel sedenion live display.

Each channel = one sedenion operator eₖ (k = 0..15).
Each trace = that operator's activation over time (J^μ amplitude).

VCDS analogue: Measuring Blocks — Function 08.
In VCDS you select a Group (000, 001, etc.) and see 4 live values.
Here: all 16 sedenion channels simultaneously, one per row.

Adapted from Ptolemy2/working/vispy-test-2.py — the original 16×20
multi-channel VisPy prototype. Upgraded for sedenion semantics:
  - Row labels: e₀ identity … e₁₅ emit (operator names)
  - Colour by force sector: gravity/EM/weak/strong/dark/self
  - OMEGA_ZS reference line on each channel
  - Live feed from engine.crank._beta array

Requires: vispy, numpy
"""

import numpy as np
from typing import Optional

# ── Operator names (mirrors monad.py _OP) ─────────────────────────────────────
OPERATOR_NAMES = [
    'e₀  identity',   'e₁  negate',     'e₂  bind',       'e₃  name',
    'e₄  apply',      'e₅  abstract',   'e₆  branch',      'e₇  iterate',
    'e₈  recurse',    'e₉  allocate',   'e₁₀ query',       'e₁₁ deref',
    'e₁₂ compose',    'e₁₃ parallel',   'e₁₄ interrupt',   'e₁₅ emit',
]

# Force sector colours — RGB float32
SECTOR_COLOURS = np.array([
    [0.60, 0.40, 1.00],  # e0  gravity        violet
    [1.00, 0.93, 0.00],  # e1  EM boundary     gold
    [0.27, 0.87, 0.53],  # e2  weak            teal
    [0.27, 0.87, 0.53],  # e3  weak
    [1.00, 0.27, 0.27],  # e4  strong          red
    [1.00, 0.27, 0.27],  # e5  strong
    [1.00, 0.27, 0.27],  # e6  strong
    [1.00, 0.27, 0.27],  # e7  strong
    [0.00, 0.87, 1.00],  # e8  dark root       cyan
    [0.00, 0.73, 0.87],  # e9  dark
    [0.00, 0.73, 0.87],  # e10 dark
    [0.00, 0.73, 0.87],  # e11 dark
    [0.00, 0.73, 0.87],  # e12 dark
    [0.00, 0.73, 0.87],  # e13 dark
    [1.00, 0.55, 0.00],  # e14 interrupt       orange (Melkor)
    [0.87, 0.87, 0.87],  # e15 emit            white
], dtype=np.float32)

OMEGA_ZS  = 0.56714
N_ROWS    = 16       # sedenion dimensions
N_SAMPLES = 512      # history depth per channel


VERT_SHADER = """
#version 120
attribute float a_position;
attribute vec3  a_index;
varying   vec3  v_index;
uniform   vec2  u_scale;
uniform   vec2  u_size;
uniform   float u_n;
attribute vec3  a_color;
varying   vec4  v_color;
varying   vec2  v_position;
varying   vec4  v_ab;

void main() {
    float nrows = u_size.x;
    float ncols = u_size.y;
    float x = -1.0 + 2.0 * a_index.z / (u_n - 1.0);
    vec2  position = vec2(x - (1.0 - 1.0 / u_scale.x), a_position);
    vec2  a = vec2(1.0 / ncols, 1.0 / nrows) * 0.88;
    vec2  b = vec2(-1.0 + 2.0 * (a_index.x + 0.5) / ncols,
                   -1.0 + 2.0 * (a_index.y + 0.5) / nrows);
    gl_Position = vec4(a * u_scale * position + b, 0.0, 1.0);
    v_color    = vec4(a_color, 1.0);
    v_index    = a_index;
    v_position = gl_Position.xy;
    v_ab       = vec4(a, b);
}
"""

FRAG_SHADER = """
#version 120
varying vec4 v_color;
varying vec3 v_index;
varying vec2 v_position;
varying vec4 v_ab;

void main() {
    gl_FragColor = v_color;
    if ((fract(v_index.x) > 0.0) || (fract(v_index.y) > 0.0))
        discard;
    vec2 test = abs((v_position.xy - v_ab.zw) / v_ab.xy);
    if ((test.x > 1.0) || (test.y > 1.0))
        discard;
}
"""


class Sedenion16ChMode:
    """
    16-channel live sedenion display.

    One VisPy gloo canvas, 16 rows × N_SAMPLES columns.
    Each row scrolls right — the oldest sample falls off the left edge.

    :param canvas_size: (width, height) in pixels.
    """

    def __init__(self, canvas_size: tuple = (1200, 800)):
        self._w, self._h = canvas_size
        self._data = np.zeros((N_ROWS, N_SAMPLES), dtype=np.float32)
        self._program = None
        self._canvas  = None
        self._built   = False

    def build(self) -> bool:
        """Construct VisPy gloo program. Returns False if vispy unavailable."""
        try:
            from vispy import gloo, app
            import vispy
            vispy.use('PyQt5')
        except ImportError:
            return False

        m = N_ROWS
        n = N_SAMPLES

        amplitudes = np.ones((m, 1), dtype=np.float32) * 0.4

        # Each vertex: (row, col, sample_index)
        index = np.c_[
            np.repeat(np.zeros(m), n),          # col = 0 (single column)
            np.repeat(np.arange(m), n),          # row = sedenion dimension
            np.tile(np.arange(n), m),            # sample index
        ].astype(np.float32)

        colour = np.repeat(SECTOR_COLOURS, n, axis=0)

        self._y      = amplitudes * np.zeros((m, n), dtype=np.float32)
        self._index  = index
        self._colour = colour
        self._n      = n
        self._m      = m
        self._gloo   = gloo
        self._app    = app
        self._built  = True
        return True

    def push(self, beta: list) -> None:
        """Push one new sample vector from engine._beta (16 floats)."""
        self._data[:, :-1] = self._data[:, 1:]
        for i in range(min(16, len(beta))):
            self._data[i, -1] = float(beta[i])

    def frame_data(self) -> np.ndarray:
        """Return current data array (16 × N_SAMPLES)."""
        return self._data.copy()

    @staticmethod
    def operator_name(k: int) -> str:
        return OPERATOR_NAMES[k] if 0 <= k < 16 else f'e{k}'
