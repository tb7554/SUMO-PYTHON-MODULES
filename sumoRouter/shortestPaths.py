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

class addEdgeWeights2Net:

    """ Standalone class for reading netfile in a sumolib net object and adding edge weights """

    def __init__(self, netfile):
        self._net = readNet(netfile)
        self._cost_attribute = 'traveltime'
        self.load_weights()

    def load_weights(self):
        # reset weights before loading
        for e in self.net.getEdges():
            e.cost = e.getLength() / e.getSpeed()
            
    def getNet(self):
        return self._net

    def getCostAttribute(self):
        return self._cost_attribute

class shortestPaths:
    
    """ Contains all the shortest paths between edges in the network """
    
    def __init__(self, net):
        self._net = net
        self._paths = {}
        self.findPaths(self._net)
    
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
                self._paths[start][end][0].append(start)
                self._paths[start][end][0].reverse()
            
            edges_evaluated += 1
            print("%d of %d completed" % (edges_evaluated, num_edges))
            
    def getPathCost(self, start, end):
        """ return cost of the shortest path (in travel time) """
        return self._paths[start][end][1]
    
    def getPath(self, start, end):
        """ return shortest path """
        return self._paths[start][end][0]
    
    def getMaxPathCost(self):
        maxCost = 0
        for start in self._paths:
            for end in self._paths[start]:
                if self._paths[start][end][1] > maxCost : maxCost = self._paths[start][end][1]
        return maxCost
    
    def getMaxElementCost(self):
        maxCost = 0
        for edge in self._net.getEdges():
            if edge.cost > maxCost : maxCost = edge.cost
        return maxCost
            
