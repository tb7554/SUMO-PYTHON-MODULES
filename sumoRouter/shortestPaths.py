from __future__ import division
from tools.sumolib.net import readNet

def findShortestPathBewtweenTwoNodes(net, start, end):
    
    # Retrieve edges from the net object
    net_edges = net.getEdges()
    
    #  Thanks to Hyperboreus @ stackoverflow.com for this Dijsktra implementation
    
    unvisited = {str(edge.getID()): None for edge in net_edges}
    visited = {str(edge.getID()): float("inf") for edge in net_edges}
    current = start
    currentTime = 0
    unvisited[current] = currentTime
    
    times = {}
    
    for edge in net_edges:
        times.update({str(edge.getID()):{}})
        for outgoing_edge in edge.getOutgoing():
            cost_to_outgoing_edge = edge.cost
            times[str(edge.getID())].update({str(outgoing_edge.getID()) : cost_to_outgoing_edge})
    
    via = {str(edge.getID()): None for edge in net_edges}
    
    while True:
        for outgoing_edge, time in times[current].items():
            if outgoing_edge not in unvisited: continue
            newTime = currentTime + time
            if unvisited[outgoing_edge] is None or unvisited[outgoing_edge] > newTime:
                unvisited[outgoing_edge] = newTime
                via.update({outgoing_edge:current})
        visited[current] = currentTime
        del unvisited[current]
        if not unvisited: break
        candidates = [edge for edge in unvisited.items() if edge[1]]
        if not candidates: break
        current, currentTime = sorted(candidates, key = lambda x: x[1])[0]
        if end in visited: break
        
    return visited, via
 
def findShortestPathToAllNodes(net, start):
    
    # Retrieve edges from the net object
    net_edges = net.getEdges()
    
    #  Thanks to Hyperboreus @ stackoverflow.com for this Dijsktra implementation
    
    unvisited = {str(edge.getID()): None for edge in net_edges}
    visited = {str(edge.getID()): float("inf") for edge in net_edges}
    current = start
    currentTime = 0
    unvisited[current] = currentTime
    
    times = {}
    
    for edge in net_edges:
        times.update({str(edge.getID()):{}})
        for outgoing_edge in edge.getOutgoing():
            cost_to_outgoing_edge = edge.cost
            times[str(edge.getID())].update({str(outgoing_edge.getID()) : cost_to_outgoing_edge})
    
    via = {str(edge.getID()): None for edge in net_edges}
    
    while True:
        for outgoing_edge, time in times[current].items():
            if outgoing_edge not in unvisited: continue
            newTime = currentTime + time
            if unvisited[outgoing_edge] is None or unvisited[outgoing_edge] > newTime:
                unvisited[outgoing_edge] = newTime
                via.update({outgoing_edge:current})
        visited[current] = currentTime
        del unvisited[current]
        if not unvisited: break
        candidates = [edge for edge in unvisited.items() if edge[1]]
        if not candidates: break
        current, currentTime = sorted(candidates, key = lambda x: x[1])[0]

    return visited, via

def find_shortest_paths_to_all_edges_not_via_these_edges(net, starting_edge, not_via=[]):

    # put not_via into a set
    not_via = set(not_via)

    # Retrieve edges from the net object
    net_edges = net.getEdges()

    #  Thanks to Hyperboreus @ stackoverflow.com for this Dijsktra implementation

    unvisited = {str(edge.getID()): None for edge in net_edges}
    visited = {str(edge.getID()): float("inf") for edge in net_edges}
    current = starting_edge
    currentTime = 0
    unvisited[current] = currentTime

    times = {}

    for edge in net_edges:
        times.update({str(edge.getID()): {}})
        for outgoing_edge in edge.getOutgoing():
            cost_to_outgoing_edge = edge.cost
            if edge in not_via : cost_to_outgoing_edge = float("inf")
            times[str(edge.getID())].update({str(outgoing_edge.getID()): cost_to_outgoing_edge})

    via = {str(edge.getID()): None for edge in net_edges}

    while True:
        for outgoing_edge, time in times[current].items():
            if outgoing_edge not in unvisited: continue
            newTime = currentTime + time
            if unvisited[outgoing_edge] is None or unvisited[outgoing_edge] > newTime:
                unvisited[outgoing_edge] = newTime
                via.update({outgoing_edge: current})
        visited[current] = currentTime
        del unvisited[current]
        if not unvisited: break
        candidates = [edge for edge in unvisited.items() if edge[1]]
        if not candidates: break
        current, currentTime = sorted(candidates, key=lambda x: x[1])[0]

    return visited, via

def find_shortest_paths_to_all_nodes_not_via_these_edges(net, starting_edge, not_via=[]):

    # from node
    starting_node = starting_edge.getToNode()

    # put not_via into a set
    not_via = set(not_via)

    # Retrieve edges from the net object
    net_nodes = net.getNodes()
    net_edges = net.getEdges()

    #  Thanks to Hyperboreus @ stackoverflow.com for this Dijsktra implementation

    unvisited = {node: None for node in net_nodes}
    visited = {node: float("inf") for node in net_nodes}
    current = starting_node
    currentTime = 0
    unvisited[current] = currentTime

    times = {}

    for node in net_nodes:
        times.update({node : {}})
        for outgoing_edge in node.getOutgoing():
            cost_via_outgoing_edge = outgoing_edge.cost
            if outgoing_edge in not_via : cost_via_outgoing_edge = float("inf")
            times[node].update({outgoing_edge.getToNode(): (outgoing_edge, cost_via_outgoing_edge)})

    via = {node : None for node in net_nodes}
    via_edges = {node : None for node in net_nodes}

    while True:
        for node, edge_and_time in times[current].items():
            via_edge = edge_and_time[0]
            time = edge_and_time[1]
            if node not in unvisited: continue
            newTime = currentTime + time
            if unvisited[node] is None or unvisited[node] > newTime:
                unvisited[node] = newTime
                via.update({node: current})
                via_edges.update({node:via_edge})
        visited[current] = currentTime
        del unvisited[current]
        if not unvisited: break
        candidates = [node for node in unvisited.items() if node[1]]
        if not candidates: break
        current, currentTime = sorted(candidates, key=lambda x: x[1])[0]

    return visited, via, via_edges

