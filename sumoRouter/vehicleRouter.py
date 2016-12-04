#!/usr/bin/env python
"""
@file    netObjFuncs.py
@author  Tim Barker
@date    09/01/2015

Class and associated functions to perform all routing algorithms on the network. This class stores the lookup tables etc, so they do not need to be stored in the main simulation

"""
from __future__ import print_function
import math
import random
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
        self.edgeOccs = edgeOccupancies.edgeOccupanciesClass(self.net)
        
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
    
    def getCoverageControlConstants(self):
        
        max_traveltime = self.shortestPaths.getMaxPathCost()
        
        max_element_time = self.shortestPaths.getMaxElementCost()         
                
        ccValues = {"max_traveltime" : max_traveltime, "max_element_time" : max_element_time}
    
        return ccValues

    def selfLoopChecker(self, starting_edge, route):

        selfLoop = False
        if len(route) == 2:
            return selfLoop
        else:
            fromNode = starting_edge.getFromNode()
            toNode = starting_edge.getToNode()
            edge_2 = route.pop(1)
            if edge_2 == ("%sto%s" % (toNode, fromNode)): selfLoop = True
        return selfLoop

    def coverageBasedRoutingTime(self, starting_edge, ending_edge, alpha):
        
        sigma = 10
        best_route = [starting_edge]
        
        # For every edge leading from the current edge:
        for road_choice in self.net.getEdge(starting_edge).getOutgoing():
            
            road_choice_ID = road_choice.getID()
            route_traveltime = self.shortestPaths.getPathCost(road_choice_ID, ending_edge)
            
            if route_traveltime != float("inf"):
                route = self.shortestPaths.getPath(road_choice_ID, ending_edge)
                
                # Calculate the distance cost using dijkstra
                time_based_cost = (route_traveltime)/(self.ccValues["max_traveltime"] + self.ccValues["max_element_time"] )
                
                # Calculate the occupancy cost using the defined relationship
                occupancy_of_edge = self.edgeOccs.getEdgeOccupancyByID(road_choice_ID)
                critical_occupancy = self.edgeOccs.getEdgeCriticalOccupancyByID(road_choice_ID)
                
                if occupancy_of_edge < critical_occupancy:
                    occupancy_based_cost = occupancy_of_edge
                else:
                    occupancy_based_cost = 1 - math.exp(-(sigma*occupancy_of_edge))
                
                # Combine the two costs using the tuning parameter alpha
                total_cost = alpha*time_based_cost + (1 - alpha)*occupancy_based_cost

                if self.selfLoopChecker(self.net.getEdge(starting_edge), route[:]):
                    total_cost = 999
            else:
                total_cost = 999
            
            self.routeOptionsContainer.update({road_choice_ID : routeOption(route, total_cost)})
                                  
        # Pick the route with the lowest total cost
        best_route.extend(self.returnLowestCostingRoute())      
        
        # clear the routeOptionsContainer
        self.clearRouteChoicesContainer()

        return best_route

    def q_learning_flow_distribution_routing(self, starting_edge, ending_edge, alpha):

        best_route = [starting_edge]

        routes = []
        route_traveltimes = []
        occ_costs = []
        cost_function = []

        for road_choice in self.net.getEdge(starting_edge).getOutgoing():
            road_choice_ID = road_choice.getID()
            route_traveltime = self.shortestPaths.getPathCost(road_choice_ID, ending_edge)

            if route_traveltime != float("inf"):
                routes.append(self.shortestPaths.getPath(road_choice_ID, ending_edge))
                route_traveltimes.append(route_traveltime)

                occupancy_of_edge = self.edgeOccs.getEdgeOccupancyByID(road_choice_ID)
                occ_costs.append(occupancy_of_edge**alpha)

        min_traveltime = min(route_traveltimes)

        for index, travel_time in route_traveltimes:
            route_cost = travel_time/min_traveltime - 1
            occ_cost = occ_costs[index]
            cost_function.append(route_cost + occ_cost)

        min_cost_routes = [routes[ii] for ii,x in cost_function if x == min(cost_function)]

        best_route.extend(random.choice(min_cost_routes))

        return best_route
    
    def route(self, router_mode, starting_edge, ending_edge, alpha):
        
        if router_mode == "CoverageBasedRouting":
            return self.coverageBasedRoutingTime(starting_edge, ending_edge, alpha)
        elif router_mode == "Q Learning Flow Distribution":
            return self.q_learning_flow_distribution_routing(starting_edge, ending_edge, alpha)
        else:
            print("No recognised routing method given. Defaulting to routing using Dijkstra's algorithm.")
            return self.dijkstra(starting_edge,  ending_edge)
        
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