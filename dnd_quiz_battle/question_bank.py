"""Question generation and management utilities."""
from __future__ import annotations

import random
import re
import string
from dataclasses import dataclass
from typing import Iterable, List, Sequence

from .models import AttackDifficulty

STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "because",
    "been",
    "but",
    "by",
    "for",
    "from",
    "had",
    "has",
    "have",
    "in",
    "into",
    "is",
    "it",
    "its",
    "of",
    "on",
    "that",
    "the",
    "their",
    "there",
    "this",
    "to",
    "was",
    "were",
    "with",
}


@dataclass
class Question:
    """Represents a multiple-choice question."""

    prompt: str
    options: Sequence[str]
    answer_index: int
    difficulty: AttackDifficulty

    def is_correct(self, choice_index: int) -> bool:
        return choice_index == self.answer_index


class QuestionBank:
    """Stores and retrieves questions for specific difficulty levels."""

    def __init__(self, questions: Iterable[Question]):
        self._by_difficulty = {
            AttackDifficulty.BASIC: [],
            AttackDifficulty.ADVANCED: [],
            AttackDifficulty.SPECIAL: [],
        }
        for question in questions:
            self._by_difficulty[question.difficulty].append(question)

        self._used_questions: List[Question] = []

    def has_questions(self) -> bool:
        return any(self._by_difficulty.values())

    def get_question(self, difficulty: AttackDifficulty) -> Question | None:
        """Return a question of the requested difficulty or gracefully degrade."""

        order: List[AttackDifficulty] = [difficulty]
        if difficulty is AttackDifficulty.SPECIAL:
            order.extend([AttackDifficulty.ADVANCED, AttackDifficulty.BASIC])
        elif difficulty is AttackDifficulty.ADVANCED:
            order.extend([AttackDifficulty.BASIC, AttackDifficulty.SPECIAL])
        else:
            order.extend([AttackDifficulty.ADVANCED, AttackDifficulty.SPECIAL])

        for tier in order:
            bucket = self._by_difficulty[tier]
            if bucket:
                question = bucket.pop(0)
                self._used_questions.append(question)
                return question
        return None

    @property
    def used_questions(self) -> Sequence[Question]:
        return tuple(self._used_questions)


def build_question_bank(source_text: str, seed: int | None = None) -> QuestionBank:
    """Create a question bank from source text."""

    random_generator = random.Random(seed)
    sentences = _extract_sentences(source_text)
    keyword_pool = _collect_keywords(sentences)
    questions: List[Question] = []

    for sentence in sentences:
        keyword = _select_keyword(sentence, keyword_pool)
        if not keyword:
            continue
        prompt = _build_prompt(sentence, keyword)
        difficulty = _estimate_difficulty(sentence)
        distractors = _pick_distractors(keyword, keyword_pool, random_generator)
        options = list(distractors) + [keyword]
        random_generator.shuffle(options)
        answer_index = options.index(keyword)
        questions.append(
            Question(
                prompt=prompt,
                options=options,
                answer_index=answer_index,
                difficulty=difficulty,
            )
        )

    return QuestionBank(questions)


def _extract_sentences(text: str) -> List[str]:
    cleaned = text.replace("\n", " ")
    fragments = re.split(r"(?<=[.!?])\s+", cleaned)
    sentences = []
    for fragment in fragments:
        fragment = fragment.strip()
        if len(fragment.split()) < 6:
            continue
        sentences.append(fragment)
    return sentences


def _collect_keywords(sentences: Iterable[str]) -> List[str]:
    keywords: List[str] = []
    for sentence in sentences:
        for word in _tokenize(sentence):
            if word.lower() in STOPWORDS:
                continue
            keywords.append(word)
    unique = []
    seen = set()
    for word in keywords:
        key = word.lower()
        if key not in seen:
            seen.add(key)
            unique.append(word)
    return unique


def _select_keyword(sentence: str, keyword_pool: Sequence[str]) -> str | None:
    tokens = [token for token in _tokenize(sentence) if token.lower() not in STOPWORDS]
    tokens.sort(key=len, reverse=True)
    for token in tokens:
        if token.lower() in {kw.lower() for kw in keyword_pool}:
            return token
    return tokens[0] if tokens else None


def _build_prompt(sentence: str, keyword: str) -> str:
    pattern = re.compile(re.escape(keyword), flags=re.IGNORECASE)
    masked_sentence = pattern.sub("____", sentence, count=1)
    return f"Fill in the blank: {masked_sentence}"


def _estimate_difficulty(sentence: str) -> AttackDifficulty:
    word_count = len(sentence.split())
    if word_count <= 12:
        return AttackDifficulty.BASIC
    if word_count <= 20:
        return AttackDifficulty.ADVANCED
    return AttackDifficulty.SPECIAL


def _pick_distractors(
    keyword: str, keyword_pool: Sequence[str], random_generator: random.Random
) -> Sequence[str]:
    alternatives = [
        word
        for word in keyword_pool
        if word.lower() != keyword.lower() and word.lower() not in STOPWORDS
    ]
    random_generator.shuffle(alternatives)
    selected = alternatives[:3]
    if len(selected) < 3:
        filler = _generate_filler_words(random_generator, 3 - len(selected))
        selected.extend(filler)
    return selected


def _generate_filler_words(random_generator: random.Random, count: int) -> List[str]:
    words = []
    for _ in range(count):
        letters = random_generator.choices(string.ascii_lowercase, k=6)
        words.append("".join(letters))
    return words


def _tokenize(sentence: str) -> List[str]:
    cleaned = re.sub(r"[^A-Za-z0-9\-']", " ", sentence)
    return [token for token in cleaned.split() if token]


__all__ = ["Question", "QuestionBank", "build_question_bank"]
