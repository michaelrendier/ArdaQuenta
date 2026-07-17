"""
modes/plasma_spectral.py — Quark-Gluon Plasma: Spectral + Shear

The plasma was NOT dark.  It was a glowing photon-baryon fog.
Every point radiates as a blackbody at its local temperature.
The colours ARE the frequency analysis.  The shear IS the Geometer.

Physics:
  T(x,y,t)        local plasma temperature → Planck colour (Wien's peak)
  ω(x,y,t)        vorticity field → Kelvin-Helmholtz shear geometry
  γₙ              13 Riemann zeros → 13 KH vortex seeds / wavenumbers
  σ(t) → ½        Noether convergence → vortices merge → cardioid emerges
  d* = 0.2460     BAO ring = frozen KH memory

Rendering:
  Main panel      T-field → Planck RGB + vorticity overlay
  Bottom strip    live spectrogram (freq×time, coloured by Planck temp)
  Precessing axis  double cardioid born from merged vortex core (Phase 2)

Run:   python3 modes/plasma_spectral.py          (interactive)
       python3 modes/plasma_spectral.py --render  (GPU video export → plasma.mp4)
"""

import sys
import os
import subprocess
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import vispy
vispy.use('PyQt5')
from vispy import gloo, app

# ── Constants ──────────────────────────────────────────────────────────────────
D_STAR   = 0.2460
T_PHASE1 = 60.0
T_TOTAL  = 90.0
FPS      = 30
N_FRAMES = int(T_TOTAL * FPS)
W, H     = 720, 1612

GAMMA = np.array([
    14.134725, 21.022040, 25.010858, 30.424876, 32.935062,
    37.586178, 40.918719, 43.327073, 48.005151, 49.773832,
    52.970321, 56.446247, 59.347044,
], dtype=np.float32)

T_EVENTS = ((GAMMA - GAMMA[0]) / (GAMMA[-1] - GAMMA[0]) * 51.0 + 3.0).astype(np.float32)

QUAD = np.array([
    [-1,-1],[1,-1],[-1,1],
    [-1,1],[1,-1],[1,1],
], dtype=np.float32)

# ── GLSL ───────────────────────────────────────────────────────────────────────
VERT = """
#version 130
in vec2 a_pos;
void main() { gl_Position = vec4(a_pos, 0.0, 1.0); }
"""

