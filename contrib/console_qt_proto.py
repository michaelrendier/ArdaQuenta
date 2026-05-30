"""
ainulindale_engine.engine.console_qt
======================================
Qt viewer — Phase 3.

Layout:
    +-----------------------------+------------------+
    |  VisPy Canvas               |  MODULE LIST     |
    |  [fano/complex/3d/text/     |  equation sel    |
    |   sonification]             |  param controls  |
    +-----------------------------+------------------+
    |  QTermWidget shell          |  OUTPUT / INFO   |
    +-----------------------------+------------------+

Display modes:
    complex_plane   polar plot of inversion trajectory
    3d_cartesian    3D flow (VisPy scatter/line)
    fano            Fano plane (G2 / octonion structure)
    sonification    audio display (waveform + play)
    text            structured text, always available

Sonification note:
    Sonification is a display mode, not a separate module.
    Viewer calls module.viewer_data(eq, params, 'sonification').
    Module returns omega/frequency data; viewer renders and plays.
    The standalone Ainulindale Synthesizer is a separate repo.

Version: 0.111
"""

import sys
import math
from typing import Dict, Any, Optional, List

try:
    from PyQt5.QtWidgets import (
        QApplication, QMainWindow, QWidget, QSplitter,
        QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
        QLabel, QPushButton, QComboBox, QTextEdit, QLineEdit,
        QGroupBox, QScrollArea, QSizePolicy, QSlider, QStatusBar,
    )
    from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QThread
    from PyQt5.QtGui import QFont, QColor, QPalette
    _HAS_QT = True
except ImportError:
    _HAS_QT = False

try:
    from vispy import app as vispy_app, scene
    from vispy.scene import visuals
    import numpy as np
    _HAS_VISPY = True
except ImportError:
    _HAS_VISPY = False

try:
    import qtermwidget
    _HAS_QTERM = True
except ImportError:
    _HAS_QTERM = False

try:
    import numpy as np
    _HAS_NP = True
except ImportError:
    _HAS_NP = False


# ── Colour palette ────────────────────────────────────────────────────────────

DARK_BG    = '#0d0d0d'
PANEL_BG   = '#111111'
ACCENT     = '#00bfff'     # deep sky blue — Ainulindale primary
ACCENT2    = '#7b2fff'     # violet — secondary
TEXT_MAIN  = '#e8e8e8'
TEXT_DIM   = '#555555'
BORDER     = '#222222'
GOLD       = '#c8a84b'     # for confidence ESTABLISHED
TEAL       = '#2fffd0'     # THEORETICAL
ORANGE     = '#ff8c00'     # CONJECTURE
RED        = '#ff3333'     # OPEN

CONFIDENCE_COLOUR = {
    'ESTABLISHED': GOLD,
    'THEORETICAL': TEAL,
    'CONJECTURE':  ORANGE,
    'OPEN':        RED,
}

STYLESHEET = f"""
QMainWindow, QWidget {{
    background-color: {DARK_BG};
    color: {TEXT_MAIN};
    font-family: 'JetBrains Mono', 'Fira Code', 'Consolas', monospace;
    font-size: 11px;
}}
QSplitter::handle {{
    background-color: {BORDER};
}}
QGroupBox {{
    border: 1px solid {BORDER};
    border-radius: 3px;
    margin-top: 8px;
    padding: 4px;
    color: {TEXT_DIM};
    font-size: 10px;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    left: 6px;
    color: {ACCENT};
}}
QListWidget {{
    background-color: {PANEL_BG};
    border: 1px solid {BORDER};
    outline: 0;
}}
QListWidget::item:selected {{
    background-color: {ACCENT2};
    color: {TEXT_MAIN};
}}
QListWidget::item:hover {{
    background-color: #1a1a2e;
}}
QComboBox {{
    background-color: {PANEL_BG};
    border: 1px solid {BORDER};
    padding: 2px 6px;
    color: {TEXT_MAIN};
}}
QComboBox QAbstractItemView {{
    background-color: {PANEL_BG};
    selection-background-color: {ACCENT2};
}}
QPushButton {{
    background-color: #1a1a2e;
    border: 1px solid {ACCENT};
    padding: 4px 10px;
    color: {ACCENT};
    border-radius: 2px;
}}
QPushButton:hover {{
    background-color: {ACCENT};
    color: {DARK_BG};
}}
QPushButton:pressed {{
    background-color: {ACCENT2};
    color: {TEXT_MAIN};
}}
QTextEdit, QLineEdit {{
    background-color: {PANEL_BG};
    border: 1px solid {BORDER};
    color: {TEXT_MAIN};
    selection-background-color: {ACCENT2};
}}
QLabel {{
    color: {TEXT_MAIN};
}}
QStatusBar {{
    background-color: {PANEL_BG};
    color: {TEXT_DIM};
    border-top: 1px solid {BORDER};
}}
QScrollBar:vertical {{
    background: {PANEL_BG};
    width: 6px;
}}
QScrollBar::handle:vertical {{
    background: {TEXT_DIM};
    border-radius: 3px;
}}
"""


