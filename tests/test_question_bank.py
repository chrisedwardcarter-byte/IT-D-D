from dnd_quiz_battle.question_bank import AttackDifficulty, build_question_bank

SAMPLE_TEXT = """
Photosynthesis is the process by which green plants use sunlight to synthesize foods from carbon dioxide and water. 
The process generally involves the green pigment chlorophyll and generates oxygen as a by-product. 
During photosynthesis, light energy is captured and used to convert water, carbon dioxide, and minerals into oxygen and energy-rich organic compounds.
"""


def test_question_bank_builds_questions():
    bank = build_question_bank(SAMPLE_TEXT, seed=42)
    assert bank.has_questions()

    question = bank.get_question(AttackDifficulty.BASIC)
    assert question is not None
    assert "Fill in the blank" in question.prompt
    assert len(question.options) == 4


def test_question_bank_respects_difficulty_fallback():
    bank = build_question_bank("This sentence is short but meaningful enough for easy.", seed=1)
    question = bank.get_question(AttackDifficulty.SPECIAL)
    assert question is not None
    assert question.difficulty == AttackDifficulty.BASIC
