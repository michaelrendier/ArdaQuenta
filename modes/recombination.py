"""
modes/recombination.py — First Proton + Hydrogen: VisPy gloo demo

Two phases driven entirely by Ainulindale mathematics:
  Phase 1 (0–60s):  Gluon plasma. 13 ZD crossing attempts.
                    σ oscillates around ½, J_red×J_blue not conserved.
                    Colour: red/orange (𝕆 face, σ≈¼)

  Phase 2 (60–90s): Stable hydrogen. σ=½ locked.
                    J_red×J_blue = e^{-E} conserved. Silence.
                    Colour: blue/purple/gold (ℍ face, BAO ring, cardioid)

Math spine:
  H = xp              Berry-Keating Hamiltonian
  x(t) = x₀·eᵗ       carrier (proton position)
  p(t) = p₀·e⁻ᵗ      envelope (plasma cooling)
  σ → ½               forced by Noether F=B convergence
  γₙ                  first 13 Riemann zeros = 13 failed ZD crossings
  d* = 0.2460         Ainulindale constant = BAO ring radius
  L_(I|O) cardioid    r = d*(1 − cos θ) = electron ground state orbital

Canvas: 720 × 1612 portrait (matches phone video from recombination session)

Run standalone:   python3 modes/recombination.py
Embed in viewer:  instantiate RecombinationCanvas(parent=qt_widget)
"""

import sys
import os
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import vispy
vispy.use('PyQt5')
from vispy import gloo, app

# ── Ainulindale constants ──────────────────────────────────────────────────────
D_STAR   = 0.2460          # Ainulindale constant — BAO ring / cardioid scale
SIGMA_H  = 0.5             # σ=½ hydrogen ground state
T_PHASE1 = 60.0            # seconds: Phase 1 duration (gluon plasma)
T_TOTAL  = 90.0            # seconds: full animation

# First 13 Riemann zeros γₙ — the 13 ZD crossing attempts
# These are the "bass spikes" of the universe
GAMMA_13 = [
    14.134725, 21.022040, 25.010858, 30.424876, 32.935062,
    37.586178, 40.918719, 43.327073, 48.005151, 49.773832,
    52.970321, 56.446247, 59.347044,
]

# ── Canvas dimensions ──────────────────────────────────────────────────────────
W, H = 720, 1612           # portrait — matches phone screen recording

# ── GLSL: single fullscreen quad ───────────────────────────────────────────────
VERT = """
#version 130
in  vec2 a_pos;
void main() {
    gl_Position = vec4(a_pos, 0.0, 1.0);
}
"""

