"""
OneShot Trust Game Implementation

A trust game where two players make decisions about money transfers.
Supports LLM players, role-playing, and internationalization.
"""

from .llm import LLMConfig, LLMsConfig
from .oneshot_game import OneShotGame, OneShotGameState, MultiOneShotPrompt
from .repeated_game import RepeatedGame, RepeatedGameState

__all__ = [
    "LLMConfig",
    "LLMsConfig",
    "OneShotGame",
    "OneShotGameState",
    "MultiOneShotPrompt",
    "RepeatedGame",
    "RepeatedGameState",
]