# ── VisPy canvas widget ───────────────────────────────────────────────────────

_QWidgetBase = QWidget if _HAS_QT else object


class VispyCanvas(_QWidgetBase):
    """
    VisPy canvas embedded in Qt.
    Renders complex_plane, 3d_cartesian, fano, sonification waveform.
    Falls back to text renderer if VisPy not available.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._canvas = None
        self._fallback_text = None
        self._current_mode = 'text'

        if _HAS_VISPY:
            self._init_vispy()
        else:
            self._init_fallback()

    def _init_vispy(self):
        self._canvas = scene.SceneCanvas(
            keys='interactive',
            bgcolor=DARK_BG,
            show=False,
        )
        self._canvas.native.setParent(self)
        self._layout.addWidget(self._canvas.native)
        self._view = self._canvas.central_widget.add_view()
        self._view.camera = 'panzoom'

    def _init_fallback(self):
        self._fallback_text = QTextEdit()
        self._fallback_text.setReadOnly(True)
        self._fallback_text.setFont(QFont('Consolas', 10))
        self._fallback_text.setStyleSheet(
            f"background:{PANEL_BG}; color:{ACCENT}; border:none;"
        )
        self._layout.addWidget(self._fallback_text)

    def render(self, display_mode: str, data: Dict[str, Any]):
        """Dispatch to correct renderer."""
        self._current_mode = display_mode

        if not _HAS_VISPY:
            self._render_text_fallback(data)
            return

        # Clear previous visuals
        self._view.scene.children[:] = []
        try:
            self._view.camera = '3d' if display_mode == '3d_cartesian' else 'panzoom'
        except Exception:
            pass

        if display_mode == 'complex_plane':
            self._render_complex_plane(data)
        elif display_mode == '3d_cartesian':
            self._render_3d(data)
        elif display_mode == 'fano':
            self._render_fano(data)
        elif display_mode == 'sonification':
            self._render_sonification_waveform(data)
        else:
            self._render_text_overlay(data.get('text', str(data)))

        self._canvas.update()

    # ── VisPy renderers ───────────────────────────────────────────────────────

    def _render_complex_plane(self, data: Dict):
        if not _HAS_NP:
            self._render_text_overlay("numpy required for complex_plane render")
            return

        dtype = data.get('type', '')
        cartesian = data.get('cartesian', [])
        if not cartesian:
            self._render_text_overlay("No trajectory data.")
            return

        pts = np.array([[x, y, 0.0] for x, y in cartesian], dtype=np.float32)
        line = visuals.Line(
            pos=pts,
            color=ACCENT,
            width=1.5,
            method='gl',
            parent=self._view.scene,
        )

        # Mark fixed point r=1
        fp = data.get('fixed_point')
        if fp:
            fp_pt = np.array([[fp[0], fp[1], 0.0]], dtype=np.float32)
            visuals.Markers(
                pos=fp_pt,
                face_color=GOLD,
                size=8,
                parent=self._view.scene,
            )

        # Mark phi attractor
        phi_pt = data.get('phi')
        if phi_pt:
            p = np.array([[phi_pt[0], phi_pt[1], 0.0]], dtype=np.float32)
            visuals.Markers(
                pos=p,
                face_color=TEAL,
                size=8,
                parent=self._view.scene,
            )

        self._view.camera.set_range()

    def _render_3d(self, data: Dict):
        if not _HAS_NP:
            self._render_text_overlay("numpy required for 3d_cartesian render")
            return

        points_3d = data.get('points', [])
        if not points_3d:
            self._render_text_overlay("No 3D point data.")
            return

        pts = np.array(points_3d, dtype=np.float32)

        try:
            self._view.camera = scene.cameras.TurntableCamera(
                elevation=20, azimuth=30, fov=45
            )
        except Exception:
            pass

        visuals.Line(
            pos=pts,
            color=ACCENT2,
            width=2.0,
            method='gl',
            parent=self._view.scene,
        )
        visuals.Markers(
            pos=pts,
            face_color=ACCENT,
            size=5,
            parent=self._view.scene,
        )

        target = data.get('target')
        if target:
            t_pt = np.array([list(target)], dtype=np.float32)
            visuals.Markers(
                pos=t_pt,
                face_color=TEAL,
                size=10,
                parent=self._view.scene,
            )

        self._view.camera.set_range()

    def _render_fano(self, data: Dict):
        """
        Fano plane — G2 / octonion structure visualiser.
        7 points, 7 lines (each 3-point). Points on unit circle + centre.
        data may provide 'labels' list of 7 strings, 'highlight' index list.
        """
        if not _HAS_NP:
            self._render_text_overlay("numpy required for Fano render")
            return

        # Standard Fano plane layout — 7 points
        angles = [i * 2 * math.pi / 7 for i in range(7)]
        pts_2d = [(math.cos(a), math.sin(a)) for a in angles]

        # 7 Fano lines (triples that are collinear)
        fano_lines = [
            (0, 1, 3), (1, 2, 4), (2, 3, 5),
            (3, 4, 6), (4, 5, 0), (5, 6, 1), (6, 0, 2),
        ]

        highlight = set(data.get('highlight', []))

        for triple in fano_lines:
            line_pts = np.array(
                [[pts_2d[i][0], pts_2d[i][1], 0.0] for i in triple],
                dtype=np.float32,
            )
            visuals.Line(
                pos=line_pts,
                color=ACCENT,
                width=1.0,
                method='gl',
                connect='strip',
                parent=self._view.scene,
            )

        colours = []
        for i in range(7):
            if i in highlight:
                colours.append(GOLD)
            else:
                colours.append(ACCENT2)

        all_pts = np.array(
            [[x, y, 0.0] for x, y in pts_2d], dtype=np.float32
        )
        visuals.Markers(
            pos=all_pts,
            face_color=colours,
            size=10,
            parent=self._view.scene,
        )

        labels = data.get('labels', [str(i) for i in range(7)])
        for i, (x, y) in enumerate(pts_2d):
            lbl = labels[i] if i < len(labels) else str(i)
            visuals.Text(
                text=lbl,
                pos=[x * 1.12, y * 1.12, 0.0],
                color=TEXT_MAIN,
                font_size=9,
                parent=self._view.scene,
            )

        self._view.camera.set_range()

    def _render_sonification_waveform(self, data: Dict):
        """
        Render waveform from sonification viewer_data.
        data keys expected:
            'waveform': list of float samples  (optional, for preview)
            'omega':    angular frequency (radians/s)
            'label':    display label
            'equation': equation name
        """
        if not _HAS_NP:
            self._render_text_overlay("numpy required for waveform render")
            return

        waveform = data.get('waveform')
        omega = data.get('omega', 0.0)
        label = data.get('label', '')

        if waveform is None:
            # Generate preview sine from omega
            if omega > 0:
                t = np.linspace(0, 2 * math.pi, 512, dtype=np.float32)
                f = omega / (2 * math.pi)
                waveform = np.sin(2 * math.pi * f * t).tolist()
            else:
                self._render_text_overlay(
                    f"Sonification: {label}\nomega = {omega}\nNo waveform data."
                )
                return

        t = np.linspace(0, 1, len(waveform), dtype=np.float32)
        y = np.array(waveform, dtype=np.float32)
        pts = np.column_stack([t, y, np.zeros_like(t)])

        visuals.Line(
            pos=pts,
            color=ACCENT,
            width=1.5,
            method='gl',
            parent=self._view.scene,
        )
        self._view.camera.set_range()

    def _render_text_overlay(self, text: str):
        """Render text as a VisPy text visual."""
        try:
            visuals.Text(
                text=text[:500],
                pos=[0, 0, 0],
                color=TEXT_MAIN,
                font_size=10,
                parent=self._view.scene,
            )
            self._view.camera.set_range()
        except Exception:
            pass

    def _render_text_fallback(self, data: Dict):
        if self._fallback_text:
            text = data.get('text', str(data))
            self._fallback_text.setPlainText(text)


# ── Sonification play panel (inside viewer) ───────────────────────────────────

class SonificationPanel(_QWidgetBase):
    """
    Audio control strip — shown when display_mode == 'sonification'.
    Plays omega-derived tone via system audio (sounddevice if available).
    Self-contained within the viewer; no Synthesizer dependency.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(4, 2, 4, 2)

        self._play_btn = QPushButton('▶ PLAY')
        self._stop_btn = QPushButton('■ STOP')
        self._omega_label = QLabel('ω = —')
        self._freq_label = QLabel('f = — Hz')

        self._play_btn.clicked.connect(self._play)
        self._stop_btn.clicked.connect(self._stop)

        self._layout.addWidget(self._omega_label)
        self._layout.addWidget(self._freq_label)
        self._layout.addStretch()
        self._layout.addWidget(self._play_btn)
        self._layout.addWidget(self._stop_btn)

        self._current_data: Dict = {}
        self._stream = None

        self.setVisible(False)

    def set_data(self, data: Dict):
        self._current_data = data
        omega = data.get('omega', 0.0)
        freq  = omega / (2 * math.pi) if omega else 0.0
        self._omega_label.setText(f'ω = {omega:.6f} rad/s')
        self._freq_label.setText(f'f = {freq:.4f} Hz')
        self.setVisible(True)

    def _play(self):
        try:
            import sounddevice as sd
            omega = self._current_data.get('omega', 440.0)
            freq  = omega / (2 * math.pi)
            dur   = float(self._current_data.get('duration_s', 2.0))
            sr    = 44100
            t     = np.linspace(0, dur, int(sr * dur), dtype=np.float32)
            wave  = 0.3 * np.sin(2 * math.pi * freq * t)
            sd.play(wave, samplerate=sr)
        except ImportError:
            pass
        except Exception:
            pass

    def _stop(self):
        try:
            import sounddevice as sd
            sd.stop()
        except Exception:
            pass


