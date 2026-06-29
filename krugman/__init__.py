"""Shared core for the Krugman/Flood-Garber crisis teaching tool."""

from .model import CrisisParams
from .simulate import deterministic_simulation, monte_carlo_simulation

__all__ = ["CrisisParams", "deterministic_simulation", "monte_carlo_simulation"]
