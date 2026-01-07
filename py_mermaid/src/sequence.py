from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


@dataclass
class Participant:
    name: str
    label: str
    width: float = 140.0
    x: float = 0.0


@dataclass
class Message:
    sender: str
    receiver: str
    text: str
    row_index: int
    dashed: bool = False
    double_head: bool = False
    async_arrow: bool = False


@dataclass
class Note:
    start_index: int
    end_index: int
    text_lines: List[str]
    row_index: int
    width: float = 0.0
    height: float = 0.0
    x: float = 0.0
    y: float = 0.0


@dataclass
class Activation:
    participant: str
    start_row: int
    end_row: int


@dataclass
class FragmentSection:
    label: str
    start_row: int
    end_row: int


@dataclass
class Fragment:
    kind: str
    label: str
    sections: List[FragmentSection]
    start_row: int
    end_row: int


class SequenceParser:
    def parse(self, text: str):
        lines = self._normalize_lines(text)
        return self._parse_sequence(lines)

    def _normalize_lines(self, text: str) -> List[str]:
        lines: List[str] = []
        inside_code_block = False
        for raw in text.splitlines():
            stripped = raw.strip()
            if stripped.startswith("```"):
                inside_code_block = not inside_code_block
                continue
            if not stripped:
                continue
            lines.append(stripped)
        return lines

    def _parse_style_line(self, line: str, style: Dict[str, str]) -> None:
        _, _, rest = line.partition(" ")
        for token in rest.split():
            if "=" in token:
                key, value = token.split("=", 1)
                style[key.strip()] = value.strip()

    def _parse_sequence(self, lines: List[str]):
        participants: Dict[str, Participant] = {}
        order: List[str] = []
        messages: List[Message] = []
        notes: List[Note] = []
        activations: List[Activation] = []
        fragments: List[Fragment] = []
        style_overrides: Dict[str, str] = {}
        row_index = 0
        activation_stack: Dict[str, List[int]] = {}
        fragment_stack: List[Dict[str, any]] = []

        def ensure_participant(token: str, label: Optional[str] = None):
            if token not in participants:
                display = label or token
                participants[token] = Participant(name=token, label=display)
                order.append(token)
            else:
                if label:
                    participants[token].label = label

        for line in lines:
            if line.startswith("%%"):
                if line.startswith("%% style"):
                    self._parse_style_line(line, style_overrides)
                continue

            if line.startswith("sequenceDiagram"):
                continue

            if line.startswith(("participant ", "actor ")):
                _, rest = line.split(None, 1)
                if " as " in rest:
                    name, label = rest.split(" as ", 1)
                else:
                    name, label = rest, None
                ensure_participant(name.strip(), label.strip() if label else None)
                continue

            if line.startswith("Note over"):
                prefix, text = line.split(":", 1)
                _, _, span = prefix.partition("over")
                span = span.strip()
                if "," in span:
                    left, right = (token.strip() for token in span.split(",", 1))
                else:
                    left = right = span
                ensure_participant(left)
                ensure_participant(right)
                note = Note(
                    start_index=min(order.index(left), order.index(right)),
                    end_index=max(order.index(left), order.index(right)),
                    text_lines=[segment.strip() for segment in text.strip().split("\\n")],
                    row_index=row_index,
                )
                notes.append(note)
                row_index += 1
                continue

            if line.startswith("activate "):
                name = line[len("activate ") :].strip()
                ensure_participant(name)
                activation_stack.setdefault(name, []).append(row_index)
                continue

            if line.startswith("deactivate "):
                name = line[len("deactivate ") :].strip()
                ensure_participant(name)
                stack = activation_stack.get(name)
                if stack:
                    start = stack.pop()
                    activations.append(Activation(participant=name, start_row=start, end_row=row_index))
                continue

            if any(line.startswith(keyword) for keyword in ("alt", "opt", "loop", "par", "rect")):
                parts = line.split(None, 1)
                kind = parts[0]
                label = parts[1] if len(parts) > 1 else kind.title()
                fragment_stack.append(
                    {
                        "kind": kind,
                        "label": label,
                        "start_row": row_index,
                        "sections": [FragmentSection(label=label, start_row=row_index, end_row=row_index)],
                    }
                )
                continue

            if line.startswith(("else", "and")) and fragment_stack:
                parts = line.split(None, 1)
                label = parts[1] if len(parts) > 1 else parts[0].title()
                frag = fragment_stack[-1]
                frag["sections"][-1].end_row = row_index
                frag["sections"].append(FragmentSection(label=label, start_row=row_index, end_row=row_index))
                continue

            if line == "end" and fragment_stack:
                frag_info = fragment_stack.pop()
                frag_info["sections"][-1].end_row = row_index
                fragments.append(
                    Fragment(
                        kind=frag_info["kind"],
                        label=frag_info["label"],
                        sections=frag_info["sections"],
                        start_row=frag_info["start_row"],
                        end_row=row_index,
                    )
                )
                continue

            if ":" in line and ("->" in line or "--" in line):
                head, text = line.split(":", 1)
                text = text.strip()
                arrow = None
                for candidate in ("-->>", "->>", "-->", "->", "--", "-x", "--x"):
                    if candidate in head:
                        arrow = candidate
                        left, right = head.split(candidate, 1)
                        break
                if not arrow:
                    continue
                sender = left.strip()
                receiver = right.strip()
                ensure_participant(sender)
                ensure_participant(receiver)
                dashed = arrow.startswith("--")
                double_head = arrow.endswith(">>")
                async_arrow = arrow in ("->>", "-->>", "-x", "--x")
                messages.append(
                    Message(
                        sender=sender,
                        receiver=receiver,
                        text=text,
                        row_index=row_index,
                        dashed=dashed,
                        double_head=double_head,
                        async_arrow=async_arrow,
                    )
                )
                row_index += 1
                continue

            tokens = [segment for segment in line.replace(",", " ").split() if segment]
            for token in tokens:
                if token.isidentifier():
                    ensure_participant(token)

        for name, stack in activation_stack.items():
            while stack:
                start = stack.pop()
                activations.append(Activation(participant=name, start_row=start, end_row=row_index))

        return (
            [participants[name] for name in order],
            messages,
            notes,
            activations,
            fragments,
            style_overrides,
        )


