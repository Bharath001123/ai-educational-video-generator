"""Convert duration-based script sections into structured video scenes.

Replace visual/voiceover generation with LLM output when integrating AI.
"""

from __future__ import annotations

import re

Section = dict[str, str]
Scene = dict[str, int | str]

SCENE_TARGETS: dict[str, int] = {
    "1": 6,
    "3": 11,
    "5": 18,
    "10": 30,
}

DURATION_SECONDS: dict[str, int] = {
    "1": 60,
    "3": 180,
    "5": 300,
    "10": 600,
}

VISUAL_STYLES: dict[str, list[str]] = {
    "1": [
        "bold cinematic hook",
        "dynamic title card",
        "focused concept diagram",
        "quick visual example",
        "highlighted key takeaway",
        "closing summary card",
    ],
    "3": [
        "story opening frame",
        "curiosity-building visual",
        "concept introduction slide",
        "process diagram",
        "classroom example scene",
        "comparison graphic",
        "step highlight",
        "memory anchor visual",
        "story continuation",
        "reinforcement graphic",
        "summary storyboard",
    ],
    "5": [
        "lesson title intro",
        "learning objective slide",
        "formal definition card",
        "concept map",
        "concept detail zoom",
        "labeled diagram",
        "worked example scene",
        "second example variation",
        "application case study",
        "industry use-case visual",
        "data or chart graphic",
        "teacher pointer overlay",
        "student engagement scene",
        "concept recap board",
        "application recap",
        "practice prompt slide",
        "key terms list",
        "final summary scene",
    ],
    "10": [
        "documentary opening aerial",
        "historical archive visual",
        "expert interview frame",
        "timeline graphic",
        "chapter title card",
        "detailed mechanism diagram",
        "animated process flow",
        "micro-detail zoom",
        "annotated illustration",
        "lab demonstration scene",
        "field footage style frame",
        "case study montage",
        "data visualization",
        "step 1 walkthrough",
        "step 2 walkthrough",
        "step 3 walkthrough",
        "step 4 walkthrough",
        "step 5 walkthrough",
        "real-world deployment scene",
        "community impact visual",
        "industry application montage",
        "future implications graphic",
        "quiz question slide",
        "quiz answer reveal",
        "review question 2",
        "review question 3",
        "expert summary frame",
        "documentary b-roll",
        "closing montage",
        "final documentary outro",
    ],
}


def sections_to_scenes(
    topic: str,
    audience: str,
    duration: str,
    sections: list[Section],
) -> list[Scene]:
    """Transform script sections into a paced list of video scenes."""
    scene_count = SCENE_TARGETS.get(duration, SCENE_TARGETS["3"])
    total_seconds = DURATION_SECONDS.get(duration, DURATION_SECONDS["3"])
    visual_styles = _visual_styles_for_duration(duration, scene_count)

    voiceovers = _distribute_voiceovers(sections, scene_count, topic, duration)
    durations = _allocate_scene_durations(total_seconds, scene_count, duration)

    scenes: list[Scene] = []
    for index in range(scene_count):
        scene_number = index + 1
        section = _section_for_scene_index(sections, index, scene_count)
        style_hint = visual_styles[index]

        scenes.append(
            {
                "scene_number": scene_number,
                "duration_seconds": durations[index],
                "visual_prompt": _build_visual_prompt(
                    topic=topic,
                    audience=audience,
                    duration=duration,
                    section_title=section["title"],
                    style_hint=style_hint,
                    scene_number=scene_number,
                ),
                "voiceover": voiceovers[index],
            }
        )

    return scenes


def _visual_styles_for_duration(duration: str, scene_count: int) -> list[str]:
    styles = VISUAL_STYLES.get(duration, VISUAL_STYLES["3"])
    if len(styles) >= scene_count:
        return styles[:scene_count]

    extended = list(styles)
    while len(extended) < scene_count:
        extended.append(f"supporting educational visual {len(extended) + 1}")
    return extended


