#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Main function in a project to extract some occupancy-velocity data from Sumo simulations. This is to be used in some analysis of coverage based routing.

Author: Tim Barker
Created: 15/05/2015
Modified: 15/05/2015
"""

from __future__ import print_function, division
import os, sys, random, subprocess
import xml.etree.ElementTree as ET

from tools.sumolib import net
from sumoFileGen import pickleFunc
from sumoRouter import shortestPaths, inductionLoop

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

def randomTrips(net_filepath, simulationDetails_filepath, tripsFolder):

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
            
            trips_filepath = ("%s/%s-CGR-%.2f-PEN-0.00-%d.trip.xml" % (tripsFolder, networkID, carGenRate, ii))
            
            if not(os.path.isfile(trips_filepath)):
                randomTripsCommand = ("%s -n %s -o %s -b %s -e %s -p %s " % (os.environ['RANDOMTRIPS_PYTHON'], net_filepath, trips_filepath, begin, end, period))
                
                if minDistance:
                    randomTripsCommand += ("--min-distance %f " % (minDistance))
                if maxDistance:
                    randomTripsCommand += ("--maxDistance %f " % (maxDistance))
                if fringeFactor:
                    randomTripsCommand += ("--fringe-factor %f " % (fringeFactor))
                
                randomTripsProcess = subprocess.Popen(randomTripsCommand, shell=True, stdout=sys.stdout)
                randomTripsProcess.wait()

def duaRouter(net_filepath, vtypes_filepath, simulationDetails_filepath, tripsFolder, routesFolder):
    
    parse_simulationDetails = ET.parse(simulationDetails_filepath) # Use the XML parser to read the net XML file
    simDetails = parse_simulationDetails.getroot()
    
    trips = []
     
    for simulation in simDetails:
        networkID = simulation.attrib["netID"]
        carGenRate = float(simulation.attrib["carGenRate"])
        runs = int(simulation.attrib["runs"])
            
        for ii in range(0,runs):
            
            trips_filepath = ("%s/%s-CGR-%.2f-PEN-0.00-%d.trip.xml" % (tripsFolder, networkID, carGenRate, ii))
            routes_filepath = ("%s/%s-CGR-%.2f-PEN-0.00-%d.rou.xml" % (routesFolder, networkID, carGenRate, ii))                
            
            if trips_filepath not in trips:
                trips.append(trips_filepath)                
                duaCommand = ('%s -n %s -t %s -d %s -o %s --remove-loops --repair --ignore-errors' % (os.environ['DUAROUTER_BINARY'], net_filepath, trips_filepath, vtypes_filepath, routes_filepath))
                duaProcess = subprocess.Popen(duaCommand, shell=True, stdout=sys.stdout, stderr=sys.stderr)
                duaProcess.wait()

def addVehTypes2RouteFile(routeFile_filepath):
    
    parse_routeFile = ET.parse(routeFile_filepath) # Use the XML parser to read the net XML file
    routes = parse_routeFile.getroot()
    
    vType = ET.Element('vType', {"id":"HumanStandard", 'color':"blue", 'guiShape':"passenger", 'length':"4.00"})
    sub = ET.SubElement(vType,'carFollowing-Krauss', {'accel':"2.50", 'decel':"4.50", 'sigma':"0.00", 'tau':"0.21"})
    
    vType.tail = "\n    "
    vType.text = "\n        "
    sub.tail = "\n    "
    
    routes.insert(0, vType)
    
    vType = ET.Element('vType', {"id":"HumanCoverageRouted", 'color':"magenta", 'guiShape':"passenger", 'length':"4.00"})
    sub = ET.SubElement(vType,'carFollowing-Krauss', {'accel':"2.50", 'decel':"4.50", 'sigma':"0.00", 'tau':"0.21"})
    
    vType.tail = "\n    "
    vType.text = "\n        "
    sub.tail = "\n    "
    
    routes.insert(1, vType)
    
    parse_routeFile.write(routeFile_filepath, "utf-8")

def addVehTypes2AllRouteFiles(routesFolder):
    """Adds the vtype for coverage based routing humans to the all the route files in a folder"""
    for routeFile in os.listdir(routesFolder):
        routeFile_filepath = ("%s/%s" % (routesFolder, routeFile))
        addVehTypes2RouteFile(routeFile_filepath)

def addPenRates2RouteFiles(simulationDetails_filepath, routesFolder):
    '''Adds vehicles types to the original route files in order to add penetration rate'''
    
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
            
                for ii in range(0,runs):
                
                    basicRoutes_filepath = ("%s/%s-CGR-%.2f-PEN-0.00-%d.rou.xml" % (routesFolder, networkID, carGenRate, ii))
                    routesWithPenRate_filepath = ("%s/%s-CGR-%.2f-PEN-%.2f-%d.rou.xml" % (routesFolder, networkID, carGenRate, PenetrationRate, ii))
                    
                    if routesWithPenRate_filepath not in newfiles:
                        basefiles.append(basicRoutes_filepath)
                        newfiles.append(routesWithPenRate_filepath)
                        penRate.append(PenetrationRate)

    for ii in range(0,len(newfiles)):
                
        parse_basicRoutes = ET.parse(basefiles[ii])
        basicRoutes = parse_basicRoutes.getroot()
                              
        for trip in basicRoutes:
            if trip.tag == 'vehicle' and random.random() < penRate[ii] : trip.set("type", "HumanCoverageRouted")
                  
        parse_basicRoutes.write(newfiles[ii])

def genInductanceLoopsContainer(netFile_filepath, inductionLoops_filepath, inductionLoop_frequency=1800):
    
    ILcontainer = inductionLoop.inductionLoopContainerClass()
    sumolibnet = net.readNet(netFile_filepath)
    
    for edge in sumolibnet.getEdges():
        for lane in edge.getLanes():          
            if edge.getSpeed() > edge.getLength(): # If the lane is too short to reliably allow a vehicle to change route, don't include it
                print("No inductance loop placed on lane %s, as it is too short" % (lane.getID()))
            else: # Otherwise, add an inductance loop to the file, and to the loop_ids list
                pos = edge.getLength() - 1*edge.getSpeed()
                ILcontainer.addIL(lane.getID(), lane.getID(), pos, inductionLoop_frequency)

    pickleFunc.save_obj(ILcontainer, inductionLoops_filepath)

def genAllAdditionalFiles(simulationDetails_filepath, additionalFilesFolder, inductionLoopsContainer_filepath, ILoutputFolder):
    
    parser = ET.XMLParser(encoding="utf-8")
    parse_simulationDetails = ET.parse(simulationDetails_filepath, parser=parser) # Use the XML parser to read the net XML file
    simDetails = parse_simulationDetails.getroot()
    
    for simulation in simDetails:
        simID = simulation.attrib["batchID"]
        runs = int(simulation.attrib["runs"])
        
        for ii in range(0, runs):
            additionalFile_filepath = ("%s/%s-%d.add.xml" % (additionalFilesFolder, simID, ii))
            ILoutput_filepath = ("%s/%s-%d.xml" % (ILoutputFolder, simID, ii))
            
            additionalFile(additionalFile_filepath, inductionLoopsContainer_filepath, ILoutput_filepath)

def additionalFile(additionalFile_filepath, inductionLoops_filepath, ILoutput_filepath):

    ADDFILE = open(additionalFile_filepath, 'w')
    print("<additional>", file=ADDFILE)
    ADDFILE.close()
    
    addInductionLoops2AdditionalFile(additionalFile_filepath, inductionLoops_filepath, ILoutput_filepath)
    
    ADDFILE= open(additionalFile_filepath, 'a')
    print("</additional>", file=ADDFILE)
    ADDFILE.close()
    
def addInductionLoops2AdditionalFile(additionalFile_filepath, inductionLoops_filepath, ILoutput_filepath):
    
    ILcontainer = pickleFunc.load_obj(inductionLoops_filepath)
    
    ADDFILE = open(additionalFile_filepath, 'a')
    
    for IL in ILcontainer.getAllIL():
        print('\t<inductionLoop id="%s" lane="%s" pos="%f" freq="%d" file="%s"/>' % (IL.getID(), IL.getLane(), IL.getPos(), IL.getFreq(), ILoutput_filepath), file=ADDFILE)
            
    ADDFILE.close()
    
def genShortestPathsObject(netFile_filepath, shortestPathsObj_filepath):
    
    shortestPathsObj = shortestPaths.shortestPathsClass(netFile_filepath)
    pickleFunc.save_obj(shortestPathsObj, shortestPathsObj_filepath)

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