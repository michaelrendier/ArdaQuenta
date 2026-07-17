"""
CorpusProcessor — Feed any text archive to the ValaQuenta.

Reads files. Splits into passages. Sets semantic domains from context.
Processes every word. Records every prime. Builds the lexicon.

No matter the language. No matter the alphabet.
The prime preexists every surface form invented to point at it.
The corpus reveals which surface forms share which primes.

Processing pipeline per passage:
    passage text  →  domain (from the passage itself)
    each word     →  read(word, domain)  →  gamma
    gamma + word  →  lexicon.record()

This is the experience layer.
Knowledge (prime) + Experience (corpus) = Wisdom (lexicon + DC).
"""

import re
import os
import time
from typing import Optional, Iterator

from .understand import Understand
from .lexicon import Lexicon
from .semantic_domain import SemanticDomain
from .hamiltonian import RIEMANN_ZEROS


# Passage separators — blank lines, verse numbers, chapter markers
_PASSAGE_RE  = re.compile(r'\n{2,}')
_VERSE_RE    = re.compile(r'^\s*\d+[\.:]\d*\s+', re.MULTILINE)
_CHAPTER_RE  = re.compile(
    r'^\s*(chapter|book|psalm|surah|verse|section|part|act|scene|hymn|'
    r'adhyaya|parasha|hadith|sutta|tantra)\b',
    re.IGNORECASE | re.MULTILINE
)
_TOKEN_RE    = re.compile(r"[\w؀-ۿ֐-׿ऀ-ॿ"
                           r"Ѐ-ӿͰ-Ͽ一-鿿"
                           r"぀-ヿ가-힯'-]+")


