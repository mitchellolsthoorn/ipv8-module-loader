from trust.trust.RandomWalk import RandomWalk
from trust.trust.NodeVision import NodeVision
from networkx import nx
from trust.trust.TransactionDiscovery import TransactionDiscovery
from random import random

gr = nx.DiGraph()
gr.add_node(0)
Gw = NodeVision(gr=gr)

disc = TransactionDiscovery()
transactions = disc.read_transactions(fake=False, tr_count=500)

for tr in transactions:
    Gw.graph.add_edge(tr['downloader'],
                      tr['uploader'],
                      weight=tr['amount'])
    if random() < 0.25 and tr['downloader'] != Gw.rootnode:
        Gw.graph.add_edge(Gw.rootnode, tr['downloader'], weight=tr['amount'])

Gw.set_root_node(transactions[0]['downloader'])

Gw.normalize_edge_weights()

Gw.reposition_nodes()
Gw.show_undirected_bfs_tree()
Gw.update_component()
Gw.show_directed_neighborhood()

rw = RandomWalk(Gw)
rw.set_walk_params({'n_walk': 50, 'reset_prob': 0.1, 'n_step': 300})
rw.set_move_params({'time_to_finish': 10})

rw.make_fake_transactions = True

rw.show_walk()
