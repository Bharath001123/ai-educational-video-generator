from dataclasses import dataclass
import re


SCIENCE_HINTS = {
    "photo", "cell", "atom", "energy", "force", "gravity", "chemical",
    "biology", "physics", "chemistry", "equation", "reaction", "dna",
    "evolution", "ecosystem", "organism", "molecule", "quantum",
}

TECH_HINTS = {
    "computer", "algorithm", "programming", "software", "network",
    "database", "machine", "learning", "artificial", "intelligence",
    "data", "code", "python", "javascript",
}

MATH_HINTS = {
    "math", "algebra", "calculus", "geometry", "theorem", "probability",
    "statistics", "number", "fraction", "equation", "trigonometry",
}

HUMANITIES_HINTS = {
    "history", "literature", "poetry", "government", "economy",
    "culture", "philosophy", "society", "war", "revolution",
}


@dataclass(frozen=True)
class TopicContext:
    topic: str
    display_topic: str
    article: str
    domain: str
    focus_phrase: str
    learning_goal: str


def build_topic_context(topic: str) -> TopicContext:
    """Derive topic-specific context used by section content builders."""
    display_topic = _normalize_display_topic(topic)
    tokens = re.findall(r"[a-z0-9]+", topic.lower())
    domain = _detect_domain(tokens)
    article = _article_for(display_topic)

    return TopicContext(
        topic=topic.strip(),
        display_topic=display_topic,
        article=article,
        domain=domain,
        focus_phrase=_focus_phrase(display_topic, domain),
        learning_goal=_learning_goal(display_topic, domain),
    )


def _normalize_display_topic(topic: str) -> str:
    cleaned = topic.strip()
    if not cleaned:
        return "this topic"
    return cleaned[0].upper() + cleaned[1:]


def _article_for(topic: str) -> str:
    return "an" if topic[:1].lower() in "aeiou" else "a"


def _detect_domain(tokens: list[str]) -> str:
    token_set = set(tokens)
    if token_set & SCIENCE_HINTS:
        return "science"
    if token_set & TECH_HINTS:
        return "technology"
    if token_set & MATH_HINTS:
        return "mathematics"
    if token_set & HUMANITIES_HINTS:
        return "humanities"
    return "general"


def _focus_phrase(topic: str, domain: str) -> str:
    phrases = {
        "science": f"the scientific principles behind {topic}",
        "technology": f"how {topic} works in modern systems",
        "mathematics": f"the mathematical reasoning used in {topic}",
        "humanities": f"the historical and social significance of {topic}",
        "general": f"the core ideas students need to understand about {topic}",
    }
    return phrases[domain]


def _learning_goal(topic: str, domain: str) -> str:
    goals = {
        "science": f"explain how {topic} operates in the natural world",
        "technology": f"show how {topic} solves practical problems",
        "mathematics": f"break down the logic and methods involved in {topic}",
        "humanities": f"connect {topic} to real events, ideas, and human experience",
        "general": f"build a clear mental model of {topic}",
    }
    return goals[domain]
