#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Main function in a project to extract some occupancy-velocity data from Sumo simulations. This is to be used in some analysis of coverage based routing.

Author: Tim Barker
Created: 15/05/2015
Modified: 15/05/2015
"""

from __future__ import print_function, division
import os, sys, random, time, subprocess
import xml.etree.ElementTree as ET

directory_path = os.getcwd()
path_components = directory_path.split('/')
directory_name = path_components.pop()

if __name__=="__main__":
    directory_path = os.path.dirname(os.getcwd())
    sys.path.append(directory_path)
    directory_name = "Grid-10x10"

from sumoFileGen import pickleFunc
from tools.sumolib import net

if not os.path.isdir("%s/inductanceLoopsDump" % (directory_path)):
    os.mkdir("%s/inductanceLoopsDump" % (directory_path))

node_filepath = ("%s/netXMLFiles/%s.nod.xml" % (directory_path, directory_name))
edge_filepath = ("%s/netXMLFiles/%s.edg.xml" % (directory_path, directory_name))

# Object filepaths
edgeTypesContainerObject_filepath = ("%s/netObjects/EdgeTypesContainer" % (directory_path))
edgeContainerObject_filepath = ("%s/netObjects/EdgeContainer" % (directory_path))
juncContainerObject_filepath = ("%s/netObjects/JuncContainer" % (directory_path))
timeTable_filepath = ("%s/netObjects/TravelTimeTable" % (directory_path))
routeTable_filepath = ("%s/netObjects/RouteTable" % (directory_path))
distTable_filepath = ("%s/netObjects/DistTable" % (directory_path))

class createSumoFiles():
    
    def nodeFile(self, nodes):
        # Prints the node file from node data input
        NODEFILE = open(node_filepath, 'w')
        print('<nodes>', file=NODEFILE)
        for node in nodes:
            print('\t<node id="%s" x="%d" y="%d" type="priority"/>' % (str(node),nodes[node][0],nodes[node][1]), file=NODEFILE)
        print('</nodes>', file=NODEFILE)
        NODEFILE.close()
        
    def edgeFile(self,edges, reverseEdges=False, reverseExceptions=[],  priorityExceptions=[]):
        # Prints the edge file from edge data input
        EDGEFILE = open(edge_filepath, 'w')
        print('<edges>', file=EDGEFILE)
        for edge in edges:
            edgePriority = 1 if edge in priorityExceptions else -1
            print('\t<edge id="%sto%s" from="%s" to="%s" priority="%s"/>' % (str(edge[0]),str(edge[1]),str(edge[0]),str(edge[1]), str(edgePriority)))
            print('\t<edge id="%sto%s" from="%s" to="%s" priority="%s"/>' % (str(edge[0]),str(edge[1]),str(edge[0]),str(edge[1]), str(edgePriority)), file=EDGEFILE)
            if reverseEdges and edge not in reverseExceptions:
                print('\t<edge id="%sto%s" from="%s" to="%s" priority="%s"/>' % (str(edge[1]),str(edge[0]),str(edge[1]),str(edge[0]), str(edgePriority)), file=EDGEFILE)
        print('</edges>', file=EDGEFILE)
        EDGEFILE.close()
        
    def netFile(self):
        # Generates the net file using the node and edge files from before
        os.system('netconvert -n %s -e %s -o %s' % (node_filepath, edge_filepath, net_filepath))
    
    def vTypeFile(self, add_filepath):
        # This file is preset with some vehicle type data. It is automatically generated when the createSumoFiles
        # class is called.
        ADDFILE = open(add_filepath, 'a')       
        print("""    <vType id="DblDecker" accel="0.9" decel="3.2" sigma="0" length="10.0" maxspeed="40" color="1,0,0" vclass="public_transport" guiShape="bus" guiWidth="2.5"/>
    <vType id="Default" accel="2.5" decel="4.5" sigma="0" length="4.0" maxspeed="100" color="0,0,1" guiShape="passenger" guiWidth="1.6" tau="0.1"/>
    <vType id="HumanStandard" accel="2.5" decel="4.5" sigma="0.2" length="4.0" maxspeed="100" color="0,0,1" vclass="private" guiShape="passenger" guiWidth="1.6" tau="0.215"/>
    <vType id="HumanCoverageRouted" accel="2.5" decel="4.5" sigma="0.2" length="4.0" maxspeed="100" color="1,0,1" vclass="private" guiShape="passenger" guiWidth="1.6" tau="0.215"/>
    <vType id="DriverlessStandard" accel="2.5" decel="4.5" sigma="0" length="4.0" maxspeed="100" color="0,1,1" vclass="private" guiShape="passenger" guiWidth="1.6" tau="0.1"/>  
    <vType id="DriverlessCoverageRouted" accel="2.5" decel="4.5" sigma="0" length="4.0" maxspeed="100" color="1,0,0" vclass="private" guiShape="passenger" guiWidth="1.6" tau="0.1"/>
    <vType id="CommuterHome" accel="2.5" decel="4.5" sigma="0" length="4.0" maxspeed="100" color="0,0,1" vclass="private" guiShape="passenger" guiWidth="1.6"/>
    <vType id="CommuterWork" accel="2.5" decel="4.5" sigma="0" length="4.0" maxspeed="100" color="0,0,1" vclass="private" guiShape="passenger" guiWidth="1.6"/>
    <vType id="Home2LeisureShort" accel="2.5" decel="4.5" sigma="0" length="4.0" maxspeed="100" color="0,0,1" vclass="private" guiShape="passenger" guiWidth="1.6"/>
    <vType id="Leisure2HomeShort" accel="2.5" decel="4.5" sigma="0" length="4.0" maxspeed="100" color="0,0,1" vclass="private" guiShape="passenger" guiWidth="1.6"/>
    <vType id="Home2LeisureLong" accel="2.5" decel="4.5" sigma="0" length="4.0" maxspeed="100" color="0,0,1" vclass="private" guiShape="passenger" guiWidth="1.6"/>
    <vType id="Leisure2HomeLong" accel="2.5" decel="4.5" sigma="0" length="4.0" maxspeed="100" color="0,0,1" vclass="private" guiShape="passenger" guiWidth="1.6"/>
    <vType id="Minibus" accel="1.1" decel="3.2" sigma="0" length="6.0" maxspeed="40" color="1,1,0" vclass="bus" guiShape="passenger/van" guiWidth="2.5"/>
    <vType id="LGV" accel="1.8" decel="3.9" sigma="0" length="6.0" maxspeed="80" color="0,0,0" vclass="delivery" guiShape="delivery" guiWidth="2.3"/>
    <vType id="MGV" accel="1.1" decel="3.2" sigma="0" length="8.0" maxspeed="65" color="0,1,0" vclass="delivery" guiShape="delivery" guiWidth="2.4"/>
    <vType id="HGV" accel="1.4" decel="3.7" sigma="0" length="11.0" maxspeed="75" color="0,1,1" vclass="delivery" guiShape="truck/semitrailer" guiWidth="2.5" guiOffset="1"/>""", file=ADDFILE)

        ADDFILE.close()
    
    def createInductionLoopFile(self,add_filepath, path_to_output, StepLength):
        edgeContainer = pickleFunc.load_obj('netObjects/EdgeContainer')
        
        loop_ids = []
        freq = 1800
        ADDFILE = open(add_filepath, 'a')
        
        for edge in edgeContainer.container:
            for lane in edgeContainer.container[edge].lanesContainer:
                
                if edgeContainer.container[edge].speed > edgeContainer.container[edge].length:
                    print("No inductance loop placed on lane %s, as it is too short" % (lane))
                elif edgeContainer.container[edge].speed < edgeContainer.container[edge].length :
                    pos = edgeContainer.container[edge].length - 1*edgeContainer.container[edge].speed
                    print('\t<inductionLoop id="%s" lane="%s" pos="%f" freq="%d" file="%s" />' % (lane, lane, pos, freq, path_to_output ),file=ADDFILE)
                    loop_ids.append(lane)
                else:
                    pos = -1*edgeContainer.container[edge].length
                    print('\t<inductionLoop id="%s" lane="%s" pos="%f" freq="%d" file="%s" />' % (lane, lane, pos, freq, path_to_output ),file=ADDFILE)
                    loop_ids.append(lane)
                
        ADDFILE.close()
        
        return loop_ids

    def addFile(self, additionalFile_filepath, loopOutput_filepath, stepLength):

        ADDFILE = open(additionalFile_filepath, 'w')
        print("<additional>", file=ADDFILE)
        ADDFILE.close()
        
        self.vTypeFile(additionalFile_filepath)
        loop_ids = self.createInductionLoopFile(additionalFile_filepath, loopOutput_filepath, stepLength)
        
        ADDFILE= open(additionalFile_filepath, 'a')
            
        print("</additional>", file=ADDFILE)
        
        ADDFILE.close()
        
        return loop_ids
    
    def configFile(self, config_filepath, route_filepath, add_filepath, start_time=0, step_length=0.1, traciPORT=8813):
        # This script generates a config file for the SUMO simulation. Defaults are for vtypes top be loaded; an
        # induction loop file to be generated and loaded; a start time of 0 and step length of 0.1; and a traci port
        # is specified. These can be turned off when the script is called by setting them to 0.
        
        CONFIG = open(config_filepath, 'w')
        
        print("""<?xml version="1.0" encoding="UTF-8"?>

