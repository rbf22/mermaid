from __future__ import annotations

import re
from typing import Dict, List, Optional, Tuple

from py_mermaid.src.db import ColumnMeta, Edge, Node, Note
from py_mermaid.src.utils import label_to_lines

DEFAULT_STYLES = {
    "header": {"fill": "#ffffff", "stroke": "#9aa2b1", "color": "#1f2530"},
    "org": {"fill": "#f9f5d7", "stroke": "#c8b46f", "color": "#3a2e0f"},
    "capability": {"fill": "#e6f4ff", "stroke": "#5a8bb5", "color": "#0f2a3a"},
    "infra": {"fill": "#f2f2f2", "stroke": "#8d8d8d", "color": "#1f1f1f"},
}

ROW_PRIORITY = ["header", "org", "capability", "infra"]
DASHED_EDGE_STYLE = {"stroke-dasharray": "6 4", "marker-end": "none"}
FLOW_DIRECTIONS = {"TB", "BT", "LR", "RL"}
EDGE_SPLIT = re.compile(r"(-->|---)")
NOTE_PATTERN = re.compile(r"note\s+(left|right|top|bottom)\s+of\s+([A-Za-z0-9_]+)\s*:\s*(.+)", re.IGNORECASE)


class Parser:
    def parse(self, text: str):
        direction = "TB"
        lines = self._normalize_lines(text)
        class_styles: Dict[str, Dict[str, str]] = {**DEFAULT_STYLES}
        node_map: Dict[str, Node] = {}
        edges: List[Edge] = []
        current_subgraph: Optional[str] = None
        pending_classes: Dict[str, str] = {}
        node_sequence: List[str] = []
        link_styles: List[Tuple[List[int], Dict[str, str]]] = []
        notes: List[Note] = []

        for raw_line in lines:
            line = raw_line.strip()
            if not line:
                continue
            if line.startswith("flowchart"):
                parts = line.split()
                if len(parts) > 1 and parts[1] in FLOW_DIRECTIONS:
                    direction = parts[1]
                continue

            if line.startswith("classDef"):
                _, rest = line.split("classDef", 1)
                parts = rest.strip().split(None, 1)
                if len(parts) == 2:
                    class_name, attributes = parts
                    attributes = attributes.rstrip(";")
                    class_styles[class_name] = self._parse_style_attributes(attributes)
                continue

            if line.startswith("subgraph"):
                remainder = line.split(None, 1)[1]
                if "[" in remainder and remainder.endswith("]"):
                    graph_id, _ = remainder.split("[", 1)
                    current_subgraph = graph_id.strip()
                else:
                    current_subgraph = remainder.strip()
                continue

            if line == "end":
                current_subgraph = None
                continue

            if line.startswith("class "):
                body = line[len("class ") :].strip().rstrip(";")
                if " " in body:
                    node_tokens, class_name = body.split(None, 1)
                    class_name = class_name.strip()
                    for node_id in (token.strip() for token in node_tokens.split(",")):
                        if node_id:
                            pending_classes[node_id] = class_name
                continue

            if line.startswith("linkStyle"):
                link_styles.append(self._parse_link_style(line))
                continue

            if line.startswith("note "):
                note = self._parse_note_line(line)
                if note:
                    notes.append(note)
                continue

            if "-->" in line or "---" in line:
                edges.extend(self._parse_edge_chain(line))
                continue

            if "[" in line and "]" in line:
                node_id, label, class_name = self._parse_node_line(line)
                node = Node(
                    node_id=node_id,
                    label=label,
                    class_name=class_name,
                    subgraph=current_subgraph,
                )
                node_map[node_id] = node
                node_sequence.append(node_id)

        for node_id, class_name in pending_classes.items():
            if node_id in node_map:
                node_map[node_id].class_name = class_name

        for indexes, style in link_styles:
            for idx in indexes:
                if 0 <= idx < len(edges):
                    edges[idx].style.update(style)

        row_map: Dict[str, int] = {}
        next_row = 0
        for class_name in ROW_PRIORITY:
            if any(node.class_name == class_name for node in node_map.values()):
                row_map[class_name] = next_row
                next_row += 1
        for node in node_map.values():
            if node.class_name and node.class_name not in row_map:
                row_map[node.class_name] = next_row
                next_row += 1
        for node in node_map.values():
            node.row_index = row_map.get(node.class_name or "", next_row)

        column_meta = self._derive_column_meta(node_sequence, node_map)
        column_lookup = {meta.key: idx for idx, meta in enumerate(column_meta)}
        for node in node_map.values():
            key = node.node_id.split("_", 1)[0]
            node.column_index = column_lookup.get(key, 0)

        return node_map, edges, column_meta, class_styles, notes, direction

    def _normalize_lines(self, raw_text: str) -> List[str]:
        raw_lines = raw_text.splitlines()
        cleaned: List[str] = []
        buffer = ""
        open_brackets = 0

        for line in raw_lines:
            stripped = line.strip()
            if not stripped or stripped.startswith("%%"):
                continue
            if stripped.startswith("```"):
                continue

            if buffer:
                buffer += " " + stripped
            else:
                buffer = stripped

            open_brackets += stripped.count("[")
            open_brackets -= stripped.count("]")

            if open_brackets > 0:
                continue

            cleaned.append(buffer)
            buffer = ""

        if buffer:
            cleaned.append(buffer)

        return cleaned

    def _parse_style_attributes(self, attr_text: str) -> Dict[str, str]:
        styles = {}
        for part in attr_text.split(","):
            piece = part.strip()
            if not piece or ":" not in piece:
                continue
            key, value = (token.strip() for token in piece.split(":", 1))
            styles[key] = value
        return styles

    def _parse_node_line(self, line: str) -> Tuple[str, str, Optional[str]]:
        if "[" not in line or "]" not in line:
            raise ValueError(f"Invalid node line: {line}")
        prefix, remainder = line.split("[", 1)
        node_id = prefix.strip()
        label_part, suffix = remainder.split("]", 1)
        class_name = None
        if ":::" in suffix:
            class_name = suffix.split(":::")[-1].strip()
        return node_id, label_part.strip(), class_name or None

    def _split_edge_segment(self, segment: str) -> Tuple[Optional[str], str]:
        segment = segment.strip()
        label = None
        if segment.startswith("|"):
            closing = segment.find("|", 1)
            if closing != -1:
                label = segment[1:closing].strip()
                segment = segment[closing + 1 :].strip()
        return label, segment.strip()

    def _parse_edge_chain(self, line: str) -> List[Edge]:
        parts = EDGE_SPLIT.split(line)
        if not parts:
            return []
        current_label, current_node = self._split_edge_segment(parts[0])
        current_node = current_node or current_label or ""
        edges: List[Edge] = []

        for idx in range(1, len(parts), 2):
            connector = parts[idx]
            target_segment = parts[idx + 1] if idx + 1 < len(parts) else ""
            label, target = self._split_edge_segment(target_segment)
            if not current_node or not target:
                current_node = target or current_node
                continue
            style = {}
            if connector == "---":
                style.update(DASHED_EDGE_STYLE)
            edges.append(Edge(source=current_node, target=target, label=label, style=style))
            current_node = target
        return edges

    def _derive_column_meta(self, node_sequence: List[str], node_map: Dict[str, Node]) -> List[ColumnMeta]:
        metas: List[ColumnMeta] = []
        seen: set[str] = set()

        def label_string(node: Node) -> str:
            lines = label_to_lines(node.label)
            return " / ".join(line.strip() for line in lines if line.strip()) or node.node_id

        for node_id in node_sequence:
            node = node_map[node_id]
            if node.class_name == "header":
                key = node_id.split("_", 1)[0]
                if key not in seen:
                    metas.append(ColumnMeta(key=key, label=label_string(node)))
                    seen.add(key)

        for node_id in node_sequence:
            key = node_id.split("_", 1)[0]
            if key not in seen:
                node = node_map[node_id]
                metas.append(ColumnMeta(key=key, label=label_string(node)))
                seen.add(key)

        return metas

    def _parse_note_line(self, line: str) -> Optional[Note]:
        match = NOTE_PATTERN.match(line)
        if not match:
            return None
        position = match.group(1).lower()
        anchor = match.group(2).strip()
        text = match.group(3).strip()
        return Note(anchor=anchor, position=position, text_lines=label_to_lines(text))

    def _parse_link_style(self, line: str) -> Tuple[List[int], Dict[str, str]]:
        tokens = line.split(None, 2)
        if len(tokens) < 3:
            return [], {}
        indexes_part = tokens[1]
        style_part = tokens[2].rstrip(";")
        indexes = []
        for chunk in indexes_part.split(","):
            chunk = chunk.strip()
            if not chunk:
                continue
            try:
                indexes.append(int(chunk))
            except ValueError:
                continue
        return indexes, self._parse_style_attributes(style_part)