FRAG = """
#version 130

uniform vec2  u_res;
uniform float u_t;
uniform float u_phase;
uniform float u_gamma[13];
uniform float u_tevents[13];

const float PI       = 3.14159265358979;
const float D_STAR   = 0.2460;           // Ainulindale constant: VEV / brim radius
const float T_PHASE1 = 60.0;
const float T_TOTAL  = 90.0;
const float SPEC_H   = 0.12;            // spectrogram strip: bottom 12% of canvas
const float FILL_PCT = 0.82;            // electron cardioid fills this fraction of panel half-height

// ── Hash noise ────────────────────────────────────────────────────────────────
float hash(vec2 p) {
    p = fract(p * vec2(234.34, 435.345));
    p += dot(p, p + 34.23);
    return fract(p.x * p.y);
}

float noise(vec2 p) {
    vec2 i = floor(p);
    vec2 f = fract(p);
    vec2 u = f*f*(3.0 - 2.0*f);
    return mix(
        mix(hash(i),           hash(i+vec2(1,0)), u.x),
        mix(hash(i+vec2(0,1)), hash(i+vec2(1,1)), u.x), u.y);
}

// ── Fractal Brownian Motion — 6 octaves of plasma turbulence ─────────────────
float fbm(vec2 p, float t) {
    float v = 0.0, a = 0.5;
    mat2  rot = mat2(cos(0.5), sin(0.5), -sin(0.5), cos(0.5));
    for (int i = 0; i < 6; i++) {
        v += a * noise(p + t * (0.07 * float(i+1)));
        p  = rot * p * 2.1;
        a *= 0.52;
    }
    return v;
}

// ── Kelvin-Helmholtz vorticity ────────────────────────────────────────────────
// 13 shear seeds with wavenumbers from Riemann zeros.
// Each vortex grows as exp(σₙ·t), rolls up, then merges at the teal flash.
float kh_vorticity(vec2 uv, float t) {
    float delta  = 0.07;                   // shear layer thickness
    float omega  = 0.0;
    float growth = min(1.0, t * 0.04);     // global ramp-up

    for (int n = 0; n < 13; n++) {
        float gv     = u_gamma[n];
        float k_n    = gv * 0.12;          // wavenumber ∝ Riemann zero
        float sig_n  = 0.5 * k_n * max(0.0, 1.0 - k_n * delta);
        float A_n    = exp(-float(n) * 0.25) * growth;

        // KH perturbation: rolls up with time
        float rollup = min(1.0, sig_n * t * 0.4);
        float theta  = k_n * uv.x + rollup * atan(uv.y, uv.x + 0.01);
        float decay  = exp(-k_n * abs(uv.y) * (1.0 + rollup * 2.0));

        omega += A_n * cos(theta) * decay;
    }

    // Vortices merge at teal flash (t≈47): single large vortex
    float t_merge  = 47.0;
    float merge_p  = smoothstep(t_merge - 4.0, t_merge + 2.0, t);
    float r        = length(uv);
    float big_vortex = merge_p * exp(-r * r * 12.0)
                     * cos(atan(uv.y, uv.x) * 3.0 - t * 2.0);

    // Vorticity decays to zero as Phase 2 stabilises
    float decay_ph2 = 1.0 - u_phase;
    return (omega + big_vortex * 3.0) * decay_ph2;
}

// ── Planck blackbody colour ───────────────────────────────────────────────────
// Mitchell Charity / Krystek-Anthony approximation.
// T in Kelvin.  Returns linear RGB (tone-mapped later).
vec3 kelvin_rgb(float T) {
    T = clamp(T, 1000.0, 40000.0);
    float t100 = T / 100.0;
    float r, g, b;

    // Red
    r = (T <= 6600.0) ? 1.0
        : clamp(pow(t100 - 60.0, -0.1332) * 1.2929, 0.0, 1.0);

    // Green
    g = (T <= 6600.0)
        ? clamp((log(t100) * 0.3902 - 0.6324), 0.0, 1.0)
        : clamp(pow(t100 - 60.0, -0.0755) * 1.1299, 0.0, 1.0);

    // Blue
    b = (T >= 6600.0) ? 1.0
      : (T <= 1900.0) ? 0.0
      : clamp((log(t100 - 10.0) * 0.5432 - 1.1963), 0.0, 1.0);

    return vec3(r, g, b);
}

// ── Temperature field ─────────────────────────────────────────────────────────
// Starts white-blue (QGP ~20000 K), drops through recombination (~3000 K),
// then dims to black (CMB, below visible).
// Log-scaled to make the transition visually meaningful.
float plasma_temperature(vec2 uv, float t) {
    // Base temperature: log-linear drop over 90 seconds
    // Phase 1: 20000 K → 8000 K  (QGP cooling)
    // Phase 2:  8000 K → 2800 K  (recombination)
    float T_hot  = 20000.0;
    float T_rec  = 2800.0;   // hydrogen recombination temperature
    float T_base = mix(T_hot, T_rec, smoothstep(0.0, 1.0,
                       log(1.0 + t / T_TOTAL * (exp(1.0)-1.0))));

    // Turbulence modulates local temperature: hot vortex cores, cool shear lanes
    float turb   = fbm(uv * 4.0, t * 0.15);
    float T_turb = T_base * (0.75 + 0.5 * turb);

    // Vorticity adds extra heat to vortex cores (compression heating)
    float omega  = kh_vorticity(uv, t);
    float T_vort = T_turb * (1.0 + abs(omega) * 0.6);

    // In Phase 2: temperature at centre drops faster (recombination releases photons)
    float r      = length(uv);
    float T_ph2  = T_vort * (1.0 - u_phase * 0.6 * exp(-r * r * 4.0));

    // Sub-visible fade after t=80s (zero-point)
    float fade   = smoothstep(80.0, 84.0, t);
    return T_ph2 * (1.0 - fade);
}

// ── ZD crossing flashes ───────────────────────────────────────────────────────
// Each Riemann zero event → brief temperature spike (vortex nucleation).
float zd_flash(vec2 uv, float t) {
    float total = 0.0;
    float r = length(uv);
    for (int i = 0; i < 13; i++) {
        float dt     = t - u_tevents[i];
        float pulse  = (dt >= 0.0) ? exp(-dt*dt*8.0) : exp(-dt*dt*2.0);
        float px     = 0.15 * sin(u_gamma[i]);
        float py     = 0.15 * cos(u_gamma[i] * 1.3);
        float d      = length(uv - vec2(px, py));
        total       += pulse * exp(-d * d * 20.0) * 8000.0;  // K spike
    }
    return total * (1.0 - u_phase);
}

// ── MEXICAN HAT POTENTIAL  V(r) = -r^2 + 0.5*r^4  (normalised) ───────────────
// Minimum at r = 1 (the brim / VEV = D_STAR in physical units).
// In SM: this IS the Higgs potential.  In Ainulindale: brim = d* = 0.2460 = sigma=half.
// 246 GeV VEV; note d* = 0.246 (D15 result: 246 = 1000 * d*).
float mexican_hat_V(float r_norm) {
    float r2 = r_norm * r_norm;
    return -r2 + 0.5 * r2 * r2;    // min = -0.5 at r_norm=1
}
float hat_glow(float r, float r_brim) {
    float r_n = r / (r_brim + 0.001);
    float V   = mexican_hat_V(r_n);
    return clamp(1.0 - (V + 0.5) * 2.0, 0.0, 1.0);  // 1 at brim, 0 at centre
}

// ── SPECTROGRAM STRIP  (local uv_s.x,y in [0,1]) ─────────────────────────────
vec3 spectrogram(vec2 uv_s, float t) {
    int   bin  = clamp(int(floor(uv_s.x * 13.0)), 0, 12);
    float gv   = u_gamma[bin];
    float dt   = t - u_tevents[bin];
    float amp1 = exp(-float(bin)*0.25)
               * smoothstep(-3.0, 0.0, dt)
               * exp(-max(0.0, dt-10.0)*0.15)
               * (1.0 - u_phase);
    float amp2 = (bin == 0) ? u_phase * smoothstep(0.0, 8.0, t - T_PHASE1) : 0.0;
    float amp  = amp1 + amp2;
    float lit  = step(uv_s.y, amp * 0.92);
    float T_f  = 2000.0 + gv * 600.0;
    vec3  col  = kelvin_rgb(T_f) * lit;
    float bedge = fract(uv_s.x * 13.0);
    col *= smoothstep(0.0, 0.03, bedge) * smoothstep(1.0, 0.97, bedge);
    col += vec3(0.03, 0.02, 0.05) * (1.0 - lit);
    return col;
}

// ── PHASE 2 ATOM: double cardioid + Mexican hat + action cone + L_dynamic ─────
//
// Portrait orientation (atom fills screen vertically):
//   J_blue (electron): r = a_je*(1 + sin th)  cusp DOWN, loop UP  = CD / future
//   J_red  (proton):   r = a_jr*(1 - sin th)  cusp UP,  loop DOWN = ZD / past
//   Both cusps at origin = barycenter = ZD crossing = quantum tunnel
//
// Mexican hat brim = L_dynamic orbit at r = D_STAR * atom_scale
// Action cone ring: half-angle arctan(D_STAR) = 13.82 deg visible at brim
// Precession: axis rotates at omega_prec = PI/6 rad/s (12-second period, measured)
//
// Standard Model mapping:
//   Phase 1: field at r=0 (unbroken symmetry, massless QGP)
//   Phase transition: SSB, field rolls to brim (mass generation = confinement)
//   Phase 2: field at brim (broken symmetry, massive proton + bound electron)
//   d* = 0.246 = VEV in natural units (SM: 246 GeV = 1000 * d* [D15])
//
vec3 phase2_atom(vec2 uv_sq, float t, float a_je) {
    float a_jr      = a_je / 15.0;                    // proton wobble (visual scale)
    float r_brim    = D_STAR * (a_je / (D_STAR * 1.6));  // Mexican hat brim in uv_sq

    // Precessing frame: omega_prec = PI/6 rad/s
    float prec  = (PI / 6.0) * (t - T_PHASE1) * u_phase;
    float cp    = cos(prec), sp = sin(prec);
    vec2  uv_p  = vec2(cp*uv_sq.x + sp*uv_sq.y, -sp*uv_sq.x + cp*uv_sq.y);
    float r     = length(uv_p);
    float th    = atan(uv_p.y, uv_p.x);

    // J_blue: electron orbital, loop UP (CD / future)
    float r_je  = a_je * (1.0 + sin(th));
    float d_je  = abs(r - r_je);
    float j_blu = exp(-d_je*d_je / (0.012*0.012));

    // J_red: proton wobble, loop DOWN (ZD / past)
    float r_jr  = a_jr * (1.0 - sin(th));
    float d_jr  = abs(r - r_jr);
    float j_red = exp(-d_jr*d_jr / (0.005*0.005));

    // Barycenter dot: ZD crossing = both cusps = quantum tunnel
    float bary  = exp(-r*r / (0.007*0.007)) * 15.0;

    // L_dynamic: massless Goldstone orbit on the Mexican hat brim
    // This IS the 27 Hz hum — orbital resonance of the ground state
    float l_dyn = exp(-pow(r - r_brim, 2.0) / (0.010*0.010));

    // Action cone ring: half-angle = arctan(D_STAR) = 13.82 deg
    // Visible as angular highlight at the brim
    float cone_a  = atan(D_STAR);    // 0.2411 rad = 13.82 deg
    float th_v    = abs(th) - PI/2.0;   // deviation from vertical axis
    float cone_glow = l_dyn * smoothstep(cone_a + 0.08, cone_a - 0.02, abs(th_v));

    // Mexican hat background: bright ring at brim, dim at centre and outside
    float hat    = hat_glow(r, r_brim);

    // Coulomb / L_(I|O) axis: vertical glow connecting J_red and J_blue
    float ax_x   = abs(uv_p.x);
    float ax_y   = uv_p.y;
    float ax_m   = exp(-ax_x*ax_x / (0.018*0.018))
                 * clamp((ax_y + a_jr) / (a_je + a_jr), 0.0, 1.0)
                 * 0.35;
    float ax_t   = clamp((ax_y + a_je) / (a_je + a_jr), 0.0, 1.0);  // 0=blue top, 1=gold bottom

    vec3 c_gold  = vec3(0.92, 0.78, 0.22);
    vec3 c_blue  = vec3(0.18, 0.65, 1.00);
    vec3 c_purp  = vec3(0.55, 0.12, 0.90);
    vec3 c_teal  = vec3(0.15, 1.00, 0.82);
    vec3 c_white = vec3(1.00, 0.95, 0.90);

    vec3 col = c_blue  * j_blu   * 4.0
             + c_gold  * j_red   * 8.0
             + c_white * bary
             + c_teal  * l_dyn   * 2.5        // L_dynamic brim orbit
             + c_gold  * cone_glow * 2.0      // action cone at arctan(d*)
             + c_purp  * hat     * 0.5        // Mexican hat background
             + mix(c_blue, c_gold, ax_t) * ax_m;

    float fade_in = u_phase * smoothstep(0.05, 0.45, u_phase);
    return col * fade_in;
}

// ─────────────────────────────────────────────────────────────────────────────
void main() {
    vec2  uv_screen = gl_FragCoord.xy / u_res;   // [0,1]^2, y=0 at bottom
    float t         = u_t;

    // SPECTROGRAM: bottom SPEC_H of canvas
    if (uv_screen.y < SPEC_H) {
        vec2 spec_uv = vec2(uv_screen.x, uv_screen.y / SPEC_H);
        gl_FragColor = vec4(spectrogram(spec_uv, t), 1.0);
        return;
    }

    // MAIN PANEL: square UV where 1.0 = half of screen WIDTH
    // panel_norm in [0,1] covers the non-spectrogram area
    float panel_norm = (uv_screen.y - SPEC_H) / (1.0 - SPEC_H);
    // pnl_asp = W / H_panel  (portrait: ~0.507 for 720x1612 with SPEC_H=0.12)
    float pnl_asp = u_res.x / (u_res.y * (1.0 - SPEC_H));

    // Square coords: 1.0 unit = half screen width (circles look round)
    vec2 uv_sq = vec2(
        (uv_screen.x - 0.5) * 2.0,            // x: [-1,  1]
        (panel_norm  - 0.5) * 2.0 / pnl_asp   // y: [-1/pnl_asp, 1/pnl_asp]
    );

    // AUTO-SCALED atom: electron cardioid fills FILL_PCT of panel half-height
    // Panel half-height in uv_sq = 1.0/pnl_asp
    // Electron loop max = 2*a_je  -->  2*a_je = FILL_PCT / pnl_asp
    float a_je = FILL_PCT / (2.0 * pnl_asp);    // e.g. 0.82/(2*0.507) ~ 0.809

    float r_sq = length(uv_sq);

    // PHASE 1: Planck colour from temperature field + KH shear geometry
    float T_loc = plasma_temperature(uv_sq, t) + zd_flash(uv_sq, t);
    vec3  col   = kelvin_rgb(T_loc);

    float omega  = kh_vorticity(uv_sq, t);
    col         *= 0.70 + 0.60 * abs(omega);
    col         += vec3(0.15, 0.05, 0.30) * max(0.0, -omega) * 0.4;
    col         += vec3(0.05, 0.20, 0.40) * max(0.0,  omega) * 0.3;
    float fine   = fbm(uv_sq * 4.5 + vec2(t*0.03, 0.0), t * 0.2);
    col         *= 0.80 + 0.40 * fine;

    // PHASE 2: double cardioid + Mexican hat + action cone + L_dynamic
    col += phase2_atom(uv_sq, t, a_je);

    // BAO ring: frozen memory of L_dynamic on the brim
    float atom_scale = a_je / (D_STAR * 1.6);
    float r_bao = D_STAR * atom_scale * (1.5 + 0.3 * u_phase);
    float bao_v = exp(-pow(r_sq - r_bao, 2.0) / (0.015*0.015)) * u_phase;
    col        += vec3(0.92, 0.78, 0.22) * bao_v * 3.0;

    // Vignette (pixel-round: undo aspect in vignette radius)
    float vig_r = length(vec2(uv_sq.x, uv_sq.y * pnl_asp));
    col        *= 1.0 - smoothstep(0.62, 1.10, vig_r);

    // Filmic tone map (Reinhard) + gamma 2.2
    col = col / (col + 1.0);
    col = pow(max(col, vec3(0.0)), vec3(1.0 / 2.2));

    gl_FragColor = vec4(col, 1.0);
}
"""

