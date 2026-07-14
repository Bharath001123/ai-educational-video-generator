"""Topic-specific content builders for each script section.

Replace this module with LLM-generated content when integrating an AI provider.
Each builder produces unique, section-appropriate text tailored to the topic.
"""

from __future__ import annotations

Section = dict[str, str]

AUDIENCE_STYLE = {
    "school": {
        "voice": "friendly and clear",
        "complexity": "simple vocabulary with relatable comparisons",
    },
    "ug": {
        "voice": "academic yet accessible",
        "complexity": "precise terminology with logical structure",
    },
    "pg": {
        "voice": "scholarly and analytical",
        "complexity": "advanced concepts with critical depth",
    },
}

DURATION_BLUEPRINTS: dict[str, list[tuple[str, str]]] = {
    "1": [
        ("introduction", "Introduction"),
        ("main_idea", "Main Idea"),
        ("summary", "Summary"),
    ],
    "3": [
        ("explanation", "Explanation"),
        ("example", "Example"),
        ("summary", "Summary"),
    ],
    "5": [
        ("introduction", "Introduction"),
        ("definition", "Definition"),
        ("concepts", "Key Concepts"),
        ("examples", "Examples"),
        ("applications", "Applications"),
        ("summary", "Summary"),
    ],
    "10": [
        ("introduction", "Introduction"),
        ("background", "Background"),
        ("detailed_explanation", "Detailed Explanation"),
        ("examples", "Examples"),
        ("step_by_step", "Step-by-Step Process"),
        ("real_world_applications", "Real-World Applications"),
        ("quiz_questions", "Quiz Questions"),
        ("conclusion", "Conclusion"),
    ],
}

SECTION_BUILDERS = {}


def _register(section_key: str):
    def decorator(func):
        SECTION_BUILDERS[section_key] = func
        return func

    return decorator


def build_sections(topic: str, audience: str, duration: str) -> list[Section]:
    """Build ordered script sections for the requested duration."""
    blueprint = DURATION_BLUEPRINTS.get(duration, DURATION_BLUEPRINTS["3"])
    style = AUDIENCE_STYLE.get(audience, AUDIENCE_STYLE["school"])

    return [
        {
            "title": title,
            "content": SECTION_BUILDERS[section_key](topic, audience, style, duration),
        }
        for section_key, title in blueprint
    ]


@_register("introduction")
def _introduction(topic: str, audience: str, style: dict[str, str], duration: str) -> str:
    if duration == "1":
        return (
            f"Welcome to this quick lesson on {topic}. "
            f"In the next minute, you will learn what {topic} is and why it is important."
        )
    if duration == "10":
        return (
            f"Welcome to this full lecture on {topic}. "
            f"Over the next ten minutes, we will move from background knowledge to "
            f"advanced explanation, examples, applications, and review questions."
        )
    return (
        f"In this lesson, we focus on {topic}. "
        f"Our goal is to explain what {topic} means, why it matters, and how learners "
        f"can understand it using a {style['voice']} approach written in "
        f"{style['complexity']}."
    )


@_register("main_idea")
def _main_idea(topic: str, audience: str, style: dict[str, str], duration: str) -> str:
    if audience == "school":
        return (
            f"The central idea of {topic} is the one concept students should remember "
            f"after watching: how {topic} works in everyday learning situations. "
            f"Think of {topic} as the key that unlocks understanding of the wider subject."
        )
    if audience == "ug":
        return (
            f"The core principle behind {topic} connects foundational theory with "
            f"observable outcomes. At this level, {topic} should be understood as a "
            f"structured idea that explains patterns, causes, and effects within its field."
        )
    return (
        f"The principal thesis of {topic} involves interpreting underlying mechanisms, "
        f"theoretical frameworks, and evidence-based relationships that define advanced "
        f"study of the subject."
    )


@_register("explanation")
def _explanation(topic: str, audience: str, style: dict[str, str], duration: str) -> str:
    return (
        f"{topic} can be explained by breaking the subject into parts: what it is, "
        f"how it functions, and what outcomes it produces. "
        f"We describe {topic} with {style['complexity']} so viewers can follow each "
        f"stage without losing the overall picture."
    )


@_register("example")
def _example(topic: str, audience: str, style: dict[str, str], duration: str) -> str:
    return (
        f"To make {topic} concrete, consider a classroom scenario where a teacher "
        f"introduces {topic} with a visual diagram and a short demonstration. "
        f"The example shows how {topic} appears in practice and helps learners connect "
        f"theory to a real situation they can recall during revision."
    )


