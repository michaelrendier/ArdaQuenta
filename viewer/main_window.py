"""
viewer/main_window.py — ArdaQuenta main Qt window.

VCDS-inspired layout. The derivation engine IS the TDI engine.
This viewer IS VCDS for that engine.

Layout (mirrors VCDS main screen structure):
┌──────────────────────────────────────────────────────────────────┐
│  [Select]  [Auto-Run]  [Data Log]  [Reset]  [About]             │ ← toolbar
├──────────────────────────────────────────────────────────────────┤
│                          │                                        │
│   VISPY CANVAS           │  CONTROL MODULES  (right panel)       │
│   active display mode    │  ─ Equation list (module selector)    │
│   (16ch / Riemann /      │  ─ Parameter sliders (Adaptation)     │
│    Phase / Fano /        │  ─ Mode selector                      │
│    Equation plot)        │  ─ Word input                         │
│                          │                                        │
├──────────────────────────────────────────────────────────────────┤
│  DTC / PROOF CHECKER     │  LIVE DIAGNOSTICS (Measuring Block 0) │
│  P0300: misfire …        │  J_Red     0.5672                     │
│  ✓ Functional eq: Δ=0   │  J_Blue   -0.5671                     │
│                          │  BAO       0.56714                    │
└──────────────────────────────────────────────────────────────────┘

:class:`MainWindow` — top-level QMainWindow.
"""

import sys
from typing import Optional

try:
    from PyQt5.QtWidgets import (
        QApplication, QMainWindow, QWidget, QSplitter,
        QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
        QLabel, QPushButton, QComboBox, QTextEdit, QLineEdit,
        QGroupBox, QSlider, QSizePolicy, QStatusBar, QAction, QToolBar,
        QDoubleSpinBox, QScrollArea,
    )
    from PyQt5.QtCore import Qt, QTimer, pyqtSignal
    from PyQt5.QtGui import QFont, QColor, QPalette
    _HAS_QT = True
except ImportError:
    _HAS_QT = False

from engine import (
    Understand, RedBlueHamiltonian, HamiltonianXP,
    NoetherCurrents, Capacitor, RIEMANN_ZEROS,
)

# ── Colour constants ───────────────────────────────────────────────────────────
DARK_BG   = '#0a0a12'
PANEL_BG  = '#0f0f1a'
ACCENT    = '#00bfff'
ACCENT2   = '#7b2fff'
TEXT      = '#e0e0e0'
TEXT_DIM  = '#555566'
GOLD      = '#c8a84b'
RED_HI    = '#ff4444'
TEAL      = '#2fffd0'
BORDER    = '#1e1e2e'

OMEGA_ZS  = 0.56714

# ── Control module definitions (equation list) ─────────────────────────────────
MODULES = [
    ('H = xp',                  'Berry-Keating — the semantic prime. Classical orbit: xp = E.'),
    ('H_Blue = ½p² + ℘(x)',     'Frey/Weierstrass — the forbidden zone. Elliptic orbits.'),
    ('H_RB = RedBlue',          'Coupled system. Balance = 0 → critical line.'),
    ('Noether J_forward',       'Forward Noether current — what the word IS.'),
    ('Noether J_backward',      'Backward current — what the word CANNOT BE.'),
    ('Functional equation',     'ξ(s) = ξ(1-s) checked numerically. J_R + J_B = 0.'),
    ('Capacitor RC',            'Semantic low-pass filter. DC extraction = the prime.'),
    ('forced_sigma()',          'σ = ½ derived from both sides. Not assumed.'),
    ('Riemann zeros γₙ',        'The 20 non-trivial zeros. The formant structure.'),
    ('SemanticWord',            'A word as a point in semantic space: prime + projections.'),
    ('SemanticDomain',          'Bounded instrument set. T_H = Hawking temperature.'),
    ('Understand.process()',    'Full five-operation pipeline: Read→Ponder→Calculate→Understand.'),
]


