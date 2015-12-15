#!/usr/bin/env python
"""

@file    vehObj.py
@author  Tim Barker
@date    09/01/2015

classes for creating a container for vehicle objects

"""

import tools.traci as traci
from sumoRouter import vehicleRouter

class vehObj():
    
    def __init__(self, vehID, vehType, route, destination, departTime, router_mode, CBR_alpha):
        # Static vehicle properties
        self.dest = destination # destination edge        
        self.router_mode = router_mode # sets the vehicle's router mode choice, to enable testing different routing algorithms, or used mixed routing algorithms
        
        if router_mode == "CoverageBasedRouting":
            self.alpha = CBR_alpha # Value of alpha used to tune the coverage based routing algorithm (if used)
        else:
            self.alpha = None
            
    def getDestination(self):
        return self.dest
    
    def getRouterMode(self):
        return self.router_mode
        
class vehObjContainer():
    
    def __init__(self, sumolibNet, loop_ids, CBR_alpha):        
        # Simulation container
        self.container = {} # The container of vehicle objects (only contains vehicles currently in the simulation)
        
        # Objects/constants for vehicle routing
        #self.routerObj = vehicleRouter.createRouterObject(sumolibNet) # The vehicle routing object which decides on the best route for a vehicle to take
        self.loop_ids = loop_ids # Array of induction loops ids, to notify when a vehicle is approaching a junction
        self.CBR_alpha = CBR_alpha
    
    # add a vehicle to the container
    def addVeh(self, vehID, vehType, route, time_step):
        vehRoute = route
        end_edge = route.pop()
        destination = end_edge

        if vehType == "HumanCoverageRouted" or vehType == "DriverlessCoverageRouted":
            router_mode = "CoverageBasedRouting"
        elif vehType == "HumanStandard" or vehType == "DriverlessStandard":
            router_mode = None
        else:
            router_mode = None
            print("Warning, vehicle type not identified and incorrect router (%s) may have been assigned to vehicle type %s" % (router_mode, vehType))

        self.container.update({vehID : vehObj(vehID, vehType, vehRoute, destination, time_step, router_mode, self.CBR_alpha)})
    
    # remove a vehicle from the container
    def remVeh(self, vehID, time_step):
        #print(self.container[vehID].route)
        self.container[vehID].arrivalTime = time_step
        self.container[vehID].tripDuration = time_step - self.container[vehID].departTime
        del self.container[vehID]
        
    def updateVehicles(self, time_step):
        arrived = traci.simulation.getArrivedIDList()
        departed = traci.simulation.getDepartedIDList()
        for veh in arrived:
            self.remVeh(veh, time_step)
        for veh in departed:
            vehRoute = traci.vehicle.getRoute(veh)
            vehType = traci.vehicle.getTypeID(veh)
            self.addVeh(veh, vehType, vehRoute, time_step)
            
    def vehiclesApproachingJunctions(self):
        vehicles_approaching_junctions = {} 
    
        for loop in self.loop_ids:
            if traci.inductionloop.getLastStepVehicleIDs(loop):
                edge = loop.split("_")[0]
                vehicles_approaching_junctions.update({edge:traci.inductionloop.getLastStepVehicleIDs(loop)}) # Gives you the IDs of all vehicles which passed over this induction loop 
# in the last time step in a dictionary
        
        return vehicles_approaching_junctions
    
    def findVehicleRoute(self, vehID, starting_edge):
        router_mode = self.container[vehID].router_mode
        alpha = self.container[vehID].alpha
        ending_edge = self.container[vehID].dest
        
        if starting_edge != ending_edge:
            vehRoute = self.routerObj.route(router_mode, starting_edge, ending_edge, alpha)
        else:
            vehRoute = self.container[vehID].route
        
        return vehRoute
                
    def updateVehicleRoutes(self):
        
        vehicles_approaching_junctions = self.vehiclesApproachingJunctions() # format {edge : [veh1, veh2, etc]}
        
        for edge in vehicles_approaching_junctions:
            for veh in vehicles_approaching_junctions[edge]:
                if not(self.container[veh].dest == self.edgeContainer.container[edge].to) and self.container[veh].router_mode != None:
                    vehRoute = self.findVehicleRoute(veh, edge)
                    traci.vehicle.setRoute(veh, vehRoute)