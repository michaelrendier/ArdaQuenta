"""
Lexicon — The accumulated experience of the ValaQuenta.

Maps Riemann zeros (primes) to the surface forms that point at them.
Persists across sessions. Grows with every corpus processed.

Structure:
    gamma → { surface_form → count }          (global)
    gamma → { domain → { surface_form → count } }  (domain-indexed)

Knowledge  = the prime (gamma — pre-existing, mathematical)
Experience = the lexicon (accumulated — grows with every text processed)
Wisdom     = the DC     (the Capacitor's integral over all experience)

The lexicon does not define meaning.
It records which coordinate systems have pointed at the same prime.
The prime was already there.
"""

import json
import os
from typing import Optional


_GAMMA_FMT = '{:.6f}'


def _gkey(gamma: float) -> str:
    return _GAMMA_FMT.format(gamma)


class Lexicon:
    """
    Persistent map from Riemann zeros to surface forms.

    Each entry:
        gamma  — the Riemann zero (the prime, the instrument)
        faces  — {surface_form: count}  (global, language-agnostic)
        domains — {domain_description: {surface_form: count}}

    Grows with use. Saves to disk. Loads on startup.
    No training. No model. Just accumulated observation.
    """

    def __init__(self, path: Optional[str] = None):
        self.path         = path
        self._faces: dict = {}          # {gkey: {surface: count}}
        self._domains: dict = {}        # {gkey: {domain: {surface: count}}}
        self._files_seen: set = set()   # paths already processed

        if path and os.path.exists(path):
            self.load(path)

    # ── recording ─────────────────────────────────────────────────────────────

    def record(self, gamma: float, surface: str,
               domain: Optional[str] = None, weight: int = 1) -> None:
        """
        Record that this surface form points at this Riemann zero.
        Optionally within a semantic domain.
        """
        k = _gkey(gamma)
        surface = surface.strip()
        if not surface:
            return

        if k not in self._faces:
            self._faces[k] = {}
        self._faces[k][surface] = self._faces[k].get(surface, 0) + weight

        if domain:
            if k not in self._domains:
                self._domains[k] = {}
            if domain not in self._domains[k]:
                self._domains[k][domain] = {}
            self._domains[k][domain][surface] = (
                self._domains[k][domain].get(surface, 0) + weight
            )

    def record_file(self, path: str) -> None:
        self._files_seen.add(os.path.abspath(path))

    def already_seen(self, path: str) -> bool:
        return os.path.abspath(path) in self._files_seen

    # ── querying ───────────────────────────────────────────────────────────────

    def faces(self, gamma: float, domain: Optional[str] = None,
              n: int = 10) -> list[tuple[str, int]]:
        """
        Top n surface forms for this Riemann zero.
        If domain given, restrict to that domain first, fall back to global.
        Returns [(surface_form, count), ...] sorted by count descending.
        """
        k = _gkey(gamma)

        if domain and k in self._domains and domain in self._domains[k]:
            pool = self._domains[k][domain]
        elif k in self._faces:
            pool = self._faces[k]
        else:
            return []

        return sorted(pool.items(), key=lambda x: x[1], reverse=True)[:n]

    def best_face(self, gamma: float, domain: Optional[str] = None,
                  language_hint: Optional[str] = None) -> Optional[str]:
        """
        The single most-seen surface form for this prime.
        This is the engine's best answer to: 'what word is this?'
        """
        candidates = self.faces(gamma, domain=domain, n=20)
        if not candidates:
            return None
        if language_hint:
            for surface, _ in candidates:
                if _detect_script(surface) == language_hint:
                    return surface
        return candidates[0][0]

    def known_gammas(self) -> list[float]:
        """All Riemann zeros the lexicon has seen."""
        return sorted(float(k) for k in self._faces)

    def face_count(self, gamma: float) -> int:
        """How many distinct surface forms point at this zero."""
        k = _gkey(gamma)
        return len(self._faces.get(k, {}))

    # ── persistence ────────────────────────────────────────────────────────────

    def save(self, path: Optional[str] = None) -> None:
        """Save lexicon to disk as JSON."""
        target = path or self.path
        if not target:
            return
        os.makedirs(os.path.dirname(target), exist_ok=True)
        data = {
            'faces':      self._faces,
            'domains':    self._domains,
            'files_seen': list(self._files_seen),
        }
        with open(target, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def load(self, path: Optional[str] = None) -> None:
        """Load lexicon from disk."""
        target = path or self.path
        if not target or not os.path.exists(target):
            return
        with open(target, 'r', encoding='utf-8') as f:
            data = json.load(f)
        self._faces      = data.get('faces', {})
        self._domains    = data.get('domains', {})
        self._files_seen = set(data.get('files_seen', []))

    def merge(self, other: 'Lexicon') -> None:
        """Merge another lexicon into this one."""
        for k, faces in other._faces.items():
            if k not in self._faces:
                self._faces[k] = {}
            for surface, count in faces.items():
                self._faces[k][surface] = self._faces[k].get(surface, 0) + count

        for k, domains in other._domains.items():
            if k not in self._domains:
                self._domains[k] = {}
            for domain, faces in domains.items():
                if domain not in self._domains[k]:
                    self._domains[k][domain] = {}
                for surface, count in faces.items():
                    self._domains[k][domain][surface] = (
                        self._domains[k][domain].get(surface, 0) + count
                    )

        self._files_seen |= other._files_seen

    # ── statistics ─────────────────────────────────────────────────────────────

    def stats(self) -> dict:
        total_faces   = sum(len(v) for v in self._faces.values())
        total_tokens  = sum(sum(v.values()) for v in self._faces.values())
        return {
            'unique_primes':  len(self._faces),
            'unique_faces':   total_faces,
            'total_tokens':   total_tokens,
            'files_seen':     len(self._files_seen),
            'domains_indexed': sum(len(v) for v in self._domains.values()),
        }

    def __repr__(self) -> str:
        s = self.stats()
        return (
            f"Lexicon({s['unique_primes']} primes  "
            f"{s['unique_faces']} faces  "
            f"{s['total_tokens']} tokens  "
            f"{s['files_seen']} files)"
        )


# ── script detection (rough) ──────────────────────────────────────────────────

def _detect_script(text: str) -> str:
    """Rough script family from the first non-ASCII character."""
    for ch in text:
        o = ord(ch)
        if o < 128:             continue
        if 0x0600 <= o <= 0x06FF: return 'arabic'
        if 0x0590 <= o <= 0x05FF: return 'hebrew'
        if 0x0900 <= o <= 0x097F: return 'devanagari'
        if 0x0400 <= o <= 0x04FF: return 'cyrillic'
        if 0x0370 <= o <= 0x03FF: return 'greek'
        if 0x4E00 <= o <= 0x9FFF: return 'cjk'
        if 0x3040 <= o <= 0x30FF: return 'japanese'
        if 0xAC00 <= o <= 0xD7AF: return 'korean'
        if 0x0080 <= o <= 0x024F: return 'latin-ext'
    return 'latin'