# MESA GLSL rejects non-ASCII even in comments — strip before compile
FRAG_CLEAN = ''.join(c if ord(c) < 128 else ' ' for c in FRAG)

# ── Canvas ─────────────────────────────────────────────────────────────────────
class PlasmaCanvas(app.Canvas):
    def __init__(self, **kwargs):
        super().__init__(title='QGP Spectral — Ainulindale',
                         size=(W, H), keys='interactive', **kwargs)
        gloo.set_viewport(0, 0, W, H)
        gloo.set_state(clear_color='black', blend=False)

        self._prog = gloo.Program(VERT, FRAG_CLEAN)
        self._prog['a_pos']      = QUAD
        self._prog['u_res']      = [float(W), float(H)]
        self._prog['u_t']        = 0.0
        self._prog['u_phase']    = 0.0
        self._prog['u_gamma']    = GAMMA.reshape(13, 1)
        self._prog['u_tevents']  = T_EVENTS.reshape(13, 1)

        self._t     = 0.0
        self._dt    = 1.0 / FPS
        self._timer = app.Timer(interval=self._dt, connect=self.on_timer, start=True)
        self.show()

    @staticmethod
    def _phase(t):
        if t < T_PHASE1:
            return 0.0
        return float(1.0 - np.exp(-(t - T_PHASE1) / 6.0))

    def on_timer(self, event):
        self._t = (self._t + self._dt) % T_TOTAL
        self._prog['u_t']    = self._t
        self._prog['u_phase'] = self._phase(self._t)
        self.update()

    def on_draw(self, event):
        gloo.clear()
        self._prog.draw('triangles')

    def on_key_press(self, event):
        if event.key == 'Escape': self.app.quit()
        elif event.key == 'Space':
            if self._timer.running: self._timer.stop()
            else: self._timer.start()
        elif event.key == 'R':
            self._t = 0.0