# ── Right panel: module + equation selector ───────────────────────────────────

class SelectorPanel(_QWidgetBase):
    """
    Module list → equation list → param controls → Run button.
    Emits signals; main window connects them to the canvas renderer.
    """

    run_requested = pyqtSignal(str, str, dict, str) if _HAS_QT else None  # module, equation, params, display_mode

    def __init__(self, registry, parent=None):
        super().__init__(parent)
        self._registry = registry
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(4, 4, 4, 4)
        self._layout.setSpacing(4)

        # ── Module list ──────────────────────────────────────────────────────
        mod_group = QGroupBox("MODULES")
        mod_layout = QVBoxLayout(mod_group)
        self._module_list = QListWidget()
        self._module_list.setMaximumHeight(120)
        mod_layout.addWidget(self._module_list)
        self._layout.addWidget(mod_group)

        # ── Equation list ────────────────────────────────────────────────────
        eq_group = QGroupBox("EQUATIONS")
        eq_layout = QVBoxLayout(eq_group)
        self._eq_list = QListWidget()
        self._eq_list.setMaximumHeight(160)
        eq_layout.addWidget(self._eq_list)
        self._layout.addWidget(eq_group)

        # ── Display mode ─────────────────────────────────────────────────────
        mode_group = QGroupBox("DISPLAY MODE")
        mode_layout = QVBoxLayout(mode_group)
        self._mode_combo = QComboBox()
        for m in ['text', 'complex_plane', '3d_cartesian', 'fano', 'sonification']:
            self._mode_combo.addItem(m)
        mode_layout.addWidget(self._mode_combo)
        self._layout.addWidget(mode_group)

        # ── Param controls ───────────────────────────────────────────────────
        param_group = QGroupBox("PARAMS")
        param_layout = QVBoxLayout(param_group)
        self._param_area = QTextEdit()
        self._param_area.setMaximumHeight(80)
        self._param_area.setPlaceholderText('r=2.0\ntheta_rad=0.0')
        self._param_area.setFont(QFont('Consolas', 10))
        param_layout.addWidget(self._param_area)
        self._layout.addWidget(param_group)

        # ── Run button ───────────────────────────────────────────────────────
        self._run_btn = QPushButton('▶  RUN')
        self._run_btn.setMinimumHeight(30)
        self._layout.addWidget(self._run_btn)
        self._layout.addStretch()

        # ── Equation info ────────────────────────────────────────────────────
        info_group = QGroupBox("EQUATION INFO")
        info_layout = QVBoxLayout(info_group)
        self._eq_info = QTextEdit()
        self._eq_info.setReadOnly(True)
        self._eq_info.setFont(QFont('Consolas', 9))
        self._eq_info.setMaximumHeight(120)
        info_layout.addWidget(self._eq_info)
        self._layout.addWidget(info_group)

        # ── Wire signals ─────────────────────────────────────────────────────
        self._module_list.currentRowChanged.connect(self._on_module_selected)
        self._eq_list.currentRowChanged.connect(self._on_eq_selected)
        self._run_btn.clicked.connect(self._on_run)

        self._populate_modules()

    def _populate_modules(self):
        self._module_list.clear()
        for name in self._registry.list_modules():
            mod = self._registry.get_module(name)
            item = QListWidgetItem(f'{mod.display_name}')
            item.setData(Qt.UserRole, name)
            self._module_list.addItem(item)
        if self._module_list.count():
            self._module_list.setCurrentRow(0)

    def _on_module_selected(self, row):
        if row < 0:
            return
        item = self._module_list.item(row)
        if not item:
            return
        mod_name = item.data(Qt.UserRole)
        self._eq_list.clear()
        for key in self._registry.list_equations(mod_name):
            eq = self._registry.get_equation(key)
            if eq is None:
                continue
            c = CONFIDENCE_COLOUR.get(eq.confidence, TEXT_MAIN)
            lbl = f'[{eq.confidence[0]}] {eq.display}'
            list_item = QListWidgetItem(lbl)
            list_item.setForeground(QColor(c))
            list_item.setData(Qt.UserRole, (mod_name, eq.name))
            self._eq_list.addItem(list_item)
        if self._eq_list.count():
            self._eq_list.setCurrentRow(0)

    def _on_eq_selected(self, row):
        if row < 0:
            return
        item = self._eq_list.item(row)
        if not item:
            return
        mod_name, eq_name = item.data(Qt.UserRole)
        eq = self._registry.get_equation(f'{mod_name}.{eq_name}')
        if eq is None:
            return

        # Update display mode options to those the equation supports
        self._mode_combo.blockSignals(True)
        self._mode_combo.clear()
        available = eq.display_options if eq.display_options else ['text']
        if 'text' not in available:
            available = ['text'] + available
        for m in available:
            self._mode_combo.addItem(m)
        self._mode_combo.blockSignals(False)

        # Pre-fill params
        if eq.params:
            self._param_area.setPlainText('\n'.join(f'{p}=' for p in eq.params))
        else:
            self._param_area.clear()

        # Info panel
        c = CONFIDENCE_COLOUR.get(eq.confidence, TEXT_MAIN)
        info = (
            f"Name:    {eq.name}\n"
            f"Display: {eq.display}\n"
            f"Confidence: {eq.confidence}\n"
            f"Verified: {eq.code_verified}\n"
            f"Radian:  {eq.radian_form}\n"
            f"Modes:   {', '.join(eq.display_options)}"
        )
        self._eq_info.setPlainText(info)

    def _on_run(self):
        mod_item = self._module_list.currentItem()
        eq_item  = self._eq_list.currentItem()
        if not mod_item or not eq_item:
            return
        mod_name, eq_name = eq_item.data(Qt.UserRole)
        display_mode = self._mode_combo.currentText()

        # Parse params from text area
        params = {}
        raw = self._param_area.toPlainText().strip()
        if raw:
            for line in raw.splitlines():
                line = line.strip()
                if '=' in line:
                    k, v = line.split('=', 1)
                    k = k.strip()
                    v = v.strip()
                    if v:
                        try:
                            params[k] = float(v)
                        except ValueError:
                            params[k] = v

        self.run_requested.emit(mod_name, eq_name, params, display_mode)


