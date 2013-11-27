import string
import sys
from collections import deque

__author__ = 'Alex'


class Edge:
    def __init__(self, node1, node2):
        self.node1 = node1
        self.node2 = node2

        node1.add_edge(self)
        node2.add_edge(self)

    def get_opposite_node(self, node):
        if node is self.node1:
            return self.node2
        if node is self.node2:
            return self.node1
        return None

    def get_node(self, first_node=True):
        if first_node:
            return self.node1
        return self.node2


class Node:
    count = 0

    def __init__(self, word):
        Node.count += 1
        self.id = Node.count
        self.word = word
        self.edges = []

    def get_neighbours(self):
        neighbours = []
        for edge in self.edges:
            neighbours.append(edge.get_opposite_node(self))
        return neighbours

    def add_edge(self, edge):
        if edge.get_opposite_node(self) is not None:
            self.edges.append(edge)
            return True
        return False


class WordWeb:
    def __init__(self, dictionary):
        self.nodes = []
        self.edges = []

        # TODO also allow anagrams and add/remove letter

        while len(dictionary):
            node = dictionary.popitem()[1]
            word = node.word

            for i in xrange(0, len(word)):
                start = word[:i]
                end = word[i + 1:]
                for c in string.lowercase:
                    new_word = start + c + end
                    if new_word in dictionary:
                        edge = Edge(node, dictionary[new_word])
                        self.edges.append(edge)

            self.nodes.append(node)

    def print_dot(self):
        print "graph G {"

        for n in self.nodes:  # dot does not allow numeric identifiers, so we use 'n' as a prefix
            print "\tn%d [label='%s'];" % (n.id, n.word)

        for e in self.edges:
            print "\tn%d -- n%d;" % (e.get_node(True), e.get_node(False))

        print "}"

    def get_disjoint_subgraphs(self):
        not_seen = list(self.nodes)
        heads = []

        while len(not_seen):
            head = not_seen.pop()
            heads.append(head)

            queue = deque([head])
            while len(queue):
                n = queue.popleft()
                kids = n.get_neighbours()
                for kid in kids:
                    if kid in not_seen:
                        not_seen.remove(kid)
                        queue.append(kid)

        return heads

    def get_disjoint_subgraph_sizes(self):
        heads = self.get_disjoint_subgraphs()
        counts = {}
        for head in heads:
            seen = []
            queue = deque([head])
            while len(queue):
                node = queue.popleft()
                seen.append(node)
                kids = node.get_neighbours()
                for kid in kids:
                    if kid not in seen and kid not in queue:
                        queue.append(kid)
            size = len(seen)
            if size not in counts:
                counts[size] = 1
            else:
                counts[size] += 1
        return counts

    def get_diameter_routes(self):
        max_depth = 0
        diameter_routes = []

        for head in self.nodes:

            done = []
            queue = deque([head])
            depths = {head: 0}

            last_seen = head

            while len(queue):
                last_seen = queue.popleft()
                done.append(last_seen)
                neighbours = last_seen.get_neighbours()
                for neighbour in neighbours:
                    if neighbour not in done and neighbour not in queue:
                        queue.append(neighbour)
                        depths[neighbour] = depths[last_seen] + 1

            if depths[last_seen] >= max_depth:
                if depths[last_seen] > max_depth:
                    diameter_routes = []
                    max_depth = depths[last_seen]

                # Suppress reversed routes
                if head.word < last_seen.word:
                    route = head.word + " - " + last_seen.word
                else:
                    route = last_seen.word + " - " + head.word
                if route not in diameter_routes:
                    diameter_routes.append(route)

        return max_depth, diameter_routes


def main(args):
    if len(args) < 3:
        sys.stderr.write(
            "Error: Too few arguments. Call is: \"python %s path-to-word-list word-length\"\n" % args[0])
        exit(1)

    # TODO: replace with command line arg
    get_longest = True
    do_graphviz = False
    get_clusters = False

    dict_file = args[1]
    length = int(args[2])

    f = open(dict_file)

    word_list = {}

    for line in f:
        word = line.strip()
        if len(word) == length:
            word_list[word] = Node(word)
    f.close()

    word_web = WordWeb(word_list)

    if get_longest:
        diameter, routes = word_web.get_diameter_routes()
        routes.sort()
        print "d = %d, %d equivalent routes:\n%s" % (diameter, len(routes), routes)

    if do_graphviz:
        word_web.print_dot()

    if get_clusters:
        print word_web.get_disjoint_subgraph_sizes()


if __name__ == "__main__":
    main(sys.argv)
