from py_mermaid.src.parser import Parser as FlowchartParser
from py_mermaid.src.renderer import Renderer as FlowchartRenderer
from py_mermaid.src.sequence import SequenceParser, SequenceRenderer

def main():
    """
    Main function to parse a Mermaid diagram and render it to SVG.
    """
    diagram_text = """
    sequenceDiagram
        participant Alice
        participant Bob
        Alice->>Bob: Hello Bob, how are you?
        Bob-->>Alice: I am good thanks!
    """

    if "sequenceDiagram" in diagram_text:
        parser = SequenceParser()
        (
            participants,
            messages,
            notes,
            activations,
            fragments,
            style_overrides,
        ) = parser.parse(diagram_text)
        renderer = SequenceRenderer()
        svg_output = renderer.render(
            participants,
            messages,
            notes,
            activations,
            fragments,
            style_overrides,
        )
    else:
        parser = FlowchartParser()
        node_map, edges, column_meta, styles, notes, direction = parser.parse(diagram_text)
        renderer = FlowchartRenderer()
        svg_output = renderer.render(node_map, edges, column_meta, styles, notes, direction)

    with open("output.svg", "w") as f:
        f.write(svg_output)

if __name__ == "__main__":
    main()
