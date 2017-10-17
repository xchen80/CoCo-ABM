# value of 'bd' was reduced to 30
# initial amount of 'a' in the global pool was increased to 1000
# 'a' was made a common resource

# 4th plot was changed to cumulative amounts of productions

import matplotlib
matplotlib.use('TkAgg')

from pylab import *
import networkx as nx

# set of conversion/combination rules
# left/right hand sides can contain multiple resources in ()
capacities = [
        (('a',), ('b',)), # 'a' -> 'b'
        (('b',), ('c',)),
        (('c',), ('d',)),
        (('b','c'), ('bc',)),
        (('c','d'), ('cd',)),
        (('b','d'), ('bd',))
        ]

# conversion done by external market (i.e., cashing of specific product)
# left hand side should be a single resource
# right hand side should be the number of 'a's given back
external_market = [
        ('bd', 30) # 'bd' -> 30 'a'
        ]

n   = 30  # number of agents
p   = 0.2 # density of directed edges
nc  = 1   # number of capacity per agent
nga = 1000 # amount of 'a' in the global pool

def init():
    global g, values
    g = nx.gnp_random_graph(n, p, directed = True)
    g.pos = nx.spring_layout(g, k = 0.25)
    for i in g.nodes_iter():
        s = np.random.choice(range(len(capacities)),
                   size = nc,
                   replace = False)
        g.node[i]['capacity'] = [capacities[j] for j in s]
        g.node[i]['resource'] = {}
    g.resource = {'a': nga}
    values = {'a':[nga], 'b':[0], 'c':[0], 'd':[0], 'bc':[0], 'cd':[0], 'bd':[0]}

def node_label(i):
    label = ''
    for left, right in g.node[i]['capacity']:
        if label == '':
            label = left[0]
        else:
            label += '\n' + left[0]
        for j in range(1, len(left)):
            label += '+' + left[j]
        label += '->' + right[0]
        for j in range(1, len(right)):
            label += '+' + right[j]
    return label

def draw():
    global g, avalues
    
    subplot(2, 2, 1)
    cla()
    nx.draw_networkx_nodes(g, g.pos, node_size = 500,
                           node_shape = 's', linewidths = 10,
                           node_color = 'c')
    nx.draw_networkx_edges(g, g.pos, alpha = 0.5)
    nx.draw_networkx_labels(g, g.pos,
                            labels = {i:node_label(i) for i in g.nodes_iter()})
    axis('off')
    
    subplot(2, 2, 2)
    cla()
    resources = {}
    for i in g.nodes_iter():
        for x in g.node[i]['resource']:
            if x not in resources:
                resources[x] = 0
            resources[x] += g.node[i]['resource'][x]
    resources = sorted(resources.items(), key = lambda x:' '*(2-len(x[0]))+x[0])
    xs = range(len(resources))
    ys = [x[1] for x in resources]
    ls = [x[0] for x in resources]
    bar(xs, ys, tick_label = ls)

    subplot(2, 2, 3)
    cla()
    plot(values['a'])
    title("Total amount of 'a' ($, energy)")

    subplot(2, 2, 4)
    cla()
    for x in values:
        if x != 'a':
            plot(values[x], label = x)
    legend()
    title("Cumulative amount of production")

def step():
    global g
    
    produced = {x:0 for x in values if x != 'a'}

    # randomize the order of agents for updating
    agent_order = g.nodes()
    np.random.shuffle(agent_order)
    for i in agent_order:
            
        # consume 'a' just for living
        if g.resource['a'] <= 0: # if no more 'a's are available, do nothing
            continue
        g.resource['a'] -= 1

        # choose one rule from its capacity
        j = np.random.choice(range(len(g.node[i]['capacity'])))
        left, right = g.node[i]['capacity'][j]
    
        # if any of the involved resources doesn't have a counter
        # in the resource dictionary, make one with 0
        for x in left + right:
            if x != 'a' and x not in g.node[i]['resource']:
                g.node[i]['resource'][x] = 0
    
        # collect all the needed resources to workspace
        workspace = []
        for x in left:
            if x == 'a':
                if g.resource['a'] > 0:
                    g.resource['a'] -= 1
                    workspace.append(x)
            elif g.node[i]['resource'][x] > 0:
                g.node[i]['resource'][x] -= 1
                workspace.append(x)
            else:
                # if anything is missing, try to get it from in-neighbors
                in_neighbors = g.predecessors(i)
                np.random.shuffle(in_neighbors)
                for j in in_neighbors:
                    if x in g.node[j]['resource']:
                        if g.node[j]['resource'][x] > 0:
                            g.node[j]['resource'][x] -= 1
                            workspace.append(x)
                            break

        # if all the needed resouces and energy are available, do the work
        if sorted(left) == sorted(workspace) and g.resource['a'] > 0:
            g.resource['a'] -= 1
            for x in right:
                if x == 'a':
                    g.resource['a'] += 1
                else:
                    g.node[i]['resource'][x] += 1
                    produced[x] += 1

        # otherwise, restock the resources in the workspace
        else:
            for x in workspace:
                if x == 'a':
                    g.resource['a'] += 1
                else:
                    g.node[i]['resource'][x] += 1

        # cash final product
        for left, right in external_market:
            if left in g.node[i]['resource']:
                g.resource['a'] += g.node[i]['resource'][left] * right
                g.node[i]['resource'][left] = 0

    # measure the total amount of 'a'
    values['a'].append(g.resource['a'])

    # measure the total amount of other products
    for x in produced:
        values[x].append(values[x][-1] + produced[x])

import pycxsimulator
pycxsimulator.GUI(title='CNH ABM',interval=0, parameterSetters = []).start(func=[init,draw,step])