class CorpusProcessor:
    """
    Feed a text archive to the ValaQuenta.

    For each passage in each file:
        1. Create a SemanticDomain from the passage text
        2. Tokenize the passage
        3. process each token through read(token, domain)
        4. Record gamma → token in the lexicon

    The lexicon accumulates experience across all files and sessions.
    """

    def __init__(self, engine: Optional[Understand] = None,
                 lexicon: Optional[Lexicon] = None,
                 min_passage_tokens: int = 5,
                 max_domain_tokens: int = 12,
                 save_every: int = 1000):
        """
        engine          — Understand instance (created if not provided)
        lexicon         — Lexicon instance (created if not provided)
        min_passage_tokens — skip passages shorter than this
        max_domain_tokens  — truncate domain descriptions to this many tokens
        save_every         — save lexicon every N passages
        """
        self.engine              = engine or Understand(tau=1.0)
        self.lexicon             = lexicon or Lexicon()
        self.min_passage_tokens  = min_passage_tokens
        self.max_domain_tokens   = max_domain_tokens
        self.save_every          = save_every

        self._passages_processed = 0
        self._words_processed    = 0
        self._files_processed    = 0

    # ── public API ─────────────────────────────────────────────────────────────

    def process_file(self, path: str, language: Optional[str] = None,
                     skip_seen: bool = True, verbose: bool = True) -> dict:
        """
        Process a single text file. Records all words to the lexicon.

        Returns stats dict for this file.
        """
        path = os.path.abspath(path)

        if skip_seen and self.lexicon.already_seen(path):
            if verbose:
                print(f'  [skip] {os.path.basename(path)} (already processed)')
            return {'skipped': True}

        try:
            text = _read_file(path)
        except Exception as e:
            if verbose:
                print(f'  [error] {os.path.basename(path)}: {e}')
            return {'error': str(e)}

        t0            = time.perf_counter()
        words_here    = 0
        passages_here = 0

        for passage, domain in self._passages_with_domains(text):
            tokens = _TOKEN_RE.findall(passage)
            if len(tokens) < self.min_passage_tokens:
                continue

            domain_desc = domain.description if domain else None

            for token in tokens:
                if len(token) < 2:
                    continue
                try:
                    word = self.engine.read(token, domain=domain)
                    self.lexicon.record(word.gamma, token, domain=domain_desc)
                    words_here += 1
                    self._words_processed += 1
                except Exception:
                    continue

            passages_here          += 1
            self._passages_processed += 1

            if self.lexicon.path and self._passages_processed % self.save_every == 0:
                self.lexicon.save()

        dt = time.perf_counter() - t0
        self.lexicon.record_file(path)
        self._files_processed += 1

        if verbose:
            rate = words_here / dt if dt > 0 else 0
            print(f'  {os.path.basename(path):<50}  '
                  f'{passages_here:>5} passages  '
                  f'{words_here:>7} words  '
                  f'{dt:.1f}s  '
                  f'{rate:.0f} w/s')

        return {
            'file':     path,
            'passages': passages_here,
            'words':    words_here,
            'time_s':   dt,
        }

    def process_directory(self, directory: str,
                          pattern: str = '*.txt',
                          recursive: bool = True,
                          skip_seen: bool = True,
                          verbose: bool = True) -> dict:
        """
        Process all matching files in a directory.
        Saves lexicon after each file.
        """
        import glob
        search = os.path.join(directory, '**', pattern) if recursive else \
                 os.path.join(directory, pattern)
        paths  = sorted(glob.glob(search, recursive=recursive))

        if not paths:
            if verbose:
                print(f'No files matching {pattern} in {directory}')
            return {}

        if verbose:
            print(f'Processing {len(paths)} files from {directory}')
            print(f'{"File":<52} {"Pass":>5} {"Words":>7} {"Time":>6} {"w/s":>8}')
            print('-' * 80)

        t0    = time.perf_counter()
        total = {'files': 0, 'passages': 0, 'words': 0}

        for path in paths:
            result = self.process_file(path, skip_seen=skip_seen, verbose=verbose)
            if not result.get('skipped') and not result.get('error'):
                total['files']    += 1
                total['passages'] += result.get('passages', 0)
                total['words']    += result.get('words', 0)
            if self.lexicon.path:
                self.lexicon.save()

        dt = time.perf_counter() - t0

        if verbose:
            print('-' * 80)
            print(f'Total: {total["files"]} files  '
                  f'{total["passages"]} passages  '
                  f'{total["words"]:,} words  '
                  f'{dt:.1f}s  '
                  f'{total["words"]/dt:.0f} w/s')
            print()
            print(self.lexicon)

        return total

    def process_parallel(self, paths: list[str],
                         verbose: bool = True) -> dict:
        """
        Process parallel texts — the same content in multiple languages.

        The first file provides the passage structure and domain descriptions.
        All subsequent files are processed against the same domains.
        This forces cross-language semantic alignment:
        words that mean the same thing, in the same passage context,
        cluster around the same Riemann zeros.
        """
        if not paths:
            return {}

        # Extract passage structure from the first (anchor) file
        try:
            anchor_text = _read_file(paths[0])
        except Exception as e:
            print(f'  [error reading anchor] {e}')
            return {}

        anchor_passages = list(self._passages_with_domains(anchor_text))

        if verbose:
            print(f'Parallel alignment: {len(paths)} languages  '
                  f'{len(anchor_passages)} passages')

        total_words = 0
        t0          = time.perf_counter()

        for path in paths:
            try:
                text   = _read_file(path)
                tokens_by_passage = list(self._passage_tokens(text))
            except Exception as e:
                if verbose:
                    print(f'  [error] {os.path.basename(path)}: {e}')
                continue

            words_here = 0
            # Align passage-by-passage with the anchor domains
            for i, (_, domain) in enumerate(anchor_passages):
                if i >= len(tokens_by_passage):
                    break
                tokens      = tokens_by_passage[i]
                domain_desc = domain.description if domain else None

                for token in tokens:
                    if len(token) < 2:
                        continue
                    try:
                        word = self.engine.read(token, domain=domain)
                        self.lexicon.record(word.gamma, token, domain=domain_desc)
                        words_here          += 1
                        self._words_processed += 1
                    except Exception:
                        continue

            if verbose:
                print(f'  {os.path.basename(path):<50}  {words_here:>7} words aligned')

            total_words += words_here
            self.lexicon.record_file(os.path.abspath(path))

        dt = time.perf_counter() - t0
        if self.lexicon.path:
            self.lexicon.save()

        if verbose:
            print(f'Total: {total_words:,} words in {dt:.1f}s  ({total_words/dt:.0f} w/s)')
            print(self.lexicon)

        return {'words': total_words, 'time_s': dt}

    # ── passage splitting ──────────────────────────────────────────────────────

    def _passages_with_domains(self, text: str
                                ) -> Iterator[tuple[str, Optional[SemanticDomain]]]:
        """
        Split text into (passage, domain) pairs.
        The domain is derived from the start of each passage.
        """
        for passage in self._split_passages(text):
            tokens = _TOKEN_RE.findall(passage)
            if len(tokens) < self.min_passage_tokens:
                continue
            domain = self._make_domain(passage, tokens)
            yield passage, domain

    def _passage_tokens(self, text: str) -> Iterator[list[str]]:
        """Split text into passages, return token lists only."""
        for passage in self._split_passages(text):
            yield _TOKEN_RE.findall(passage)

    def _split_passages(self, text: str) -> Iterator[str]:
        """
        Split text into semantic passages.
        Priority: verse numbers > chapter headings > blank lines.
        """
        # Try verse-level splitting first
        if _VERSE_RE.search(text):
            for passage in _VERSE_RE.split(text):
                passage = passage.strip()
                if passage:
                    yield passage
            return

        # Chapter-level splitting
        if _CHAPTER_RE.search(text):
            parts = _CHAPTER_RE.split(text)
            for passage in parts:
                passage = passage.strip()
                if passage:
                    yield passage
            return

        # Fall back to blank-line paragraphs
        for passage in _PASSAGE_RE.split(text):
            passage = passage.strip()
            if passage:
                yield passage

    def _make_domain(self, passage: str,
                     tokens: Optional[list[str]] = None) -> Optional[SemanticDomain]:
        """
        Derive a semantic domain from a passage.
        Uses the first N tokens as the domain description.
        """
        if tokens is None:
            tokens = _TOKEN_RE.findall(passage)
        if not tokens:
            return None

        desc = ' '.join(tokens[:self.max_domain_tokens])
        try:
            return self.engine.describe(desc)
        except Exception:
            return None

    # ── statistics ─────────────────────────────────────────────────────────────

    @property
    def stats(self) -> dict:
        return {
            'files_processed':    self._files_processed,
            'passages_processed': self._passages_processed,
            'words_processed':    self._words_processed,
            'lexicon':            self.lexicon.stats(),
        }


# ── file reading ───────────────────────────────────────────────────────────────

def _read_file(path: str) -> str:
    """Read a text file, trying UTF-8 then latin-1."""
    for enc in ('utf-8', 'utf-8-sig', 'latin-1', 'cp1252'):
        try:
            with open(path, 'r', encoding=enc) as f:
                return f.read()
        except (UnicodeDecodeError, LookupError):
            continue
    raise ValueError(f'Cannot decode {path}')