# ── GPU video render ───────────────────────────────────────────────────────────
def render_video():
    import soundfile as sf
    from scipy.signal import butter, sosfilt

    out_file = os.path.join(os.path.dirname(__file__), '..', 'plasma_spectral.mp4')
    wav_file = os.path.join(os.path.dirname(__file__), '..', 'recombination_audio.wav')
    out_file = os.path.normpath(out_file)

    print('QGP Spectral — GPU Video Render')
    print(f'  Canvas:   {W}×{H}  (native, no upscale)')
    print(f'  Duration: {T_TOTAL:.0f}s  @{FPS}fps  ({N_FRAMES} frames)')
    print(f'  Renderer: VisPy GLSL / GPU')

    # Reuse audio from previous render if present, else synthesise
    if not os.path.exists(wav_file):
        print('[1/3] Synthesising audio...')
        SR = 44100
        t_a = np.linspace(0, T_TOTAL, int(SR * T_TOTAL), endpoint=False)
        audio = np.zeros(len(t_a))
        ph1 = (t_a < T_PHASE1).astype(float)
        for i, (gv, tev) in enumerate(zip(GAMMA, T_EVENTS)):
            fg = gv * (27.0 / GAMMA[0])
            audio += 0.35 * np.exp(-i*0.12) * np.sin(2*np.pi*fg*t_a) * ph1
            dt = t_a - tev
            pulse = np.where(dt>=0, np.exp(-dt**2*8), np.exp(-dt**2*2))
            audio += pulse * np.sin(2*np.pi*27.0*(t_a-tev)) * 0.8
        ph2 = np.maximum(0, np.minimum(1, (t_a - T_PHASE1) / 8.0))
        for f, a in [(27,.5),(55,.25),(109,.12),(139,.08)]:
            audio += a * np.sin(2*np.pi*f*t_a) * ph2
        audio *= np.minimum(1, np.maximum(0, (80-t_a)/4))
        audio = audio / (np.abs(audio).max()+1e-8) * 0.85
        sf.write(wav_file, audio.astype(np.float32), SR)
        print(f'      Written: {wav_file}')
    else:
        print(f'[1/3] Reusing audio: {wav_file}')

    print('[2/3] Starting ffmpeg pipeline...')
    cmd = [
        'ffmpeg', '-y',
        '-f', 'rawvideo', '-vcodec', 'rawvideo',
        '-s', f'{W}x{H}', '-pix_fmt', 'rgb24', '-r', str(FPS),
        '-i', 'pipe:0',
        '-i', wav_file,
        '-c:v', 'libx264', '-preset', 'fast', '-crf', '18',
        '-pix_fmt', 'yuv420p',
        '-c:a', 'aac', '-b:a', '192k',
        '-movflags', '+faststart',
        out_file,
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE,
                            stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)

    print('[3/3] Rendering frames on GPU...')
    canvas = PlasmaCanvas()
    canvas._timer.stop()

    ts = np.linspace(0, T_TOTAL, N_FRAMES, endpoint=False)
    report = max(1, N_FRAMES // 20)
    import time
    t0 = time.time()

    for i, t_val in enumerate(ts):
        ph = canvas._phase(float(t_val))
        canvas._prog['u_t']    = float(t_val)
        canvas._prog['u_phase'] = ph
        # Force viewport to W×H before every readback.
        # process_events() lets the window manager resize the window on tall canvases;
        # we skip it here and restore the viewport explicitly so canvas.render() always
        # returns the correct (H, W, 3) array.
        gloo.set_viewport(0, 0, W, H)
        frame = canvas.render(alpha=False)              # (H, W, 3) uint8 — GPU readback
        if frame.shape[0] != H or frame.shape[1] != W:
            import PIL.Image
            import io
            img = PIL.Image.fromarray(frame).resize((W, H), PIL.Image.LANCZOS)
            frame = np.array(img)
        proc.stdin.write(frame.tobytes())

        if (i+1) % report == 0 or i == N_FRAMES-1:
            elapsed = time.time() - t0
            fps_actual = (i+1) / elapsed
            eta = (N_FRAMES - i - 1) / fps_actual
            print(f'  Frame {i+1:4d}/{N_FRAMES}  t={t_val:5.1f}s  '
                  f'phase={ph:.3f}  {fps_actual:.1f}fps  ETA {eta:.0f}s')
            sys.stdout.flush()

    proc.stdin.close()
    proc.wait()
    if proc.returncode != 0:
        print('FFmpeg error:', proc.stderr.read().decode())
        sys.exit(1)

    elapsed = time.time() - t0
    size_mb = os.path.getsize(out_file) / 1e6
    print(f'\nDone.  {out_file}  ({size_mb:.1f} MB)')
    print(f'GPU render time: {elapsed:.1f}s  ({N_FRAMES/elapsed:.1f} fps)')
    print(f'CPU numpy time was ~283s — speedup: {283/elapsed:.1f}×')


# ── Entry point ────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    if '--render' in sys.argv:
        render_video()
    else:
        canvas = PlasmaCanvas()
        app.run()
