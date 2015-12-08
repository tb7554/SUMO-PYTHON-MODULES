#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Functions for extracting node and edge XML files from a net file generated using OSM data. It removes cycleways and pedestrian paths and rebuilds the network.

Author: Tim Barker
Created: 10/06/2015
Modified: 10/06/2015
"""

from __future__ import print_function, division
import sys, os
import xml.etree.ElementTree as ET
from sumoFileGen import pickleFunc
from sumoRouter import netObjects, netObjFuncs
    
def edgeFile(net, edge_filepath, allowed_road_types, ETC):
    
    EC = netObjects.edgeObjContainer()
    usedJuncs = []
    usedEdges = []
    
    EDGEFILE = open(edge_filepath, 'w')
    print('<edges>', file=EDGEFILE)

    for item in net:
        name = item.tag
        if name == "edge":
            edge_attributes = item.attrib
            if "function" in edge_attributes.keys():
                if edge_attributes["function"] != "internal":
                    if "type" in edge_attributes.keys():
                        if edge_attributes["type"] in allowed_road_types:
                            edge_id = edge_attributes["id"]
                            edge_frm = edge_attributes["from"]
                            edge_to = edge_attributes["to"]
                            edge_type = edge_attributes["type"]
                            print('\t<edge id="%s" from="%s" to="%s" type="%s"/>' % (edge_id, edge_frm, edge_to, edge_type), file=EDGEFILE)      
                            
                            num_lanes = 0
                            for lane in item:
                                edge_speed = lane.attrib["speed"]
                                edge_length = lane.attrib["length"]
                                num_lanes += 1
                            
                            EC.addEdge(edge_id, edge_type, edge_frm, edge_to, edge_length, edge_speed, num_lanes, crit_occupancy=0.2)
                            
                            if edge_frm not in usedJuncs:
                                usedJuncs.append(edge_frm)
                            if edge_to not in usedJuncs:
                                usedJuncs.append(edge_to)
                                
                            usedEdges.append(edge_id)
                            
                    elif "default" in allowed_road_types:
                        edge_id = edge_attributes["id"]
                        edge_frm = edge_attributes["from"]
                        edge_to = edge_attributes["to"]
                        edge_type = "default"
                        print('\t<edge id="%s" from="%s" to="%s" type="%s"/>' % (edge_id, edge_frm, edge_to, edge_type), file=EDGEFILE)
                        
                        num_lanes = 0
                        for lane in item:
                            edge_speed = lane.attrib["speed"]
                            edge_length = lane.attrib["length"]
                            num_lanes += 1
                    
                        EC.addEdge(edge_id, edge_type, edge_frm, edge_to, edge_length, edge_speed, num_lanes, crit_occupancy=0.2)
                        
                        if edge_frm not in usedJuncs:
                            usedJuncs.append(edge_frm)
                        if edge_to not in usedJuncs:
                            usedJuncs.append(edge_to)
                            
                        usedEdges.append(edge_id)
                        
            elif "type" in edge_attributes.keys() and edge_attributes["type"] in allowed_road_types:
                edge_id = edge_attributes["id"]
                edge_frm = edge_attributes["from"]
                edge_to = edge_attributes["to"]
                edge_type = edge_attributes["type"]
                print('\t<edge id="%s" from="%s" to="%s" type="%s"/>' % (edge_id, edge_frm, edge_to, edge_type), file=EDGEFILE)
                
                num_lanes = 0
                for lane in item:
                    edge_speed = lane.attrib["speed"]
                    edge_length = lane.attrib["length"]
                    num_lanes += 1
                    
                EC.addEdge(edge_id, edge_type, edge_frm, edge_to, edge_length, edge_speed, num_lanes, crit_occupancy=0.2)
        
                if edge_frm not in usedJuncs:
                    usedJuncs.append(edge_frm)
                if edge_to not in usedJuncs:
                    usedJuncs.append(edge_to)
                    
                usedEdges.append(edge_id)
                    
            elif "default" in allowed_road_types:
                edge_id = edge_attributes["id"]
                edge_frm = edge_attributes["from"]
                edge_to = edge_attributes["to"]
                edge_type = "default"
                print('\t<edge id="%s" from="%s" to="%s" type="%s"/>' % (edge_id, edge_frm, edge_to, edge_type), file=EDGEFILE)
                
                num_lanes = 0
                for lane in item:
                    edge_speed = lane.attrib["speed"]
                    edge_length = lane.attrib["length"]
                    num_lanes += 1
                    
                EC.addEdge(edge_id, edge_type, edge_frm, edge_to, edge_length, edge_speed, num_lanes, crit_occupancy=0.2)
                
                if edge_frm not in usedJuncs:
                    usedJuncs.append(edge_frm)
                if edge_to not in usedJuncs:
                    usedJuncs.append(edge_to)
                    
                usedEdges.append(edge_id)
                                   
    print('</edges>', file=EDGEFILE)
    EDGEFILE.close()
    
    return EC, usedEdges, usedJuncs

def nodeFile(net, node_filepath, usedJuncs):
    
    JC = netObjects.junctionObjContainer()
    
    # Prints the node file from the net file
    NODEFILE = open(node_filepath, 'w') # Open the node file
    print('<nodes>', file=NODEFILE) # Print the first line
                            
    for item in net:
        name = item.tag
        if name == "junction":
            junc_attributes = item.attrib
            junc_id = junc_attributes["id"]            
            if junc_id in usedJuncs:
                if "type" in junc_attributes.keys():
                    if junc_attributes["type"] != "internal":      
                        junc_x = junc_attributes["x"]
                        junc_y = junc_attributes["y"]
                        junc_type = junc_attributes["type"]
        
                        print('\t<node id="%s" x="%s" y="%s" type="%s"/>' % (junc_id, junc_x, junc_y, junc_type), file=NODEFILE)
                        
                        JC.addJunction(junc_id, junc_x, junc_y, junc_type)
                
                else:            
                    junc_x = junc_attributes["x"]
                    junc_y = junc_attributes["y"]
                    junc_type = "None"
                    
                    print('\t<node id="%s" x="%s" y="%s"/>' % (junc_id, junc_x, junc_y), file=NODEFILE)  
                    
                    JC.addJunction(junc_id, junc_x, junc_y, junc_type)
    
    print('</nodes>', file=NODEFILE)
    NODEFILE.close()

    return JC

def roadTypesFile(net, edgeTypes_filepath):
    
    ETC = netObjects.edgeTypeContainer()
    road_types = ['default']
    
    TYPEFILE = open(edgeTypes_filepath, 'w')
    print("<types>", file=TYPEFILE)
    
    print('\t<type id="default" priority="-1" numLanes="1" speed="13.4"/>', file=TYPEFILE)
          
    for item in net:
        name = item.tag
        if name == "edge":
            edge_attributes = item.attrib
            if "function" in edge_attributes.keys():
                if edge_attributes["function"] != "internal":
                    if "type" in edge_attributes.keys():
                        if edge_attributes["type"] not in road_types:
                            
                            edge_type = edge_attributes["type"]
                            edge_priority = edge_attributes["priority"]
                            
                            num_lanes = 0
                            for lane in item:
                                num_lanes += 1
                                edge_speed = lane.attrib["speed"]
                            
                            road_types.append(edge_type)
                            
                            print('\t<type id="%s" priority="%s" numLanes="%s" speed="%s"/>' % (str(edge_type), str(edge_priority), str(num_lanes), str(edge_speed)), file=TYPEFILE)
                            
                            ETC.addEdgeType(edge_type, edge_priority, num_lanes, edge_speed)
                            
            elif "type" in edge_attributes.keys():
                if edge_attributes["type"] not in road_types:
                    
                    edge_type = edge_attributes["type"]
                    edge_priority = edge_attributes["priority"]
                    
                    num_lanes = 0
                    for lane in item:
                        num_lanes += 1
                        edge_speed = lane.attrib["speed"]
                    
                    road_types.append(edge_type)
                    
                    print('\t<type id="%s" priority="%s" numLanes="%s" speed="%s"/>' % (str(edge_type), str(edge_priority), str(num_lanes), str(edge_speed)), file=TYPEFILE)     
                    
                    ETC.addEdgeType(edge_type, edge_priority, num_lanes, edge_speed)
                    
    print("</types>", file=TYPEFILE)
    TYPEFILE.close()
    
    return ETC
    
def connFile(net, connections_filepath, usedEdges):

    CONNFILE = open(connections_filepath, 'w')
    print("<connections>", file=CONNFILE)
    
    for item in net:
        name = item.tag
        if name == "connection":
            con_attributes = item.attrib
            con_from = con_attributes["from"]
            con_to = con_attributes["to"]
            if con_from in usedEdges and con_to in usedEdges:
                con_fromLane = con_attributes["fromLane"]
                con_toLane = con_attributes["toLane"]
                print('\t<connection from="%s" to="%s" fromLane="%s" toLane="%s"' % (con_from, con_to, con_fromLane, con_toLane), end="", file=CONNFILE)
                
                if "via" in con_attributes.keys():
                    if con_attributes["via"] in usedEdges:
                        print(' via="%s"' % (con_attributes["via"]), end="", file=CONNFILE)
                        
                if "dir" in con_attributes.keys():
                    print(' dir="%s"' % (con_attributes["dir"]), end="", file=CONNFILE)

                if "state" in con_attributes.keys():
                    print(' state="%s"' % (con_attributes["state"]), end="", file=CONNFILE)
                    
                print("/>", file=CONNFILE)
                
    print("</connections>", file=CONNFILE)
    CONNFILE.close()      

def main(net_identifier, allowed_road_types = ['highway.unclassified', 'highway.service', 'highway.residential', 'highway.tertiary', 'highway.secondary', \
       'highway.primary', 'highway.trunk', 'highway.primary_link', 'highway.trunk_link']):
    
    # Define filepaths for all the key files
    edgeTypesContainerObject_filepath = ("%s/netObjects/%s_edgeTypesContainer" % (os.environ['DIRECTORY_PATH'], net_identifier))
    edgeContainerObject_filepath = ("%s/netObjects/%s_edgeContainer" % (os.environ['DIRECTORY_PATH'], net_identifier))
    juncContainerObject_filepath = ("%s/netObjects/%s_juncContainer" % (os.environ['DIRECTORY_PATH'], net_identifier))
    
    node_filepath = ("%s/netXMLFiles/%s.nod.xml" % (os.environ['DIRECTORY_PATH'], net_identifier))
    edge_filepath = ("%s/netXMLFiles/%s.edg.xml" % (os.environ['DIRECTORY_PATH'], net_identifier))
    edgeTypes_filepath = ("%s/netXMLFiles/%s.typ.xml" % (os.environ['DIRECTORY_PATH'], net_identifier))
    connections_filepath = ("%s/netXMLFiles/%s.con.xml" % (os.environ['DIRECTORY_PATH'], net_identifier))
    net_filepath = ("%s/netXMLFiles/%s.net.xml" % (os.environ['DIRECTORY_PATH'], net_identifier))

    timeTable_filepath = ("%s/netObjects/%s_TravelTimeTable" % (os.environ['DIRECTORY_PATH'], net_identifier))   
    routeTable_filepath = ("%s/netObjects/%s_RouteTable" % (os.environ['DIRECTORY_PATH'], net_identifier))
    distTable_filepath = ("%s/netObjects/%s_DistTable" % (os.environ['DIRECTORY_PATH'], net_identifier))

    # Parse the net file for processing into edge and node files
    print("Parsing net file...")
    netData = ET.parse(net_filepath) # Use the XML parser to read the net XML file
    net = netData.getroot()
    
    # Produce the EdgeType, Edge, Junc Containers (ETC, EC, JC) and save using pickle wickle
    print("Producing edge type container...")
    ETC = roadTypesFile(net, edgeTypes_filepath)
    print("Producing edge container...")
    EC, usedEdges, usedJuncs = edgeFile(net, edge_filepath, allowed_road_types, ETC)
    print("Producing junction container...")
    JC = nodeFile(net, node_filepath, usedJuncs)
    JC = netObjects.findJuncChildren(JC, EC)
    
    print("Saving containers...")
    pickleFunc.save_obj(ETC, edgeTypesContainerObject_filepath)
    pickleFunc.save_obj(EC, edgeContainerObject_filepath)
    pickleFunc.save_obj(JC, juncContainerObject_filepath)
        
    print("Now calculating time, distance and route tables for %d vertices..." % len(JC.container))
    timeTable, routeTable = netObjFuncs.genTimeAndRouteTables(JC, EC, print_time_table = False, print_route_table = False)
    distTable, unused = netObjFuncs.genDistanceAndRouteTables(JC, EC, print_distance_table= False, print_route_table = False)
      
    print("Saving tables...")
    pickleFunc.save_obj(timeTable, timeTable_filepath)
    pickleFunc.save_obj(routeTable, routeTable_filepath) 
    pickleFunc.save_obj(distTable, distTable_filepath)   
    
    print("Finished!")
    
if __name__=="__main__":
    
    os.environ["DIRECTORY_PATH"] = '/Users/tb7554/UniversityCloud/Home/workspace/_011_Scalefree-10x10_'
    
    net_identifier = "Scalefree-10x10"
    allowed_road_types = ['default', 'highway.unclassified', 'highway.service', 'highway.residential', 'highway.tertiary', 'highway.secondary', \
       'highway.primary', 'highway.trunk', 'highway.primary_link', 'highway.trunk_link'] # A preset list of road types from the net file which we want to include
    
    main(net_identifier, allowed_road_types)