<configuration xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="%s/data/xsd/sumoConfiguration.xsd">

    <input>
        <net-file value="%s"/>
        <route-files value="%s"/>
        <additional-files value="%s"/>
    </input>

    <time>
        <begin value="%d"/>
        <step-length value="%f"/>
    </time> 
    
    <report>
        <no-step-log value="true"/>
    </report>
        
    <traci_server>
        <remote-port value="%d"/>
    </traci_server>

</configuration>
""" % (os.environ['SUMO_HOME'], net_filepath, route_filepath, add_filepath, start_time, step_length, traciPORT), file=CONFIG)

def randomTrips(simulationDetails_filepath, tripsFolder):

    parse_simulationDetails = ET.parse(simulationDetails_filepath) # Use the XML parser to read the net XML file
    simDetails = parse_simulationDetails.getroot()

    for simulation in simDetails:
        networkID = simulation.attrib["netID"]
        carGenRate = float(simulation.attrib["carGenRate"])
        period = 1/carGenRate
        begin = int(simulation.attrib["begin"])
        end = int(simulation.attrib["end"])
        runs = int(simulation.attrib["runs"])
        if "minTripDistance" in simulation.keys() : minDistance = int(simulation.attrib["minTripDistance"])
        if "maxTripDistance" in simulation.keys() : 
            maxDistance = int(simulation.attrib["maxTripDistance"])
        else:
            maxDistance = None
        if "fringeFactor" in simulation.keys() : fringeFactor = float(simulation.attrib["fringeFactor"])
        
        for ii in range(0,runs):
            
            net_filepath = ("%s/netXMLFiles/%s.net.xml" % (directory_path, networkID))
            trips_filepath = ("%s/%s-CGR-%.2f-%d.trip.xml" % (tripsFolder, networkID, carGenRate, ii))
            
            randomTripsCommand = ("%s -n %s -o %s -b %s -e %s -p %s " % (os.environ['RANDOMTRIPS_PYTHON'],net_filepath, trips_filepath, begin, end, period))
            
            if minDistance:
                randomTripsCommand += ("--min-distance %f " % (minDistance))
            if maxDistance:
                randomTripsCommand += ("--maxDistance %f " % (maxDistance))
            if fringeFactor:
                randomTripsCommand += ("--fringe-factor %f " % (fringeFactor))
            
            randomTripsProcess = subprocess.Popen(randomTripsCommand, shell=True, stdout=sys.stdout)
            randomTripsProcess.wait()

def vTypeFile(tripsFolder):
    # This file is preset with some vehicle type data. It is automatically generated when the createSumoFiles
    # class is called.

    vTypes_filepath = ("%s/vtypes.add.xml" % (tripsFolder))
    
    VTYPESFILE = open(vTypes_filepath, 'w')
    print("<additional>", file=VTYPESFILE)       
    print("""    <vType id="DblDecker" accel="0.9" decel="3.2" sigma="0" length="10.0" maxspeed="40" color="1,0,0" vclass="public_transport" guiShape="bus" guiWidth="2.5"/>
    <vType id="Default" accel="2.5" decel="4.5" sigma="0" length="4.0" maxspeed="100" color="0,0,1" guiShape="passenger" guiWidth="1.6" tau="0.1"/>
    <vType id="HumanStandard" accel="2.5" decel="4.5" sigma="0" length="4.0" maxspeed="100" color="0,0,1" vclass="private" guiShape="passenger" guiWidth="1.6" tau="0.215"/>
    <vType id="HumanCoverageRouted" accel="2.5" decel="4.5" sigma="0" length="4.0" maxspeed="100" color="1,0,1" vclass="private" guiShape="passenger" guiWidth="1.6" tau="0.215"/>
    <vType id="DriverlessStandard" accel="2.5" decel="4.5" sigma="0" length="4.0" maxspeed="100" color="0,1,1" vclass="private" guiShape="passenger" guiWidth="1.6" tau="0.1"/>  
    <vType id="DriverlessCoverageRouted" accel="2.5" decel="4.5" sigma="0" length="4.0" maxspeed="100" color="1,0,0" vclass="private" guiShape="passenger" guiWidth="1.6" tau="0.1"/>
    <vType id="CommuterHome" accel="2.5" decel="4.5" sigma="0" length="4.0" maxspeed="100" color="0,0,1" vclass="private" guiShape="passenger" guiWidth="1.6"/>
    <vType id="CommuterWork" accel="2.5" decel="4.5" sigma="0" length="4.0" maxspeed="100" color="0,0,1" vclass="private" guiShape="passenger" guiWidth="1.6"/>
    <vType id="Home2LeisureShort" accel="2.5" decel="4.5" sigma="0" length="4.0" maxspeed="100" color="0,0,1" vclass="private" guiShape="passenger" guiWidth="1.6"/>
    <vType id="Leisure2HomeShort" accel="2.5" decel="4.5" sigma="0" length="4.0" maxspeed="100" color="0,0,1" vclass="private" guiShape="passenger" guiWidth="1.6"/>
    <vType id="Home2LeisureLong" accel="2.5" decel="4.5" sigma="0" length="4.0" maxspeed="100" color="0,0,1" vclass="private" guiShape="passenger" guiWidth="1.6"/>
    <vType id="Leisure2HomeLong" accel="2.5" decel="4.5" sigma="0" length="4.0" maxspeed="100" color="0,0,1" vclass="private" guiShape="passenger" guiWidth="1.6"/>
    <vType id="Minibus" accel="1.1" decel="3.2" sigma="0" length="6.0" maxspeed="40" color="1,1,0" vclass="bus" guiShape="passenger/van" guiWidth="2.5"/>
    <vType id="LGV" accel="1.8" decel="3.9" sigma="0" length="6.0" maxspeed="80" color="0,0,0" vclass="delivery" guiShape="delivery" guiWidth="2.3"/>
    <vType id="MGV" accel="1.1" decel="3.2" sigma="0" length="8.0" maxspeed="65" color="0,1,0" vclass="delivery" guiShape="delivery" guiWidth="2.4"/>
    <vType id="HGV" accel="1.4" decel="3.7" sigma="0" length="11.0" maxspeed="75" color="0,1,1" vclass="delivery" guiShape="truck/semitrailer" guiWidth="2.5" guiOffset="1"/>""", file=VTYPESFILE)
    print("</additional>", file=VTYPESFILE) 
    
    VTYPESFILE.close()
    
def addInductionLoops2AdditionalFile(netFile_filepath, additionalFile_filepath, loopOutput_filepath):
    sumolibnet = net.readNet(netFile_filepath)
    edges = sumolibnet.getEdges()
    
    loop_ids = []
    freq = 1800
    ADDFILE = open(additionalFile_filepath, 'a')
    
    for edge in sumolibnet.getEdges():
        for lane in edge.getLanes():
            
            if edge.getSpeed() > edge.getLength():
                print("No inductance loop placed on lane %s, as it is too short" % (lane))
            elif edgeContainer.container[edge].speed < edgeContainer.container[edge].length :
                pos = edgeContainer.container[edge].length - 1*edgeContainer.container[edge].speed
                print('\t<inductionLoop id="%s" lane="%s" pos="%f" freq="%d" file="%s" />' % (lane, lane, pos, freq, loopOutput_filepath),file=ADDFILE)
                loop_ids.append(lane)
            else:
                pos = -1*edgeContainer.container[edge].length
                print('\t<inductionLoop id="%s" lane="%s" pos="%f" freq="%d" file="%s" />' % (lane, lane, pos, freq, loopOutput_filepath),file=ADDFILE)
                loop_ids.append(lane)
            
    ADDFILE.close()
    
    return loop_ids

def additionalFile(netID, additionalFile_filepath, loopOutput_filepath):

    ADDFILE = open(additionalFile_filepath, 'w')
    print("<additional>", file=ADDFILE)
    ADDFILE.close()
    
    loop_ids = addInductionLoops2AdditionalFile(netID, additionalFile_filepath, loopOutput_filepath)
    
    ADDFILE= open(additionalFile_filepath, 'a')
        
    print("</additional>", file=ADDFILE)
    
    ADDFILE.close()
    
    return loop_ids
           
def addVehTypesToTrips(simulationDetails_filepath, tripsFolder):
        
    parse_simulationDetails = ET.parse(simulationDetails_filepath) # Use the XML parser to read the net XML file
    simDetails = parse_simulationDetails.getroot()
    
    basefiles = []
    newfiles = []
    penRate = []
    
    for simulation in simDetails:
        networkID = simulation.attrib["netID"]
        carGenRate = float(simulation.attrib["carGenRate"])
        runs = int(simulation.attrib["runs"])
        routingMethod = simulation.attrib['routingMethod']
        
        for routingType in simulation:
            if routingMethod == "CBR" : 
                PenetrationRate = float(routingType.attrib["PenetrationRate"])                
            else:
                PenetrationRate = 0
            
            for ii in range(0,runs):
                
                basicTrips_filepath = ("%s/%s-CGR-%.2f-%d.trip.xml" % (tripsFolder, networkID, carGenRate, ii))
                tripsWithVehicles_filepath = ("%s/%s-CGR-%.2f-PEN-%.2f-%d.trip.xml" % (tripsFolder, networkID, carGenRate, PenetrationRate, ii))
                
                if tripsWithVehicles_filepath not in newfiles:
                    basefiles.append(basicTrips_filepath)
                    newfiles.append(tripsWithVehicles_filepath)
                    penRate.append(PenetrationRate)

    for ii in range(0,len(newfiles)):
                
        parse_basicTrips = ET.parse(basefiles[ii])
        basicTrips = parse_basicTrips.getroot()
                              
        for trip in basicTrips:
            if random.random() > penRate[ii]:
                vType = "HumanStandard"
            else:
                vType = "HumanCoverageRouted"
                  
            trip.set("type", vType)
                  
        parse_basicTrips.write(newfiles[ii])
                
def duaRouter(simulationDetails_filepath, tripsFolder, routesFolder, netID):
    
    parse_simulationDetails = ET.parse(simulationDetails_filepath) # Use the XML parser to read the net XML file
    simDetails = parse_simulationDetails.getroot()
    
    vtypes_filepath = ("%s/vtypes.add.xml" % (tripsFolder))
    net_filepath = ("%s/netXMLFiles/%s.net.xml" % (os.environ['DIRECTORY_PATH'], netID))
    
    trips = []
    routes = []
        
    for simulation in simDetails:
        networkID = simulation.attrib["netID"]
        carGenRate = float(simulation.attrib["carGenRate"])
        runs = int(simulation.attrib["runs"])
        routingMethod = simulation.attrib['routingMethod']
        
        for routingType in simulation:
            if routingMethod == "CBR" : 
                PenetrationRate = float(routingType.attrib["PenetrationRate"])                
            else:
                PenetrationRate = 0
            
            for ii in range(0,runs):
                
                trips_filepath = ("%s/%s-CGR-%.2f-PEN-%.2f-%d.trip.xml" % (tripsFolder, networkID, carGenRate, PenetrationRate, ii))
                routes_filepath = ("%s/%s-CGR-%.2f-PEN-%.2f-%d.rou.xml" % (routesFolder, networkID, carGenRate, PenetrationRate, ii))                
                
                if trips_filepath not in trips:
                    trips.append(trips_filepath)
                    routes.append(routes_filepath)
                
    for ii in range(0, len(trips)):
        duaCommand = ('%s -n %s -t %s -d %s -o %s --remove-loops --repair --ignore-errors' % (os.environ['DUAROUTER_BINARY'], net_filepath, trips[ii], vtypes_filepath, routes[ii]))
        duaProcess = subprocess.Popen(duaCommand, shell=True, stdout=sys.stdout, stderr=sys.stderr)
        duaProcess.wait()
             
def route2Trips(simulationDetails_filepath, tripsFolder, routesFolder, vtypes_filepath, netXMLFilesFolder):
    
    parse_simulationDetails = ET.parse(simulationDetails_filepath) # Use the XML parser to read the net XML file
    simDetails = parse_simulationDetails.getroot()
    
    for simulation in simDetails:
        networkID = simulation.attrib["id"]
        carGenRate = float(simulation.attrib["carGenRate"])
        runs = int(simulation.attrib["runs"])
        
        net_filepath = ("%s/%s.net.xml" % (netXMLFilesFolder, networkID))
    
        for routingType in simulation:
            if routingType.attrib["routingMethod"] == "CBR" : 
                PenetrationRate = float(routingType.attrib["PenetrationRate"])                
            else:
                PenetrationRate = 0
            
            for ii in range(0,runs):
                
                trips_filepath = ("%s/%s-CGR-%.2f-PEN-%.2f-%d.trip.xml" % (tripsFolder, networkID, carGenRate, PenetrationRate, ii))
                routes_filepath = ("%s/%s-CGR-%.2f-PEN-%.2f-%d.rou.xml" % (routesFolder, networkID, carGenRate, PenetrationRate, ii))
                
                os.system("%s %s > %s" % (os.environ["ROUTE2TRIPS_PYTHON"], routes_filepath, trips_filepath))
                
                time.sleep(1)
                    
class tripGeneration():
    
    def __init__(self):
        print("Loading Network Objects for trip calculation")
        self.EC = pickleFunc.load_obj(edgeContainerObject_filepath)
        self.JC = pickleFunc.load_obj(juncContainerObject_filepath)
        self.TTT = pickleFunc.load_obj(timeTable_filepath)
        self.DT = pickleFunc.load_obj(distTable_filepath)
        self.RT = pickleFunc.load_obj(routeTable_filepath)
        print("Objects Loaded")
        
    def passingThroughGrid(self, trips_filepath, minimum_trip_time, car_generation_rate, start_time, duration, grid_size, DriverlessCar_PenetrationRate, \
                           CoverageBasedRouting_PenetrationRate_Human, CoverageBasedRouting_PenetrationRate_DriverlessCar):
        # We use our network knowledge to generate trips according to how many trips are generated at each point on the network
        
        od_junc_identifier = ["top", "right", "bottom", "left"]
        
        trips = int(car_generation_rate*duration)
        possibleJuncs = []
        travel_times = []
        selected_trips = []
                
        for junc in od_junc_identifier:
            for ii in range(0,grid_size):
                possibleJuncs.append(junc + str(ii))
        
        for start_junction in self.TTT:
            for end_junction in self.TTT:
                if self.TTT[start_junction][end_junction] >= minimum_trip_time and start_junction in possibleJuncs and end_junction in possibleJuncs:
                    travel_times.append(self.TTT[start_junction][end_junction])
                    selected_trips.append((start_junction, end_junction, self.TTT[start_junction][end_junction]))
        
        step = start_time
        
        TRIPS = open(trips_filepath, 'w')
        print("<vehicles>", file=TRIPS)
        
        print("""    <vType id="DblDecker" accel="0.9" decel="3.2" sigma="0" length="10.0" maxspeed="40" color="1,0,0" vclass="public_transport" guiShape="bus" guiWidth="2.5"/>
    <vType id="Default" accel="2.5" decel="4.5" sigma="0" length="4.0" maxspeed="100" color="0,0,1" guiShape="passenger" guiWidth="1.6" tau="0.1"/>
    <vType id="HumanStandard" accel="2.5" decel="4.5" sigma="0.2" length="4.0" maxspeed="100" color="0,0,1" vclass="private" guiShape="passenger" guiWidth="1.6" tau="0.215"/>
    <vType id="HumanCoverageRouted" accel="2.5" decel="4.5" sigma="0.2" length="4.0" maxspeed="100" color="1,0,1" vclass="private" guiShape="passenger" guiWidth="1.6" tau="0.215"/>
    <vType id="DriverlessStandard" accel="2.5" decel="4.5" sigma="0" length="4.0" maxspeed="100" color="0,1,1" vclass="private" guiShape="passenger" guiWidth="1.6" tau="0.1"/>  
    <vType id="DriverlessCoverageRouted" accel="2.5" decel="4.5" sigma="0" length="4.0" maxspeed="100" color="1,0,0" vclass="private" guiShape="passenger" guiWidth="1.6" tau="0.1"/>
    <vType id="CommuterHome" accel="2.5" decel="4.5" sigma="0" length="4.0" maxspeed="100" color="0,0,1" vclass="private" guiShape="passenger" guiWidth="1.6"/>
    <vType id="CommuterWork" accel="2.5" decel="4.5" sigma="0" length="4.0" maxspeed="100" color="0,0,1" vclass="private" guiShape="passenger" guiWidth="1.6"/>
    <vType id="Home2LeisureShort" accel="2.5" decel="4.5" sigma="0" length="4.0" maxspeed="100" color="0,0,1" vclass="private" guiShape="passenger" guiWidth="1.6"/>
    <vType id="Leisure2HomeShort" accel="2.5" decel="4.5" sigma="0" length="4.0" maxspeed="100" color="0,0,1" vclass="private" guiShape="passenger" guiWidth="1.6"/>
    <vType id="Home2LeisureLong" accel="2.5" decel="4.5" sigma="0" length="4.0" maxspeed="100" color="0,0,1" vclass="private" guiShape="passenger" guiWidth="1.6"/>
    <vType id="Leisure2HomeLong" accel="2.5" decel="4.5" sigma="0" length="4.0" maxspeed="100" color="0,0,1" vclass="private" guiShape="passenger" guiWidth="1.6"/>
    <vType id="Minibus" accel="1.1" decel="3.2" sigma="0" length="6.0" maxspeed="40" color="1,1,0" vclass="bus" guiShape="passenger/van" guiWidth="2.5"/>
    <vType id="LGV" accel="1.8" decel="3.9" sigma="0" length="6.0" maxspeed="80" color="0,0,0" vclass="delivery" guiShape="delivery" guiWidth="2.3"/>
    <vType id="MGV" accel="1.1" decel="3.2" sigma="0" length="8.0" maxspeed="65" color="0,1,0" vclass="delivery" guiShape="delivery" guiWidth="2.4"/>
    <vType id="HGV" accel="1.4" decel="3.7" sigma="0" length="11.0" maxspeed="75" color="0,1,1" vclass="delivery" guiShape="truck/semitrailer" guiWidth="2.5" guiOffset="1"/>""", file=TRIPS)
        
        for ii in range(0, trips):
            trip_id = ('veh_%d' % (ii))
            departure_time = step
            step += 1/car_generation_rate
            trip = random.choice(selected_trips)
            route = self.RT[trip[0]][trip[1]]
            start = ("%sto%s" % (route[0], route[1]))
            end = ("%sto%s" % (route[-2], route[-1]))
            
            # Determine if this car will be human or driverless
            if random.random() < DriverlessCar_PenetrationRate:
                if random.random() < CoverageBasedRouting_PenetrationRate_DriverlessCar:
                    vehType = "DriverlessCoverageRouted"
                else:
                    vehType = "DriverlessStandard"
            else:
                if random.random() < CoverageBasedRouting_PenetrationRate_Human:
                    vehType = "HumanCoverageRouted"
                else:
                    vehType = "HumanStandard"
                        
            print('\t<trip id="%s" type="%s" depart="%f" from="%s" to="%s"/>' % (trip_id, vehType, departure_time, start, end), file=TRIPS)
        print("</vehicles>", file=TRIPS)
        
        TRIPS.close()
        
    def scaleFreeMinDistance(self, trips_filepath, minimum_trip_distance, car_generation_rate, start_time, duration, DriverlessCar_PenetrationRate, \
                           CoverageBasedRouting_PenetrationRate_Human, CoverageBasedRouting_PenetrationRate_DriverlessCar):
        # We use our network knowledge to generate trips according to how many trips are generated at each point on the network
        
        trips = int(car_generation_rate*duration)
        
        selectedTrips_filepath = ("%s/netObjects/%s_SelectedTrips_MinDistance%d" % (directory_path, directory_name, minimum_trip_distance))
        
        if os.path.exists(selectedTrips_filepath + ".pkl"):
            print("Appropriate Trips Identified")
            selected_trips = pickleFunc.load_obj(selectedTrips_filepath)
        else:
            print("Identifying Approprite Trips")
            selected_trips = []
            for start_junction in self.DT:
                for end_junction in self.DT:
                    if self.DT[start_junction][end_junction] >= minimum_trip_distance and self.DT[start_junction][end_junction] != float("inf"):
                        selected_trips.append((start_junction, end_junction, self.DT[start_junction][end_junction]))
            print("Trips Identified")
            pickleFunc.save_obj(selected_trips, selectedTrips_filepath)
        
        step = start_time
        
        TRIPS = open(trips_filepath, 'w')
        print("<vehicles>", file=TRIPS)
        
        print("""    <vType id="DblDecker" accel="0.9" decel="3.2" sigma="0" length="10.0" maxspeed="40" color="1,0,0" vclass="public_transport" guiShape="bus" guiWidth="2.5"/>
    <vType id="Default" accel="2.5" decel="4.5" sigma="0" length="4.0" maxspeed="100" color="0,0,1" guiShape="passenger" guiWidth="1.6" tau="0.1"/>
    <vType id="HumanStandard" accel="2.5" decel="4.5" sigma="0.2" length="4.0" maxspeed="100" color="0,0,1" vclass="private" guiShape="passenger" guiWidth="1.6" tau="0.215"/>
    <vType id="HumanCoverageRouted" accel="2.5" decel="4.5" sigma="0.2" length="4.0" maxspeed="100" color="1,0,1" vclass="private" guiShape="passenger" guiWidth="1.6" tau="0.215"/>
    <vType id="DriverlessStandard" accel="2.5" decel="4.5" sigma="0" length="4.0" maxspeed="100" color="0,1,1" vclass="private" guiShape="passenger" guiWidth="1.6" tau="0.1"/>  
    <vType id="DriverlessCoverageRouted" accel="2.5" decel="4.5" sigma="0" length="4.0" maxspeed="100" color="1,0,0" vclass="private" guiShape="passenger" guiWidth="1.6" tau="0.1"/>
    <vType id="CommuterHome" accel="2.5" decel="4.5" sigma="0" length="4.0" maxspeed="100" color="0,0,1" vclass="private" guiShape="passenger" guiWidth="1.6"/>
    <vType id="CommuterWork" accel="2.5" decel="4.5" sigma="0" length="4.0" maxspeed="100" color="0,0,1" vclass="private" guiShape="passenger" guiWidth="1.6"/>
    <vType id="Home2LeisureShort" accel="2.5" decel="4.5" sigma="0" length="4.0" maxspeed="100" color="0,0,1" vclass="private" guiShape="passenger" guiWidth="1.6"/>
    <vType id="Leisure2HomeShort" accel="2.5" decel="4.5" sigma="0" length="4.0" maxspeed="100" color="0,0,1" vclass="private" guiShape="passenger" guiWidth="1.6"/>
    <vType id="Home2LeisureLong" accel="2.5" decel="4.5" sigma="0" length="4.0" maxspeed="100" color="0,0,1" vclass="private" guiShape="passenger" guiWidth="1.6"/>
    <vType id="Leisure2HomeLong" accel="2.5" decel="4.5" sigma="0" length="4.0" maxspeed="100" color="0,0,1" vclass="private" guiShape="passenger" guiWidth="1.6"/>
    <vType id="Minibus" accel="1.1" decel="3.2" sigma="0" length="6.0" maxspeed="40" color="1,1,0" vclass="bus" guiShape="passenger/van" guiWidth="2.5"/>
    <vType id="LGV" accel="1.8" decel="3.9" sigma="0" length="6.0" maxspeed="80" color="0,0,0" vclass="delivery" guiShape="delivery" guiWidth="2.3"/>
    <vType id="MGV" accel="1.1" decel="3.2" sigma="0" length="8.0" maxspeed="65" color="0,1,0" vclass="delivery" guiShape="delivery" guiWidth="2.4"/>
    <vType id="HGV" accel="1.4" decel="3.7" sigma="0" length="11.0" maxspeed="75" color="0,1,1" vclass="delivery" guiShape="truck/semitrailer" guiWidth="2.5" guiOffset="1"/>""", file=TRIPS)        

        for ii in range(0, trips):
            trip_id = ('veh_%d' % (ii))
            departure_time = step
            step += 1/car_generation_rate
            trip = random.choice(selected_trips)
            route = self.RT[trip[0]][trip[1]]
            start = self.JC.container[route[0]].children[route[1]]
            end = self.JC.container[route[-2]].children[route[-1]]
            
            # Determine if this car will be human or driverless
            if random.random() < DriverlessCar_PenetrationRate:
                if random.random() < CoverageBasedRouting_PenetrationRate_DriverlessCar:
                    vehType = "DriverlessCoverageRouted"
                else:
                    vehType = "DriverlessStandard"
            else:
                if random.random() < CoverageBasedRouting_PenetrationRate_Human:
                    vehType = "HumanCoverageRouted"
                else:
                    vehType = "HumanStandard"
                        
            print('\t<trip id="%s" type="%s" depart="%f" from="%s" to="%s"/>' % (trip_id, vehType, departure_time, start, end), file=TRIPS)
        print("</vehicles>", file=TRIPS)
        
        TRIPS.close()
        
    def duaRouter(self, trips_filepath, routes_filepath):
        
        duarouterBinary = ("%s" % (os.environ['DUAROUTER_BINARY']))
        vehTypes_filepath = ("%s/addFiles/vehTypes.add.xml" % (directory_path))
        os.system('%s -n %s -t %s -o %s' % (duarouterBinary, net_filepath, trips_filepath, routes_filepath))
        
        time.sleep(10)
        
    def duaRouterIterative(self, trips_filepath, routes_filepath):
        
        duaIteratePythonPath = ("python %s/tools/assign/duaIterate.py -n %s -t %s" % (os.environ['SUMO_HOME'], net_filepath, trips_filepath))
        os.system(duaIteratePythonPath)
        
        time.sleep(10)
        
            

class edgeData():
    
    def __init__(self, edgeID, sampledSeconds, traveltime, density, occupancy, waitingTime, speed, departed, arrived, entered, left, laneChangedFrom, laneChangedTo):
        self.id=edgeID
        self.sampledSeconds=sampledSeconds
        self.traveltime=traveltime
        self.density=density
        self.occupancy=occupancy
        self.waitingTime=waitingTime
        self.speed=speed
        self.departed=departed
        self.arrived=arrived
        self.entered=entered
        self.left=left
        self.laneChangedFrom=laneChangedFrom
        self.laneChangedTo=laneChangedTo

class dataContainer():
    
    def __init__(self):
        self.container={}
        self.orgStructure=None
        
    def addContainerSlotByCarGenRate(self, carGenRate, dataType):
        if self.orgStructure == None:
            print("This data container is now organised by car generation rate -> Data type (e.g. Edge) -> Data")
            self.orgStructure = "Car Generation Rate"
        
        if self.orgStructure is not "Car Generation Rate":
            print("This data container is not organised by car generation rate, it is organised by %s" % (self.orgStructure))
        else:
            self.container.update({str(carGenRate):{dataType:{}}})
             
    def addEdgeDataByCarGenRate(self, carGenRate, intervalID, edgeID, sampledSeconds, traveltime, density, occupancy, waitingTime, speed, departed, arrived, entered, left, laneChangedFrom, laneChangedTo):
        self.container[str(carGenRate)]['EdgeData'][intervalID].update({edgeID:edgeData(edgeID, sampledSeconds, traveltime, density, occupancy, waitingTime, speed, departed, arrived, entered, left, laneChangedFrom, laneChangedTo)})
    
    def extractEdgeFiles(self, alphaToAnalyse, carGenRateToAnalyse):        
        
#        for carGenRate in carGenRatesToAnalyse:
#            cgr_str = str(carGenRate)
            
            if cgr_str not in self.container.keys():
                self.addContainerSlotByCarGenRate(carGenRate, 'EdgeData')               
            
#            cgr_ints = cgr_str.split('.')[0]
#            cgr_deci = cgr_str.split('.')[1]
#            XMLfile = ('%s/sumo_output/%s_Edge_coverage_based_routing_alpha_%s_%s.xml' % (directory_path, directory_name, cgr_ints, cgr_deci))
            XMLfile = ('%s/sumo_output/edgeData/%s_Edge_coverage_based_routing_alpha_%d_car_gen_rate_%d.xml' % (directory_path, directory_name, alpha, car_gen_rate))
        
            edgeData = ET.parse(XMLfile)
            meandata = edgeData.getroot()
                        
            for interval in meandata:
                for edge in interval:
                    if interval.attrib['id'] not in self.container[cgr_str]['EdgeData'].keys():
                        self.container[cgr_str]['EdgeData'].update({interval.attrib['id']:{}})                    
                    self.addEdgeDataByCarGenRate(carGenRate, interval.attrib['id'], edge.attrib['id'], edge.attrib['sampledSeconds'], edge.attrib['traveltime'], \
                                                          edge.attrib['density'], edge.attrib['occupancy'], edge.attrib['waitingTime'], edge.attrib['speed'], \
                                                          edge.attrib['departed'], edge.attrib['arrived'], edge.attrib['entered'], edge.attrib['left'], \
                                                          edge.attrib['laneChangedFrom'], edge.attrib['laneChangedTo'])
                    
    
class analyseSumoOutput():
    
    def edgeFiles(self, dataContainer, carGenRatesToAnalyse):
        for carGenRate in carGenRatesToAnalyse:
            cgr_str = str(carGenRate)
            cgr_ints = cgr_str.split('.')[0]
            cgr_deci = cgr_str.split('.')[1]
            XMLfile = ('%s/Output/%s_Edge_carGenRate_%s_%s.xml' % (directory_path, directory_name, cgr_ints, cgr_deci))
        
            edgeData = ET.parse(XMLfile)
            meandata = edgeData.getroot()
                        
            for interval in meandata:
                for edge in interval:
                    dataContainer.addEdgeDataByCarGenRate(carGenRate, edge.attrib['id'], edge.attrib['sampledSeconds'], edge.attrib['traveltime'], \
                                                          edge.attrib['density'], edge.attrib['occupancy'], edge.attrib['waitingTime'], edge.attrib['speed'], \
                                                          edge.attrib['departed'], edge.attrib['arrived'], edge.attrib['entered'], edge.attrib['left'], \
                                                          edge.attrib['laneChangedFrom'], edge.attrib['laneChangedTo'])
            
        return dataContainer        
            
def mainSim():
   
    nodes = {'-1/-1':[-10,-10],'0/0':[0,0], '0/1':[0,100], '0/2':[0,200], '1/0':[100,0], '1/1':[100,100], '1/2':[100,200], '2/0':[200,0], '2/1':[200,100], '2/2':[200,200]}
    edges = [('-1/-1', '0/0'),('0/0','0/1'), ('0/0','1/0'), ('1/0','2/0'), ('1/0','1/1'), ('2/0','2/1'), ('2/1','2/2'), ('1/1','1/2'), ('1/2','2/2'), ('0/2','1/2'), ('0/1', '0/2'), ('0/1', '1/1'), ('1/1','2/1')]
    
    step_length_variable = 0.1
    car_generation_rates_to_run = [x*0.1 for x in range(1,40)]
    
    fileGenerator = createSumoFiles()
    fileGenerator.nodeFile(nodes)
    fileGenerator.edgeFile(edges, reverseEdges=True)#, reverseExceptions=[('-1/-1', '0/0')], priorityExceptions=[('-1/-1', '0/0')])
    fileGenerator.netFile()
    fileGenerator.configFile(inductionloops=0, step_length=step_length_variable)
    
    os.system('netconvert -e %s -n %s -o %s' % (edge_filepath, node_filepath, net_filepath))

    print("Files Generated") 
    """
    for car_generation_rate in car_generation_rates_to_run:
        cgr_str = str(car_generation_rate)
        cgr_ints = cgr_str.split('.')[0]
        cgr_deci = cgr_str.split('.')[1]
        trip_output_filepath = ("%s/Output/%s_Trip_carGenRate_%s_%s.xml" % (directory_path, directory_name, cgr_ints, cgr_deci))
        edge_output_id_str = "1to2"
        edge_output_filepath_str = ("%s/Output/%s_Edge_carGenRate_%s_%s.xml" % (directory_path, directory_name, cgr_ints, cgr_deci)) 
        fileGenerator.routeFile(car_generation_rate)
        
        fileGenerator.addFile(edge_output_id=edge_output_id_str, edge_output_file=edge_output_filepath_str)
        
        sumo_process_command=("sumo -c %s --tripinfo-output %s" % (config_filepath, trip_output_filepath))    
        sumoProcess = subprocess.Popen(sumo_process_command, shell=True, stdout=sys.stdout)
        # open up the traci port
        traci.init(PORT)
        # initialise the step
        step = 0
        
        # run the simulation
        while step == 0 or traci.simulation.getMinExpectedNumber() > 0:
            traci.simulationStep()
            timeNow = traci.simulation.getCurrentTime()                        
            step += step_length_variable
        
        traci.close()
        sys.stdout.flush()
        sumoProcess.terminate()
    """
    
    parseXML.net2EdgeAndNodeFiles()

    #---------------- Generate edgeContainer And juncContainer Objects From The Edge and Node Files -------------------------------------
    
    edgeContainer = parseXML.edgeObjContainer_from_XMLfile()
    juncContainer = parseXML.junctionObjContainer_from_XMLfile()
    juncContainer = netObjFuncs.findJuncChildren(juncContainer, edgeContainer)
    
    #---Save to a pickle object file
    sumoFileGen.pickleFunc.save_obj(edgeContainer, 'obj/edgeContainer')
    sumoFileGen.pickleFunc.save_obj(juncContainer, 'obj/juncContainer')

    for edge in edgeContainer.container:
        print(edgeContainer.container[edge].lanesContainer)

def mainResults():

    directory = ('%s/Output' % (directory_path))
    carGenRates = [x*0.1 for x in range(1,40)]
    
    data = dataContainer()
    data.extractEdgeFiles(carGenRates)
    
    edges = ['1to2', '2to3', '4to2']
    oc_data = {}
    speed_data = {}    
    
    for edge in edges:
        oc_data.update({edge:[]})
        speed_data.update({edge:[]})
    
    for carGenRate in carGenRates:
        for edge in data.container[str(carGenRate)]['EdgeData']['1to2']:
            oc = data.container[str(carGenRate)]['EdgeData']['1to2'][edge].occupancy
            speed = data.container[str(carGenRate)]['EdgeData']['1to2'][edge].speed
            oc_data[edge].append(oc)
            speed_data[edge].append(speed)

    fig = pp.figure(1)
    pp.plot(carGenRates, oc_data['1to2'], hold=1)
    pp.plot(carGenRates, oc_data['2to3'], hold=1)
    pp.plot(carGenRates, oc_data['4to2'], hold=1)
    #save_to = ('../../Documents/%s_oc.pdf' % (directory_name))
    #pp.savefig(save_to, bbox_inches='tight')
    
    fig = pp.figure(2)
    pp.plot(carGenRates, speed_data['1to2'], hold=1)
    pp.plot(carGenRates, speed_data['2to3'], hold=1)
    pp.plot(carGenRates, speed_data['4to2'], hold=1)
    #save_to = ('../../Documents/%s_speed.pdf' % (directory_name))
    #pp.savefig(save_to, bbox_inches='tight')
    pp.show()
        
if __name__ == '__main__':
    tripGen = tripGeneration()
    
    trips_filepath = "/Users/tb7554/lbox/lbox_workspace/TEST_4/TEST_4/tripFiles/Grid10_DCPR-0_CBRPR_H-0_D-None_CBRalpha-None_CGR-5.00_RUN-1.trip.xml"
    routes_filepath = "/Users/tb7554/lbox/lbox_workspace/TEST_4/TEST_4/EdgeOccupancyOutput/Grid10_DCPR-0_CBRPR_H-0_D-None_CBRalpha-None_CGR-5.00_RUN-1.rou.xml"
    
    tripGen.duaRouterIterative(trips_filepath, routes_filepath)
    