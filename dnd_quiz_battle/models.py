"""Core data models for the D&D-inspired quiz battle game."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List


class AttackDifficulty(str, Enum):
    """Enumerates the three difficulty tiers for player actions."""

    BASIC = "basic"
    ADVANCED = "advanced"
    SPECIAL = "special"

    @property
    def label(self) -> str:
        labels = {
            AttackDifficulty.BASIC: "Basic Attack",
            AttackDifficulty.ADVANCED: "Advanced Attack",
            AttackDifficulty.SPECIAL: "Special Attack",
        }
        return labels[self]


ATTACK_DAMAGE: Dict[AttackDifficulty, int] = {
    AttackDifficulty.BASIC: 12,
    AttackDifficulty.ADVANCED: 22,
    AttackDifficulty.SPECIAL: 35,
}


@dataclass
class Player:
    """Represents a student-controlled hero."""

    name: str
    description: str
    portrait_path: str | None = None
    is_active: bool = True
    damage_dealt: int = 0
    questions_answered: int = 0

    def record_attack(self, damage: int) -> None:
        self.damage_dealt += damage
        self.questions_answered += 1


@dataclass
class Monster:
    """Represents the AI-controlled enemy."""

    name: str
    topic: str
    max_health: int
    health: int
    enrage_level: int = 0
    history: List[str] = field(default_factory=list)

    def apply_damage(self, amount: int) -> None:
        self.health = max(self.health - amount, 0)
        self.history.append(f"Monster took {amount} damage. Remaining health: {self.health}.")

    def is_defeated(self) -> bool:
        return self.health <= 0

    def empower(self, reason: str) -> None:
        self.enrage_level += 1
        self.history.append(
            f"Monster power increases to {self.enrage_level} due to {reason}."
        )

    def attack_damage(self) -> int:
        base_damage = 8
        return base_damage + self.enrage_level * 4


@dataclass
class AttackResult:
    """Captures the result of a single question exchange."""

    player: Player
    difficulty: AttackDifficulty
    correct: bool
    damage: int
    question_text: str
    selected_option: str
    correct_option: str
    feedback: str


__all__ = [
    "AttackDifficulty",
    "ATTACK_DAMAGE",
    "Player",
    "Monster",
    "AttackResult",
]
