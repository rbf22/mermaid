from __future__ import annotations

import math
from typing import Dict, List, Tuple

from py_mermaid.src.db import ColumnFrame, Edge, Node, Note, ColumnMeta
from py_mermaid.src.utils import label_to_lines

LAYOUT_MARGIN = 40.0
FONT_STACK = "Helvetica Neue, Arial, sans-serif"
COLUMN_BACKGROUND_COLORS = ["#fefaf3", "#f4f9ff", "#f4fff6"]
DEFAULT_EDGE_STYLE = {"stroke": "#7b7b7b", "stroke-width": "2", "marker-end": "url(#arrow)"}
NODE_TEXT_PADDING = 16.0
NODE_LINE_HEIGHT = 18.0
AVG_CHAR_WIDTH = 6.5
TEXT_WIDTH_SCALE = 1.1
COLUMN_INNER_PADDING = 14.0
BOX_CORNER_RADIUS = 0.0
NODE_COLUMN_INSET = 10.0
MIN_NODE_WIDTH = 150.0
MAX_NODE_WIDTH = 360.0

def _svg_escape(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )

class Renderer:
    def render(
        self,
        node_map: Dict[str, Node],
        edges: List[Edge],
        column_meta: List[ColumnMeta],
        styles: Dict[str, Dict[str, str]],
        notes: List[Note],
        direction: str,
    ) -> str:
        canvas_size, columns, margin = self._layout_nodes(node_map, column_meta, direction)
        self._layout_notes(notes, node_map, margin)
        return self._render_svg(node_map, edges, styles, canvas_size, columns, margin, notes)

    def _compute_node_box(self, node: Node) -> None:
        char_width = AVG_CHAR_WIDTH
        line_height = NODE_LINE_HEIGHT
        padding = NODE_TEXT_PADDING

        node.text_lines = label_to_lines(node.label)
        longest_line = max((len(line) for line in node.text_lines), default=1)
        text_width = longest_line * char_width * TEXT_WIDTH_SCALE
        node.width = max(MIN_NODE_WIDTH, min(MAX_NODE_WIDTH, text_width + 2 * padding))
        text_height = len(node.text_lines) * line_height
        node.height = max(60.0, text_height + 2 * padding)

    def _layout_nodes(
        self,
        node_map: Dict[str, Node],
        column_meta: List[ColumnMeta],
        direction: str,
        column_gap: float = 70.0,
        row_gap: float = 50.0,
        margin: float = LAYOUT_MARGIN,
    ) -> Tuple[Tuple[float, float], List[ColumnFrame], float]:
        columns = len(column_meta)
        for node in node_map.values():
            self._compute_node_box(node)

        column_widths = [0.0 for _ in range(max(columns, 1))]
        for node in node_map.values():
            index = min(node.column_index, len(column_widths) - 1)
            column_widths[index] = max(column_widths[index], node.width + NODE_COLUMN_INSET * 2)

        row_heights: Dict[int, float] = {}
        for node in node_map.values():
            row_heights[node.row_index] = max(row_heights.get(node.row_index, 0.0), node.height)

        col_positions: Dict[int, float] = {}
        current_x = margin
        for idx in range(columns):
            col_positions[idx] = current_x
            extra = column_gap if idx < columns - 1 else 0.0
            current_x += column_widths[idx] + extra

        row_positions: Dict[int, float] = {}
        sorted_rows = sorted(row_heights.keys())
        current_y = margin
        for idx, row in enumerate(sorted_rows):
            row_positions[row] = current_y
            extra = row_gap if idx < len(sorted_rows) - 1 else 0.0
            current_y += row_heights[row] + extra

        for node in node_map.values():
            col_x = col_positions.get(node.column_index, margin)
            row_y = row_positions.get(node.row_index, margin)
            col_width = column_widths[node.column_index] if column_widths else node.width
            row_height = row_heights.get(node.row_index, node.height)
            inner_width = max(col_width - NODE_COLUMN_INSET * 2, 0.0)
            node.x = col_x + NODE_COLUMN_INSET + max((inner_width - node.width) / 2.0, 0.0)
            node.y = row_y + (row_height - node.height) / 2.0

        total_width = sum(column_widths[:columns]) + column_gap * max(columns - 1, 0) + 2 * margin
        total_height = (
            sum(row_heights[row] for row in sorted_rows)
            + row_gap * max(len(sorted_rows) - 1, 0)
            + 2 * margin
        )
        column_frames: List[ColumnFrame] = []
        for idx, meta in enumerate(column_meta):
            column_frames.append(
                ColumnFrame(
                    identifier=meta.key,
                    label=meta.label,
                    x=col_positions.get(idx, margin),
                    width=column_widths[idx] if columns else column_widths[0],
                )
            )

        if direction in {"RL", "BT"}:
            for node in node_map.values():
                if direction == "RL":
                    node.x = total_width - node.x - node.width
                if direction == "BT":
                    node.y = total_height - node.y - node.height
            for column in column_frames:
                if direction == "RL":
                    column.x = total_width - column.x - column.width

        return (math.ceil(total_width), math.ceil(total_height)), column_frames, margin

    def _compute_note_box(self, note: Note) -> None:
        char_width = 6.0
        line_height = 16
        padding = 10
        longest = max((len(line) for line in note.text_lines), default=1)
        text_width = longest * char_width
        note.width = max(120.0, min(240.0, text_width + 2 * padding))
        text_height = len(note.text_lines) * line_height
        note.height = max(48.0, text_height + 2 * padding)

    def _layout_notes(self, notes: List[Note], node_map: Dict[str, Node], margin: float) -> None:
        gap = 24.0
        for note in notes:
            self._compute_note_box(note)
            anchor = node_map.get(note.anchor)
            if not anchor:
                continue
            if note.position == "left":
                note.x = anchor.x - gap - note.width
                note.y = anchor.y + anchor.height / 2 - note.height / 2
            elif note.position == "right":
                note.x = anchor.x + anchor.width + gap
                note.y = anchor.y + anchor.height / 2 - note.height / 2
            elif note.position == "top":
                note.x = anchor.x + anchor.width / 2 - note.width / 2
                note.y = max(margin / 2, anchor.y - gap - note.height)
            else:  # bottom
                note.x = anchor.x + anchor.width / 2 - note.width / 2
                note.y = anchor.y + anchor.height + gap

    def _render_svg(
        self,
        node_map: Dict[str, Node],
        edges: List[Edge],
        styles: Dict[str, Dict[str, str]],
        canvas_size: Tuple[float, float],
        columns: List[ColumnFrame],
        margin: float,
        notes: List[Note],
    ) -> str:
        width, height = canvas_size
        lines: List[str] = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
            '<defs>',
            '<marker id="arrow" viewBox="0 0 10 10" refX="10" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">',
            '<path d="M 0 0 L 10 5 L 0 10 z" fill="#7b7b7b" />',
            '</marker>',
            '<filter id="shadow" x="-20%" y="-20%" width="160%" height="160%">',
            '<feDropShadow dx="0" dy="2" stdDeviation="3" flood-color="#000" flood-opacity="0.15"/>',
            '</filter>',
            '</defs>',
        ]

        bg_y = margin * 0.75
        bg_height = max(height - (margin * 1.5), 0)
        header_y = margin / 2
        for idx, column in enumerate(columns):
            bg_color = COLUMN_BACKGROUND_COLORS[idx % len(COLUMN_BACKGROUND_COLORS)]
            rect_x = column.x - COLUMN_INNER_PADDING / 2
            rect_width = column.width + COLUMN_INNER_PADDING
            lines.append(
                f'<rect x="{rect_x:.2f}" y="{bg_y:.2f}" width="{rect_width:.2f}" height="{bg_height:.2f}" '
                f'rx="0" ry="0" fill="{bg_color}" opacity="0.55"/>'
            )
            lines.append(
                f'<text x="{column.x + column.width / 2:.2f}" y="{header_y:.2f}" fill="#2c2c2c" '
                f'font-size="16" font-weight="600" text-anchor="middle" font-family="{FONT_STACK}">'
                f'{_svg_escape(column.label)}</text>'
            )

        for edge in edges:
            source = node_map.get(edge.source)
            target = node_map.get(edge.target)
            if not source or not target:
                continue
            sx, sy = source.center()
            tx, ty = target.center()
            style = {**DEFAULT_EDGE_STYLE, **edge.style}
            style_attr = " ".join(f'{key}="{value}"' for key, value in style.items())
            lines.append(f'<line x1="{sx:.2f}" y1="{sy:.2f}" x2="{tx:.2f}" y2="{ty:.2f}" {style_attr} />')
            if edge.label:
                label_x = (sx + tx) / 2
                label_y = (sy + ty) / 2 - 8
                lines.append(
                    f'<text x="{label_x:.2f}" y="{label_y:.2f}" fill="#454545" font-size="12" '
                    f'text-anchor="middle" font-family="{FONT_STACK}">{_svg_escape(edge.label)}</text>'
                )

        for node in node_map.values():
            style = styles.get(node.class_name, {})
            fill = style.get("fill", "#ffffff")
            stroke = style.get("stroke", "#666666")
            text_color = style.get("color", "#1f1f1f")
            radius = BOX_CORNER_RADIUS
            lines.append(
                f'<rect x="{node.x:.2f}" y="{node.y:.2f}" width="{node.width:.2f}" height="{node.height:.2f}" '
                f'rx="{radius}" ry="{radius}" fill="{fill}" stroke="{stroke}" stroke-width="2" filter="url(#shadow)"/>'
            )
            text_y = node.y + node.height / 2 - (len(node.text_lines) - 1) * 9
            for idx, text_line in enumerate(node.text_lines):
                lines.append(
                    f'<text x="{node.x + node.width / 2:.2f}" y="{text_y + idx * 18:.2f}" '
                    f'fill="{text_color}" font-size="14" text-anchor="middle" dominant-baseline="middle" '
                    f'font-family="{FONT_STACK}">{_svg_escape(text_line)}</text>'
                )

        for note in notes:
            anchor = node_map.get(note.anchor)
            if not anchor:
                continue
            lines.append(
                f'<rect x="{note.x:.2f}" y="{note.y:.2f}" width="{note.width:.2f}" height="{note.height:.2f}" '
                f'rx="10" ry="10" fill="#fffceb" stroke="#cba135" stroke-dasharray="5 3"/>'
            )
            note_text_y = note.y + note.height / 2 - (len(note.text_lines) - 1) * 8
            for idx, text_line in enumerate(note.text_lines):
                lines.append(
                    f'<text x="{note.x + note.width / 2:.2f}" y="{note_text_y + idx * 16:.2f}" '
                    f'fill="#4b3800" font-size="12" text-anchor="middle" dominant-baseline="middle" '
                    f'font-family="{FONT_STACK}">{_svg_escape(text_line)}</text>'
                )
            sx, sy = anchor.center()
            nx = note.x + note.width / 2
            ny = note.y + note.height / 2
            lines.append(
                f'<line x1="{sx:.2f}" y1="{sy:.2f}" x2="{nx:.2f}" y2="{ny:.2f}" stroke="#cba135" stroke-dasharray="4 3"/>'
            )

        lines.append("</svg>")
        return "\n".join(lines) + "\n"