def _style_sheet() -> str:
    return f"""
    QMainWindow, QWidget {{
        background-color: {DARK_BG};
        color: {TEXT};
    }}
    QToolBar {{
        background-color: {PANEL_BG};
        border-bottom: 1px solid {BORDER};
        spacing: 6px;
        padding: 4px;
    }}
    QPushButton {{
        background-color: {PANEL_BG};
        color: {ACCENT};
        border: 1px solid {ACCENT};
        border-radius: 3px;
        padding: 4px 12px;
        font-family: monospace;
    }}
    QPushButton:hover {{
        background-color: {ACCENT};
        color: {DARK_BG};
    }}
    QListWidget {{
        background-color: {PANEL_BG};
        color: {TEXT};
        border: 1px solid {BORDER};
        font-family: monospace;
        font-size: 11px;
    }}
    QListWidget::item:selected {{
        background-color: {ACCENT2};
        color: white;
    }}
    QTextEdit {{
        background-color: {PANEL_BG};
        color: {TEXT};
        border: 1px solid {BORDER};
        font-family: monospace;
        font-size: 10px;
    }}
    QLabel {{
        color: {TEXT};
        font-family: monospace;
    }}
    QGroupBox {{
        border: 1px solid {BORDER};
        border-radius: 4px;
        margin-top: 8px;
        font-family: monospace;
        color: {TEXT_DIM};
    }}
    QGroupBox::title {{
        subcontrol-origin: margin;
        left: 8px;
        padding: 0 4px;
        color: {ACCENT};
    }}
    QSlider::groove:horizontal {{
        height: 4px;
        background: {BORDER};
        border-radius: 2px;
    }}
    QSlider::handle:horizontal {{
        background: {ACCENT};
        width: 12px;
        height: 12px;
        margin: -4px 0;
        border-radius: 6px;
    }}
    QLineEdit {{
        background-color: {PANEL_BG};
        color: {TEXT};
        border: 1px solid {BORDER};
        font-family: monospace;
        padding: 3px;
    }}
    QComboBox {{
        background-color: {PANEL_BG};
        color: {TEXT};
        border: 1px solid {BORDER};
        font-family: monospace;
        padding: 3px;
    }}
    QStatusBar {{
        background-color: {PANEL_BG};
        color: {TEXT_DIM};
        font-family: monospace;
        font-size: 10px;
    }}
    """


class LiveDiagnostics(QWidget):
    """Measuring Block 0 — live J_Red, J_Blue, balance, BAO."""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        self._labels = {}
        rows = [
            ('J_Red',    GOLD,     '—'),
            ('J_Blue',   '#4488ff', '—'),
            ('Balance',  TEAL,     '—'),
            ('σ',        GOLD,     '0.500000'),
            ('BAO',      ACCENT,   str(OMEGA_ZS)),
            ('DC prime', '#ffffff', '—'),
            ('Δ J',      RED_HI,   '—'),
        ]
        for name, colour, default in rows:
            row_w = QWidget()
            row_l = QHBoxLayout(row_w)
            row_l.setContentsMargins(0, 0, 0, 0)
            key_l = QLabel(f'{name}:')
            key_l.setFixedWidth(70)
            key_l.setStyleSheet(f'color: {TEXT_DIM}; font-size: 10px;')
            val_l = QLabel(default)
            val_l.setStyleSheet(f'color: {colour}; font-family: monospace; font-size: 11px;')
            row_l.addWidget(key_l)
            row_l.addWidget(val_l)
            layout.addWidget(row_w)
            self._labels[name] = val_l

        layout.addStretch()

    def update_values(self, j_red: float, j_blue: float, dc: float,
                      sigma: float = 0.5, bao: float = OMEGA_ZS):
        bal = j_red + j_blue
        dj  = abs(bal)
        self._labels['J_Red'].setText(f'{j_red:+.6f}')
        self._labels['J_Blue'].setText(f'{j_blue:+.6f}')
        self._labels['Balance'].setText(f'{bal:+.6f}')
        self._labels['σ'].setText(f'{sigma:.6f}')
        self._labels['BAO'].setText(f'{bao:.5f}')
        self._labels['DC prime'].setText(f'{dc:.6f}')
        self._labels['Δ J'].setText(f'{dj:.2e}')