@_register("definition")
def _definition(topic: str, audience: str, style: dict[str, str], duration: str) -> str:
    return (
        f"{topic} refers to a defined area of knowledge with specific components, "
        f"rules, and outcomes. A precise definition of {topic} names its essential "
        f"elements and distinguishes it from related ideas that students often confuse."
    )


@_register("concepts")
def _concepts(topic: str, audience: str, style: dict[str, str], duration: str) -> str:
    return (
        f"Key concepts in {topic} include foundational terms, relationships between "
        f"ideas, and the conditions under which {topic} behaves differently. "
        f"Understanding these concepts allows learners to analyze new problems involving "
        f"{topic} instead of memorizing isolated facts."
    )


@_register("examples")
def _examples(topic: str, audience: str, style: dict[str, str], duration: str) -> str:
    return (
        f"Examples of {topic} appear in textbooks, lab activities, and daily life. "
        f"We walk through two cases: a basic illustration of {topic} for beginners, "
        f"and a slightly deeper case showing how {topic} changes when variables are "
        f"adjusted."
    )


@_register("applications")
def _applications(topic: str, audience: str, style: dict[str, str], duration: str) -> str:
    return (
        f"{topic} is applied in education, research, and professional settings where "
        f"specialists use it to solve problems and make decisions. "
        f"Recognizing these applications helps students see why studying {topic} is "
        f"valuable beyond examinations."
    )


@_register("background")
def _background(topic: str, audience: str, style: dict[str, str], duration: str) -> str:
    return (
        f"The background of {topic} includes the historical development, major "
        f"discoveries, and prior knowledge required to study it effectively. "
        f"Knowing where {topic} came from prepares learners for the detailed analysis "
        f"that follows in this lecture."
    )


@_register("detailed_explanation")
def _detailed_explanation(topic: str, audience: str, style: dict[str, str], duration: str) -> str:
    return (
        f"A detailed look at {topic} examines underlying mechanisms, supporting "
        f"evidence, and the logical sequence that experts use to explain results. "
        f"This section uses {style['complexity']} to build a complete understanding "
        f"of how and why {topic} operates."
    )


@_register("step_by_step")
def _step_by_step(topic: str, audience: str, style: dict[str, str], duration: str) -> str:
    return (
        f"Step 1: Identify the core question related to {topic}.\n"
        f"Step 2: Gather the facts, terms, and conditions relevant to {topic}.\n"
        f"Step 3: Apply the main rules or methods associated with {topic}.\n"
        f"Step 4: Evaluate the outcome and check whether the result fits expected "
        f"patterns in {topic}.\n"
        f"Step 5: Summarize what was learned and note common mistakes when working "
        f"with {topic}."
    )


@_register("real_world_applications")
def _real_world_applications(topic: str, audience: str, style: dict[str, str], duration: str) -> str:
    return (
        f"In real-world contexts, {topic} influences industry practices, public policy, "
        f"technology design, and scientific research. "
        f"Professionals rely on {topic} to improve efficiency, solve complex challenges, "
        f"and communicate findings to non-specialist audiences."
    )


@_register("quiz_questions")
def _quiz_questions(topic: str, audience: str, style: dict[str, str], duration: str) -> str:
    return (
        f"1. What is the primary purpose of studying {topic}?\n"
        f"2. Name two key components or ideas associated with {topic}.\n"
        f"3. How would you explain {topic} to a classmate in one sentence?\n"
        f"4. Give one example where {topic} is used in a real-world setting.\n"
        f"5. What is the most common misunderstanding students have about {topic}?"
    )


@_register("summary")
def _summary(topic: str, audience: str, style: dict[str, str], duration: str) -> str:
    if duration == "1":
        return (
            f"To recap, {topic} is the main concept covered in this short video. "
            f"Remember its purpose and how it fits into your lesson."
        )
    if duration == "3":
        return (
            f"In summary, {topic} was explained clearly and illustrated with a practical "
            f"example. Review the explanation and example to reinforce your understanding."
        )
    return (
        f"In summary, {topic} was defined, broken into key concepts, supported with "
        f"examples, and linked to real applications. Review each section before your "
        f"next class."
    )


@_register("conclusion")
def _conclusion(topic: str, audience: str, style: dict[str, str], duration: str) -> str:
    return (
        f"This lecture on {topic} covered background knowledge, detailed explanation, "
        f"worked examples, practical applications, and review questions. "
        f"Continue exploring {topic} through readings and practice to strengthen long-term "
        f"mastery."
    )
