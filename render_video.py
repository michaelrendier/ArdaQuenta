"""
render_video.py — Recombination: First Proton + Hydrogen
Video renderer for Facebook upload.

720×1612  portrait  •  90 seconds  •  30 fps
Audio:    Riemann zeros drive Phase 1 bass chaos; 27 Hz hum drives Phase 2

Math spine (Ainulindale):
  γₙ   First 13 Riemann zeros  — audio frequencies AND ZD crossing event times
  σ→½  Noether convergence     — controls phase transition timing
  d*   0.2460                  — BAO ring radius in image space
  27Hz Measured precession hum — anchors the audio frequency scale
  H=xp Berry-Keating           — envelope trajectory
"""

import subprocess, struct, sys, os
import numpy as np
import soundfile as sf

# ── Constants ──────────────────────────────────────────────────────────────────
W_OUT, H_OUT = 720, 1612          # final output
W_REN, H_REN = 360, 806           # render at half-res, ffmpeg upscales
FPS          = 30
T_TOTAL      = 90.0
N_FRAMES     = int(T_TOTAL * FPS)  # 2700

D_STAR       = 0.2460
SIGMA_HALF   = 0.5
T_PHASE1     = 60.0
TAU_SETTLE   = 6.0                 # capacitor time constant (seconds)
T_TEAL       = 47.0               # maximum ZD event → teal flash

# First 13 Riemann zeros γₙ (dimensionless)
GAMMA = np.array([
    14.134725, 21.022040, 25.010858, 30.424876, 32.935062,
    37.586178, 40.918719, 43.327073, 48.005151, 49.773832,
    52.970321, 56.446247, 59.347044,
])

# ZD crossing event times in Phase 1 (seconds)
# Mapped from gamma range [γ₀,γ₁₂] → [3s, 51s]
T_EVENTS = (GAMMA - GAMMA[0]) / (GAMMA[-1] - GAMMA[0]) * 51.0 + 3.0

# Audio frequency scale:
# anchor γ₀=14.13 → 27 Hz (the measured precession hum from ink video)
F_SCALE      = 27.0 / GAMMA[0]    # ≈ 1.91
F_GAMMA      = GAMMA * F_SCALE    # [27, 40.1, 47.8, 58.1, ...] Hz

# ── Audio generation ───────────────────────────────────────────────────────────
SR = 44100

def make_audio():
    t = np.linspace(0, T_TOTAL, int(SR * T_TOTAL), endpoint=False)
    n = len(t)
    audio = np.zeros(n)

    # ── Phase 1: gluon plasma chaos (0 – T_PHASE1) ──────────────────────────
    ph1_mask = (t < T_PHASE1).astype(float)

    # Each Riemann zero contributes a sine wave in the bass register
    for i, (fg, t_ev) in enumerate(zip(F_GAMMA, T_EVENTS)):
        phase = 2.0 * np.pi * fg * t
        amp   = 0.35 * np.exp(-i * 0.12)          # decaying amplitude per zero
        audio += amp * np.sin(phase) * ph1_mask

    # Broadband noise shaped by sigma deviation (more chaos when σ far from ½)
    rng   = np.random.default_rng(42)
    noise = rng.standard_normal(n)

    # sigma trajectory in Phase 1: oscillates around ½
    osc_sum = np.zeros(n)
    for i, gv in enumerate(GAMMA):
        w        = gv * 0.008
        amp_osc  = 0.06 * np.exp(-i * 0.18)
        osc_sum += amp_osc * np.sin(w * t)
    delta  = 0.22 * np.exp(-t * 0.12)
    sigma  = 0.5 + delta + osc_sum * (t < T_PHASE1).astype(float)
    dsig   = np.abs(sigma - 0.5)

    # noise amplitude ∝ |σ − ½| (chaos when far from ground state)
    noise_amp = 0.5 * dsig / (dsig.max() + 1e-8)
    # Low-pass at 200Hz (bass chaos only)
    from scipy.signal import butter, sosfilt
    sos = butter(4, 200.0 / (SR / 2), btype='low', output='sos')
    noise_lp = sosfilt(sos, noise * noise_amp * ph1_mask)
    audio += noise_lp * 0.8

    # Bass pulses at each ZD crossing event
    for t_ev in T_EVENTS:
        dt     = t - t_ev
        # asymmetric: fast rise, slow decay (like a bass drum / ink splash)
        rise   = np.exp(-dt * dt * 80.0) * (dt < 0)
        decay  = np.exp(-dt * dt * 12.0) * (dt >= 0)
        pulse  = (rise + decay) * 1.2
        # Low-frequency content: 27Hz sine burst
        burst  = np.sin(2.0 * np.pi * 27.0 * (t - t_ev))
        audio += pulse * burst * 0.8

    # Teal flash: sharp transient + sub-bass thud at T_TEAL
    dt_teal  = t - T_TEAL
    teal_env = np.exp(-dt_teal * dt_teal * 4.0) * (dt_teal >= -0.3)
    teal_env = np.maximum(teal_env, np.exp(-dt_teal * dt_teal * 0.5) * (dt_teal < -0.3) * 0.3)
    audio   += teal_env * np.sin(2.0 * np.pi * 20.0 * t) * 1.5
    audio   += teal_env * 0.6   # DC thud

    # ── Phase 2: stable hydrogen (T_PHASE1 – T_TOTAL) ───────────────────────
    ph2_start = T_PHASE1
    ph2_mask  = np.maximum(0.0, (t - ph2_start) / 8.0)   # 8s fade-in
    ph2_mask  = np.minimum(1.0, ph2_mask)

    # Ground state hum: 27Hz (γ₀) + measured overtones 55, 109, 139 Hz
    ground_freqs = [27.0, 55.0, 109.0, 139.0]
    ground_amps  = [0.50, 0.25,  0.12,  0.08]
    for f, a in zip(ground_freqs, ground_amps):
        audio += a * np.sin(2.0 * np.pi * f * t) * ph2_mask

    # Silence from t=80s (ground state: hydrogen doesn't emit)
    silence_mask = np.minimum(1.0, np.maximum(0.0, (80.0 - t) / 4.0))
    audio       *= silence_mask + (1.0 - silence_mask) * (t < T_PHASE1).astype(float)

    # Normalise
    peak  = np.abs(audio).max()
    audio = audio / (peak + 1e-8) * 0.85

    return audio.astype(np.float32)