class DTCPanel(QWidget):
    """Fault Codes — Function 02. Proof checker output."""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        lbl = QLabel('FAULT CODES / PROOF CHECKER')
        lbl.setStyleSheet(f'color: {ACCENT}; font-size: 10px;')
        layout.addWidget(lbl)
        self._log = QTextEdit()
        self._log.setReadOnly(True)
        self._log.setMinimumHeight(80)
        layout.addWidget(self._log)

    def add_dtc(self, code: str, message: str, ok: bool = False):
        colour = '#44dd88' if ok else '#ff6655'
        marker = '✓' if ok else '✗'
        self._log.append(
            f'<span style="color:{colour};font-family:monospace;">'
            f'{marker} {code}: {message}</span>'
        )

    def clear(self):
        self._log.clear()


class EquationPanel(QWidget):
    """
    Right panel — Control Modules + Adaptation.

    module_selected: emitted with module index when user selects an equation.
    """

    module_selected = pyqtSignal(int) if _HAS_QT else None

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumWidth(280)
        self.setMaximumWidth(380)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)

        # ── Control Module selector ───────────────────────────────────────────
        grp_mod = QGroupBox('CONTROL MODULES')
        mod_lay = QVBoxLayout(grp_mod)
        self._module_list = QListWidget()
        self._module_list.setMaximumHeight(220)
        for name, desc in MODULES:
            item = QListWidgetItem(name)
            item.setToolTip(desc)
            self._module_list.addItem(item)
        self._module_list.setCurrentRow(0)
        if _HAS_QT:
            self._module_list.currentRowChanged.connect(self.module_selected)
        mod_lay.addWidget(self._module_list)
        layout.addWidget(grp_mod)

        # ── Word input ────────────────────────────────────────────────────────
        grp_word = QGroupBox('WORD INPUT')
        word_lay = QVBoxLayout(grp_word)
        self._word_input = QLineEdit()
        self._word_input.setPlaceholderText('Enter word or phrase…')
        self._calc_btn   = QPushButton('CALCULATE  ⊗')
        word_lay.addWidget(self._word_input)
        word_lay.addWidget(self._calc_btn)
        layout.addWidget(grp_word)

        # ── Adaptation (Function 10) — parameter tuning ───────────────────────
        grp_adapt = QGroupBox('ADAPTATION  (Function 10)')
        adapt_lay = QVBoxLayout(grp_adapt)

        self._tau_lbl = QLabel(f'τ  (Capacitor)  1.0')
        self._tau_slider = QSlider(Qt.Horizontal)
        self._tau_slider.setRange(1, 200)
        self._tau_slider.setValue(10)
        self._tau_slider.valueChanged.connect(
            lambda v: self._tau_lbl.setText(f'τ  (Capacitor)  {v/10:.1f}')
        )

        self._n_lbl = QLabel(f'N  (zeros)  20')
        self._n_slider = QSlider(Qt.Horizontal)
        self._n_slider.setRange(1, 20)
        self._n_slider.setValue(20)
        self._n_slider.valueChanged.connect(
            lambda v: self._n_lbl.setText(f'N  (zeros)  {v}')
        )

        adapt_lay.addWidget(self._tau_lbl)
        adapt_lay.addWidget(self._tau_slider)
        adapt_lay.addWidget(self._n_lbl)
        adapt_lay.addWidget(self._n_slider)
        layout.addWidget(grp_adapt)

        # ── Display mode (like VCDS screen selector) ──────────────────────────
        grp_mode = QGroupBox('DISPLAY MODE')
        mode_lay = QVBoxLayout(grp_mode)
        self._mode_combo = QComboBox()
        for m in ['16ch Sedenion', 'Riemann Strip', 'Phase Space (x,p)',
                  'Fano Plane', 'Equation Plot', 'Balance Manifold']:
            self._mode_combo.addItem(m)
        mode_lay.addWidget(self._mode_combo)
        layout.addWidget(grp_mode)

        layout.addStretch()

    @property
    def tau(self) -> float:
        return self._tau_slider.value() / 10.0

    @property
    def n_zeros(self) -> int:
        return self._n_slider.value()

    @property
    def word(self) -> str:
        return self._word_input.text().strip()

    @property
    def mode(self) -> str:
        return self._mode_combo.currentText()


