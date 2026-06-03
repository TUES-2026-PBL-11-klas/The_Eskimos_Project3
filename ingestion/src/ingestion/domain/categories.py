"""The category taxonomy and the keyword map the Categorizer (Phase 4) classifies against.

Seven real categories plus an explicit ``UNCATEGORIZED`` fallback. Keywords cover both
Bulgarian and English terms since the sources are Bulgarian event sites.

Matching is substring-based (so Bulgarian inflections like концерт/концерта/концерти all
hit). Because of that, very short or ambiguous English tokens are deliberately avoided
("run" → "Run on AWS", "art" → "start", "dj" → "adjust") to limit false positives — prefer
specific, longer terms instead.
"""

from __future__ import annotations

from enum import StrEnum


class Category(StrEnum):
    MUSIC = "music"
    SPORT = "sport"
    LITERATURE = "literature"
    EDUCATION = "education"
    CINEMA = "cinema"
    THEATRE = "theatre"
    ART = "art"
    UNCATEGORIZED = "uncategorized"


# Lowercased keyword sets matched (substring) against title + description. UNCATEGORIZED has
# no keywords — it is the fallback when nothing else matches.
KEYWORD_MAP: dict[Category, set[str]] = {
    Category.MUSIC: {
        "concert",
        "концерт",
        "music",
        "музика",
        "jazz",
        "джаз",
        "rock",
        "рок",
        "opera",
        "опера",
        "symphony",
        "симфони",
        "festival",
        "фестивал",
        "recital",
    },
    Category.SPORT: {
        "sport",
        "спорт",
        "match",
        "мач",
        "football",
        "футбол",
        "basketball",
        "баскетбол",
        "маратон",
        "marathon",
        "tennis",
        "тенис",
        "tournament",
        "турнир",
    },
    Category.LITERATURE: {
        "book",
        "книга",
        "literature",
        "литература",
        "poetry",
        "поезия",
        "reading",
        "четене",
        "author",
        "автор",
        "writer",
        "писател",
    },
    Category.EDUCATION: {
        "lecture",
        "лекция",
        "workshop",
        "уоркшоп",
        "seminar",
        "семинар",
        "course",
        "курс",
        "training",
        "обучение",
        "education",
        "образование",
        "conference",
        "конференция",
        "meetup",
        "webinar",
    },
    Category.CINEMA: {
        "cinema",
        "кино",
        "film",
        "филм",
        "movie",
        "premiere",
        "премиера",
        "screening",
        "прожекция",
        "documentary",
        "документален",
    },
    Category.THEATRE: {
        "theatre",
        "theater",
        "театър",
        "спектакъл",
        "drama",
        "драма",
        "performance",
        "представление",
        "ballet",
        "балет",
    },
    Category.ART: {
        "изкуство",
        "exhibition",
        "изложба",
        "gallery",
        "галерия",
        "painting",
        "живопис",
        "sculpture",
        "скулптура",
        "museum",
        "музей",
        "vernissage",
    },
}