FRAG = """
#version 130

uniform vec2  u_res;       // canvas resolution
uniform float u_t;         // current time 0..90
uniform float u_phase;     // 0=plasma, 1=hydrogen (smooth)

const float PI     = 3.14159265358979323846;
const float D_STAR = 0.2460;

// ── Sigma trajectory: oscillates in Phase 1, locks at 0.5 in Phase 2 ─────────
float sigma_t(float t) {
    // 13 Riemann zero oscillations — each one a ZD crossing attempt
    float g[13];
    g[0]=14.134725; g[1]=21.022040; g[2]=25.010858; g[3]=30.424876;
    g[4]=32.935062; g[5]=37.586178; g[6]=40.918719; g[7]=43.327073;
    g[8]=48.005151; g[9]=49.773832; g[10]=52.970321; g[11]=56.446247;
    g[12]=59.347044;

    float osc = 0.0;
    for (int i = 0; i < 13; i++) {
        float w   = g[i] * 0.008;
        float amp = exp(-float(i) * 0.18);
        osc += amp * sin(w * t);
    }
    float delta = 0.22 * exp(-t * 0.12);       // envelope decaying to 0
    return 0.5 + delta + 0.06 * osc * (1.0 - u_phase);
}

// ── Noether convergence glow: concentrates at origin as σ→½ ──────────────────
float noether_glow(vec2 uv, float t) {
    float sig  = sigma_t(t);
    float dsig = abs(sig - 0.5);
    float r    = length(uv);
    return exp(-r * 6.0) * exp(-dsig * 25.0) * (0.3 + 0.7 * u_phase);
}

// ── Gluon plasma field: Dirichlet-series approximation of Re(ζ(σ+it)) ─────────
float plasma(vec2 uv, float t) {
    float g[13];
    g[0]=14.134725; g[1]=21.022040; g[2]=25.010858; g[3]=30.424876;
    g[4]=32.935062; g[5]=37.586178; g[6]=40.918719; g[7]=43.327073;
    g[8]=48.005151; g[9]=49.773832; g[10]=52.970321; g[11]=56.446247;
    g[12]=59.347044;

    float field = 0.0;
    float r     = length(uv);
    for (int n = 1; n <= 13; n++) {
        float fn    = float(n);
        float angle = g[n-1] * log(fn + 1.0) - t * g[n-1] * 0.04
                    + r * g[n-1] * 1.8;
        field += cos(angle) / fn;
    }
    return field;
}

// ── ZD crossing pulse: flash at each γₙ event time ────────────────────────────
float zd_flash(vec2 uv, float t) {
    float g[13];
    g[0]=14.134725; g[1]=21.022040; g[2]=25.010858; g[3]=30.424876;
    g[4]=32.935062; g[5]=37.586178; g[6]=40.918719; g[7]=43.327073;
    g[8]=48.005151; g[9]=49.773832; g[10]=52.970321; g[11]=56.446247;
    g[12]=59.347044;

    float flash = 0.0;
    float r     = length(uv);
    for (int i = 0; i < 13; i++) {
        // Each gamma_i maps to a time event in Phase 1
        float t_event = (g[i] - g[0]) / (g[12] - g[0]) * T_PHASE1 * 0.85;
        float dt      = t - t_event;
        // Asymmetric pulse: fast rise, slow decay (like a bass spike)
        float pulse   = (dt >= 0.0)
            ? exp(-dt * dt * 8.0)
            : exp(-dt * dt * 2.0);
        // Radial falloff from a random-ish position near centre
        float px = 0.12 * sin(g[i]);
        float py = 0.12 * cos(g[i] * 1.3);
        float d  = length(uv - vec2(px, py));
        flash += pulse * exp(-d * d * 30.0);
    }
    return flash;
}

// ── Phase-transition flash: the teal moment (σ locks, Bang) ──────────────────
float trans_flash(vec2 uv, float t) {
    float t_lock = 47.0;              // the teal flash: maximum ZD event
    float dt     = t - t_lock;
    float r      = length(uv);
    float radial = exp(-r * 2.5);
    float time_p = exp(-dt * dt * 0.25) * float(dt >= 0.0)
                 + exp(-dt * dt * 0.08) * float(dt < 0.0);
    return radial * time_p;
}

// ── Double cardioid helper ─────────────────────────────────────────────────────
// r_j = scale * (1 ± cos θ): cusp at origin, loop in -x or +x direction
float j_cardioid(vec2 uv, float scale, float width, float sign_cos) {
    float r  = length(uv);
    float th = atan(uv.y, uv.x);
    float r_c = scale * (1.0 + sign_cos * cos(th));  // sign_cos = +1 or -1
    float d   = abs(r - r_c);
    return exp(-d * d / (width * width));
}

// ── BAO ring: circle at r = d* (the frozen memory of L_(I|O)) ────────────────
float bao(vec2 uv, float r_ring, float width) {
    float r = length(uv);
    float d = abs(r - r_ring);
    return exp(-d * d / (width * width));
}

// ── Quark triplet: three dots at 120° trying to close into proton ─────────────
float quark_triplet(vec2 uv, float t, float attempt_i) {
    float angle_base = attempt_i * 2.0 * PI / 13.0;
    float r_orb      = 0.08 + 0.04 * sin(t * 3.0 + attempt_i);
    float result     = 0.0;
    for (int q = 0; q < 3; q++) {
        float angle = angle_base + float(q) * 2.0 * PI / 3.0
                    + t * (2.0 + attempt_i * 0.3);
        vec2  qpos  = r_orb * vec2(cos(angle), sin(angle));
        float d     = length(uv - qpos);
        result     += exp(-d * d * 800.0);
    }
    return result;
}

// ─────────────────────────────────────────────────────────────────────────────
// MAIN
// ─────────────────────────────────────────────────────────────────────────────
void main() {
    vec2 uv = (gl_FragCoord.xy / u_res.xy) * 2.0 - 1.0;
    // Portrait aspect: x is narrow. Correct so math space is square.
    float aspect = u_res.x / u_res.y;
    uv.x *= aspect;

    float t      = u_t;
    float phase  = u_phase;
    float inv_ph = 1.0 - phase;

    // ── Colours ───────────────────────────────────────────────────────────
    vec3 c_plasma  = vec3(1.00, 0.28, 0.05);  // red/orange  — 𝕆 face σ≈¼
    vec3 c_orange  = vec3(1.00, 0.60, 0.12);  // orange
    vec3 c_teal    = vec3(0.15, 1.00, 0.82);  // teal        — phase transition
    vec3 c_blue    = vec3(0.18, 0.65, 1.00);  // blue        — σ=½ ℍ face
    vec3 c_purple  = vec3(0.55, 0.12, 0.90);  // purple      — ZD boundary
    vec3 c_gold    = vec3(0.92, 0.78, 0.22);  // gold        — d*, BAO, CD shadow
    vec3 c_white   = vec3(1.00, 0.95, 0.90);  // white       — proton core

    // ── Phase 1: gluon plasma ─────────────────────────────────────────────
    float field    = plasma(uv, t);
    float sig      = sigma_t(t);

    // Plasma base — colour shifts with σ deviation from ½
    float sigma_col = smoothstep(0.0, 0.35, abs(sig - 0.5));
    vec3  p_col     = mix(c_orange, c_plasma, sigma_col);

    float p_glow    = (0.15 + 0.55 * abs(field))
                    * exp(-length(uv) * 1.8)
                    * inv_ph;
    vec3  plasma_c  = p_col * p_glow;

    // Radial plasma texture rings (concentric waves = BAO precursors)
    float r        = length(uv);
    float rings    = 0.5 + 0.5 * sin(r * 22.0 - t * 3.5);
    plasma_c      += c_orange * rings * exp(-r * 3.5) * 0.25 * inv_ph;

    // ZD crossing flickers
    float zd       = zd_flash(uv, t);
    vec3  zd_c     = mix(c_orange, c_white, 0.6) * zd * 3.0 * inv_ph;

    // Quark triplets (active during Phase 1, one set per ZD attempt visible)
    float quarks   = 0.0;
    float g_arr[13];
    g_arr[0]=14.134725; g_arr[1]=21.022040; g_arr[2]=25.010858;
    g_arr[3]=30.424876; g_arr[4]=32.935062; g_arr[5]=37.586178;
    g_arr[6]=40.918719; g_arr[7]=43.327073; g_arr[8]=48.005151;
    g_arr[9]=49.773832; g_arr[10]=52.970321; g_arr[11]=56.446247;
    g_arr[12]=59.347044;
    for (int i = 0; i < 13; i++) {
        float t_ev  = (g_arr[i] - g_arr[0]) / (g_arr[12] - g_arr[0]) * 50.0;
        float dt_q  = abs(t - t_ev);
        float weight = exp(-dt_q * dt_q * 3.0);
        quarks += quark_triplet(uv, t, float(i)) * weight;
    }
    vec3  quark_c  = c_orange * quarks * inv_ph * 2.5;

    // Phase transition teal flash
    float tf       = trans_flash(uv, t);
    vec3  trans_c  = c_teal * tf * 4.0;

    // ── Phase 2: stable hydrogen ──────────────────────────────────────────

    // Noether convergence: σ=½ glow building from centre
    float n_glow   = noether_glow(uv, t);
    vec3  noether_c = mix(c_purple, c_blue, phase) * n_glow * 3.5;

    // ── Double cardioid: barycenter geometry ──────────────────────────────────
    // Barycenter = origin = ZD cusp where both J_red and J_blue touch.
    // The axis of the double cardioid precesses at ω_prec = π/6 rad/s
    // (one rotation per 12 seconds — the measured spin period from the ink video).
    float prec_w  = PI / 6.0;
    float prec_a  = prec_w * (t - 60.0) * phase;
    float cos_a   = cos(prec_a);
    float sin_a   = sin(prec_a);
    // Rotate uv into precessing frame
    vec2 uv_bc    = vec2( cos_a * uv.x + sin_a * uv.y,
                         -sin_a * uv.x + cos_a * uv.y);

    // J_red — proton wobble cardioid: tiny, cusp at origin, loop opens RIGHT
    // Scale: proton is 1836× heavier → wobble = electron scale / 1836
    float a_jr    = D_STAR * 0.055;   // ≈ D_STAR/18 for visual clarity
    float j_red_v = j_cardioid(uv_bc, a_jr, 0.006, 1.0) * phase;
    vec3  j_red_c = c_gold * j_red_v * 6.0;

    // J_blue — electron orbital cardioid: large, cusp at origin, loop opens LEFT
    float a_je    = D_STAR * 1.6;
    float j_blue_v = j_cardioid(uv_bc, a_je, 0.009, -1.0) * phase;
    vec3  j_blue_c = c_blue * j_blue_v * 3.0;

    // Barycenter dot: tiny white point at origin = ZD = both cusps
    float bary_r  = length(uv);
    float bary_v  = exp(-bary_r * bary_r * 800.0) * phase;
    vec3  bary_c  = c_white * bary_v * 10.0;

    // Coulomb axis: faint blue-gold gradient along the precessing cardioid axis
    // This is the L_(I|O) pathway connecting J_red and J_blue
    float axis_perp = abs(uv_bc.y);
    float axis_pos  = uv_bc.x;
    float axis_mask = exp(-axis_perp * axis_perp / (0.018 * 0.018))
                    * smoothstep(-a_je * 2.2, -a_jr, axis_pos)
                    * smoothstep( a_jr, a_je * 2.2, -axis_pos + a_jr - a_je)
                    * phase * 0.4;
    // Colour: gold near proton side (+x), blue near electron side (-x)
    float axis_t  = smoothstep(-a_je * 2.0, a_jr * 2.0, axis_pos);
    vec3  axis_c  = mix(c_blue, c_gold, axis_t) * axis_mask;

    // BAO ring — frozen memory of L_(I|O) circle around the whole system
    float bao_r    = D_STAR * (1.5 + 0.3 * phase);
    float bao_w    = 0.010;
    float bao_val  = bao(uv, bao_r, bao_w) * phase;
    vec3  bao_c    = c_gold * bao_val * 4.0;

    // Inner recombination shell
    float shell_r  = D_STAR * (1.1 + 0.2 * phase);
    float shell_v  = bao(uv, shell_r, 0.007) * phase;
    vec3  shell_c  = c_blue * shell_v * 2.5;

    // Dark-field background for Phase 2 (like the ink video after stability)
    float dark_bg   = phase * 0.04 * (1.0 - smoothstep(0.0, 0.8, r));
    vec3  bg_c      = c_purple * dark_bg;

    // Tri-layer colour wash (ZD/σ=½/CD) — the rainbow emerging
    float r_uv      = length(uv);
    float angle_uv  = atan(uv.y, uv.x) / PI;  // -1..1
    vec3  tri_layer = mix(c_purple, c_blue,   smoothstep(-0.5, 0.0, angle_uv));
    tri_layer       = mix(tri_layer, c_gold,  smoothstep( 0.0, 0.5, angle_uv));
    float tri_mask  = exp(-abs(r_uv - bao_r * 0.75) * 12.0) * phase * 0.8;
    vec3  tri_c     = tri_layer * tri_mask;

    // ── Composite ─────────────────────────────────────────────────────────
    vec3 col = vec3(0.0);

    // Phase 1 layers
    col += plasma_c;
    col += zd_c;
    col += quark_c;

    // Transition
    col += trans_c;

    // Phase 2 layers
    col += bg_c;
    col += noether_c;
    col += tri_c;
    col += j_blue_c;      // electron orbital cardioid
    col += axis_c;        // Coulomb / L_(I|O) axis
    col += j_red_c;       // proton wobble cardioid (on top of axis)
    col += shell_c;
    col += bao_c;
    col += bary_c;        // barycenter dot (ZD cusp, topmost)

    // Vignette (portrait: stronger vertical)
    float vig_r    = length(vec2(uv.x / aspect, uv.y));
    float vignette = 1.0 - smoothstep(0.55, 1.15, vig_r);
    col *= vignette;

    // Filmic tone map + gamma
    col  = col / (col + 0.85);
    col  = pow(max(col, vec3(0.0)), vec3(0.42));

    gl_FragColor = vec4(col, 1.0);
}
"""

