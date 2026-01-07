import unittest
from py_mermaid.src.sequence import SequenceParser, SequenceRenderer

class TestSequenceDiagram(unittest.TestCase):
    def test_simple_sequence(self):
        sequence_text = """
        sequenceDiagram
            participant Alice
            participant Bob
            Alice->>Bob: Hello Bob, how are you?
            Bob-->>Alice: I am good thanks!
        """
        parser = SequenceParser()
        (
            participants,
            messages,
            notes,
            activations,
            fragments,
            style_overrides,
        ) = parser.parse(sequence_text)

        self.assertEqual(len(participants), 2)
        self.assertEqual(participants[0].name, "Alice")
        self.assertEqual(participants[1].name, "Bob")
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0].sender, "Alice")
        self.assertEqual(messages[0].receiver, "Bob")
        self.assertEqual(messages[0].text, "Hello Bob, how are you?")
        self.assertEqual(messages[1].sender, "Bob")
        self.assertEqual(messages[1].receiver, "Alice")
        self.assertEqual(messages[1].text, "I am good thanks!")

    def test_svg_generation(self):
        sequence_text = """
        sequenceDiagram
            participant Alice
            participant Bob
            Alice->>Bob: Hello Bob, how are you?
        """
        parser = SequenceParser()
        (
            participants,
            messages,
            notes,
            activations,
            fragments,
            style_overrides,
        ) = parser.parse(sequence_text)
        renderer = SequenceRenderer()
        svg_output = renderer.render(
            participants,
            messages,
            notes,
            activations,
            fragments,
            style_overrides,
        )

        self.assertTrue(svg_output.startswith('<?xml version="1.0" encoding="UTF-8"?>'))
        self.assertIn('<svg', svg_output)
        self.assertIn('</svg>', svg_output)
        self.assertIn('Alice', svg_output)
        self.assertIn('Bob', svg_output)
        self.assertIn('Hello Bob, how are you?', svg_output)

    def test_fragment_parsing(self):
        sequence_text = """
        sequenceDiagram
            participant A
            participant B
            alt successful case
                A->>B: Do something
            else an error
                A->>B: Handle error
            end
        """
        parser = SequenceParser()
        (
            participants,
            messages,
            notes,
            activations,
            fragments,
            style_overrides,
        ) = parser.parse(sequence_text)

        self.assertEqual(len(fragments), 1)
        fragment = fragments[0]
        self.assertEqual(fragment.kind, "alt")
        self.assertEqual(fragment.label, "successful case")
        self.assertEqual(len(fragment.sections), 2)
        self.assertEqual(fragment.sections[0].label, "successful case")
        self.assertEqual(fragment.sections[1].label, "an error")

if __name__ == '__main__':
    unittest.main()
