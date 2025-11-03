# IT-D-D – Dungeons & Didactics

A cooperative classroom activity that mixes Dungeons & Dragons style encounters with formative assessment. Students describe fantasy avatars, face an AI-generated monster inspired by the lesson topic, and answer multiple-choice questions to defeat it. The harder the question, the more damage the team deals.

## Features

- Load lesson content from text, PDF, or PowerPoint files to automatically build a quiz bank.
- Supports up to eight student heroes, each with an automatically generated portrait (with optional Stable Diffusion integration when available).
- Adaptive monster scaling based on player count with escalating damage when questions are missed.
- Three attack tiers (basic, advanced, special) mapped to easy, medium, and hard questions respectively.
- CLI experience for facilitators to run battles in-person, plus helper utilities to export results as JSON logs.
- Extensible Python package architecture with unit tests covering question generation and battle flow.

## Getting Started

### Requirements

- Python 3.10+
- Optional libraries for richer experiences:
  - `pillow` for placeholder AI-style portraits
  - `diffusers` and `torch` for real Stable Diffusion artwork
  - `python-pptx` to read PowerPoint decks
  - `pdfplumber` to extract text from PDFs

Install the project in a virtual environment and include the extras you need:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt  # optional, see below
pip install pillow pdfplumber python-pptx diffusers torch  # pick what you need
```

> The repository does not enforce dependencies automatically. Install the libraries you plan to use based on your classroom setup.

### Running the Battle CLI

```bash
python -m dnd_quiz_battle.cli
```

Follow the prompts to provide lesson material (paste a description or supply a file path) and register up to eight students. Each turn students select their attack difficulty, answer a multiple-choice question, and the engine resolves damage.

Portraits are stored in the `portraits/` directory by default. You can disable portrait generation by setting `generate_portraits=False` when using the API.

### Using the Python API

```python
from dnd_quiz_battle import AttackDifficulty, export_session, start_battle

description = """Gravity affects objects differently depending on their mass and distance."""
players = [
    {"name": "Lyra", "description": "An elven archer who studies astrophysics"},
    {"name": "Milo", "description": "A dwarven engineer fascinated by gravity wells"},
]

game = start_battle(
    topic_description=description,
    players=players,
    generate_portraits=False,  # skip image generation when running automated sessions
)

while not game.is_battle_over():
    question = game.draw_question(AttackDifficulty.BASIC)
    if not question:
        break
    game.play_turn(game.config.players[0], AttackDifficulty.BASIC, answer_index=question.answer_index, question=question)

export_session(game, "reports/session.json")
```

### Running Tests

```bash
pytest
```

## Project Structure

```
dnd_quiz_battle/
├── cli.py             # CLI entry point and orchestration helpers
├── content_loader.py  # Reading text from PDFs, PPTs, or Markdown/Text files
├── game_engine.py     # Core combat mechanics and logging
├── image_generation.py# AI/placeholder portrait generation helpers
├── models.py          # Dataclasses describing players, monsters, and attack results
└── question_bank.py   # Automatic MCQ generation from lesson content
```

Unit tests live under `tests/` and validate the question generator and combat loop.

## Roadmap Ideas

- Web-based interface with real-time multiplayer controls.
- Analytics dashboard for reviewing student performance trends.
- Integration with LMS platforms to pull learning objectives directly.