class MainWindow(QMainWindow):
    """
    ArdaQuenta — VCDS for the Ptolemy mathematics engine.

    The derivation engine IS a TDI engine.
    This window IS the VCDS diagnostic tool for it.
    """

    def __init__(self):
        if not _HAS_QT:
            raise RuntimeError('PyQt5 required')
        super().__init__()
        self.setWindowTitle('ArdaQuenta — Ptolemy Supermath Calculator')
        self.setMinimumSize(1024, 700)
        self.setStyleSheet(_style_sheet())

        # ── Engine instances ──────────────────────────────────────────────────
        self._rb    = RedBlueHamiltonian()
        self._H     = HamiltonianXP()
        self._N     = NoetherCurrents()
        self._C     = Capacitor(tau=1.0)
        self._eng   = Understand(tau=1.0)

        self._build_toolbar()
        self._build_central()
        self._build_statusbar()

        # ── Refresh timer (like VCDS live data polling) ───────────────────────
        self._timer = QTimer(self)
        self._timer.setInterval(250)    # 4 Hz — same cadence as VCDS Measuring Blocks
        self._timer.timeout.connect(self._tick)
        self._timer.start()

        self._run_dtc_check()

    def _build_toolbar(self):
        tb = QToolBar('Main')
        tb.setMovable(False)
        self.addToolBar(tb)

        for label, slot in [
            ('[Select]',     self._select),
            ('[Auto-Run]',   self._auto_run),
            ('[Data Log]',   self._data_log),
            ('[DTC Reset]',  self._dtc_reset),
            ('[About]',      self._about),
        ]:
            btn = QPushButton(label)
            btn.setFixedHeight(28)
            btn.clicked.connect(slot)
            tb.addWidget(btn)

    def _build_central(self):
        central = QWidget()
        self.setCentralWidget(central)
        outer = QVBoxLayout(central)
        outer.setContentsMargins(4, 4, 4, 4)
        outer.setSpacing(4)

        # ── Top: canvas + right panel ─────────────────────────────────────────
        top_split = QSplitter(Qt.Horizontal)

        # Canvas placeholder — VisPy embeds here when available
        self._canvas_widget = QWidget()
        self._canvas_widget.setMinimumWidth(600)
        self._canvas_widget.setStyleSheet(f'background: #050510; border: 1px solid {BORDER};')
        canvas_lbl = QLabel(
            '⊗  ArdaQuenta\n\n'
            'VisPy canvas mounts here.\n'
            'Select a Control Module →\n'
            'then choose a Display Mode.',
            self._canvas_widget
        )
        canvas_lbl.setAlignment(Qt.AlignCenter)
        canvas_lbl.setStyleSheet(f'color: {TEXT_DIM}; font-size: 13px; font-family: monospace;')
        canvas_lbl.setGeometry(0, 0, 600, 500)

        self._eq_panel = EquationPanel()
        if _HAS_QT:
            self._eq_panel.module_selected.connect(self._on_module_selected)
            self._eq_panel._calc_btn.clicked.connect(self._calculate_word)

        top_split.addWidget(self._canvas_widget)
        top_split.addWidget(self._eq_panel)
        top_split.setSizes([680, 300])

        # ── Bottom: DTC panel + live diagnostics ─────────────────────────────
        bot_split = QSplitter(Qt.Horizontal)
        self._dtc    = DTCPanel()
        self._diag   = LiveDiagnostics()
        bot_split.addWidget(self._dtc)
        bot_split.addWidget(self._diag)
        bot_split.setSizes([580, 400])

        # ── Main vertical split ───────────────────────────────────────────────
        v_split = QSplitter(Qt.Vertical)
        v_split.addWidget(top_split)
        v_split.addWidget(bot_split)
        v_split.setSizes([480, 180])

        outer.addWidget(v_split)

        # ── Output log ────────────────────────────────────────────────────────
        self._output = QTextEdit()
        self._output.setReadOnly(True)
        self._output.setMaximumHeight(110)
        outer.addWidget(self._output)

    def _build_statusbar(self):
        sb = QStatusBar()
        self.setStatusBar(sb)
        self._status_lbl = QLabel(
            f'Engine ready  |  Ω_ZS={OMEGA_ZS}  |  GAP=0.000707  |  σ_crit=½'
        )
        sb.addPermanentWidget(self._status_lbl)

    # ── Toolbar slots ──────────────────────────────────────────────────────────

    def _select(self):
        self._output.append('→ Select Control Module — use the list →')

    def _auto_run(self):
        self._output.append('→ Auto-Run: cycling all 12 control modules…')
        for i in range(len(MODULES)):
            self._on_module_selected(i)

    def _data_log(self):
        self._output.append('→ Data Log: recording to derivation_log.json…')

    def _dtc_reset(self):
        self._dtc.clear()
        self._output.append('→ DTC Reset: fault log cleared.')
        self._run_dtc_check()

    def _about(self):
        self._output.append(
            '⊗ ArdaQuenta — Ptolemy Supermath Calculator\n'
            '  H_RB = Σ_p p^{-σ} [R̂_p ⊗ ∂̂_{∂M} + ∂̂†_{∂M} ⊗ B̂_p]\n'
            f'  {len(MODULES)} control modules  |  VCDS-protocol diagnostic interface\n'
            '  © 2026 Cody Michael Allison'
        )

    # ── Module selection ───────────────────────────────────────────────────────

    def _on_module_selected(self, idx: int):
        if idx < 0 or idx >= len(MODULES):
            return
        name, desc = MODULES[idx]
        self._output.append(f'\n[{idx:02d}] {name}')
        self._output.append(f'     {desc}')
        self._run_module(idx, name)

    def _run_module(self, idx: int, name: str):
        """Execute the selected derivation module and display results."""
        try:
            x0, p0 = 1.5, 0.5
            if 'xp' in name or 'H =' in name:
                e = self._H.prime(x0, p0)
                xT, pT = self._H.trajectory(x0, p0, 1.0)
                self._output.append(
                    f'  E = xp = {e:.6f}\n'
                    f'  (x,p) @ t=1: ({xT:.4f}, {pT:.4f})\n'
                    f'  Scale check: {self._H.scale_check(x0, p0)}'
                )
                self._diag.update_values(e, -e, e)

            elif 'RedBlue' in name or 'H_RB' in name:
                balance = self._rb.balance(x0, p0)
                j_fwd   = self._rb.noether_forward(x0, p0)
                j_bck   = self._rb.noether_backward(x0, p0)
                feq     = self._rb.functional_equation_check(x0, p0)
                self._output.append(
                    f'  J_Red  = {j_fwd:+.6f}\n'
                    f'  J_Blue = {j_bck:+.6f}\n'
                    f'  Balance= {balance:+.6f}\n'
                    f'  ξ(s)=ξ(1-s) check: ΔJ = {feq:.2e}'
                )
                self._diag.update_values(j_fwd, j_bck, balance)

            elif 'Capacitor' in name:
                tau = self._eq_panel.tau
                c   = Capacitor(tau=tau)
                signals = [self._H.prime(x0, p0 * (1 + 0.1*i)) for i in range(20)]
                dc = c.dc(signals)
                self._output.append(
                    f'  τ = {tau:.1f}\n'
                    f'  DC extracted: {dc:.6f}\n'
                    f'  Samples: {c.samples}'
                )
                self._diag.update_values(signals[0], -signals[0], dc)

            elif 'forced_sigma' in name:
                from engine.noether import NoetherCurrents
                n    = NoetherCurrents()
                word = self._make_test_word()
                n.forward(word)
                n.backward(word)
                sigma = n.forced_sigma(word.magnitude)
                self._output.append(
                    f'  σ_forced = {sigma:.10f}\n'
                    f'  (should be exactly 0.5000000000)\n'
                    f'  Error: {abs(sigma - 0.5):.2e}'
                )
                self._diag.update_values(
                    word.noether_forward, word.noether_backward,
                    word.dc, sigma=sigma
                )

            elif 'zeros' in name.lower():
                n = self._eq_panel.n_zeros
                zeros = self._H.zeros(n)
                self._output.append(
                    f'  First {n} Riemann zeros γₙ:\n  ' +
                    ', '.join(f'{g:.3f}' for g in zeros[:10]) +
                    ('…' if n > 10 else '')
                )

            elif 'SemanticWord' in name:
                word = self._make_test_word()
                self._output.append(f'  {word!r}')
                self._diag.update_values(
                    word.noether_forward, word.noether_backward,
                    word.dc, sigma=word.prime.real
                )

        except Exception as exc:
            self._output.append(f'  ✗ {exc}')
            self._dtc.add_dtc('P0300', f'Random misfire: {exc}', ok=False)

    def _make_test_word(self):
        from engine.understand import Understand as U
        text = self._eq_panel.word or 'prime'
        eng  = U(tau=self._eq_panel.tau)
        return eng.process(text)

    # ── Word calculation ───────────────────────────────────────────────────────

    def _calculate_word(self):
        text = self._eq_panel.word
        if not text:
            return
        try:
            word = self._make_test_word()
            self._output.append(
                f'\n⊗ WORD: "{text}"\n'
                f'  {word!r}\n'
                f'  γ (zero)  = {word.gamma:.6f}\n'
                f'  |E| (xp)  = {word.magnitude:.6f}\n'
                f'  DC prime  = {word.dc:.6f}\n'
                f'  Faces     = {word.faces()}'
            )
            self._N.forward(word)
            self._N.backward(word)
            feq = abs(word.noether_forward + word.noether_backward)
            self._diag.update_values(
                word.noether_forward, word.noether_backward,
                word.dc, sigma=word.prime.real
            )
            if feq > 0.1:
                self._dtc.add_dtc('P0171', f'Field too lean for "{text}"', ok=False)
            else:
                self._dtc.add_dtc('B0001', f'Word "{text}" balanced ΔJ={feq:.2e}', ok=True)
        except Exception as exc:
            self._output.append(f'  ✗ calculate: {exc}')

    # ── DTC check (like VCDS Auto-Scan) ───────────────────────────────────────

    def _run_dtc_check(self):
        self._dtc.clear()
        try:
            x0, p0 = 1.0, 1.0
            e = self._H.prime(x0, p0)
            self._dtc.add_dtc('P0340', 'CMP — HamiltonianXP loaded', ok=True)
        except Exception as ex:
            self._dtc.add_dtc('P0340', f'CMP fault — {ex}', ok=False)

        try:
            feq = abs(self._rb.functional_equation_check(1.5, 0.5))
            ok  = feq < 0.1
            self._dtc.add_dtc('RH001',
                f'Functional eq ξ(s)=ξ(1-s)  ΔJ={feq:.2e}', ok=ok)
        except Exception as ex:
            self._dtc.add_dtc('RH001', f'FEQ fault — {ex}', ok=False)

        try:
            from engine.noether import NoetherCurrents as NC
            NC()
            self._dtc.add_dtc('P0335', 'CKP — NoetherCurrents loaded', ok=True)
        except Exception as ex:
            self._dtc.add_dtc('P0335', f'CKP fault — {ex}', ok=False)

        try:
            Capacitor(tau=1.0)
            self._dtc.add_dtc('P0401', 'EGR — Capacitor loaded', ok=True)
        except Exception as ex:
            self._dtc.add_dtc('P0401', f'EGR fault — {ex}', ok=False)

        try:
            Understand(tau=1.0)
            self._dtc.add_dtc('P0304', 'Glow plug — Understand loaded', ok=True)
        except Exception as ex:
            self._dtc.add_dtc('P0304', f'Glow plug fault — {ex}', ok=False)

    # ── Live data refresh ──────────────────────────────────────────────────────

    def _tick(self):
        """4 Hz poll — updates live diagnostics like VCDS Measuring Blocks."""
        try:
            x0, p0 = 1.5, 0.5
            j_fwd  = self._rb.noether_forward(x0, p0)
            j_bck  = self._rb.noether_backward(x0, p0)
            bal    = j_fwd + j_bck
            self._C.charge(j_fwd)
            self._diag.update_values(j_fwd, j_bck, self._C.state)
        except Exception:
            pass


def run():
    """Launch the ArdaQuenta application."""
    if not _HAS_QT:
        print('PyQt5 not available. Install with: pip install PyQt5')
        return 1
    app = QApplication.instance() or QApplication(sys.argv)
    app.setApplicationName('ArdaQuenta')
    win = MainWindow()
    win.show()
    return app.exec_()
