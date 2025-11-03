"""Core gameplay loop for the cooperative quiz battle."""
from __future__ import annotations

import itertools
from dataclasses import dataclass
from typing import Iterable, List, Sequence

from .models import ATTACK_DAMAGE, AttackDifficulty, AttackResult, Monster, Player
from .question_bank import Question, QuestionBank


@dataclass
class GameConfiguration:
    """Parameters that influence the monster scaling and battle pacing."""

    topic: str
    monster_name: str
    players: Sequence[Player]

    @property
    def monster_health(self) -> int:
        base = 80
        scaling = 18 * max(len(self.players), 1)
        return base + scaling


class GameEngine:
    """Coordinates question flow between the players and the monster."""

    def __init__(self, config: GameConfiguration, question_bank: QuestionBank):
        self.config = config
        self.question_bank = question_bank
        self.monster = Monster(
            name=config.monster_name,
            topic=config.topic,
            max_health=config.monster_health,
            health=config.monster_health,
        )
        self.turn_order: Iterable[Player] = itertools.cycle(config.players)
        self.event_log: List[AttackResult] = []

    def play_turn(
        self, player: Player, difficulty: AttackDifficulty, *, answer_index: int, question: Question
    ) -> AttackResult:
        damage = 0
        correct = question.is_correct(answer_index)
        selected_option = question.options[answer_index]
        correct_option = question.options[question.answer_index]

        if correct:
            damage = ATTACK_DAMAGE[difficulty]
            self.monster.apply_damage(damage)
            player.record_attack(damage)
            feedback = f"{player.name} strikes true for {damage} damage!"
        else:
            self.monster.empower(f"{player.name}'s missed {difficulty.label} question")
            feedback = (
                f"{player.name} misses the mark. The {self.monster.name} grows stronger and deals "
                f"{self.monster.attack_damage()} damage on its next attack."
            )

        result = AttackResult(
            player=player,
            difficulty=difficulty,
            correct=correct,
            damage=damage,
            question_text=question.prompt,
            selected_option=selected_option,
            correct_option=correct_option,
            feedback=feedback,
        )
        self.event_log.append(result)
        return result

    def draw_question(self, difficulty: AttackDifficulty) -> Question | None:
        return self.question_bank.get_question(difficulty)

    def monster_turn(self) -> str:
        damage = self.monster.attack_damage()
        self.monster.history.append(
            f"The {self.monster.name} unleashes an attack empowered to {damage} damage!"
        )
        self.monster.enrage_level = 0
        return self.monster.history[-1]

    def is_battle_over(self) -> bool:
        if self.monster.is_defeated():
            return True
        if not self.question_bank.has_questions():
            return True
        if not any(player.is_active for player in self.config.players):
            return True
        return False

    def summary(self) -> str:
        lines = [
            f"Battle Summary against {self.monster.name} (Topic: {self.monster.topic})",
            f"Monster defeated: {'Yes' if self.monster.is_defeated() else 'No'}",
            "",
            "Player Contributions:",
        ]
        for player in self.config.players:
            lines.append(
                f"- {player.name}: {player.damage_dealt} damage across {player.questions_answered} questions"
            )
        lines.append("")
        lines.append("Monster Events:")
        lines.extend(self.monster.history)
        return "\n".join(lines)


__all__ = ["GameConfiguration", "GameEngine"]
