from abc import ABC
from typing import ClassVar, Literal, Union

from pydantic import BaseModel, Field, field_validator

from .points_system import (
    DefenderPointsSystem,
    KeeperPointsSystem,
    MidfielderPointsSystem,
    PlayerPointsSystem,
    StrikerPointsSystem,
)


class Player(BaseModel, ABC):
    """Base player class with Pydantic validation."""

    ps: ClassVar[PlayerPointsSystem]  # Class attribute, defined by subclasses
    goals: int = Field(default=0, ge=0, description="Number of goals scored")
    assists: int = Field(default=0, ge=0, description="Number of assists")
    yellow_cards: int = Field(default=0, ge=0, description="Number of yellow cards")
    red_cards: int = Field(default=0, ge=0, description="Number of red cards")
    own_goals: int = Field(default=0, ge=0, description="Number of own goals")
    clean_sheets: int = Field(default=0, ge=0, description="Number of clean sheets")
    appearances: int = Field(default=0, ge=0, description="Number of appearances")

    man_of_the_match: int = Field(
        default=0, ge=0, description="Number of man of the match awards"
    )
    rating: float = Field(
        default=0.0,
        ge=0.0,
        le=10.0,
        description="Player performance rating (uniform across all positions)",
    )

    class Config:
        arbitrary_types_allowed = True  # Allow custom types like PlayerPointsSystem

    def get_points(self) -> float:
        """Calculate points based on player statistics and position."""
        return self.ps.calculate_points(self)


class Striker(Player):
    """Striker player with offensive statistics."""

    position: Literal["forward"] = "forward"
    ps: ClassVar[PlayerPointsSystem] = StrikerPointsSystem()

    @field_validator("goals")
    @classmethod
    def validate_realistic_goals(cls, v: int) -> int:
        if v > 100:
            raise ValueError("Goals cannot exceed 100 in a season")
        return v


class Defender(Player):
    """Defender player with defensive statistics."""

    position: Literal["defender"] = "defender"
    ps: ClassVar[PlayerPointsSystem] = DefenderPointsSystem()


class Midfielder(Player):
    """Midfielder player with balanced statistics."""

    position: Literal["midfielder"] = "midfielder"
    ps: ClassVar[PlayerPointsSystem] = MidfielderPointsSystem()


class Keeper(Player):
    """Goalkeeper player with specialized statistics."""

    position: Literal["keeper", "goalkeeper"] = "keeper"
    ps: ClassVar[PlayerPointsSystem] = KeeperPointsSystem()
    penalties_saved: int = Field(
        default=0, ge=0, description="Number of penalties saved"
    )

    @field_validator("goals")
    @classmethod
    def validate_keeper_goals(cls, v: int) -> int:
        if v > 5:
            raise ValueError("Goalkeeper with more than 5 goals is unusual")
        return v


# Type alias for discriminated union of all player types
PlayerUnion = Union[Striker, Defender, Midfielder, Keeper]


def create_player(data: dict) -> Player:
    """Factory function to create appropriate Player subclass from dictionary/JSON data.

    Uses Pydantic's discriminated union to automatically determine the correct
    player type based on the 'position' field.

    Args:
        data: Dictionary containing 'position' field and player statistics

    Returns:
        Instance of appropriate Player subclass (Striker, Defender, Midfielder, or Keeper)

    Raises:
        ValidationError: If data is invalid or position is not recognized

    Example:
        >>> player = create_player({"position": "striker", "goals": 15, "assists": 7})
        >>> isinstance(player, Striker)
        True
        >>> player.get_points()
        45.0
    """
    from pydantic import TypeAdapter

    adapter = TypeAdapter(PlayerUnion)
    return adapter.validate_python(data)


def create_player_from_json(json_str: str) -> Player:
    """Factory function to create appropriate Player subclass from JSON string.

    Args:
        json_str: JSON string containing 'position' field and player statistics

    Returns:
        Instance of appropriate Player subclass

    Raises:
        ValidationError: If JSON is invalid or position is not recognized

    Example:
        >>> json_data = '{"position": "keeper", "clean_sheets": 10, "penalties_saved": 2}'
        >>> player = create_player_from_json(json_data)
        >>> isinstance(player, Keeper)
        True
    """
    from pydantic import TypeAdapter

    adapter = TypeAdapter(PlayerUnion)
    return adapter.validate_json(json_str)
