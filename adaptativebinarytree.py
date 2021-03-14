import numpy as np
from operator import attrgetter


class Node():

    def __init__(self, symbol, weight, number, bitstream=None):
        self.symbol = symbol
        self.weight = weight
        self.number = number
        self.bitstream = bitstream



class AdaptativeBinaryTree():

    def __init__(self, code_length):
        self.root_node_number = 2 * code_length - 1
        root_node = Node("NYT", 0, self.root_node_number)
        self.nodes = np.array([root_node])
        self.last_searched_index = 0


    def insert_symbol(self, symbol):
        if len(self.nodes) == 1:
            self.insert_first_symbol(symbol)

        else:
            node = next((node for node in self.nodes if node.symbol == symbol), None)
            if node is None:
                self.insert_new_symbol(symbol)
            else:
                self.update_existing_symbol(node)
                self.sibling_property()

            self.update_weights()
            self.update_weights() if self.sibling_property() else None

    
    def get_symbol_codeword(self, symbol):
        node = next((node for node in self.nodes if node.symbol == symbol), None)
        try:
            return node.bitstream
        except:
            return None


    def get_codeword_for_nyt(self):
        return self.nodes[-1].bitstream


    def get_symbol_from_codeword(self, codeword):       
        for node_idx in range(self.last_searched_index + 1, len(self.nodes)):
            node = self.nodes[node_idx]
            if node.bitstream == codeword:
                if node.symbol is not 'IN':
                    self.last_searched_index = 0
                    return node.symbol
                else:
                    self.last_searched_index = node_idx
                    return None
    
    
    def insert_first_symbol(self, symbol):
        self.nodes[0].symbol = "IN"
        self.nodes[0].weight = 1
        self.nodes = np.append(self.nodes, Node(symbol, 1, self.nodes[0].number - 1, '1'))
        self.nodes = np.append(self.nodes, Node("NYT", 0, self.nodes[0].number - 2, '0'))


    def insert_new_symbol(self, symbol):
        self.nodes[-1].symbol = "IN"
        in_bitstream = self.nodes[-1].bitstream
        in_number    = self.nodes[-1].number
        self.nodes = np.append(self.nodes, Node(symbol, 1, in_number - 1, in_bitstream + '1'))
        self.nodes = np.append(self.nodes, Node("NYT", 0, in_number - 2, in_bitstream + '0'))


    def update_existing_symbol(self, node):
        node_index = np.where(self.nodes == node)[0][0]
        self.nodes[node_index].weight += 1


    def sibling_property(self):
        node_with_smallest_weight = self.nodes[1]
        node_with_greater_weight = None
        nodes_to_be_replaced = []

        for node in self.nodes[2:-1]:
            if node.weight < node_with_smallest_weight.weight:
                node_with_smallest_weight = node
            elif node.weight > node_with_smallest_weight.weight:
                node_with_greater_weight = node
                if not node_with_greater_weight.bitstream.startswith(node_with_smallest_weight.bitstream):
                    nodes_to_be_replaced = [node_with_smallest_weight, node_with_greater_weight]

        if nodes_to_be_replaced != []:
            self.vectorized_prefix_replacing(nodes_to_be_replaced[0].bitstream, nodes_to_be_replaced[1].bitstream)
            self.correct_node_numbers()
            ##### Return True to sinalize that a new weight update is required
            return True
        
        return False


    def update_weights(self):
        longest_codeword = len(self.nodes[-1].bitstream)
        next_level_indexes = np.where(np.vectorize(self.filter_nodes_by_bs_length)(self.nodes, longest_codeword) == True)[0]

        for current_level in range(longest_codeword - 1, 0, -1):
            current_level_indexes = np.where(np.vectorize(self.filter_nodes_by_bs_length)(self.nodes, current_level) == True)[0]

            next_level_nodes = self.nodes[next_level_indexes]
            next_level_bitstreams = np.array(list(map(lambda node: node.bitstream, next_level_nodes)))
            next_level_weights = np.array(list(map(lambda node: node.weight, next_level_nodes)))

            list(map(lambda index: self.update_weight_of_given_node(index, next_level_bitstreams, next_level_weights), current_level_indexes))

            next_level_indexes = current_level_indexes

        self.nodes[0].weight = np.sum((self.nodes[1].weight, self.nodes[2].weight))


    def filter_nodes_by_bs_length(self, node, bs_length):
        try:
            return True if len(node.bitstream) == bs_length else False
        except:
            return False

    
    def update_weight_of_given_node(self, node_index, next_level_bitstreams, next_level_weights):
        if self.nodes[node_index].symbol not in ["IN", "NYT"]:
            return
        prefix = self.nodes[node_index].bitstream
        prefix_indexes = list(map(lambda bitstream: bitstream.startswith(prefix), next_level_bitstreams))
        offsprings_weights = next_level_weights[prefix_indexes]
        self.nodes[node_index].weight = np.sum(offsprings_weights)


    def vectorized_prefix_replacing(self, bs_1, bs_2):
        vect_func = np.vectorize(self.replace_prefixes)
        self.nodes = vect_func(self.nodes, bs_1, bs_2)

    
    def replace_prefixes(self, node, bs_1, bs_2):
        if node.bitstream is None:
            return node
        if node.bitstream.startswith(bs_1):
            node.bitstream = node.bitstream.replace(bs_1, bs_2, 1)
        elif node.bitstream.startswith(bs_2):
            node.bitstream = node.bitstream.replace(bs_2, bs_1, 1)
        return node


    def correct_node_numbers(self):
        self.nodes[1:] = np.array(sorted(self.nodes[1:], key=lambda node: (len(node.bitstream), -int(node.bitstream, base=2))))
        numbers_list = np.arange(self.root_node_number - 1, self.root_node_number - 1 - len(self.nodes[1:]), -1)
        self.nodes[1:] = np.vectorize(self.assign_number)(self.nodes[1:], numbers_list)


    def assign_number(self, node, new_number):
        node.number = new_number
        return node