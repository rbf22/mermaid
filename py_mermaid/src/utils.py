from typing import List

MAX_LINE_CHARACTERS = 32

def wrap_segment(text: str) -> List[str]:
    stripped = text.strip()
    if not stripped:
        return [" "]
    lines: List[str] = []
    current = ""
    for word in stripped.split():
        if len(word) >= MAX_LINE_CHARACTERS:
            if current:
                lines.append(current)
                current = ""
            start = 0
            while start < len(word):
                lines.append(word[start : start + MAX_LINE_CHARACTERS])
                start += MAX_LINE_CHARACTERS
            continue
        candidate = f"{current} {word}".strip() if current else word
        if len(candidate) <= MAX_LINE_CHARACTERS:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines or [" "]


def label_to_lines(label: str) -> List[str]:
    html_breaks = label.replace("<br/>", "\n").replace("<br>", "\n")
    raw_segments = html_breaks.splitlines()
    lines: List[str] = []
    for segment in raw_segments:
        lines.extend(wrap_segment(segment))
    return lines or [" "]