class addEdgeWeights2Net:

    """ Standalone class for reading netfile in a sumolib net object and adding edge weights """

    def __init__(self, net):
        self._net = net
        self._cost_attribute = 'traveltime'
        self.load_weights()

    def load_weights(self):
        # reset weights before loading
        for e in self._net.getEdges():
            e.cost = e.getLength() / e.getSpeed()
            
    def getNet(self):
        return self._net

    def getCostAttribute(self):
        return self._cost_attribute

class shortestPathsClass:
    
    """ Contains all the shortest paths between edges in the network """
    
    def __init__(self, net_filepath):
        net = readNet(net_filepath)
        netWithEdgeWeights = addEdgeWeights2Net(net)
        net = netWithEdgeWeights.getNet()

        self._paths = {}
        self.findPaths(net)
        
        self._maxPathCost = self.findMaxPathCost()
        self._maxElementCost = self.findMaxElementCost(net)
    
    def findPaths(self, net):
        """ Generate all the shortest paths and store in the _paths dict """
        
        net_edges = net.getEdges()
        num_edges = len(net_edges)
        edges_evaluated = 0
        # Initialise a dictionary which contains all the data 
        
        for start in net_edges:
            start = str(start.getID())
            self._paths.update({start:{}})
            [dijkstra_visited, dijkstra_via] = findShortestPathToAllNodes(net, start)
            for end in net_edges:
                end = str(end.getID())
                self._paths[start].update({end:([],dijkstra_visited[end])})
                current_edge = end
                while current_edge != None:
                    self._paths[start][end][0].append(current_edge)
                    current_edge = dijkstra_via[current_edge]
                self._paths[start][end][0].reverse()
            
            edges_evaluated += 1
            print("%d of %d completed" % (edges_evaluated, num_edges))
            
    def getPathCost(self, start, end):
        """ return cost of the shortest path (in travel time) """
        return self._paths[start][end][1]
    
    def getPath(self, start, end):
        """ return shortest path """
        return self._paths[start][end][0]
    
    def findMaxPathCost(self):
        maxCost = 0
        for start in self._paths:
            for end in self._paths[start]:
                if self._paths[start][end][1] > maxCost : maxCost = self._paths[start][end][1]
        return maxCost
    
    def findMaxElementCost(self, net):
        maxCost = 0
        for edge in net.getEdges():
            if edge.cost > maxCost : maxCost = edge.cost
        return maxCost
    
    def getMaxPathCost(self):
        return self._maxPathCost
    
    def getMaxElementCost(self):
        return self._maxElementCost

class shortestPathsNotViaOtherOutEdges(shortestPathsClass):

    def findPaths(self, net):
        """ Generate all the shortest paths and store in the _paths dict """

        net_edges = net.getEdges()
        num_edges = len(net_edges)
        edges_evaluated = 0
        # Initialise a dictionary which contains all the data

        for start in net_edges:

            from_node = start.getFromNode()
            out_edges = from_node.getOutgoing()
            out_edges_set = set(out_edges)
            out_edges_set.remove(start)

            start = str(start.getID())
            self._paths.update({start: {}})
            [dijkstra_visited, dijkstra_via] = find_shortest_paths_to_all_edges_not_via_these_edges(net, start, not_via=out_edges_set)
            for end in net_edges:
                end = str(end.getID())
                self._paths[start].update({end: ([], dijkstra_visited[end])})
                current_edge = end
                while current_edge != None:
                    self._paths[start][end][0].append(current_edge)
                    current_edge = dijkstra_via[current_edge]
                self._paths[start][end][0].reverse()

            edges_evaluated += 1
            print("%d of %d completed" % (edges_evaluated, num_edges))

class shortestPathToEndNodeNotViaOtherOutEdges(shortestPathsClass):

    def findPaths(self, net):
        """ Generate all the shortest paths and store in the _paths dict """

        net_edges = net.getEdges()
        num_edges = len(net_edges)
        edges_evaluated = 0
        # Initialise a dictionary which contains all the data

        for start in net_edges:

            from_node = start.getFromNode()
            out_edges = from_node.getOutgoing()
            out_edges_set = set(out_edges)
            out_edges_set.remove(start)

            self._paths.update({start.getID(): {}})
            [dijkstra_visited, dijkstra_via, dijkstra_via_edges] = find_shortest_paths_to_all_nodes_not_via_these_edges(net, start, not_via=out_edges_set)
            for end in net_edges:
                end_node = end.getToNode()
                self._paths[start.getID()].update({end.getID(): ([], dijkstra_visited[end_node])})
                current_node = end_node
                current_edge = end
                while current_node != None:
                    self._paths[start.getID()][end.getID()][0].append(current_edge.getID())
                    current_edge = dijkstra_via_edges[current_node]
                    current_node = dijkstra_via[current_node]
                self._paths[start.getID()][end.getID()][0].reverse()

            edges_evaluated += 1
            print("%d of %d completed" % (edges_evaluated, num_edges))

if __name__ == "__main__":

    # netfile = "../../_606_Random_/Net_XML_Files/Random-10x10-1-Lane-TLS.net.xml"
    #
    # sp = shortestPathToEndNodeNotViaOtherOutEdges(netfile)


    pass