#!/usr/bin/env python
"""
@file    netObjFuncs.py
@author  Tim Barker
@date    09/01/2015

Functions which take the juncObj and edgeObj classes defined in the ApiExtension file

"""
from __future__ import print_function

def findShortestDistance(juncContainer, edgeContainer, start):
    
    #  Thanks to Hyperboreus @ stackoverflow.com for this Dijsktra implementation
  
    nodes = juncContainer.container
    unvisited = {node: None for node in nodes}
    visited = {node: float("inf") for node in nodes}
    current = start
    currentDistance = 0
    unvisited[current] = currentDistance
    
    distances = {}
    
    for junc in juncContainer.container:
        distances.update({junc:{}})
        for child in juncContainer.container[junc].children:
            distance_to_child = edgeContainer.container[juncContainer.container[junc].children[child]].length
            distances[junc].update({ child : distance_to_child})
    
    via = {node: None for node in nodes}
    
    while True:
        for neighbour, distance in distances[current].items():
            if neighbour not in unvisited: continue
            newDistance = currentDistance + distance
            if unvisited[neighbour] is None or unvisited[neighbour] > newDistance:
                unvisited[neighbour] = newDistance
                via.update({neighbour:current})
        visited[current] = currentDistance
        del unvisited[current]
        if not unvisited: break
        candidates = [node for node in unvisited.items() if node[1]]
        if not candidates: break
        current, currentDistance = sorted(candidates, key = lambda x: x[1])[0]
    
    return visited, via

def findShortestTime(juncContainer, edgeContainer, start):
    
    #  Thanks to Hyperboreus @ stackoverflow.com for this Dijsktra implementation
  
    nodes = juncContainer.container
    unvisited = {node: None for node in nodes}
    visited = {node: float("inf") for node in nodes}
    current = start
    currentTime = 0
    unvisited[current] = currentTime
    
    times = {}
    
    for junc in juncContainer.container:
        times.update({junc:{}})
        for child in juncContainer.container[junc].children:
            time_to_child = edgeContainer.container[juncContainer.container[junc].children[child]].minTravelTime
            times[junc].update({ child : time_to_child})
    
    via = {node: None for node in nodes}
    
    while True:
        for neighbour, time in times[current].items():
            if neighbour not in unvisited: continue
            newTime = currentTime + time
            if unvisited[neighbour] is None or unvisited[neighbour] > newTime:
                unvisited[neighbour] = newTime
                via.update({neighbour:current})
        visited[current] = currentTime
        del unvisited[current]
        if not unvisited: break
        candidates = [node for node in unvisited.items() if node[1]]
        if not candidates: break
        current, currentTime = sorted(candidates, key = lambda x: x[1])[0]

    return visited, via

def findShortestPath(via, start, end):
    
    current = end
    route = []
    
    while start not in route:
        route.append(current)
        if current == None: break
        current = via[current]
         
    route_reversed=[]
    
    n = len(route)
    ii = 0
    while ii < n:
        route_reversed.append(route.pop())
        ii += 1

    return route_reversed

def genDistanceAndRouteTables(juncContainer, edgeContainer,  print_distance_table = False, print_route_table = False):
    
    # DISTANCE TABLE
    # Set up dictionaries to hold the shortest distances between nodes, and the shortest paths between nodes
    distanceTable = {}
    routeTable = {}
    
    # For every junction, update the distance table with dictionary of shortest distances to each node
    for start in juncContainer.container:
        distances, via = findShortestDistance(juncContainer, edgeContainer, start)
        distanceTable.update({start:distances})
        routeTable.update({start : {}})
        for end in juncContainer.container:
            if via[end] != None:
                route = findShortestPath(via, start, end)
                routeTable[start].update({end : route})
            elif start == end:
                routeTable[start].update({end : [start]})
            else:
                routeTable[start].update({end : None})
            
    if print_distance_table:
        # Print the two tables in a table like format
        
        print("\t", end = "")
        for item in distanceTable:
            print("%s" % item, end = "\t")
        print("\n")
        
        for item in distanceTable:
            print(item, end = "\t")
            for other_item in distanceTable:
                print(distanceTable[item][other_item], end = "\t")
            print("\n")
    
    if print_route_table:
        for item in routeTable:
            for other_item in routeTable:
                print("%s -> %s: %s" % (item, other_item, routeTable[item][other_item]))
        
    return distanceTable, routeTable

def genTimeAndRouteTables(juncContainer, edgeContainer, print_time_table = False, print_route_table = False):
    # TIMES TABLE
    timeTable = {}
    routeTable = {}
    
    # For every junction, update the distance table with dictionary of shortest distances to each node
    for start in juncContainer.container:
        times, via = findShortestTime(juncContainer, edgeContainer, start)
        timeTable.update({start:times})
        routeTable.update({start : {}})
        for end in juncContainer.container:
            if via[end] != None:
                route = findShortestPath(via, start, end)
                routeTable[start].update({end : route})
            elif start == end:
                routeTable[start].update({end : [start]})
            else:
                routeTable[start].update({end : None})
                
    if print_time_table:
        # Print the two tables in a table like format
        
        print("\t", end = "")
        for item in timeTable:
            print("%s" % item, end = "\t")
        print("\n")
        
        for item in timeTable:
            print(item, end = "\t")
            for other_item in timeTable:
                try:
                    print(int(timeTable[item][other_item]), end = "\t")
                except OverflowError:
                    print(str(timeTable[item][other_item]), end = "\t")
            print("\n")
    
    if print_route_table:
    
        for item in routeTable:
            for other_item in routeTable:
                print("%s -> %s: %s" % (item, other_item, routeTable[item][other_item]))
        
    return timeTable, routeTable

def lookupTable(table, row, column):
    
    return table[row][column]

def printTable(table):
    
    print("\t", end = "")
    for item in table:
        print("%s" % item, end = "\t")
    print("\n")
    
    for item in table:
        print(item, end = "\t")
        for other_item in table:
            try:
                print(int(table[item][other_item]), end = "\t")
            except OverflowError:
                print(str(table[item][other_item]), end = "\t")
        print("\n")
        
def printRoutes(table):
    
    for item in table:
        for other_item in table:
            print("%s -> %s: %s" % (item, other_item, table[item][other_item]))


def debug():
    from sumoFileGen import pickleFunc
    edgeContainer = pickleFunc.load_obj('/space/tb7554/workspace/grid_3by3_1O_1D/obj/edgeContainer')
    juncContainer = pickleFunc.load_obj('/space/tb7554/workspace/grid_3by3_1O_1D/obj/juncContainer')
    #ist, route = genDistanceAndRouteTables(juncContainer, edgeContainer, print_distance_table = False)
    
    #for node in dist:
    #    print(node, ":", dist[node])
    
    time, route = genTimeAndRouteTables(juncContainer, edgeContainer, print_time_table = 1, print_route_table = 1)
    #for node in time:
        #print(node, ":", time[node])
     
if __name__ == '__main__':
    debug()