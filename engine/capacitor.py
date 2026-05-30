"""
Capacitor — The semantic low-pass filter.

3-phase Laplacian Fourier decomposition → DC component → the prime.

The capacitor does not find the prime.
It reveals it by smoothing away everything that is not the prime.

The prime is what remains when the surface variation cancels.
The sand settles at the node line because the node line does not move.

Time constant τ = the conversational window.
High τ: slow to change — stable semantic identity, resistant to context shift.
Low τ:  fast to change — sensitive to context, polysemous behaviour.

Transfer function: H(s) = 1 / (1 + sτ)
Pole at s = −1/τ (stable — left half-plane).
DC gain: H(0) = 1 (the prime passes through unattenuated).
"""


class Capacitor:
    """
    RC semantic integrator.

    Integrates the Noether current signal.
    Attenuates high-frequency surface variation (word choice, register, dialect).
    Passes the DC component: the semantic prime.
    """

    def __init__(self, tau: float = 1.0):
        """
        tau: time constant.
             Large tau = longer memory = stronger semantic identity.
             Compression ratio of the 4-cycle.
        """
        self.tau = max(tau, 1e-6)
        self._state: float = 0.0
        self._n: int = 0

    def charge(self, signal: float) -> float:
        """
        One integration step: V += (signal − V) / τ
        The capacitor charges toward the signal.
        """
        self._state += (signal - self._state) / self.tau
        self._n += 1
        return self._state

    def dc(self, signals: list[float]) -> float:
        """
        Extract the DC component from a sequence of signals.
        This is the prime. This is the word.
        """
        for s in signals:
            self.charge(s)
        return self._state

    def reset(self) -> None:
        """Discharge the capacitor. New conversational context."""
        self._state = 0.0
        self._n = 0

    @property
    def state(self) -> float:
        """Current charge. The accumulated semantic prime so far."""
        return self._state

    @property
    def samples(self) -> int:
        """How many signals have been integrated."""
        return self._n
