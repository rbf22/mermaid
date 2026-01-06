from py_mermaid.src.db import Node, Edge

class Parser:
    def parse(self, text: str) -> tuple[str, list[Node], list[Edge]]:
        """
        Parses a simple flowchart definition and extracts the direction.
        Example: graph TD; A --> B --> C;
        """
        lines = text.strip().split(';')
        nodes = {}
        edges = []
        direction = 'TD'  # Default direction

        first_line = lines[0].strip()
        if first_line.lower().startswith('graph'):
            parts = first_line.split()
            if len(parts) > 1:
                direction = parts[1]
            lines = lines[1:]

        for line in lines:
            line = line.strip()
            if not line:
                continue

            if '-->' in line:
                parts = line.split('-->')
                for i in range(len(parts) - 1):
                    start_id = parts[i].strip()
                    end_id = parts[i+1].strip()

                    if start_id not in nodes:
                        nodes[start_id] = Node(start_id)
                    if end_id not in nodes:
                        nodes[end_id] = Node(end_id)

                    edges.append(Edge(nodes[start_id], nodes[end_id]))

        return direction, list(nodes.values()), edges