MARGIN = 60.0
COLUMN_GAP = 80.0
HEADER_HEIGHT = 50.0
MESSAGE_GAP = 80.0
MESSAGE_BASELINE = HEADER_HEIGHT + 80.0
NOTE_BASELINE = HEADER_HEIGHT + 60.0
LIFELINE_TOP = HEADER_HEIGHT + 28.0
LIFELINE_EXTRA = 180.0
FONT_FAMILY = "Helvetica Neue, Arial, sans-serif"
NOTE_PADDING = 14.0
NOTE_LINE_HEIGHT = 16.0
ACTIVATION_WIDTH = 16.0

DEFAULT_STYLE = {
    "participantFill": "#ffffff",
    "participantStroke": "#4b5563",
    "participantText": "#111827",
    "lifeline": "#94a3b8",
    "message": "#2c3e50",
    "activation": "#dbeafe",
    "activationStroke": "#2563eb",
    "noteFill": "#fffbea",
    "noteStroke": "#f6ad55",
    "noteText": "#7c3415",
    "fragmentStroke": "#475569",
    "fragmentFill": "#f8fafc",
}

class SequenceRenderer:
    def render(
        self,
        participants: List[Participant],
        messages: List[Message],
        notes: List[Note],
        activations: List[Activation],
        fragments: List[Fragment],
        style_overrides: Dict[str, str],
    ) -> str:
        canvas = self._compute_layout(participants, messages, notes)
        style = {**DEFAULT_STYLE, **style_overrides}
        return self._render_svg(participants, messages, notes, activations, fragments, canvas, style)

    def _estimate_width(self, label: str) -> float:
        return max(140.0, len(label) * 7 + 40)

    def _compute_layout(
        self,
        participants: List[Participant],
        messages: List[Message],
        notes: List[Note],
    ) -> Tuple[float, float]:
        current_x = MARGIN
        for participant in participants:
            participant.width = self._estimate_width(participant.label)
            participant.x = current_x + participant.width / 2
            current_x += participant.width + COLUMN_GAP

        if participants:
            min_left = min(p.x - p.width / 2 for p in participants)
            if min_left < MARGIN / 2:
                shift = (MARGIN / 2) - min_left
                for participant in participants:
                    participant.x += shift
            min_left = min(p.x - p.width / 2 for p in participants)
            max_right = max(p.x + p.width / 2 for p in participants)
        else:
            min_left = MARGIN / 2
            max_right = MARGIN

        total_rows = 1 + max(
            [msg.row_index for msg in messages]
            + [note.row_index for note in notes]
            if messages or notes
            else [0]
        )
        body_height = MESSAGE_BASELINE + total_rows * MESSAGE_GAP + LIFELINE_EXTRA
        width = max(max_right + MARGIN / 2, (MARGIN * 2 + 200))

        for note in notes:
            width_span = sum(p.width for p in participants[note.start_index : note.end_index + 1]) + (
                note.end_index - note.start_index
            ) * COLUMN_GAP
            note.width = max(200.0, width_span - 40)
            note.height = max(48.0, len(note.text_lines) * NOTE_LINE_HEIGHT + 2 * NOTE_PADDING)
            start_x = participants[note.start_index].x - participants[note.start_index].width / 2
            note.x = start_x + (width_span - note.width) / 2
            note.x = max(MARGIN / 2, note.x)
            note.y = NOTE_BASELINE + note.row_index * MESSAGE_GAP
            width = max(width, note.x + note.width + MARGIN / 2)
            body_height = max(body_height, note.y + note.height + MARGIN / 2)

        return width, body_height

    def _svg_escape(self, value: str) -> str:
        return (
            value.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&apos;")
        )

    def _message_y(self, row_index: int) -> float:
        return MESSAGE_BASELINE + row_index * MESSAGE_GAP

    def _render_self_message(self, x: float, y: float, text: str, async_arrow: bool, dashed: bool, style: Dict[str, str]):
        curve_height = 40.0
        dx = 80.0
        marker = "arrowhead"
        dash_attr = 'stroke-dasharray="6 4"' if dashed else ""
        return [
            f'<path d="M {x:.2f} {y:.2f} C {x + dx:.2f} {y - curve_height:.2f}, {x + dx:.2f} {y + curve_height:.2f}, {x:.2f} {y + curve_height:.2f}" '
            f'stroke="{style["message"]}" stroke-width="2" fill="none" {dash_attr} marker-end="url(#{marker})"/>',
            f'<text x="{x + dx/2:.2f}" y="{y - 14:.2f}" text-anchor="middle" font-size="13" font-family="{FONT_FAMILY}" fill="{style["message"]}">{self._svg_escape(text)}</text>',
        ]

    def _render_fragments(
        self,
        participants: List[Participant],
        fragments: List[Fragment],
        canvas_height: float,
        style: Dict[str, str],
    ) -> List[str]:
        lines: List[str] = []
        total_width = (
            participants[-1].x
            + participants[-1].width / 2
            - (participants[0].x - participants[0].width / 2)
        )
        left = participants[0].x - participants[0].width / 2
        for fragment in fragments:
            top = self._message_y(fragment.start_row) - MESSAGE_GAP / 2
            bottom = self._message_y(fragment.end_row) + MESSAGE_GAP / 2
            height = bottom - top
            lines.append(
                f'<rect x="{left:.2f}" y="{top:.2f}" width="{total_width:.2f}" height="{height:.2f}" '
                f'stroke="{style["fragmentStroke"]}" fill="{style["fragmentFill"]}" opacity="0.6" stroke-dasharray="8 6"/>'
            )
            lines.append(
                f'<text x="{left + 12:.2f}" y="{top + 20:.2f}" font-size="13" font-weight="600" font-family="{FONT_FAMILY}" fill="{style["fragmentStroke"]}">{self._svg_escape(fragment.kind.upper())}: {self._svg_escape(fragment.label)}</text>'
            )
            section_top = top
            for section in fragment.sections:
                section_bottom = self._message_y(section.end_row)
                lines.append(
                    f'<text x="{left + 20:.2f}" y="{section_top + 40:.2f}" font-size="12" font-family="{FONT_FAMILY}" fill="{style["fragmentStroke"]}">{self._svg_escape(section.label)}</text>'
                )
                section_top = section_bottom
        return lines

    def _render_svg(
        self,
        participants: List[Participant],
        messages: List[Message],
        notes: List[Note],
        activations: List[Activation],
        fragments: List[Fragment],
        canvas: Tuple[float, float],
        style: Dict[str, str],
    ) -> str:
        width, height = canvas
        lines: List[str] = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{math.ceil(width)}" height="{math.ceil(height)}" viewBox="0 0 {math.ceil(width)} {math.ceil(height)}">',
            "<defs>",
            '<marker id="arrowhead" viewBox="0 0 10 10" refX="10" refY="5" markerWidth="6" markerHeight="6" orient="auto">',
            f'<path d="M 0 0 L 10 5 L 0 10 z" fill="{style["message"]}" />',
            "</marker>",
            '<marker id="doublehead" viewBox="0 0 10 10" refX="10" refY="5" markerWidth="8" markerHeight="8" orient="auto">',
            f'<path d="M 0 0 L 10 5 L 0 10 z" fill="none" stroke="{style["message"]}" stroke-width="2"/>',
            "</marker>",
            "</defs>",
        ]

        for participant in participants:
            x = participant.x
            header_y = MARGIN / 2
            lines.append(
                f'<line x1="{x:.2f}" y1="{LIFELINE_TOP:.2f}" x2="{x:.2f}" y2="{height - MARGIN / 2:.2f}" '
                f'stroke="{style["lifeline"]}" stroke-width="2" stroke-dasharray="6 4"/>'
            )
            lines.append(
                f'<rect x="{x - participant.width/2:.2f}" y="{header_y:.2f}" width="{participant.width:.2f}" height="{HEADER_HEIGHT:.2f}" '
                f'stroke="{style["participantStroke"]}" fill="{style["participantFill"]}" stroke-width="2"/>'
            )
            lines.append(
                f'<text x="{x:.2f}" y="{header_y + HEADER_HEIGHT/2:.2f}" text-anchor="middle" '
                f'font-size="14" font-family="{FONT_FAMILY}" fill="{style["participantText"]}" dominant-baseline="middle">{self._svg_escape(participant.label)}</text>'
            )

        for activation in activations:
            participant = next((p for p in participants if p.name == activation.participant), None)
            if not participant:
                continue
            start_y = self._message_y(activation.start_row) - MESSAGE_GAP / 2 + 10
            end_y = self._message_y(activation.end_row) + MESSAGE_GAP / 2 - 10
            lines.append(
                f'<rect x="{participant.x - ACTIVATION_WIDTH/2:.2f}" y="{start_y:.2f}" width="{ACTIVATION_WIDTH:.2f}" height="{max(20.0, end_y - start_y):.2f}" '
                f'fill="{style["activation"]}" stroke="{style["activationStroke"]}" stroke-width="1.5" opacity="0.85"/>'
            )

        lines.extend(self._render_fragments(participants, fragments, height, style))

        for message in messages:
            sender = next((p for p in participants if p.name == message.sender), None)
            receiver = next((p for p in participants if p.name == message.receiver), None)
            if not sender or not receiver:
                continue
            y = self._message_y(message.row_index)
            x1 = sender.x
            x2 = receiver.x
            dash_attr = 'stroke-dasharray="6 4"' if message.dashed else ""
            marker = "doublehead" if message.double_head else "arrowhead"
            if sender.name == receiver.name:
                lines.extend(self._render_self_message(x1, y, message.text, message.async_arrow, message.dashed, style))
                continue
            lines.append(
                f'<line x1="{x1:.2f}" y1="{y:.2f}" x2="{x2:.2f}" y2="{y:.2f}" stroke="{style["message"]}" stroke-width="2" {dash_attr} marker-end="url(#{marker})"/>'
            )
            label_x = (x1 + x2) / 2
            lines.append(
                f'<text x="{label_x:.2f}" y="{y - 12:.2f}" text-anchor="middle" font-size="13" font-family="{FONT_FAMILY}" fill="{style["message"]}">{self._svg_escape(message.text)}</text>'
            )

        for note in notes:
            lines.append(
                f'<rect x="{note.x:.2f}" y="{note.y:.2f}" width="{note.width:.2f}" height="{note.height:.2f}" '
                f'rx="8" ry="8" fill="{style["noteFill"]}" stroke="{style["noteStroke"]}" stroke-width="2"/>'
            )
            for idx, text_line in enumerate(note.text_lines):
                lines.append(
                    f'<text x="{note.x + note.width/2:.2f}" y="{note.y + NOTE_PADDING + idx * NOTE_LINE_HEIGHT + NOTE_LINE_HEIGHT/2:.2f}" '
                    f'text-anchor="middle" font-size="12" font-family="{FONT_FAMILY}" fill="{style["noteText"]}" dominant-baseline="middle">{self._svg_escape(text_line)}</text>'
                )

        lines.append("</svg>")
        return "\n".join(lines) + "\n"