def _distribute_voiceovers(
    sections: list[Section],
    scene_count: int,
    topic: str,
    duration: str,
) -> list[str]:
    chunks = _extract_voiceover_chunks(sections)

    if not chunks:
        return [f"This scene introduces {topic}." for _ in range(scene_count)]

    if len(chunks) >= scene_count:
        return _merge_chunks_evenly(chunks, scene_count)

    expanded: list[str] = []
    for chunk in chunks:
        sentences = _split_sentences(chunk)
        expanded.extend(sentences if sentences else [chunk])

    if len(expanded) < scene_count:
        expanded.extend(
            _generate_support_voiceovers(topic, duration, scene_count - len(expanded))
        )

    return _merge_chunks_evenly(expanded[: scene_count * 2], scene_count)


def _extract_voiceover_chunks(sections: list[Section]) -> list[str]:
    chunks: list[str] = []
    for section in sections:
        content = section["content"].strip()
        if not content:
            continue

        if "\n" in content:
            parts = [part.strip() for part in re.split(r"\n+", content) if part.strip()]
            chunks.extend(parts)
        else:
            chunks.extend(_split_sentences(content) or [content])
    return chunks


def _split_sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return [part.strip() for part in parts if part.strip()]


def _merge_chunks_evenly(chunks: list[str], scene_count: int) -> list[str]:
    if scene_count <= 0:
        return []

    grouped: list[list[str]] = [[] for _ in range(scene_count)]
    for index, chunk in enumerate(chunks):
        grouped[index % scene_count].append(chunk)

    return [
        " ".join(group).strip() if group else "Transition to the next learning point."
        for group in grouped
    ]


def _generate_support_voiceovers(topic: str, duration: str, count: int) -> list[str]:
    templates = {
        "1": [
            f"Here is the essential idea behind {topic}.",
            f"Remember this key point about {topic}.",
        ],
        "3": [
            f"Let's connect this part of {topic} to what we just learned.",
            f"This moment shows why {topic} matters in practice.",
        ],
        "5": [
            f"Notice how this detail strengthens your understanding of {topic}.",
            f"This example helps clarify an important part of {topic}.",
        ],
        "10": [
            f"This segment adds historical and practical context to {topic}.",
            f"Observe how each step builds a complete picture of {topic}.",
        ],
    }
    pool = templates.get(duration, templates["3"])
    return [pool[index % len(pool)] for index in range(count)]


def _allocate_scene_durations(
    total_seconds: int,
    scene_count: int,
    duration: str,
) -> list[int]:
    if scene_count <= 0:
        return []

    base = total_seconds // scene_count
    remainder = total_seconds % scene_count
    durations = [base] * scene_count

    if duration == "1" and scene_count > 0:
        durations[0] = max(6, base - 2)
        durations[-1] = max(6, base - 1)
        durations[1] = base + 1

    for index in range(remainder):
        durations[index % scene_count] += 1

    total_allocated = sum(durations)
    if total_allocated != total_seconds:
        durations[-1] += total_seconds - total_allocated

    return durations


def _section_for_scene_index(
    sections: list[Section],
    scene_index: int,
    scene_count: int,
) -> Section:
    if not sections:
        return {"title": "Scene", "content": ""}

    section_index = (scene_index * len(sections)) // scene_count
    return sections[min(section_index, len(sections) - 1)]


def _build_visual_prompt(
    topic: str,
    audience: str,
    duration: str,
    section_title: str,
    style_hint: str,
    scene_number: int,
) -> str:
    audience_note = {
        "school": "school-friendly educational style",
        "ug": "undergraduate lecture style",
        "pg": "advanced academic documentary style",
    }.get(audience, "educational style")

    pacing_note = {
        "1": "fast-paced short-form video",
        "3": "story-driven educational video",
        "5": "detailed classroom lesson",
        "10": "documentary-style educational film",
    }.get(duration, "educational video")

    return (
        f"{style_hint} for {topic} — {section_title}. "
        f"Scene {scene_number}, {audience_note}, {pacing_note}, "
        f"clean modern AI video aesthetic, high clarity, no text clutter."
    )


def format_scenes_as_script(title: str, duration: str, scenes: list[Scene]) -> str:
    """Render scene voiceovers as a readable script string for the frontend."""
    lines = [
        f"# {title}",
        "",
        f"Duration: {duration}",
        f"Scenes: {len(scenes)}",
        "",
    ]

    for scene in scenes:
        lines.extend(
            [
                f"## Scene {scene['scene_number']} ({scene['duration_seconds']}s)",
                f"Visual: {scene['visual_prompt']}",
                f"Voiceover: {scene['voiceover']}",
                "",
            ]
        )

    return "\n".join(lines).strip()
