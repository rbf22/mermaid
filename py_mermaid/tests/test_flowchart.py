import unittest
from py_mermaid.src.parser import Parser

class TestFlowchartParser(unittest.TestCase):
    def test_parse_simple_flowchart_with_direction(self):
        parser = Parser()
        flowchart_text = "graph LR; A --> B;"
        direction, nodes, edges = parser.parse(flowchart_text)

        self.assertEqual(direction, "LR")
        self.assertEqual(len(nodes), 2)
        self.assertEqual(len(edges), 1)

    def test_parse_chained_flowchart(self):
        parser = Parser()
        flowchart_text = "graph TD; A --> B --> C;"
        direction, nodes, edges = parser.parse(flowchart_text)

        self.assertEqual(direction, "TD")
        self.assertEqual(len(nodes), 3)
        self.assertEqual(len(edges), 2)

        node_ids = {node.id for node in nodes}
        self.assertIn("A", node_ids)
        self.assertIn("B", node_ids)
        self.assertIn("C", node_ids)

        self.assertEqual(edges[0].start_node.id, "A")
        self.assertEqual(edges[0].end_node.id, "B")
        self.assertEqual(edges[1].start_node.id, "B")
        self.assertEqual(edges[1].end_node.id, "C")

if __name__ == '__main__':
    unittest.main()
