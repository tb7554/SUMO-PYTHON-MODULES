#!/usr/bin/env python
"""
@file    netObjFuncs.py
@author  Tim Barker
@date    09/01/2015

Class and associated functions to perform all routing algorithms on the network. This class stores the lookup tables etc, so they do not need to be stored in the main simulation

"""
from __future__ import print_function
import math
from random import randint
from sumoRouter import edgeOccupancies

# This class stores a route and its score when you multiple routes to choose from, it is meant to be a temporary object
class routeOption():
    
    def __init__(self, route, cost):
        self.route = route
        self.cost = cost

class createRouterObject():
    
    def __init__(self, shortestPathContainer, sumolibnet):
        # netObjects
        self.net = sumolibnet
        
        # Constants used for vehicle routing
        self.shortestPaths = shortestPathContainer
        self.ccValues = self.getCoverageControlConstants() # Constants used in coverage control
        
        # Variables used for routing
        self.edgeOccs = edgeOccupancies.edgeOccupancies(self.net)
        
        # Temporary Containers (dynamic, usually erased after use)
        self.routeOptionsContainer = {}
    
    def updateEdgeOccupancies(self):
        self.edgeOccs.updateAllEdgeOccupancies()
                
    def returnLowestCostingRoute(self):
        min_cost = 999
        route_choice = None
        for route in self.routeOptionsContainer:
                if self.routeOptionsContainer[route].cost < min_cost:
                    min_cost = self.routeOptionsContainer[route].cost
                    route_choice = self.routeOptionsContainer[route].route
                elif self.routeOptionsContainer[route].cost == min_cost:
                    change_route = randint(0,1)
                    if change_route:
                        route_choice = self.routeOptionsContainer[route].route
        
        return route_choice
    
    def clearRouteChoicesContainer(self):
        self.routeOptionsContainer = {}
    
    def getCoverageControlConstants(self, sumolibnet):
        
        max_traveltime = self.shortestPaths.getMaxCost()
        
        max_element_time = self.shortestPaths.getMaxElementCost()         
                
        ccValues = {"max_traveltime" : max_traveltime, "max_element_time" : max_element_time}
    
        return ccValues
    
    def selfLoopChecker(self, route_by_junctions):

        selfLoop = False
        if len(route_by_junctions) == 1:
            return selfLoop
        else:
            while route_by_junctions:
                junc = route_by_junctions.pop(0)
                if junc in route_by_junctions:
                    selfLoop = True         
        return selfLoop
    
    def coverageBasedRoutingTime(self, start_edge, end_junction, alpha):
        
        sigma = 10
        
        # Convert starting edge starting junction
        start_junction = self.edgeContainer.container[start_edge].to
        
        # For every edge leading from the current edge:
        for road_choice in self.juncContainer.container[start_junction].children:
            
            # Create an array to store the actual route being suggested
            route = []
            route.append(start_junction)

            # Evaluate the time to travel along the edge you are looking at, and the estimated time the car will have to travel for if it takes it
            evaluate_time_from_this_junction = self.edgeContainer.container[self.juncContainer.container[start_junction].children[road_choice]].to
            
            route_traveltime = netObjFuncs.lookupTable(self.timeTable, evaluate_time_from_this_junction, end_junction)
            
            if route_traveltime != float("inf"):
                rest_of_route = netObjFuncs.lookupTable(self.routeTable, evaluate_time_from_this_junction, end_junction)
                #print(rest_of_route)
                # Append the other junctions to the route
                for element in rest_of_route:
                    route.append(element)
                #print(route)
                road_traveltime = self.edgeContainer.container[self.juncContainer.container[start_junction].children[road_choice]].minTravelTime
                
                # Calculate the distance cost using dijkstra
                time_based_cost = (route_traveltime + road_traveltime)/(self.ccValues["max_traveltime"] + self.ccValues["max_element_time"] )
                
                # Calculate the occupancy cost using the defined relationship
                
                occupancy_of_edge = self.edgeContainer.container[self.juncContainer.container[start_junction].children[road_choice]].occupancy
                critical_occupancy = self.edgeContainer.container[self.juncContainer.container[start_junction].children[road_choice]].crit_occupancy
                
                if occupancy_of_edge < critical_occupancy:
                    occupancy_based_cost = occupancy_of_edge
                else:
                    occupancy_based_cost = 1 - math.exp(-(sigma*occupancy_of_edge))
                
                # Combine the two costs using the tuning parameter alpha
                total_cost = alpha*time_based_cost + (1 - alpha)*occupancy_based_cost
                
                route_by_junctions = []
                for junc in route:
                    route_by_junctions.append(junc)
    
                if self.selfLoopChecker(route_by_junctions):
                    total_cost = 999
            else:
                total_cost = 999
                #print("loop")
            # Add this option to the route choices container
            #print(route, total_cost)
            
            self.routeOptionsContainer.update({road_choice : routeOption(route, total_cost)})
            
                        
        # Pick the route with the lowest total cost
        best_route = self.returnLowestCostingRoute()
        
        #print(best_route)
        
        # Convert from junctions to edges
        route_via_edges = self.junctions2Edges(start_edge, best_route)
        
        #print(start_edge, route_via_edges)
        
        # clear the routeOptionsContainer
        self.clearRouteChoicesContainer()

        return route_via_edges
    
    def route(self, router_mode, starting_edge, end_edge, alpha):
        
        if router_mode == "CoverageBasedRouting":
            return self.coverageBasedRoutingTime(starting_edge, end_junction, alpha)
        
        else:
            print("No recognised routing method given. Defaulting to routing using Dijkstra's algorithm.")
            return self.dijkstra(starting_edge,  end_junction)
        
def debugger():
    from sumoFileGen import pickleFunc
    directory_path = os.getcwd()
    
    edgeContainer = pickleFunc.load_obj('%s/../netObjects/EdgeContainer' % (directory_path))
    juncContainer = pickleFunc.load_obj('%s/../netObjects/JuncContainer'% (directory_path))
    alpha = 0.1
    
    router =  createRouterObject(edgeContainer, juncContainer, alpha)
    router.route('coverage_based_routing', '-1/-1to0/0', '2/2')
    
if __name__ == "__main__":
    debugger()