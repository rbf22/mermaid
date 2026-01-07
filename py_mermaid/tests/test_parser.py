import unittest
from py_mermaid.src.parser import Parser

class TestParser(unittest.TestCase):
    def test_simple_flowchart(self):
        flowchart_text = """
        flowchart TB
            A[Start]
            B[Decision]
            C[End]
            A --> B
            B --> C
        """
        parser = Parser()
        node_map, edges, _, _, _, direction = parser.parse(flowchart_text)

        self.assertEqual(direction, "TB")
        self.assertIn("A", node_map)
        self.assertIn("B", node_map)
        self.assertIn("C", node_map)
        self.assertEqual(len(edges), 2)
        self.assertEqual(edges[0].source, "A")
        self.assertEqual(edges[0].target, "B")
        self.assertEqual(edges[1].source, "B")
        self.assertEqual(edges[1].target, "C")

if __name__ == '__main__':
    unittest.main()