# ── Output / info panel ───────────────────────────────────────────────────────

class OutputPanel(_QWidgetBase):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        label = QLabel("OUTPUT")
        label.setStyleSheet(f"color:{ACCENT}; font-size:9px; letter-spacing:2px;")
        layout.addWidget(label)

        self._text = QTextEdit()
        self._text.setReadOnly(True)
        self._text.setFont(QFont('Consolas', 9))
        self._text.setStyleSheet(f"background:{PANEL_BG}; color:{TEXT_MAIN}; border:none;")
        layout.addWidget(self._text)

    def write(self, text: str):
        self._text.append(text)

    def clear(self):
        self._text.clear()


# ── Shell panel ───────────────────────────────────────────────────────────────

class ShellPanel(_QWidgetBase):
    """
    QTermWidget when available; plain Python REPL fallback otherwise.
    Registry shell_commands() are injected into the REPL namespace.
    """

    def __init__(self, registry, parent=None):
        super().__init__(parent)
        self._registry = registry
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        if _HAS_QTERM:
            self._term = qtermwidget.QTermWidget()
            self._term.setColorScheme('DarkPastels')
            self._term.startShellProgram()
            layout.addWidget(self._term)
        else:
            self._build_fallback_repl(layout)

    def _build_fallback_repl(self, layout):
        self._output = QTextEdit()
        self._output.setReadOnly(True)
        self._output.setFont(QFont('Consolas', 10))
        self._output.setStyleSheet(
            f"background:{DARK_BG}; color:{TEAL}; border:none;"
        )

        # Build repl namespace from all registered shell_commands
        self._ns: Dict[str, Any] = {'__builtins__': {}}
        for mod_name in self._registry.list_modules():
            mod = self._registry.get_module(mod_name)
            if mod:
                self._ns.update(mod.shell_commands())

        input_row = QWidget()
        row_layout = QHBoxLayout(input_row)
        row_layout.setContentsMargins(0, 0, 0, 0)
        self._prompt = QLabel('>>>')
        self._prompt.setStyleSheet(f"color:{ACCENT}; font-family:Consolas;")
        self._input = QLineEdit()
        self._input.setFont(QFont('Consolas', 10))
        self._input.setStyleSheet(
            f"background:{DARK_BG}; color:{TEXT_MAIN}; border:none;"
            f"border-top: 1px solid {BORDER};"
        )
        self._input.returnPressed.connect(self._execute)
        row_layout.addWidget(self._prompt)
        row_layout.addWidget(self._input)

        layout.addWidget(self._output)
        layout.addWidget(input_row)

        self._output.append(
            f'<span style="color:{ACCENT}">Ainulindale Engine — Python shell</span>'
        )
        self._output.append(
            f'<span style="color:{TEXT_DIM}">Available: {", ".join(self._ns.keys())}</span>'
        )
        self._output.append(
            f'<span style="color:{TEXT_DIM}">QTermWidget not found — using fallback REPL</span>'
        )

    def _execute(self):
        cmd = self._input.text().strip()
        if not cmd:
            return
        self._output.append(
            f'<span style="color:{ACCENT}">>>> {cmd}</span>'
        )
        self._input.clear()
        try:
            result = eval(cmd, self._ns)        # noqa: S307
            if result is not None:
                self._output.append(
                    f'<span style="color:{TEXT_MAIN}">{result}</span>'
                )
        except SyntaxError:
            try:
                exec(cmd, self._ns)             # noqa: S102
            except Exception as e:
                self._output.append(
                    f'<span style="color:{RED}">{type(e).__name__}: {e}</span>'
                )
        except Exception as e:
            self._output.append(
                f'<span style="color:{RED}">{type(e).__name__}: {e}</span>'
            )