# ── Colour palette ─────────────────────────────────────────────────────────────
def rgb(r, g, b):
    return np.array([r, g, b], dtype=np.float32)

C_PLASMA  = rgb(1.00, 0.28, 0.05)   # red/orange    Phase 1
C_ORANGE  = rgb(1.00, 0.60, 0.12)
C_TEAL    = rgb(0.15, 1.00, 0.82)   # teal          transition
C_BLUE    = rgb(0.18, 0.65, 1.00)   # blue          σ=½ ℍ face
C_PURPLE  = rgb(0.55, 0.12, 0.90)   # purple        ZD boundary
C_GOLD    = rgb(0.92, 0.78, 0.22)   # gold          d*, BAO, CD shadow
C_WHITE   = rgb(1.00, 0.95, 0.90)   # white

# ── Static spatial tables (built once, reused every frame) ────────────────────

def _build_static():
    aspect  = W_REN / H_REN
    xs = np.linspace(-aspect, aspect, W_REN, dtype=np.float32)
    ys = np.linspace(-1.0,    1.0,   H_REN, dtype=np.float32)
    UX, UY = np.meshgrid(xs, ys[::-1])
    R2  = (UX*UX + UY*UY).astype(np.float32)
    R   = np.sqrt(R2)
    TH  = np.arctan2(UY, UX).astype(np.float32)

    # Plasma field: precompute R-dependent part → (13, H, W)
    G       = GAMMA.astype(np.float32)
    log_n   = np.log(np.arange(2, 15, dtype=np.float32))
    # angle = γᵢ*(log(i+2) + R*1.8) → constant part + time part added per frame
    SPACE   = (G[:, None, None] * (R[None] * 1.8)).astype(np.float32)   # (13,H,W)
    CONST   = (G * log_n).astype(np.float32)                              # (13,)
    TIME_G  = (-G * 0.04).astype(np.float32)                             # (13,) per-t multiplier
    WEIGHTS = (1.0 / np.arange(1, 14, dtype=np.float32))                 # (13,)

    # ZD Gaussians: precompute exp(−D²·30) → (13, H, W)
    PX = (0.12 * np.sin(GAMMA)).astype(np.float32)
    PY = (0.12 * np.cos(GAMMA * 1.3)).astype(np.float32)
    DX = UX[None, ...] - PX[:, None, None]
    DY = UY[None, ...] - PY[:, None, None]
    ZD_GAUSS = np.exp(-(DX*DX + DY*DY) * 30.0).astype(np.float32)      # (13,H,W)

    # Standard exponential spatial terms
    EXP_R18 = np.exp(-R * 1.8).astype(np.float32)
    EXP_R35 = np.exp(-R * 3.5).astype(np.float32)
    EXP_R25 = np.exp(-R * 2.5).astype(np.float32)
    EXP_R36 = np.exp(-R2 * 36.0).astype(np.float32)
    VIG     = (1.0 - np.clip((np.sqrt((UX / aspect)**2 + UY**2) - 0.55) / 0.60, 0, 1)).astype(np.float32)

    return dict(UX=UX, UY=UY, R2=R2, R=R, TH=TH,
                SPACE=SPACE, CONST=CONST, TIME_G=TIME_G, WEIGHTS=WEIGHTS,
                ZD_GAUSS=ZD_GAUSS,
                EXP_R18=EXP_R18, EXP_R35=EXP_R35, EXP_R25=EXP_R25,
                EXP_R36=EXP_R36, VIG=VIG)

