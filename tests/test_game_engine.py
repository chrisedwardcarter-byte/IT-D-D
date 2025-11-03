from dnd_quiz_battle.cli import start_battle
from dnd_quiz_battle.models import AttackDifficulty


def build_engine():
    description = (
        "Energy transfer occurs in ecosystems as organisms consume one another. "
        "Food chains represent these relationships."
    )
    players = [
        {"name": "Aria", "description": "A strategist with a keen mind"},
        {"name": "Bram", "description": "A bold warrior"},
    ]
    return start_battle(
        topic_description=description,
        players=players,
        portraits_dir="./test_portraits",
        seed=1,
        generate_portraits=False,
    )


def test_engine_initialisation():
    engine = build_engine()
    assert engine.monster.max_health > 0
    assert engine.question_bank.has_questions()
    assert len(engine.config.players) == 2


def test_play_turn_records_results():
    engine = build_engine()
    question = engine.draw_question(AttackDifficulty.BASIC)
    assert question is not None

    result = engine.play_turn(
        engine.config.players[0],
        AttackDifficulty.BASIC,
        answer_index=question.answer_index,
        question=question,
    )
    assert result.correct is True
    assert engine.monster.health < engine.monster.max_health
    assert engine.config.players[0].damage_dealt > 0