# ── Main window ───────────────────────────────────────────────────────────────

_QMainBase = QMainWindow if _HAS_QT else object


class AinulindalWindow(_QMainBase):

    def __init__(self, registry):
        super().__init__()
        self._registry = registry
        self.setWindowTitle('Ainulindale Derivation Engine')
        self.resize(1280, 800)
        self.setStyleSheet(STYLESHEET)

        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # ── Title bar ────────────────────────────────────────────────────────
        title_bar = QWidget()
        title_bar.setFixedHeight(30)
        title_bar.setStyleSheet(f"background:{PANEL_BG}; border-bottom:1px solid {BORDER};")
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(12, 0, 12, 0)
        lbl = QLabel('◈  AINULINDALE  —  DERIVATION ENGINE')
        lbl.setStyleSheet(f"color:{ACCENT}; font-size:11px; letter-spacing:3px;")
        version_lbl = QLabel('v0.111')
        version_lbl.setStyleSheet(f"color:{TEXT_DIM}; font-size:9px;")
        title_layout.addWidget(lbl)
        title_layout.addStretch()
        title_layout.addWidget(version_lbl)
        root_layout.addWidget(title_bar)

        # ── Main splitter (vertical: top / bottom) ───────────────────────────
        v_split = QSplitter(Qt.Vertical)
        root_layout.addWidget(v_split)

        # Top: canvas | selector
        top_widget = QWidget()
        h_split = QSplitter(Qt.Horizontal)
        top_layout = QVBoxLayout(top_widget)
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.addWidget(h_split)

        # Canvas area (left)
        canvas_widget = QWidget()
        canvas_layout = QVBoxLayout(canvas_widget)
        canvas_layout.setContentsMargins(0, 0, 0, 0)
        canvas_layout.setSpacing(0)

        self._canvas = VispyCanvas()
        canvas_layout.addWidget(self._canvas)

        self._soni_panel = SonificationPanel()
        canvas_layout.addWidget(self._soni_panel)

        h_split.addWidget(canvas_widget)

        # Selector (right)
        self._selector = SelectorPanel(registry)
        self._selector.setMaximumWidth(280)
        self._selector.setMinimumWidth(200)
        h_split.addWidget(self._selector)
        h_split.setStretchFactor(0, 3)
        h_split.setStretchFactor(1, 1)

        v_split.addWidget(top_widget)

        # Bottom: shell | output
        bottom_widget = QWidget()
        bottom_h_split = QSplitter(Qt.Horizontal)
        bottom_layout = QVBoxLayout(bottom_widget)
        bottom_layout.setContentsMargins(0, 0, 0, 0)
        bottom_layout.addWidget(bottom_h_split)

        self._shell  = ShellPanel(registry)
        self._output = OutputPanel()
        bottom_h_split.addWidget(self._shell)
        bottom_h_split.addWidget(self._output)
        bottom_h_split.setStretchFactor(0, 2)
        bottom_h_split.setStretchFactor(1, 1)

        v_split.addWidget(bottom_widget)
        v_split.setStretchFactor(0, 3)
        v_split.setStretchFactor(1, 1)

        # ── Status bar ───────────────────────────────────────────────────────
        self._status = QStatusBar()
        self.setStatusBar(self._status)
        mods = registry.list_modules()
        eqs  = len(registry.list_equations())
        self._status.showMessage(
            f'  {len(mods)} module(s)  |  {eqs} equation(s)  |  '
            f'VisPy: {"ok" if _HAS_VISPY else "missing"}  |  '
            f'QTermWidget: {"ok" if _HAS_QTERM else "missing"}'
        )

        # ── Connect selector signal ───────────────────────────────────────────
        self._selector.run_requested.connect(self._on_run)

    # ── Run handler ───────────────────────────────────────────────────────────

    def _on_run(self, mod_name: str, eq_name: str,
                params: Dict, display_mode: str):
        self._output.clear()
        self._soni_panel.setVisible(False)

        mod = self._registry.get_module(mod_name)
        if not mod:
            self._output.write(f'[ERROR] Module not found: {mod_name}')
            return

        try:
            data = mod.viewer_data(eq_name, params, display_mode)
        except Exception as e:
            self._output.write(f'[ERROR] viewer_data failed:\n{type(e).__name__}: {e}')
            return

        # Always write text result to output panel
        text = data.get('text', '')
        if text:
            self._output.write(text)
        else:
            result_key = data.get('type', display_mode)
            self._output.write(f'mode: {result_key}\n{str(data)[:400]}')

        # Sonification panel
        if display_mode == 'sonification':
            self._soni_panel.set_data(data)

        # Canvas render
        self._canvas.render(display_mode, data)

        self._status.showMessage(
            f'  {mod_name}.{eq_name}  |  mode: {display_mode}  |  params: {params}'
        )


# ── Entry point ───────────────────────────────────────────────────────────────

def run_qt(registry):
    if not _HAS_QT:
        raise ImportError("PyQt5 not available")

    if _HAS_VISPY:
        vispy_app.use_app('pyqt5')

    qt_app = QApplication.instance() or QApplication(sys.argv)
    win = AinulindalWindow(registry)
    win.show()
    sys.exit(qt_app.exec_())