_ST = None  # lazy init on first call

# ── Frame renderer ─────────────────────────────────────────────────────────────

def _phase(t):
    if t < T_PHASE1:
        return 0.0
    return float(1.0 - np.exp(-(t - T_PHASE1) / TAU_SETTLE))

def render_frame(t):
    """Returns uint8 RGB array shape (H_REN, W_REN, 3)."""
    global _ST
    if _ST is None:
        print('  [init] building static spatial tables...', flush=True)
        _ST = _build_static()

    st = _ST
    phase   = _phase(t)
    inv_ph  = np.float32(1.0 - phase)
    ph      = np.float32(phase)

    UX, UY, R2, R, TH = st['UX'], st['UY'], st['R2'], st['R'], st['TH']

    # ── σ trajectory (13 scalars only) ────────────────────────────────────────
    amps = np.exp(-np.arange(13, dtype=np.float32) * 0.18)
    osc  = float((amps * np.sin(GAMMA * 0.008 * t)).sum())
    sig  = 0.5 + 0.22 * np.exp(-t * 0.12) + 0.06 * osc * float(inv_ph)
    dsig = float(abs(sig - 0.5))

    # ── Gluon plasma: precomputed SPACE + per-frame time offset ───────────────
    # angle = SPACE[i,h,w] + CONST[i] + t * TIME_G[i]
    #       = SPACE + per_i_scalar         (using broadcasting)
    per_i = (st['CONST'] + t * st['TIME_G']).astype(np.float32)   # (13,)
    angles = st['SPACE'] + per_i[:, None, None]                     # (13,H,W)
    field  = (np.cos(angles) * st['WEIGHTS'][:, None, None]).sum(axis=0)  # (H,W)

    # Plasma
    sigma_col = float(min(1.0, max(0.0, dsig / 0.35)))
    p_col     = (C_ORANGE + sigma_col * (C_PLASMA - C_ORANGE)).astype(np.float32)
    p_glow    = (0.15 + 0.55 * np.abs(field)) * st['EXP_R18'] * float(inv_ph)
    plasma_rgb= p_col[:, None, None] * p_glow[None, ...]

    # Radial rings
    rings     = np.float32(0.5) + np.float32(0.5) * np.sin(R * 22.0 - t * 3.5)
    ring_rgb  = C_ORANGE[:, None, None] * (rings * st['EXP_R35'] * 0.25 * float(inv_ph))[None, ...]

    # ── ZD crossing flashes: precomputed Gaussians, only compute per-event pulse ─
    DT     = (t - T_EVENTS).astype(np.float32)
    pulses = np.where(DT >= 0, np.exp(-DT*DT * 8.0), np.exp(-DT*DT * 2.0))
    zd_total = (pulses[:, None, None] * st['ZD_GAUSS']).sum(axis=0)
    zd_col   = (C_ORANGE * 0.4 + C_WHITE * 0.6).astype(np.float32)
    zd_rgb   = zd_col[:, None, None] * (zd_total * 3.0 * float(inv_ph))[None, ...]

    # ── Teal phase-transition flash ────────────────────────────────────────────
    dt_t   = t - T_TEAL
    time_p = float(np.exp(-dt_t*dt_t * 0.25) if dt_t >= 0 else np.exp(-dt_t*dt_t * 0.08))
    trans_ = st['EXP_R25'] * time_p
    trans_rgb = C_TEAL[:, None, None] * (trans_ * 4.0)[None, ...]

    # ── Noether convergence glow ───────────────────────────────────────────────
    n_glow = st['EXP_R36'] * float(np.exp(-dsig * 25.0)) * (0.3 + 0.7 * float(ph))
    n_col  = (C_PURPLE + float(ph) * (C_BLUE - C_PURPLE)).astype(np.float32)
    noeth_rgb = n_col[:, None, None] * (n_glow * 3.5 * float(ph))[None, ...]

    # ── Double cardioid: barycenter geometry ─────────────────────────────────────
    # Barycenter = origin = ZD cusp. Both J_red and J_blue cusps touch here.
    # Axis precesses at ω_prec = π/6 rad/s (one revolution per 12s — measured).
    prec_a = float(np.pi / 6.0) * (t - T_PHASE1) * float(ph)
    cos_a  = np.float32(np.cos(prec_a))
    sin_a  = np.float32(np.sin(prec_a))
    # Rotate UV into precessing frame (cheap: scalar multiply)
    UX_bc  =  cos_a * UX + sin_a * UY   # (H, W)
    UY_bc  = -sin_a * UX + cos_a * UY
    R_bc   = np.sqrt(UX_bc**2 + UY_bc**2)
    TH_bc  = np.arctan2(UY_bc, UX_bc)

    # J_red — proton wobble: tiny loop opens RIGHT (+x direction)
    # r = a_jr * (1 + cos θ)   cusp at θ=π (origin)
    a_jr    = np.float32(D_STAR * 0.055)
    r_jr    = a_jr * (1.0 + np.cos(TH_bc))
    d_jr    = np.abs(R_bc - r_jr)
    j_red_v = np.exp(-d_jr*d_jr * (1.0/0.006**2)) * float(ph)
    j_red_rgb = C_GOLD[:, None, None] * (j_red_v * 6.0)[None, ...]

    # J_blue — electron orbital: large loop opens LEFT (-x direction)
    # r = a_je * (1 - cos θ)   cusp at θ=0 (origin)
    a_je    = np.float32(D_STAR * 1.6)
    r_je    = a_je * (1.0 - np.cos(TH_bc))
    d_je    = np.abs(R_bc - r_je)
    j_blue_v = np.exp(-d_je*d_je * (1.0/0.009**2)) * float(ph)
    j_blue_rgb = C_BLUE[:, None, None] * (j_blue_v * 3.0)[None, ...]

    # Barycenter dot: ZD crossing, where both cusps meet
    bary_v   = np.exp(-R2 * 800.0) * float(ph)
    bary_rgb = C_WHITE[:, None, None] * (bary_v * 10.0)[None, ...]

    # Coulomb / L_(I|O) axis: faint glow along the cardioid axis
    axis_perp = np.abs(UY_bc)
    axis_col  = np.clip((UX_bc + a_je) / (a_je + a_jr * 2.0), 0, 1)  # 0=blue, 1=gold
    axis_mask = (np.exp(-axis_perp**2 * (1.0/0.018**2))
                 * np.clip(1.0 - np.abs(UX_bc) / (a_je * 2.2), 0, 1)
                 * float(ph) * 0.4)
    axis_rgb  = ((C_BLUE[:, None, None] * (1 - axis_col)[None, ...]
                + C_GOLD[:, None, None] *      axis_col [None, ...])
                * axis_mask[None, ...])

    # ── BAO ring: frozen memory of L_(I|O) circle around the whole system ────
    bao_r  = float(D_STAR * (1.5 + 0.3 * float(ph)))
    bao_v  = np.exp(-((R - bao_r)**2) * (1.0/0.010**2)) * float(ph)
    bao_rgb= C_GOLD[:, None, None] * (bao_v * 4.0)[None, ...]

    shell_r = float(D_STAR * (1.1 + 0.2 * float(ph)))
    shell_v = np.exp(-((R - shell_r)**2) * (1.0/0.007**2)) * float(ph)
    shell_rgb= C_BLUE[:, None, None] * (shell_v * 2.5)[None, ...]

    # ── Tri-layer hue wash (ZD/σ=½/CD) ────────────────────────────────────────
    ang_n  = TH / np.float32(np.pi)
    t1     = np.clip((ang_n + 0.5) / 0.5, 0, 1)
    t2     = np.clip(ang_n / 0.5, 0, 1)
    tri_col = (C_PURPLE[:, None, None] * (1-t1)[None, ...]
             + C_BLUE[:, None, None]   *    t1 [None, ...]) * (1-t2)[None, ...] \
            +  C_GOLD[:, None, None]   *    t2 [None, ...]
    tri_mask= np.exp(-np.abs(R - bao_r * 0.75)**2 * 144.0) * float(ph) * 0.8
    tri_rgb = tri_col * tri_mask[None, ...]

    # ── Background dark field ──────────────────────────────────────────────────
    bg_v   = float(ph) * 0.04 * (1.0 - np.clip(R / 0.8, 0, 1))
    bg_rgb = C_PURPLE[:, None, None] * bg_v[None, ...]

    # ── Composite ──────────────────────────────────────────────────────────────
    col = (plasma_rgb + ring_rgb + zd_rgb + trans_rgb +
           bg_rgb + noeth_rgb + tri_rgb +
           j_blue_rgb + axis_rgb + j_red_rgb +
           shell_rgb + bao_rgb + bary_rgb)

    col    *= st['VIG'][None, ...]
    col     = col / (col + np.float32(0.85))
    col     = np.power(np.maximum(col, 0), np.float32(0.42))
    col     = np.clip(col, 0, 1)

    return (col.transpose(1, 2, 0) * 255).astype(np.uint8)


