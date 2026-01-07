from py_mermaid.src.parser import Parser
from py_mermaid.src.renderer import Renderer

def main():
    """
    Main function to parse a Mermaid flowchart and render it to SVG.
    """
    flowchart_text = """
    flowchart TB
        subgraph "Client"
            A[Browser] -->|HTTP Request| B(Web Server)
        end
        subgraph "Server"
            B --> C{Application Logic}
            C -->|Success| D[Database]
            C -->|Error| E[Error Logging]
        end
        D --> F((Save Data))
    """

    parser = Parser()
    node_map, edges, column_meta, styles, notes, direction = parser.parse(flowchart_text)

    renderer = Renderer()
    svg_output = renderer.render(node_map, edges, column_meta, styles, notes, direction)

    with open("output.svg", "w") as f:
        f.write(svg_output)

if __name__ == "__main__":
    main()
