from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


@dataclass
class Node:
    node_id: str
    label: str
    class_name: Optional[str]
    subgraph: Optional[str]
    column_index: int = 0
    row_index: int = 0
    text_lines: List[str] = field(default_factory=list)
    width: float = 0.0
    height: float = 0.0
    x: float = 0.0  # top-left
    y: float = 0.0  # top-left

    def center(self) -> Tuple[float, float]:
        return (self.x + self.width / 2.0, self.y + self.height / 2.0)


@dataclass
class ColumnMeta:
    key: str
    label: str


@dataclass
class ColumnFrame:
    identifier: str
    label: str
    x: float
    width: float


@dataclass
class Edge:
    source: str
    target: str
    label: Optional[str] = None
    style: Dict[str, str] = field(default_factory=dict)


@dataclass
class Note:
    anchor: str
    position: str
    text_lines: List[str]
    width: float = 0.0
    height: float = 0.0
    x: float = 0.0
    y: float = 0.0
