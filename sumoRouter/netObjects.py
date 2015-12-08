#!/usr/bin/env python
"""
@file    netObjects.py
@author  Tim Barker
@date    09/01/2015

Edge and Junction objects and their object containers

"""
from __future__ import print_function, division
import tools.traci as traci

# Lane object
class laneObj():
    
    def __init__(self, index):
        self.index = str(index)
        self.occupancy = 0

# Edge object
class edgeObj():
    
    def __init__(self, edge_id, edge_type, frm, to, length, speed, num_lanes, crit_occupancy):
        # Static values used during the simulation
        self.edge_id = edge_id
        self.type = str(edge_type)
        self.frm = str(frm)
        self.to = str(to)
        self.length = float(length)
        self.speed = float(speed)
        self.minTravelTime = self.length/self.speed
        self.crit_occupancy = float(crit_occupancy)
        self.lanesContainer = {} # Lane array
        
        for ii in range(0, num_lanes):
            self.addLane(ii)
        
        # Dynamic values used during the simulation
        self.occupancy = 0

        # Recorded values for the purposes of analysing results
        #self.occupancy_over_time = []
    
    def __repr__(self):
        string = ("Type: %s, From: %s, To: %s, Length: %f, Speed: %f, Min Travel Time: %f, Critical Occupancy: %f, Num Lanes: %d" \
                  % (self.type, self.frm, self.to, self.length, self.speed, self.minTravelTime, self.crit_occupancy, len(self.lanesContainer)))
        return string
    
    def addLane(self, index):
        laneID = ("%s_%d" % (self.edge_id, index))
        self.lanesContainer.update({str(laneID):laneObj(index)})
        
    def updateOccupancy(self):
        numlanes = len(self.lanesContainer)
        self.occupancy = 0
        for lane in self.lanesContainer:
            self.lanesContainer[lane].occupancy = traci.lane.getLastStepOccupancy(lane)
            self.occupancy += self.lanesContainer[lane].occupancy
        self.occupancy /= numlanes
        
        # update the max occupancy and cumulative occupancy values
#self.occupancy_over_time.append(self.occupancy)
        
# Edge object array
class edgeObjContainer():
    
    def __init__(self):
        self.container = {}
        
    def addEdge(self, edge_id, edge_type, frm, to, length, speed, num_lanes, crit_occupancy=0.2):
        self.container.update({str(edge_id):edgeObj(edge_id, edge_type, frm, to, length, speed, num_lanes, crit_occupancy)})
        
    def addLane2Edge(self, edgeID, index):
        laneID = str(edgeID) + "_" + str(index)
        self.container[str(edgeID)].addLane(laneID, index)
        
    def updateOccupancies(self):
        for edge in self.container:
            self.container[edge].updateOccupancy()
            
class junctionObj():
    
    def __init__(self, x, y, junc_type):
        self.x = float(x)
        self.y = float(y)
        self.type = str(junc_type)
        self.incLanes = []
        # Identify nodes that can be reached via this node. A dictionary is used with the format {junction ID : connecting edge}
        self.children = {}
        self.degree = 0
        
class junctionObjContainer():
    
    def __init__(self):
        self.container = {}
        
    def addJunction(self, juncID, x, y, junc_type):
        self.container.update({str(juncID):junctionObj(x, y, junc_type)})
        
    def addIncLane2Junc(self, juncID, lane):
        self.container[str(juncID)].incLanes.append(lane)
        
    def addChild2Junc(self, juncID, child, viaEdge):
        self.container[str(juncID)].children.update({str(child):str(viaEdge)})
        self.container[str(juncID)].degree += 1

class edgeType():
    
    def __init__(self, priority, numLanes, speed):
        self.priority = priority
        self.numLanes = numLanes
        self.speed = speed

class edgeTypeContainer():
      
    def __init__(self):
        self.container = {}
        self.addEdgeType("default", "-1", "1", "13.9")
          
    def addEdgeType(self, id, priority, numLanes, speed):
        self.container.update({id:edgeType(priority, numLanes, speed)})
        
def findJuncChildren(juncContainer, edgeContainer):
    
    # for every edge, go through and work out the parent and child node, and therefore assign children to every node
    for edge in edgeContainer.container:
        juncID = edgeContainer.container[edge].frm
        child = edgeContainer.container[edge].to
        viaEdge = edge
        juncContainer.addChild2Junc(juncID, child, viaEdge)
    
    return juncContainer
      
def main():
    
    node_filepath = ("%s/config_files/%s.nod.xml" % (directory_path, directory_name))
    edge_filepath = ("%s/config_files/%s.edg.xml" % (directory_path, directory_name))
    edgeTypes_filepath = ("%s/config_files/%s.typ.xml" % (directory_path, directory_name))
    connections_filepath = ("%s/config_files/%s.con.xml" % (directory_path, directory_name))
    netoutput_filepath = ("%s/config_files/%s.net.xml" % (directory_path, directory_name))