import unittest
from py_mermaid.src.parser import Parser
from py_mermaid.src.renderer import Renderer

class TestRenderer(unittest.TestCase):
    def test_svg_generation(self):
        flowchart_text = """
        flowchart TB
            A[Start]
            B[End]
            A --> B
        """
        parser = Parser()
        node_map, edges, column_meta, styles, notes, direction = parser.parse(flowchart_text)

        renderer = Renderer()
        svg_output = renderer.render(node_map, edges, column_meta, styles, notes, direction)

        self.assertTrue(svg_output.startswith('<?xml version="1.0" encoding="UTF-8"?>'))
        self.assertIn('<svg', svg_output)
        self.assertIn('</svg>', svg_output)
        self.assertIn('Start', svg_output)
        self.assertIn('End', svg_output)

if __name__ == '__main__':
    unittest.main()
