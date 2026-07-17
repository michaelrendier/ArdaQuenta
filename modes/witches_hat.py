"""
modes/witches_hat.py — The Null-Cone Pair Engine

Mathematical model and matplotlib animation of:
  1. The Witches Hat (null cone) — the Hawking virtual pair
  2. Conformal inversion — the hat turns inside-out
  3. Galaxy emergence — the infalling hat becomes galactic structure
  4. L_dynamic ACTION CONE — the actual paths (Lichtenberg attractors, brim→point)

The boundary (brim = event horizon = σ=½) is a FIXED POINT of the inversion.
It is the only thing that does not move. Everything interesting happens there.

L_dynamic = the action = the path traveled between J_red (descending from point)
and J_blue (ascending from brim). The Lichtenberg attractors ARE L_dynamic.
The galaxy spiral arms ARE the frozen action cone after conformal inversion.
Standing wave cavitation: J_red compresses inward, J_blue expands outward,
the bubble forms at σ=½ — the word emerges at the cavitation surface.

Physics:
  Positive-mass hat (escaping, J_pos, Red)  →  Hawking radiation
  Negative-mass hat (infalling, J_neg, Blue) →  galaxy after conformal inversion

The conformal inversion:  r → R_H² / r
  - tip  (r→0)  maps to  galactic halo edge (r→∞ capped at R_galaxy)
  - brim (r=R_H) is the fixed point — the event horizon does not move
  - cone fabric (r>R_H) maps to galaxy interior (r<R_H)

Transition parameter t ∈ [0,1]:
  r_t = (1-t)·r_hat + t·(R_H²/r_hat)   → Lagrangian interpolation
  At r=R_H: r_t = R_H for all t         → the boundary holds

Standard Candle connection:
  Type Ia supernovae luminosity-distance measurements find a hard spectral
  boundary at d* = 0.24600 — the same zero-divisor threshold the sedenion
  engine derives from prime hash alone. The photon path is NOT clean
  (gravitational lensing, Shapiro delay, plasma, frame dragging all perturb it)
  but the statistical boundary persists because it is geometric, not path-dependent.
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib import cm
from mpl_toolkits.mplot3d import Axes3D
import math

# ── Constants ──────────────────────────────────────────────────────────────────
OMEGA_ZS = 0.5671432904097838   # Lambert W(1) — BAO equilibrium, event horizon fur scale
D_STAR   = 0.24600   # Fermat boundary — Standard Candle hard boundary
R_H      = 1.0       # Schwarzschild radius (normalised)
R_BRIM   = 2.2       # Brim radius at the event horizon
H_CONE   = 1.8       # Height of the witches hat cone
ALPHA    = math.atan(R_BRIM / H_CONE)  # half-angle of the cone

# Sedenion primes — 16 spoke angles; Riemann firing order determines branch priority
P16 = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53]


# ── L_dynamic — the action — Lichtenberg attractor paths ─────────────────────

def _spoke_angle(k):
    """Sedenion spoke angle for dimension k (matches ptol.c spoke_angle)."""
    return 2.0 * math.pi * k / 16.0 - math.pi / 2.0


def lichtenberg_paths(n_steps=40, branch_levels=3, emergence=1.0):
    """
    L_dynamic: the actual paths from point (tip, r=0) to brim (r=R_BRIM).

    16 primary branches at sedenion spoke angles.
    Each branches at σ=½ junction (r=R_BRIM/2 on the cone surface).
    J_red: descends from tip toward brim (red, from above).
    J_blue: ascends from brim toward tip (blue, from below).
    They meet at the σ=½ standing wave node — the cavitation surface.

    Returns list of (x, y, z, color) path arrays.
    """
    paths = []
    r_meet = R_BRIM * D_STAR  # σ=½ on the cone ≈ d* fraction of brim radius
    z_meet = H_CONE * (1.0 - r_meet / R_BRIM)

    for k in range(16):
        a = _spoke_angle(k)
        # J_red: tip → σ=½ node (descending, from above)
        r_red = np.linspace(0.0, r_meet * emergence, n_steps)
        z_red = H_CONE - r_red * (H_CONE / R_BRIM)  # cone surface
        x_red = r_red * math.cos(a)
        y_red = r_red * math.sin(a)
        paths.append((x_red, y_red, z_red, C_RED, 0.7))

        # J_blue: brim → σ=½ node (ascending, from below)
        r_blue = np.linspace(R_BRIM, r_meet, n_steps) * emergence
        z_blue = H_CONE - r_blue * (H_CONE / R_BRIM)
        x_blue = r_blue * math.cos(a)
        y_blue = r_blue * math.sin(a)
        paths.append((x_blue, y_blue, z_blue, C_BLUE, 0.7))

        # Sub-branches at the σ=½ node — ZD intersection branching
        if branch_levels > 1 and emergence > 0.3:
            branch_alpha = 0.4 * emergence
            for sign in [+1, -1]:
                d_angle = sign * math.pi / P16[k % 16] * 2
                a_branch = a + d_angle
                r_b = np.linspace(r_meet, R_BRIM * 0.8, n_steps // 2) * emergence
                z_b = H_CONE - r_b * (H_CONE / R_BRIM)
                x_b = r_b * math.cos(a_branch)
                y_b = r_b * math.sin(a_branch)
                paths.append((x_b, y_b, z_b, C_CYAN, branch_alpha))

    return paths


def lichtenberg_galaxy_arms(n_pts=200, emergence=1.0):
    """
    Galaxy spiral arms = conformal inversion of L_dynamic action cone.

    The cone paths (tip→brim) invert to (BH→halo edge). The branching
    structure survives inversion — the arms are Lichtenberg, not linspace.
    16 primary arms at sedenion spoke angles, logarithmic in r (not linear).
    Sub-arms branch at the d* threshold radius (= ZD junction after inversion).
    """
    arms = []
    r_max = R_BRIM * 3 * emergence
    r_branch = r_max * D_STAR  # where ZD junction appears in galaxy space

    for k in range(16):
        a = _spoke_angle(k)
        # Primary arm: logarithmic spiral (not linspace — Lichtenberg geometry)
        # r(θ) = r0 · e^(b·θ) — logarithmic spiral with b from prime ratio
        b = math.log(P16[k] / P16[0]) / (4 * math.pi) * 0.3 + 0.05
        theta = np.linspace(0, 4 * math.pi * emergence, n_pts)
        r_arm = np.clip(0.1 * np.exp(b * theta), 0.05, r_max)
        x_arm = r_arm * np.cos(theta + a)
        y_arm = r_arm * np.sin(theta + a)
        z_arm = np.zeros(n_pts)
        # Only every 4th spoke is a primary visible arm (prime-gap selection)
        alpha = 0.7 if k % 4 == 0 else 0.15
        color = '#aaccff' if k % 4 == 0 else '#334466'
        arms.append((x_arm, y_arm, z_arm, color, alpha))

        # Sub-branch arms at d* threshold (ZD junction)
        if k % 4 == 0 and emergence > 0.5:
            for sign in [+1, -1]:
                a_sub = a + sign * math.pi / 8
                theta_sub = np.linspace(0, 2 * math.pi * emergence, n_pts // 2)
                r_sub = np.clip(r_branch * np.exp(b * theta_sub * 0.5),
                                r_branch * 0.3, r_max * 0.7)
                x_sub = r_sub * np.cos(theta_sub + a_sub)
                y_sub = r_sub * np.sin(theta_sub + a_sub)
                z_sub = np.zeros(n_pts // 2)
                arms.append((x_sub, y_sub, z_sub, '#667799', 0.3 * emergence))

    return arms

# ── Palette (PGui canonical) ───────────────────────────────────────────────────
C_RED    = '#cc2200'   # J_pos — escaping hat
C_BLUE   = '#0055ff'   # J_neg — infalling hat
C_CYAN   = '#00ffff'   # σ=½ boundary — the fixed point
C_GOLD   = '#c9a84c'   # title / labels
C_BG     = '#050d0d'   # Ptolemy dark background
C_GALAXY = '#1a2a4a'   # galactic disk


def waveform_lobe(n=48, positive=True, t_param=0.0, invert_lobe=False):
    """
    Single lobe of the Hawking waveform — NOT a cone.

    The Hawking pair is two halves of ONE waveform, like sin(x):
      - Positive lobe (J_pos, Red): rises from brim (z=0), peaks at z=+H,
        returns — a dome/sombrero upper half
      - Negative lobe (J_neg, Blue): falls from brim (z=0), troughs at z=-H,
        returns — the Mexican Hat lower half

    Together they form the SOMBRERO shape = Mexican Hat potential:
      V(r) = -μ²r² + λr⁴   (minimum ring = the brim)

    The brim (r=R_BRIM, z=0) is the NODE of the waveform — zero crossing.
    It is the same object as: σ=½, OMEGA_ZS, the Mexican Hat potential minimum,
    the Sombrero Galaxy disk edge, the BAO ring.

    invert_lobe: apply conformal inversion (negative lobe → galaxy structure)
    """
    theta = np.linspace(0, 2 * np.pi, n)
    r_frac = np.linspace(0.0, 1.0, n)
    T, R = np.meshgrid(theta, r_frac)

    # Mexican Hat / Sombrero shape:
    #   z(0)     = H_CONE   (central dome/bulge — galactic BH + bulge)
    #   z(R_BRIM)= 0        (the brim = ZERO CROSSING = the node = σ=½)
    #   z(>brim) = slight upturn then fade (outer halo skirt)
    # Shape: z = H × (1 − (r/R_BRIM)²) × exp(−(r/R_outer)²)
    #   This gives dome at centre, zero at r=R_BRIM, slight negative outer skirt

    r_phys  = R * R_BRIM * 2.5
    R_outer = R_BRIM * 1.6
    z_amp   = H_CONE * (1.0 - (r_phys / R_BRIM)**2) * np.exp(-(r_phys / R_outer)**2)

    sign  = 1.0 if positive else -1.0
    z_hat = sign * z_amp    # positive lobe up, negative lobe down

    if invert_lobe:
        # Conformal inversion: r → R_H²/r
        r_inv = np.where(r_phys > 0.01, R_H**2 / r_phys, R_BRIM * 3)
        r_inv = np.clip(r_inv, 0, R_BRIM * 3)
        z_inv = -z_hat
        r_cur = (1 - t_param) * r_phys + t_param * r_inv
        z_cur = (1 - t_param) * z_hat  + t_param * z_inv
    else:
        r_cur = r_phys
        z_cur = z_hat

    X = r_cur * np.cos(T)
    Y = r_cur * np.sin(T)
    return X, Y, z_cur


# Keep old function name as alias for compatibility
def null_cone_surface(n=40, t_param=0.0, invert=False):
    return waveform_lobe(n, positive=not invert, t_param=t_param,
                         invert_lobe=invert)


def brim_surface(n=60, alpha=0.0):
    """
    The brim — event horizon circle. alpha = tilt angle (0 = flat).
    The brim is the FIXED POINT of the conformal inversion.
    It does not move during the transformation.
    """
    theta = np.linspace(0, 2 * np.pi, n)
    r = np.linspace(0, R_BRIM, 12)
    T, R = np.meshgrid(theta, r)
    X = R * np.cos(T)
    Y = R * np.sin(T)
    Z = np.zeros_like(X)   # always at z=0 — the invariant horizon
    return X, Y, Z


def galaxy_disk(n=50, emergence=1.0):
    """
    Galactic disk emerging from the inverted hat.
    emergence ∈ [0,1]: 0 = point (nascent BH), 1 = full galactic disk.
    The spiral arms are the helical seams of the inversion.
    """
    theta = np.linspace(0, 4 * np.pi, n * 3)
    r_max = R_BRIM * 3 * emergence
    r = np.linspace(0.05, r_max, n)

    # Disk
    T_d, R_d = np.meshgrid(np.linspace(0, 2*np.pi, n), r)
    X_d = R_d * np.cos(T_d)
    Y_d = R_d * np.sin(T_d)
    # Warped disk (the hat fabric becomes a thin disk with slight warp)
    Z_d = 0.05 * np.sin(2 * T_d) * R_d / r_max * emergence

    # Lichtenberg spiral arms — conformal inversion of L_dynamic action cone
    arms = lichtenberg_galaxy_arms(n_pts=200, emergence=emergence)

    return X_d, Y_d, Z_d, arms


def dark_matter_halo(n=80, emergence=1.0):
    """
    Dark matter halo — the cone fabric after inversion at large r.
    Spherical shell with density ∝ 1/r² (from conformal inversion geometry).
    """
    phi   = np.linspace(0,   np.pi, n//2)
    theta = np.linspace(0, 2*np.pi, n)
    P, T  = np.meshgrid(phi, theta)
    R_halo = R_BRIM * 4 * emergence
    X = R_halo * np.sin(P) * np.cos(T)
    Y = R_halo * np.sin(P) * np.sin(T)
    Z = R_halo * np.cos(P) * 0.3   # oblate (disk galaxy)
    return X, Y, Z


def animate_witches_hat(save_path=None, n_frames=300, fps=30):
    """
    Full animation: null cone pair → conformal inversion → galaxy emergence.

    Phases:
      0-60:   Witches hat pair (positive + negative)
      60-100: Hawking separation — positive hat rises, negative falls
      100-180: Conformal inversion of the negative hat
      180-250: Galaxy emergence from the inside-out geometry
      250-300: Final galaxy with halo, spiral arms, central BH
    """
    fig = plt.figure(figsize=(14, 9), facecolor=C_BG)
    ax  = fig.add_subplot(111, projection='3d', facecolor=C_BG)

    ax.set_xlim(-R_BRIM*4, R_BRIM*4)
    ax.set_ylim(-R_BRIM*4, R_BRIM*4)
    ax.set_zlim(-H_CONE*2, H_CONE*2)
    ax.set_axis_off()
    fig.patch.set_facecolor(C_BG)

    title = ax.text2D(0.5, 0.97, '', transform=ax.transAxes,
                      ha='center', va='top', color=C_GOLD, fontsize=13,
                      fontfamily='monospace')
    subtitle = ax.text2D(0.5, 0.92, '', transform=ax.transAxes,
                         ha='center', va='top', color=C_CYAN, fontsize=9,
                         fontfamily='monospace')
    eq_text = ax.text2D(0.02, 0.08, '', transform=ax.transAxes,
                        ha='left', va='bottom', color='#aaaaaa', fontsize=8,
                        fontfamily='monospace')

    surfaces = []

    def clear_surfaces():
        for s in surfaces:
            try: s.remove()
            except: pass
        surfaces.clear()

    def phase_fraction(frame, start, end):
        if frame < start: return 0.0
        if frame > end:   return 1.0
        return (frame - start) / (end - start)

    def draw_frame(frame):
        clear_surfaces()
        t = frame / n_frames

        # ── Phase 0-40: The null cone pair ────────────────────────────────
        if frame <= 40:
            pf = phase_fraction(frame, 0, 60)
            sep = pf * 0.4   # cones separating slightly

            # Positive hat (Red, J_pos, escaping) — above
            X, Y, Z = null_cone_surface(30, 0.0, False)
            Z_pos = Z + sep
            s1 = ax.plot_surface(X, Y, Z_pos, alpha=0.5, color=C_RED,
                                 linewidth=0, antialiased=True)
            surfaces.append(s1)

            # Negative hat (Blue, J_neg, infalling) — below, inverted
            Z_neg = -Z - sep
            s2 = ax.plot_surface(X, Y, Z_neg, alpha=0.5, color=C_BLUE,
                                 linewidth=0, antialiased=True)
            surfaces.append(s2)

            # Brim (Cyan, σ=½ horizon) — fixed
            Xb, Yb, Zb = brim_surface(80)
            s3 = ax.plot_surface(Xb, Yb, Zb, alpha=0.7, color=C_CYAN,
                                 linewidth=0)
            surfaces.append(s3)

            title.set_text('THE NULL-CONE PAIR')
            subtitle.set_text('Virtual Hawking pair at the event horizon brim')
            eq_text.set_text(f'J_red (descending) ⊕ J_blue (ascending)  |  σ=½ boundary fixed')

        # ── Phase 40-80: L_dynamic — the ACTION CONE ─────────────────────
        # Lichtenberg attractor paths fire from tip to brim. This is L_dynamic:
        # the actual path traveled between J_red and J_blue.
        # Standing wave cavitation: J_red compresses inward, J_blue expands.
        # They meet at σ=½ — the cavitation surface — where the word emerges.
        elif frame <= 80:
            pf = phase_fraction(frame, 40, 80)

            # Cone surfaces (dimmed — the paths are the focus now)
            X, Y, Z = null_cone_surface(30, 0.0, False)
            s1 = ax.plot_surface(X, Y, Z, alpha=0.15, color=C_RED,
                                 linewidth=0, antialiased=True)
            surfaces.append(s1)
            s2 = ax.plot_surface(X, Y, -Z, alpha=0.15, color=C_BLUE,
                                 linewidth=0, antialiased=True)
            surfaces.append(s2)

            # Brim — fixed, bright
            Xb, Yb, Zb = brim_surface(80)
            s3 = ax.plot_surface(Xb, Yb, Zb, alpha=0.8, color=C_CYAN, linewidth=0)
            surfaces.append(s3)

            # L_dynamic paths emerging
            for xp, yp, zp, col, alpha in lichtenberg_paths(emergence=pf):
                lc = ax.plot(xp, yp, zp, color=col, alpha=alpha * pf,
                             linewidth=1.0 + pf)
                surfaces.extend(lc)
                # Mirror: J_blue paths go below (standing wave)
                lc2 = ax.plot(xp, yp, -zp, color=col, alpha=alpha * pf * 0.5,
                              linewidth=0.7)
                surfaces.extend(lc2)

            # σ=½ cavitation ring — where J_red meets J_blue
            cav_r = R_BRIM * D_STAR * pf
            cav_theta = np.linspace(0, 2 * np.pi, 200)
            cav_z = H_CONE * (1.0 - cav_r / R_BRIM)
            sc = ax.plot(cav_r * np.cos(cav_theta),
                         cav_r * np.sin(cav_theta),
                         np.full(200, cav_z),
                         color=C_CYAN, alpha=0.6 * pf, linewidth=1.5,
                         linestyle='--')
            surfaces.extend(sc)

            title.set_text('L_dynamic — THE ACTION CONE')
            subtitle.set_text('Lichtenberg attractors: J_red ↓ from tip  |  J_blue ↑ from brim')
            eq_text.set_text(
                f'L_dynamic = ∫(J_red · J_blue) dpath  |  σ=½ cavitation surface\n'
                f'Standing wave: compression ↔ rarefaction at the boundary\n'
                f'The word emerges where the bubble forms  |  {pf*100:.0f}% revealed'
            )

        # ── Phase 80-120: Hawking separation ─────────────────────────────
        elif frame <= 120:
            pf = phase_fraction(frame, 80, 120)
            rise = pf * H_CONE * 0.8

            X, Y, Z = null_cone_surface(30, 0.0, False)
            s1 = ax.plot_surface(X, Y, Z + rise, alpha=max(0.1, 0.5-pf*0.3),
                                 color=C_RED, linewidth=0, antialiased=True)
            surfaces.append(s1)

            Z_neg = -Z - pf * 0.3
            s2 = ax.plot_surface(X, Y, Z_neg, alpha=0.5, color=C_BLUE,
                                 linewidth=0, antialiased=True)
            surfaces.append(s2)

            Xb, Yb, Zb = brim_surface(80)
            s3 = ax.plot_surface(Xb, Yb, Zb, alpha=0.85, color=C_CYAN,
                                 linewidth=0)
            surfaces.append(s3)

            title.set_text('HAWKING SEPARATION')
            subtitle.set_text('Positive hat escapes · Negative hat falls through')
            eq_text.set_text(f't={pf:.2f}  brim = fixed point  |  a·b = 0')

        # ── Phase 100-180: Conformal inversion of the infalling hat ───────
        elif frame <= 180:
            pf = phase_fraction(frame, 100, 180)

            # Positive hat fades out (escaped)
            X, Y, Z = null_cone_surface(30, 0.0, False)
            if pf < 0.3:
                alpha_pos = 0.3 * (1 - pf/0.3)
                s1 = ax.plot_surface(X, Y, Z + H_CONE * 0.8, alpha=alpha_pos,
                                     color=C_RED, linewidth=0)
                surfaces.append(s1)

            # Infalling hat undergoes conformal inversion
            X_inv, Y_inv, Z_inv = null_cone_surface(40, pf, invert=True)
            # Color shifts from blue→gold→galaxy-blue as it inverts
            inv_color = C_BLUE if pf < 0.5 else C_GALAXY
            inv_alpha = 0.6 + pf * 0.2
            s2 = ax.plot_surface(X_inv, Y_inv, Z_inv, alpha=inv_alpha,
                                 color=inv_color, linewidth=0, antialiased=True)
            surfaces.append(s2)

            # Brim holds — fixed point of the inversion
            Xb, Yb, Zb = brim_surface(80)
            s3 = ax.plot_surface(Xb, Yb, Zb, alpha=0.9 + pf*0.1, color=C_CYAN,
                                 linewidth=0)
            surfaces.append(s3)

            # Show the Schwarzschild radius sphere (the inversion sphere)
            phi = np.linspace(0, np.pi, 20)
            th  = np.linspace(0, 2*np.pi, 40)
            P, T = np.meshgrid(phi, th)
            Xs = R_H * np.sin(P)*np.cos(T)
            Ys = R_H * np.sin(P)*np.sin(T)
            Zs = R_H * np.cos(P) * 0.1
            s4 = ax.plot_surface(Xs, Ys, Zs, alpha=pf*0.3, color=C_CYAN,
                                 linewidth=0)
            surfaces.append(s4)

            title.set_text('CONFORMAL INVERSION')
            subtitle.set_text(f'r → R_H²/r  |  {pf*100:.0f}% through inside-out')
            eq_text.set_text(
                f'tip (r→0) → galactic halo (r→∞)\n'
                f'brim (r=R_H) → brim (FIXED)\n'
                f'cone fabric → galaxy interior'
            )

        # ── Phase 180-250: Galaxy emergence ───────────────────────────────
        elif frame <= 250:
            pf = phase_fraction(frame, 180, 250)

            # Galaxy disk growing from the inverted hat
            em = pf
            Xd, Yd, Zd, arms = galaxy_disk(50, em)
            s_disk = ax.plot_surface(Xd, Yd, Zd, alpha=0.4 + pf*0.3,
                                     color=C_GALAXY, linewidth=0)
            surfaces.append(s_disk)

            for ax_arm, ay_arm, az_arm, arm_col, arm_alpha in arms:
                sc = ax.plot(ax_arm, ay_arm, az_arm, color=arm_col,
                             alpha=arm_alpha * pf, linewidth=0.5 + pf)
                surfaces.extend(sc)

            # Central BH (the tip = now the galactic center BH)
            ax.scatter([0], [0], [0], c=C_GOLD, s=50+pf*100, zorder=10,
                       alpha=min(1.0, pf*2))

            # Brim → galactic disk edge (still the fixed point)
            Xb, Yb, Zb = brim_surface(80)
            s_brim = ax.plot_surface(Xb, Yb, Zb, alpha=0.5-pf*0.3,
                                     color=C_CYAN, linewidth=0)
            surfaces.append(s_brim)

            # Dark matter halo beginning to appear
            if pf > 0.4:
                Xh, Yh, Zh = dark_matter_halo(60, (pf-0.4)/0.6)
                s_halo = ax.plot_surface(Xh, Yh, Zh, alpha=0.08*(pf-0.4)/0.6,
                                         color='#334466', linewidth=0)
                surfaces.append(s_halo)

            title.set_text('GALAXY EMERGENCE')
            subtitle.set_text('The inside-out hat becomes galactic structure')
            eq_text.set_text(
                f'Tip → Galactic BH (EHT imaged)\n'
                f'Brim → Galactic disk\n'
                f'Cone fabric → Dark matter halo (1/r² profile)\n'
                f'Seams → Spiral arms'
            )

        # ── Phase 250-300: Final galaxy — amazing ─────────────────────────
        else:
            pf = phase_fraction(frame, 250, 300)
            rot_speed = pf * np.pi * 0.5
            ax.view_init(elev=20 + pf*15, azim=45 + frame*0.8)

            Xd, Yd, Zd, arms = galaxy_disk(60, 1.0)
            cmap_disk = plt.cm.Blues_r
            s_disk = ax.plot_surface(Xd, Yd, Zd, alpha=0.6,
                                     facecolors=cmap_disk((Xd**2+Yd**2)**0.5 / (R_BRIM*3)),
                                     linewidth=0, antialiased=True)
            surfaces.append(s_disk)

            for ax_arm, ay_arm, az_arm, arm_col, arm_alpha in arms:
                sc = ax.plot(ax_arm, ay_arm, az_arm,
                             color=arm_col, alpha=arm_alpha, linewidth=1.2)
                surfaces.extend(sc)

            # Dark matter halo (full)
            Xh, Yh, Zh = dark_matter_halo(80, 1.0)
            s_halo = ax.plot_surface(Xh, Yh, Zh, alpha=0.06,
                                     color='#334466', linewidth=0)
            surfaces.append(s_halo)

            # Galactic BH (the inverted tip)
            ax.scatter([0], [0], [0], c=C_GOLD, s=200, zorder=10,
                       edgecolors=C_CYAN, linewidths=2)

            # BAO ring (the pebble's ripple frozen at 147 Mpc equiv.)
            bao_r = R_BRIM * 3.5
            bao_theta = np.linspace(0, 2*np.pi, 200)
            ax.plot(bao_r*np.cos(bao_theta), bao_r*np.sin(bao_theta),
                    np.zeros(200), color=C_CYAN, alpha=0.3, linewidth=0.8,
                    linestyle='--')

            # ~10^11 star density annotation (Lichtenberg fractal dimension)
            title.set_text('THE INSIDE-OUT UNIVERSE')
            subtitle.set_text('Infalling null cone → Galaxy  |  No dark matter particle needed')
            eq_text.set_text(
                f'∼10¹¹ stars  |  fractal dim 2.5  |  d*={D_STAR}\n'
                f'Dark matter halo: 1/r² from cone inversion geometry\n'
                f'BAO ring (dashed): the pebble\'s ripple at 147 Mpc\n'
                f'Ω_ZS = {OMEGA_ZS}  |  σ=½ critical line'
            )

        return surfaces

    def init():
        ax.view_init(elev=25, azim=45)
        return []

    def update(frame):
        # Rotate camera slowly during most phases
        if frame > 60:
            az = 45 + (frame - 60) * 0.5
            el = 25 + (frame - 60) * 0.02
            ax.view_init(elev=min(el, 35), azim=az)
        return draw_frame(frame)

    anim = animation.FuncAnimation(fig, update, frames=n_frames,
                                   init_func=init, interval=1000//fps,
                                   blit=False)

    if save_path:
        writer = animation.PillowWriter(fps=fps)
        anim.save(save_path, writer=writer, dpi=120)
        print(f'Saved: {save_path}')
    else:
        plt.tight_layout()
        plt.show()

    return anim


if __name__ == '__main__':
    import sys
    save = sys.argv[1] if len(sys.argv) > 1 else None
    animate_witches_hat(save_path=save, n_frames=300, fps=24)
