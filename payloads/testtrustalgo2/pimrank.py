import networkx as nx
import scipy
import numpy


class PimRank:

    def __init__(self, graph, personalization, weight='contribution'):
        self.graph = graph
        self.personalization = personalization
        self.weight = weight

    def compute(self, summarize=True):
        try:
            pimrank = self.pagerank_scipy_patched(self.graph, personalization=self.personalization, weight=self.weight)
        except nx.NetworkXException as e:
            print(str(e))
            print("Empty Temporal PageRank, returning empty scores")
            return {}

        if not summarize:
            return pimrank

        sums = {}

        for interaction in pimrank.keys():
            sums[interaction] = sums.get(interaction, 0) + pimrank[interaction]

        return sums

    def pagerank_scipy_patched(self, G, alpha=0.85, personalization=None,
                               max_iter=100, tol=1.0e-6, weight='weight',
                               dangling=None):
        """Return the PageRank of the nodes in the graph.
        PageRank computes a ranking of the nodes in the graph G based on
        the structure of the incoming links. It was originally designed as
        an algorithm to rank web pages.
        Parameters
        ----------
        G : graph
          A NetworkX graph.  Undirected graphs will be converted to a directed
          graph with two directed edges for each undirected edge.
        alpha : float, optional
          Damping parameter for PageRank, default=0.85.
        personalization: dict, optional
           The "personalization vector" consisting of a dictionary with a
           key for every graph node and nonzero personalization value for each
           node. By default, a uniform distribution is used.
        max_iter : integer, optional
          Maximum number of iterations in power method eigenvalue solver.
        tol : float, optional
          Error tolerance used to check convergence in power method solver.
        weight : key, optional
          Edge data key to use as weight.  If None weights are set to 1.
        dangling: dict, optional
          The outedges to be assigned to any "dangling" nodes, i.e., nodes without
          any outedges. The dict key is the node the outedge points to and the dict
          value is the weight of that outedge. By default, dangling nodes are given
          outedges according to the personalization vector (uniform if not
          specified) This must be selected to result in an irreducible transition
          matrix (see notes under google_matrix). It may be common to have the
          dangling dict to be the same as the personalization dict.
        Returns
        -------
        pagerank : dictionary
           Dictionary of nodes with PageRank as value
        Examples
        --------
        >>> G = nx.DiGraph(nx.path_graph(4))
        >>> pr = nx.pagerank_scipy(G, alpha=0.9)
        Notes
        -----
        The eigenvector calculation uses power iteration with a SciPy
        sparse matrix representation.
        This implementation works with Multi(Di)Graphs. For multigraphs the
        weight between two nodes is set to be the sum of all edge weights
        between those nodes.
        See Also
        --------
        pagerank, pagerank_numpy, google_matrix
        References
        ----------
        .. [1] A. Langville and C. Meyer,
           "A survey of eigenvector methods of web information retrieval."
           http://citeseer.ist.psu.edu/713792.html
        .. [2] Page, Lawrence; Brin, Sergey; Motwani, Rajeev and Winograd, Terry,
           The PageRank citation ranking: Bringing order to the Web. 1999
           http://dbpubs.stanford.edu:8090/pub/showDoc.Fulltext?lang=en&doc=1999-66&format=pdf
        """
        import scipy.sparse

        N = len(G)
        if N == 0:
            return {}

        nodelist = G.nodes()
        M = nx.to_scipy_sparse_matrix(G, nodelist=nodelist, weight=weight,
                                      dtype=float)
        S = scipy.array(M.sum(axis=1)).flatten()
        S[S != 0] = 1.0 / S[S != 0]
        Q = scipy.sparse.spdiags(S.T, 0, *M.shape, format='csr')
        M = Q * M

        # initial vector
        x = scipy.repeat(1.0 / N, N)

        # Personalization vector
        if personalization is None:
            p = scipy.repeat(1.0 / N, N)
        else:
            p = scipy.array([personalization.get(n, 0) for n in nodelist],
                            dtype=float)
            p = p / p.sum()

        # Dangling nodes
        if dangling is None:
            dangling_weights = p
        else:
            missing = set(nodelist) - set(dangling)
            if missing:
                raise nx.NetworkXError('Dangling node dictionary '
                                       'must have a value for every node. '
                                       'Missing nodes %s' % missing)
            # Convert the dangling dictionary into an array in nodelist order
            dangling_weights = scipy.array([dangling[n] for n in nodelist],
                                           dtype=float)
            dangling_weights /= dangling_weights.sum()
        is_dangling = scipy.where(S == 0)[0]

        # power iteration: make up to max_iter iterations
        for _ in range(max_iter):
            xlast = x
            x = alpha * (x * M + sum(x[is_dangling]) * dangling_weights) + \
                (1 - alpha) * p
            # check convergence, l1 norm
            err = scipy.absolute(x - xlast).sum()
            if err < N * tol:
                return dict(zip(nodelist, map(float, x)))
        print(err)
        raise nx.NetworkXError('pagerank_scipy: power iteration failed to converge '
                               'in %d iterations.' % max_iter)

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

n = PimRank(graph, {1: 0.1, 2: 0.0, 3: 0.1, 4: 0.2, 5: 0.1, 6: 0.1, 7: 0.1, 8: 0.1, 9: 0.1, 10: 0.1})
score = n.compute()

print "Trust score is: " + str(score[4])
