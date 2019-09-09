import networkx as nx


class Netflow:
    """
    This class implements the Netflow algorithm.
    """

    def __init__(self, graph, identity=None, alpha=2):
        self.graph = graph

        if identity is not None:
            self.identity = identity
        else:
            self.identity = graph.nodes()[0]

        for neighbour in self.graph.out_edges([self.identity], 'capacity', 0):
            cap = self.graph[self.identity][neighbour[1]]['capacity']
            self.graph[self.identity][neighbour[1]]['capacity'] = float(cap) / float(alpha)

    def compute(self):
        self.initial_step()
        self.transform_graph()
        self.netflow_step()

    def initial_step(self):
        """
        In the intial step, all capactities are computed
        """

        for node in self.graph.nodes:
            self.compute_capacity(node)

    def transform_graph(self):
        """
        In this step, the graph is transformed, based on the capacities computed in step 1
        """

        self.augmented_graph = nx.DiGraph()

        for edge in self.graph.edges(data=True):
            self.augmented_graph.add_edge(str(edge[0]) + "OUT", str(edge[1]) + "IN", capacity=edge[2]['capacity'])

        for node in self.graph.nodes(data=True):
            if node[0] == self.identity:
                self.augmented_graph.add_edge(str(node[0]) + "IN", str(node[0]) + "OUT")
            else:
                self.augmented_graph.add_edge(str(node[0]) + "IN", str(node[0]) + "OUT", capacity=node[1]['capacity'])

    def netflow_step(self):

        for node in self.graph.nodes():
            if node == self.identity:
                self.graph.node[node]['score'] = 0

                continue
            score = nx.maximum_flow_value(self.augmented_graph, str(node) + "IN", str(self.identity) + "OUT")

            self.graph.node[node]['score'] = score

    def compute_capacity(self, node):
        if node == self.identity:
            return
        contribution = nx.maximum_flow_value(self.graph, node, self.identity)
        consumption = nx.maximum_flow_value(self.graph, self.identity, node)

        self.graph.add_node(node, capacity=max(0, contribution - consumption))
        self.graph.add_node(node, bartercast=contribution - consumption)

graph = nx.DiGraph()
graph.add_node(1)
graph.add_node(2)
graph.add_node(3)
graph.add_node(4)
graph.add_node(5)
graph.add_node(6)
graph.add_node(7)
graph.add_node(8)
graph.add_node(9)
graph.add_node(10)
graph.add_edge(1, 2, capacity=20)
graph.add_edge(1, 3, capacity=40)
graph.add_edge(1, 4, capacity=12)
graph.add_edge(1, 5, capacity=0)
graph.add_edge(1, 6, capacity=0)
graph.add_edge(1, 7, capacity=0)
graph.add_edge(1, 8, capacity=0)
graph.add_edge(1, 9, capacity=0)
graph.add_edge(1, 10, capacity=0)
graph.add_edge(2, 1, capacity=20)
graph.add_edge(2, 3, capacity=0)
graph.add_edge(2, 4, capacity=0)
graph.add_edge(2, 5, capacity=10)
graph.add_edge(2, 6, capacity=0)
graph.add_edge(2, 7, capacity=0)
graph.add_edge(2, 8, capacity=0)
graph.add_edge(2, 9, capacity=0)
graph.add_edge(2, 10, capacity=0)
graph.add_edge(3, 1, capacity=0)
graph.add_edge(3, 2, capacity=0)
graph.add_edge(3, 4, capacity=0)
graph.add_edge(3, 5, capacity=0)
graph.add_edge(3, 6, capacity=0)
graph.add_edge(3, 7, capacity=0)
graph.add_edge(3, 8, capacity=0)
graph.add_edge(3, 9, capacity=0)
graph.add_edge(3, 10, capacity=0)
graph.add_edge(4, 1, capacity=14)
graph.add_edge(4, 2, capacity=0)
graph.add_edge(4, 3, capacity=0)
graph.add_edge(4, 5, capacity=0)
graph.add_edge(4, 6, capacity=0)
graph.add_edge(4, 7, capacity=80)
graph.add_edge(4, 8, capacity=0)
graph.add_edge(4, 9, capacity=0)
graph.add_edge(4, 10, capacity=0)
graph.add_edge(5, 1, capacity=0)
graph.add_edge(5, 2, capacity=5)
graph.add_edge(5, 3, capacity=0)
graph.add_edge(5, 4, capacity=0)
graph.add_edge(5, 6, capacity=0)
graph.add_edge(5, 7, capacity=0)
graph.add_edge(5, 8, capacity=0)
graph.add_edge(5, 9, capacity=0)
graph.add_edge(5, 10, capacity=0)
graph.add_edge(6, 1, capacity=0)
graph.add_edge(6, 2, capacity=0)
graph.add_edge(6, 3, capacity=0)
graph.add_edge(6, 4, capacity=0)
graph.add_edge(6, 5, capacity=0)
graph.add_edge(6, 7, capacity=0)
graph.add_edge(6, 8, capacity=0)
graph.add_edge(6, 9, capacity=0)
graph.add_edge(6, 10, capacity=0)
graph.add_edge(7, 1, capacity=0)
graph.add_edge(7, 2, capacity=0)
graph.add_edge(7, 3, capacity=0)
graph.add_edge(7, 4, capacity=60)
graph.add_edge(7, 5, capacity=0)
graph.add_edge(7, 6, capacity=0)
graph.add_edge(7, 8, capacity=0)
graph.add_edge(7, 9, capacity=6)
graph.add_edge(7, 10, capacity=0)
graph.add_edge(8, 1, capacity=0)
graph.add_edge(8, 2, capacity=0)
graph.add_edge(8, 3, capacity=0)
graph.add_edge(8, 4, capacity=0)
graph.add_edge(8, 5, capacity=0)
graph.add_edge(8, 6, capacity=0)
graph.add_edge(8, 7, capacity=0)
graph.add_edge(8, 9, capacity=0)
graph.add_edge(8, 10, capacity=0)
graph.add_edge(9, 1, capacity=0)
graph.add_edge(9, 2, capacity=0)
graph.add_edge(9, 3, capacity=0)
graph.add_edge(9, 4, capacity=0)
graph.add_edge(9, 5, capacity=0)
graph.add_edge(9, 6, capacity=0)
graph.add_edge(9, 7, capacity=3)
graph.add_edge(9, 8, capacity=0)
graph.add_edge(9, 10, capacity=0)
graph.add_edge(10, 1, capacity=0)
graph.add_edge(10, 2, capacity=0)
graph.add_edge(10, 3, capacity=0)
graph.add_edge(10, 4, capacity=0)
graph.add_edge(10, 5, capacity=0)
graph.add_edge(10, 6, capacity=0)
graph.add_edge(10, 7, capacity=0)
graph.add_edge(10, 8, capacity=0)
graph.add_edge(10, 9, capacity=0)

n = Netflow(graph, 3)
n.compute()

print "Trust score is: " + str(n.graph.nodes()[1]['score'])