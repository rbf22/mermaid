class Node:
    def __init__(self, id, text=''):
        self.id = id
        self.text = text

class Edge:
    def __init__(self, start_node, end_node, text=''):
        self.start_node = start_node
        self.end_node = end_node
        self.text = text