# ── fullscreen quad: two triangles covering NDC ──────────────────────────────
QUAD = np.array([
    [-1, -1], [ 1, -1], [-1,  1],
    [-1,  1], [ 1, -1], [ 1,  1],
], dtype=np.float32)


class RecombinationCanvas(app.Canvas):
    """
    Standalone VisPy canvas for the proton+hydrogen recombination animation.

    720 × 1612 portrait.  90 seconds.  30 fps.

    Driven entirely by Ainulindale mathematics:
      - Hamiltonian H=xp  (trajectory equations)
      - Noether J_red/J_blue convergence to σ=½
      - Riemann zeros γ₁–γ₁₃ as ZD crossing event times
      - d* = 0.2460 as BAO ring radius
      - L_(I|O) cardioid as electron orbital geometry
    """

    def __init__(self, **kwargs):
        super().__init__(
            title   = 'Recombination — Ainulindale',
            size    = (W, H),
            keys    = 'interactive',
            **kwargs,
        )
        gloo.set_viewport(0, 0, W, H)
        gloo.set_state(clear_color='black', blend=False)

        self._prog = gloo.Program(VERT, FRAG)
        self._prog['a_pos']  = QUAD
        self._prog['u_res']  = [float(W), float(H)]
        self._prog['u_t']    = 0.0
        self._prog['u_phase'] = 0.0

        self._t     = 0.0
        self._dt    = 1.0 / 30.0    # 30 fps
        self._timer = app.Timer(interval=self._dt, connect=self.on_timer,
                                start=True)
        self.show()

    # ── Holcus engine: σ phase from time ────────────────────────────────────
    @staticmethod
    def _phase(t):
        """
        Smooth phase parameter 0→1.
        Uses capacitor charging curve: V(t) = 1 − e^{−(t−T_PHASE1)/τ}
        τ = 6s (6-second settling time, like ink video 9→15s hum decay)
        """
        if t < T_PHASE1:
            return 0.0
        tau = 6.0
        return float(1.0 - np.exp(-(t - T_PHASE1) / tau))

    def on_timer(self, event):
        self._t += self._dt
        if self._t > T_TOTAL:
            self._t = 0.0          # loop

        phase = self._phase(self._t)
        self._prog['u_t']     = self._t
        self._prog['u_phase'] = phase
        self.update()

    def on_draw(self, event):
        gloo.clear()
        self._prog.draw('triangles')

    def on_key_press(self, event):
        if event.key == 'Escape':
            self.app.quit()
        elif event.key == 'Space':
            # Pause/resume
            if self._timer.running:
                self._timer.stop()
            else:
                self._timer.start()
        elif event.key == 'R':
            self._t = 0.0          # reset


# ── Standalone entry point ───────────────────────────────────────────────────
if __name__ == '__main__':
    canvas = RecombinationCanvas()
    app.run()
