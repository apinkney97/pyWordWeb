from __future__ import division
import logging
import string
import sys
import argparse
from collections import deque
from setqueue import SetQueue

__author__ = 'Alex Pinkney'


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
    def __init__(self, dictionary, letter_swaps=True, add_remove=True, use_anagrams=True):
        self.nodes = []
        self.edges = []
        self.dictionary = dictionary

        if use_anagrams:
            logging.info('finding anagrams')
            self.anagrams = {}
            for word in self.dictionary:
                key = get_anagram_key(dictionary[word])
                if key not in self.anagrams:
                    self.anagrams[key] = []
                self.anagrams[key].append(word)

        logging.info("Building graph")
        while len(self.dictionary):
            node = self.dictionary.popitem()[1]

            neighbours = []

            if letter_swaps:
                neighbours.extend(self.find_letter_swaps(node))

            if add_remove:
                neighbours.extend(self.find_add_letter(node))
                neighbours.extend(self.find_remove_letter(node))

            if use_anagrams:
                anagrams = self.anagrams[get_anagram_key(node)]
                anagrams.remove(node.word)
                neighbours.extend(anagrams)

            for neighbour in neighbours:
                edge = Edge(node, self.dictionary[neighbour])
                self.edges.append(edge)

            self.nodes.append(node)

    def find_letter_swaps(self, node):
        word = node.word
        neighbours = []

        for i in xrange(0, len(word)):
            start = word[:i]
            end = word[i + 1:]
            for c in string.lowercase:
                new_word = start + c + end
                if new_word in self.dictionary:
                    neighbours.append(new_word)

        return neighbours

    def find_add_letter(self, node):
        word = node.word
        neighbours = []

        for i in xrange(0, len(word) + 1):
            start = word[:i]
            end = word[i:]
            for c in string.lowercase:
                new_word = start + c + end
                if new_word in self.dictionary:
                    neighbours.append(new_word)

        return neighbours

    def find_remove_letter(self, node):
        word = node.word
        neighbours = []

        for i in xrange(0, len(word)):
            start = word[:i]
            end = word[i + 1:]
            new_word = start + end
            if new_word in self.dictionary:
                neighbours.append(new_word)

        return neighbours

    def print_dot(self):
        logging.info("Printing dot")
        print "graph G {"

        # dot does not allow numeric identifiers, so we use 'n' as a prefix
        for node in self.nodes:
            print '\tn%d [label="%s"];' % (node.id, node.word)

        for edge in self.edges:
            print "\tn%d -- n%d;" % (edge.get_node(True).id, edge.get_node(False).id)

        print "}"

    def get_disjoint_subgraphs(self):
        logging.info("Calculating disjoint subgraphs")
        not_seen = {}
        for node in self.nodes:
            not_seen[node.word] = node

        heads = []

        while len(not_seen):
            head = not_seen.popitem()[1]
            heads.append(head)

            logging.debug("Expanding %s", head.word)
            queue = deque([head])
            while len(queue):
                n = queue.popleft()
                kids = n.get_neighbours()
                for kid in kids:
                    if kid.word in not_seen:
                        not_seen.pop(kid.word)
                        queue.append(kid)

        return heads

    def get_disjoint_subgraph_sizes(self):
        heads = self.get_disjoint_subgraphs()
        logging.info("Calculating sizes of subgraphs")
        counts = {}
        n = 0
        for head in heads:
            n += 1
            logging.info("Counting subgraph %d of %d", n, len(heads))
            seen = set()
            queue = SetQueue([head])
            while len(queue):
                node = queue.remove()
                seen.add(node)
                kids = node.get_neighbours()
                for kid in kids:
                    if kid not in seen and kid not in queue:
                        queue.add(kid)
            size = len(seen)
            if size not in counts:
                counts[size] = 1
            else:
                counts[size] += 1
        return counts

    def get_diameter_routes(self):
        logging.info("Finding shortest paths.")
        max_depth = 0
        diameter_routes = []

        count = 0
        for head in self.nodes:

            count += 1
            logging.info("Word %d of %d: %s (%.2f%%)", count, len(self.nodes), head.word, 100 * count / len(self.nodes))
            done = set()
            queue = SetQueue([head])

            depths = {head: 0}

            last_seen = head

            while len(queue):
                last_seen = queue.remove()

                done.add(last_seen)
                neighbours = last_seen.get_neighbours()
                for neighbour in neighbours:
                    if neighbour not in done and neighbour not in queue:
                        queue.add(neighbour)
                        depths[neighbour] = depths[last_seen] + 1
            logging.info("Furthest word: %d (%s)", depths[last_seen], last_seen.word)
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


def get_anagram_key(node):
    letters = list(node.word)
    letters.sort()
    return ''.join(letters)


def main():

    parser = argparse.ArgumentParser(description='Generate a graph from a word list.',
                                     epilog="The value of -l is ignored if -r is supplied. "
                                            "If none of -a, -s or -r are supplied, -s is implied.")
    parser.add_argument("word_list", help="path to file containing the list of words to process (one word per line)")
    parser.add_argument("-a", "--anagrams", help="allow anagrams", action="store_true")
    parser.add_argument("-s", "--substitutions", help="allow letter substitutions", action="store_true")
    parser.add_argument("-r", "--removals-additions", help="allow letters to be removed/added", action="store_true")
    parser.add_argument("-l", "--word-length", help="use words only of length LEN", type=int, metavar='LEN')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-L", "--longest-paths", help="find shortest paths of maximum length", action="store_true")
    group.add_argument("-D", "--print-dot", help="output the entire graph in dot notation", action="store_true")
    group.add_argument("-S", "--print-graph-sizes", help="output histogram data of disjoint subgraph sizes and their "
                                                         "frequencies", action="store_true")
    parser.add_argument("-v", "--verbose", help="increase output verbosity", action="count", default=0)
    args = parser.parse_args()

    verbosity = args.verbose
    if verbosity == 1:
        logging.basicConfig(level=logging.INFO)
    elif verbosity > 1:
        logging.basicConfig(level=logging.DEBUG)

    get_longest = args.longest_paths
    print_dot = args.print_dot
    get_clusters = args.print_graph_sizes

    letter_swaps = args.substitutions
    add_remove = args.removals_additions
    anagrams = args.anagrams

    if True not in (letter_swaps, add_remove, anagrams):
        letter_swaps = True

    dict_file = args.word_list
    length = args.word_length

    f = open(dict_file)

    word_list = {}

    read_all = add_remove or length is None

    if read_all:
        logging.info("Reading in all words")
    else:
        logging.info("Reading in words of length %d", length)

    for line in f:
        word = line.strip()
        if read_all or len(word) == length:
            word_list[word] = Node(word)
    f.close()

    logging.info("%d words read", len(word_list))

    word_web = WordWeb(word_list, letter_swaps, add_remove, anagrams)
    logging.info("Graph initialised")

    if get_longest:
        diameter, routes = word_web.get_diameter_routes()
        routes.sort()
        print "%d:\t%d\t%s" % (length, diameter, routes)

    if print_dot:
        word_web.print_dot()

    if get_clusters:
        data = word_web.get_disjoint_subgraph_sizes()
        for k in sorted(data.keys()):
            print "%s\t%s" % (k, data[k])


if __name__ == "__main__":
    main()
