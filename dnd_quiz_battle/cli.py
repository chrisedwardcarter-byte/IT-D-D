"""Command line interface for hosting a D&D style quiz battle."""
from __future__ import annotations

import json
from pathlib import Path
from typing import List, Sequence

from .content_loader import load_content_from_file
from .game_engine import GameConfiguration, GameEngine
from .image_generation import ImageGenerationError, generate_character_portrait
from .models import ATTACK_DAMAGE, AttackDifficulty, Player
from .question_bank import build_question_bank


def start_battle(
    *,
    topic_description: str | None = None,
    content_file: str | None = None,
    players: Sequence[dict] | None = None,
    portraits_dir: str | Path = "portraits",
    seed: int | None = None,
    generate_portraits: bool = True,
) -> GameEngine:
    """Create a configured game engine from various inputs."""

    if not topic_description and not content_file:
        raise ValueError("Either a topic description or a content file must be provided.")

    if topic_description is None:
        topic_description = load_content_from_file(str(content_file))
    topic_title = _derive_topic_title(topic_description)

    player_objects = _initialise_players(players or [], portraits_dir, generate_portraits)
    if not player_objects:
        raise ValueError("At least one player must be registered to start the battle.")

    question_bank = build_question_bank(topic_description, seed=seed)
    if not question_bank.has_questions():
        raise ValueError("Unable to generate questions from the provided material.")

    monster_name = f"Guardian of {topic_title}"
    config = GameConfiguration(topic=topic_title, monster_name=monster_name, players=player_objects)
    engine = GameEngine(config=config, question_bank=question_bank)
    return engine


def interactive_cli() -> None:
    """Interactive shell for facilitators running the activity."""

    print("Welcome to the D&D Quiz Battle!")
    choice = input("Do you have a content file to upload? (y/n): ").strip().lower()
    if choice == "y":
        file_path = input("Enter the path to the PDF/PPT/text file: ").strip()
        topic_description = load_content_from_file(file_path)
    else:
        print("Describe the learning topic (end with an empty line):")
        lines: List[str] = []
        while True:
            line = input()
            if not line:
                break
            lines.append(line)
        topic_description = "\n".join(lines)

    players = _prompt_players()
    engine = start_battle(topic_description=topic_description, players=players)
    _run_battle_loop(engine)


def _run_battle_loop(engine: GameEngine) -> None:
    round_counter = 1
    while not engine.is_battle_over():
        print(f"\n--- Round {round_counter} ---")
        for player in engine.config.players:
            if engine.is_battle_over():
                break
            if not player.is_active:
                continue
            difficulty = _prompt_difficulty(player)
            question = engine.draw_question(difficulty)
            if not question:
                print("No more questions available. The monster retreats for now!")
                return
            print(f"Question for {player.name}: {question.prompt}")
            for index, option in enumerate(question.options):
                print(f"  {index + 1}. {option}")
            selection = _prompt_option(len(question.options)) - 1
            result = engine.play_turn(player, difficulty, answer_index=selection, question=question)
            print(result.feedback)
            if result.correct:
                print(f"Correct answer: {result.correct_option}")
            else:
                print(f"The correct answer was: {result.correct_option}")
        if not engine.monster.is_defeated() and engine.monster.enrage_level:
            print(engine.monster.monster_turn())
        round_counter += 1

    print("\nBattle complete!")
    print(engine.summary())


def _prompt_players() -> Sequence[dict]:
    players: List[dict] = []
    print("Enter up to 8 players. Leave the name empty to finish.")
    while len(players) < 8:
        name = input("Player name: ").strip()
        if not name:
            break
        description = input("Describe their hero persona: ").strip()
        players.append({"name": name, "description": description})
    return players


def _prompt_difficulty(player: Player) -> AttackDifficulty:
    print(
        f"{player.name}, choose your attack: 1) Basic ({ATTACK_DAMAGE[AttackDifficulty.BASIC]} dmg) "
        f"2) Advanced ({ATTACK_DAMAGE[AttackDifficulty.ADVANCED]} dmg) 3) Special ({ATTACK_DAMAGE[AttackDifficulty.SPECIAL]} dmg)"
    )
    choice = _prompt_option(3)
    return [AttackDifficulty.BASIC, AttackDifficulty.ADVANCED, AttackDifficulty.SPECIAL][choice - 1]


def _prompt_option(maximum: int) -> int:
    while True:
        try:
            selection = int(input("Choose an option: "))
        except ValueError:
            print("Please enter a number.")
            continue
        if 1 <= selection <= maximum:
            return selection
        print(f"Enter a number between 1 and {maximum}.")


def _derive_topic_title(description: str) -> str:
    lines = [line.strip() for line in description.splitlines() if line.strip()]
    if lines:
        return lines[0][:60]
    return "Mystery Lesson"


def _initialise_players(
    players: Sequence[dict], portraits_dir: str | Path, generate_portraits: bool
) -> Sequence[Player]:
    player_objects: List[Player] = []
    for index, payload in enumerate(players):
        if index >= 8:
            break
        name = payload.get("name", f"Hero {index + 1}")
        description = payload.get("description", "Adventurous student")
        portrait_path = None
        if generate_portraits:
            portrait_prompt = f"Fantasy portrait of {name}, {description}"
            try:
                portrait_path = str(
                    generate_character_portrait(portrait_prompt, portraits_dir, filename=f"player_{index + 1}")
                )
            except ImageGenerationError as error:
                print(f"Warning: Could not generate portrait for {name}: {error}")
        player_objects.append(Player(name=name, description=description, portrait_path=portrait_path))
    return player_objects


def export_session(engine: GameEngine, output_path: str | Path) -> None:
    """Export the event log and summary to a JSON report."""

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "topic": engine.config.topic,
        "monster": engine.config.monster_name,
        "monster_health": engine.monster.max_health,
        "players": [
            {
                "name": player.name,
                "description": player.description,
                "portrait_path": player.portrait_path,
                "damage_dealt": player.damage_dealt,
                "questions_answered": player.questions_answered,
            }
            for player in engine.config.players
        ],
        "events": [
            {
                "player": result.player.name,
                "difficulty": result.difficulty.value,
                "correct": result.correct,
                "damage": result.damage,
                "question": result.question_text,
                "selected_option": result.selected_option,
                "correct_option": result.correct_option,
                "feedback": result.feedback,
            }
            for result in engine.event_log
        ],
        "monster_history": list(engine.monster.history),
        "battle_summary": engine.summary(),
    }

    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Session exported to {path}")


__all__ = ["start_battle", "interactive_cli", "export_session"]