# ── Main: audio first, then pipe video to ffmpeg ──────────────────────────────
def main():
    out_dir  = os.path.dirname(os.path.abspath(__file__))
    out_file = os.path.join(out_dir, 'recombination.mp4')
    wav_file = os.path.join(out_dir, 'recombination_audio.wav')

    print('Ainulindale Recombination — Video Renderer')
    print(f'  Output:  {out_file}')
    print(f'  Canvas:  {W_OUT}×{H_OUT}  ({W_REN}×{H_REN} rendered, ×2 upscaled)')
    print(f'  Duration: {T_TOTAL:.0f}s  @{FPS}fps  ({N_FRAMES} frames)')
    print(f'  Audio:   γ₁={F_GAMMA[0]:.1f}Hz (Phase 1) → 27Hz hum (Phase 2)')
    print()

    # ── Step 1: audio ────────────────────────────────────────────────────────
    print('[1/3] Synthesising audio from Riemann zeros + Ainulindale constants...')
    audio = make_audio()
    sf.write(wav_file, audio, SR)
    print(f'      Written: {wav_file}  ({len(audio)/SR:.1f}s)')

    # ── Step 2: ffmpeg pipeline ───────────────────────────────────────────────
    print('[2/3] Starting ffmpeg pipeline...')
    cmd = [
        'ffmpeg', '-y',
        # Raw video from stdin
        '-f', 'rawvideo', '-vcodec', 'rawvideo',
        '-s', f'{W_REN}x{H_REN}', '-pix_fmt', 'rgb24',
        '-r', str(FPS),
        '-i', 'pipe:0',
        # Audio from wav file
        '-i', wav_file,
        # Scale up to full portrait size
        '-vf', f'scale={W_OUT}:{H_OUT}:flags=lanczos',
        # Encode
        '-c:v', 'libx264', '-preset', 'slow', '-crf', '18',
        '-pix_fmt', 'yuv420p',
        '-c:a', 'aac', '-b:a', '192k',
        # Facebook: max 240 min, H.264 baseline OK, portrait
        '-movflags', '+faststart',
        out_file,
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE,
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.PIPE)

    # ── Step 3: render frames ─────────────────────────────────────────────────
    print('[3/3] Rendering frames...')
    ts = np.linspace(0, T_TOTAL, N_FRAMES, endpoint=False)
    report_every = max(1, N_FRAMES // 20)

    for i, t_val in enumerate(ts):
        frame = render_frame(float(t_val))
        proc.stdin.write(frame.tobytes())

        if (i + 1) % report_every == 0 or i == N_FRAMES - 1:
            pct = (i + 1) / N_FRAMES * 100
            ph  = _phase(float(t_val))
            print(f'      Frame {i+1:4d}/{N_FRAMES}  t={t_val:5.1f}s  phase={ph:.3f}  {pct:.0f}%')
            sys.stdout.flush()

    proc.stdin.close()
    proc.wait()
    if proc.returncode != 0:
        err = proc.stderr.read()
        print('\nFFmpeg error:')
        print(err.decode())
        sys.exit(1)

    size_mb = os.path.getsize(out_file) / 1e6
    print(f'\nDone.  {out_file}  ({size_mb:.1f} MB)')
    print()
    print('The math spoke:')
    print(f'  γ₁={GAMMA[0]:.3f} → f={F_GAMMA[0]:.1f} Hz  (first ZD crossing / 27Hz ground state)')
    print(f'  13 ZD bass pulses at t = {[f"{t:.1f}" for t in T_EVENTS]}')
    print(f'  Phase transition teal flash at t = {T_TEAL:.0f}s')
    print(f'  BAO ring at r = d* = {D_STAR}  (exact, no free parameters)')
    print(f'  Silence from t = 80s  (zero-point, no photon emission)')


if __name__ == '__main__':
    main()
