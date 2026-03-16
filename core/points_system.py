from abc import ABC
from math import ceil
from typing import TYPE_CHECKING, Generic, TypeVar

if TYPE_CHECKING:
    from .players import Defender, Keeper, Midfielder, Player, Striker

P = TypeVar("P", bound="Player")


# Base interface
class PlayerPointsSystem(ABC, Generic[P]):
    # Subclasses should override these
    points_per_goal: int
    points_per_assist: int
    points_per_clean_sheet: int
    points_per_penalty_save: int
    points_per_penalty_miss: int = -2
    points_per_yellow_card: int = -1
    points_per_red_card: int = -3
    points_per_own_goal: int = -2
    points_per_2_goals_conceded: int = -1
    points_per_man_of_the_match: int

    def calculate_points(self, player: P) -> int:
        """Calculate total points for a player"""
        return (
            player.goals * self.points_per_goal
            + player.assists * self.points_per_assist
            + player.clean_sheets * self.points_per_clean_sheet
            + player.man_of_the_match * self.points_per_man_of_the_match
            + player.yellow_cards * self.points_per_yellow_card
            + player.red_cards * self.points_per_red_card
            + ceil(player.appearances * player.rating)
        )


class StrikerPointsSystem(PlayerPointsSystem["Striker"]):
    points_per_goal = 4
    points_per_assist = 3
    points_per_clean_sheet = 0
    points_per_man_of_the_match = 5


class MidfielderPointsSystem(PlayerPointsSystem["Midfielder"]):
    points_per_goal = 5
    points_per_assist = 3
    points_per_clean_sheet = 1
    points_per_man_of_the_match = 8


class DefenderPointsSystem(PlayerPointsSystem["Defender"]):
    points_per_goal = 6
    points_per_assist = 3
    points_per_clean_sheet = 4
    points_per_man_of_the_match = 12


class KeeperPointsSystem(PlayerPointsSystem["Keeper"]):
    points_per_goal = 10
    points_per_assist = 3
    points_per_clean_sheet = 4
    points_per_penalty_save = 5
    points_per_man_of_the_match = 15

    def calculate_points(self, player: "Keeper") -> int:
        """Calculate total points for a keeper"""
        base_calculation = super().calculate_points(player)
        return base_calculation + (
            player.penalties_saved * self.points_per_penalty_save
        )
