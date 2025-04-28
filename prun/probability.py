# mypy: ignore-errors
from typing import List, Dict, Any
import numpy as np
import json


class FillProbabilityModel:
    """Base class for fill probability models."""

    def __init__(self, params: Dict[str, Any]):
        self.params = params
        self.historical_data = self._load_historical_data()

    def _load_historical_data(self) -> List[Dict[str, Any]]:
        """Load historical fill data for the item."""
        # TODO: Implement loading from database
        return []

    def probability(self, t: float) -> float:
        """Calculate probability of fill by time t."""
        raise NotImplementedError

    @property
    def expected_fill_time(self) -> float:
        """Get the expected fill time from parameters."""
        return self.params.get("expected_fill_time", 7)  # Default 7 days

    def expected_inflow(
        self, quantity: float, price: float, start_t: float, end_t: float
    ) -> float:
        """Calculate expected inflow for a time period.

        Args:
            quantity: Amount of item
            price: Price per unit
            start_t: Start time
            end_t: End time

        Returns:
            Expected inflow amount
        """
        return quantity * price * (self.probability(end_t) - self.probability(start_t))


class LinearFillModel(FillProbabilityModel):
    """Linear fill probability model for steady-demand commodities."""

    def probability(self, t: float) -> float:
        return min(1.0, t / self.expected_fill_time)

    def expected_inflow(
        self, quantity: float, price: float, start_t: float, end_t: float
    ) -> float:
        """Override for linear model to handle edge cases."""
        if start_t >= self.expected_fill_time:
            return 0.0
        if end_t > self.expected_fill_time:
            end_t = self.expected_fill_time
        return quantity * price * (end_t - start_t) / self.expected_fill_time


class ExponentialFillModel(FillProbabilityModel):
    """Exponential fill probability model for volatile markets."""

    @property
    def lambda_(self) -> float:
        """Get the decay rate from parameters."""
        return self.params.get("lambda", 0.5)  # Default decay rate

    def probability(self, t: float) -> float:
        return 1 - np.exp(-self.lambda_ * t)

    def expected_inflow(
        self, quantity: float, price: float, start_t: float, end_t: float
    ) -> float:
        """Override for exponential model to handle edge cases."""
        return (
            quantity
            * price
            * (np.exp(-self.lambda_ * start_t) - np.exp(-self.lambda_ * end_t))
        )


class MonteCarloFillModel(FillProbabilityModel):
    """Monte Carlo fill probability model for high-value sales."""

    def __init__(self, params: Dict[str, Any]):
        super().__init__(params)
        self.samples = self._load_historical_samples()

    def _load_historical_samples(self) -> List[float]:
        """Load historical fill times for Monte Carlo simulation."""
        # TODO: Implement loading from database
        return []

    @property
    def num_samples(self) -> int:
        """Get the number of samples."""
        return len(self.samples)

    def probability(self, t: float) -> float:
        if not self.samples:
            return 0.0
        return sum(1 for sample in self.samples if sample <= t) / self.num_samples

    def expected_inflow(
        self, quantity: float, price: float, start_t: float, end_t: float
    ) -> float:
        """Override for Monte Carlo model to use actual samples."""
        if not self.samples:
            return 0.0
        relevant_samples = [s for s in self.samples if start_t <= s <= end_t]
        return quantity * price * len(relevant_samples) / self.num_samples
