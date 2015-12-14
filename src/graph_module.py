import numpy as np
import datetime
import networkx as nx
import matplotlib.pyplot as plt
from collections import OrderedDict
from creat_train_graph_module import create_train_graph, station_id2name

def create_predefind_graph():
    G = nx.DiGraph()

    for ind in range(4):
        G.add_node(ind, label=ind)
        G.add_edge(0, 1, w=[1, 5])
        G.add_edge(0, 2, w=[2, 3])
        G.add_edge(1, 3, w=[1, 1])
        G.add_edge(2, 3, w=[1, 1])
    return G
### -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


def create_toy_graph(n, m, time_len=1):
    G = nx.DiGraph()
    np.random.seed(0)
    # Create n nodes
    for ind in range(n):
        G.add_node(ind, label=ind)

    # Create m edges
    cnt = 0
    while cnt < m:
        ind1 = np.random.randint(n)
        ind2 = np.random.randint(n)
        w = np.zeros(time_len)
        w[0] = np.random.randint(1, 10)
        for i in range(1, time_len):
            w[i] = w[i-1] + np.random.randint(1, 10)

        if (ind1 != ind2) and ((ind1, ind2) not in G.edges()) and ((ind2, ind1) not in G.edges()):
            G.add_edge(ind1, ind2, w=w)
            cnt += 1
    return G

### -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

def display_graph(G, course=None, dist=None, draw_edge_label=True):
    labels = dict((n, d['label']) for n, d in G.nodes(data=True))
    edge_labels = nx.get_edge_attributes(G, 'w')
    # nx.draw_graphviz(G, labels=labels, node_color='c')
    pos = nx.pygraphviz_layout(G)
    nx.draw_networkx_nodes(G, pos, node_color='g', node_size=400)
    nx.draw_networkx_labels(G, pos, labels=labels, font_size=10)
    nx.draw_networkx_edges(G, pos)
    if draw_edge_label:
        nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels)

    if not course is None:
        nx.draw_networkx_nodes(G, pos, nodelist=[course[0]], node_size=400, node_color='r')
        nx.draw_networkx_nodes(G, pos, nodelist=[course[-1]], node_size=400, node_color='b')
        for ind in range(len(course)-1):
            nx.draw_networkx_edges(G, pos, edgelist=[[course[ind], course[ind+1]]], edge_color='y')
        plt.title(dist[course[-1]])
    plt.show()

### -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

def backtrack_path(prev, target):
    s = []
    u = target
    while not prev[u] is None:               # Construct the shortest path with a stack S
        s.insert(0, u)                        # Push the vertex onto the stack
        u = prev[u]                           # Traverse from target to source
    s.insert(0, u)                           # Push the source onto the stack

    return s

### -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

def find_shortest_path(G, source, target):
    # Initialization
    q = []
    dist = OrderedDict()
    prev = OrderedDict()
    for vertex in G.nodes():
        dist[vertex] = np.inf
        prev[vertex] = None
        q.append(vertex)

    dist[source] = 0
    if source == target:
        course = [target]
        return dist, course

    # Main iterative loop
    while len(q) > 0:
        dist_vec = map(lambda x: dist[x], q)
        u = q[np.argmin(dist_vec)]
        if u == target:
            course = backtrack_path(prev, target)

            return dist, course
        q.remove(u)
        tmp_set = set(G.neighbors(u)).intersection(set(q))
        for v in tmp_set:
            alt = dist[u] + G[u][v]['w'][-1]
            if alt < dist[v]:
                dist[v] = alt
                prev[v] = u

    # Backtracking
    course = backtrack_path(prev, target)

    return dist, course

### -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

def static_all_to_one(G, target):
    node_list = G.node.keys()
    dist_vec = OrderedDict(zip(node_list, np.inf * np.ones_like(node_list)))
    path_vec = OrderedDict(zip(node_list, np.inf * np.ones_like(node_list)))
    dist_vec[target] = 0
    for node in node_list:
        print "Processing node %d" % (node)
        if node != target:
            dist_tmp, course = find_shortest_path(G, node, target)
            dist_vec[node] = dist_tmp[target]
            path_vec[node] = course
            # display_graph(G, path)
        else:
            dist_vec[node] = 0
            path_vec[node] = [node]

    return dist_vec, path_vec

### -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

def dynamic_all_to_one(G, target, M=3):
    # Based on the DOT algorithm, described in "Discrete Dynamic Shortest Path Problems in Transportation Applications:
    #   Complexity and Algorithms with Optimal Run time", Ismail Chabini, 1997

    # Initalization
    node_list = G.node.keys()
    time_vec = np.ones(M, dtype=np.int)
    dist_vec = OrderedDict(zip(node_list, np.inf * np.array([time_vec for xi in node_list])))
    path_vec = OrderedDict(zip(node_list,  np.array([OrderedDict() for xi in node_list])))
    dist_vec_static, path_vec_static = static_all_to_one(G, target)
    for node in dist_vec:
        dist_vec[node][M-1] = dist_vec_static[node]
        path_vec[node][M-1] = path_vec_static[node]
    for t in range(M-2, -1, -1):
        dist_vec[target][t] = 0
        path_vec[target][t] = [target]

    # Main loop
    for t in range(M-2, -1, -1):
        for edge in G.edges():
            i, j = edge
            time_next = np.min([t + G[i][j]['w'][t], M-1])
            tmp_vec = [dist_vec[i][t], G[i][j]['w'][t] + dist_vec[j][time_next]]
            tmp_ind = np.argmin(tmp_vec)
            if tmp_ind == 1:
                dist_vec[i][t] = tmp_vec[tmp_ind]
                path_vec[i][t] = [i] + path_vec[j][time_next]

    return dist_vec, path_vec

### -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

if __name__ == '__main__':

    # Create graph
    # time_len = 2
    # G = create_toy_graph(10, 25, time_len=time_len)
    # G = create_predefind_graph()

    import manage
    session = manage.get_session()
    stop_names = manage.get_stop_names()
    station_id_dict = station_id2name('../data/stops_ids_and_names.txt')


    date_val = datetime.date(2014, 1, 1)
    G = create_train_graph(session, stop_names, station_id_dict, date_val)

    target = 4600
    time_len = 60*24
    hour_vec = np.array(range(24*60))/60
    minuete_vec = np.array(range(24*60)) % 60
    time_indx_real = map(lambda x: '%04d'%x, hour_vec*100 + minuete_vec)

    dist_vec, path_vec = dynamic_all_to_one(G, target, time_len)

    display_graph(G, draw_edge_label=False)

