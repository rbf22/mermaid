from py_mermaid.src.db import Node, Edge

class Renderer:
    def render(self, direction: str, nodes: list[Node], edges: list[Edge]) -> str:
        """
        Renders a simple flowchart with nodes and edges to SVG.
        Supports a basic directional layout.
        """
        node_positions = {}
        node_width = 100
        node_height = 50
        h_spacing = 100
        v_spacing = 80

        if direction == 'TD':
            # Simple top-down layout
            for i, node in enumerate(nodes):
                node_positions[node.id] = {'x': 150, 'y': (i * (node_height + v_spacing)) + 100}
        else:
            # Default to horizontal layout
            for i, node in enumerate(nodes):
                node_positions[node.id] = {'x': (i * (node_width + h_spacing)) + 100, 'y': 100}

        svg_elements = []

        # Render edges first so they are in the background
        for edge in edges:
            start_pos = node_positions[edge.start_node.id]
            end_pos = node_positions[edge.end_node.id]
            x1, y1, x2, y2 = start_pos['x'], start_pos['y'], end_pos['x'], end_pos['y']

            if direction == 'TD':
                y1 += node_height / 2
                y2 -= node_height / 2
            else: #LR
                x1 += node_width / 2
                x2 -= node_width / 2

            line = f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" style="stroke: #333; stroke-width: 2px;" marker-end="url(#arrowhead)" />'
            svg_elements.append(line)

        # Render nodes
        for node in nodes:
            pos = node_positions.get(node.id)
            x, y = pos['x'], pos['y']
            rect_x = x - node_width / 2
            rect_y = y - node_height / 2

            rect = f'<rect x="{rect_x}" y="{rect_y}" width="{node_width}" height="{node_height}" rx="5" ry="5" style="fill: #f9f9f9; stroke: #333; stroke-width: 2px;" />'
            text = f'<text x="{x}" y="{y}" dominant-baseline="middle" text-anchor="middle">{node.id}</text>'
            svg_elements.append(rect)
            svg_elements.append(text)

        # SVG wrapper with arrowhead definition
        svg_content = "".join(svg_elements)
        arrowhead = """
        <defs>
            <marker id="arrowhead" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">
                <polygon points="0 0, 10 3.5, 0 7" fill="#333" />
            </marker>
        </defs>
        """

        # Calculate dynamic canvas size
        if direction == 'TD':
            width = 300
            height = len(nodes) * (node_height + v_spacing) + 100
        else:
            width = len(nodes) * (node_width + h_spacing) + 100
            height = 200

        return f'<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">{arrowhead}{svg_content}</svg>'
