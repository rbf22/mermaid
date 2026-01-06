from py_mermaid.src.parser import Parser
from py_mermaid.src.renderer import Renderer

def main():
    """
    Main function to parse a Mermaid flowchart and render it to SVG.
    """
    flowchart_text = "graph TD; A --> B; B --> C;"

    parser = Parser()
    direction, nodes, edges = parser.parse(flowchart_text)

    renderer = Renderer()
    svg_output = renderer.render(direction, nodes, edges)

    with open("output.svg", "w") as f:
        f.write(svg_output)

if __name__ == "__main__":
    main()
