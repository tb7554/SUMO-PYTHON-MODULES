#!/usr/bin/env python
"""
@file    runSim.py
@author  Tim Barker
@date    20/06/2015

Function for executing a SUMO simulation using the sumoRouter package.

"""

from __future__ import print_function, division
import subprocess, sys, os
import traci
from sumoRouter import vehObj
from sumoFileGen import pickleFunc
from blueCrystalFuncs import checkPorts
from tools.sumolib import net

def covBasedRoutingMain(netID, stepLength, carGenRate, penetrationRate, run, alpha, guiOn = False):
    
    # Input filepaths
    netFile_filepath = ("%s/netXMLFiles/%s.net.xml" % (os.environ['DIRECTORY_PATH'], netID))
    routeFile_filepath = ("%s/SUMO_Input_Files/routeFiles/%s-CGR-%.2f-PEN-%.2f-%d.rou.xml" % (os.environ['DIRECTORY_PATH'], netID, carGenRate, penetrationRate, run))
    addFile_filepath = ("%s/SUMO_Input_Files/additionalFiles/%s-CGR-%.2f-CBR-PEN-%.2f-ALPHA-%.2f-%d.add.xml" % (os.environ['DIRECTORY_PATH'], netID, carGenRate, penetrationRate, alpha, run))
    
    # Output filepath
    tripInfoOutput_filepath = ("%s/SUMO_Output_Files/tripFiles/tripInfo-%s-CGR-%.2f-CBR-PEN-%.2f-ALPHA-%.2f-%d.xml" % (os.environ['DIRECTORY_PATH'], netID, carGenRate, penetrationRate, alpha, run))
    vehRoutesOutput_filepath = ("%s/SUMO_Output_Files/vehRoutes/vehRoutes-%s-CGR-%.2f-CBR-PEN-%.2f-ALPHA-%.2f-%d.rou.xml" % (os.environ['DIRECTORY_PATH'], netID, carGenRate, penetrationRate, alpha, run))
    
    # Python objects
    inductionLoopsContainer_filepath = ("%s/netObjects/%s_inductionLoops" % (os.environ['DIRECTORY_PATH'], netID)) 
    inductionLoopsContainer = pickleFunc.load_obj(inductionLoopsContainer_filepath)
    loop_ids = inductionLoopsContainer.getILids()
    
    shortestPaths_filepath = ("%s/netObjects/%s_shortestPaths" % (os.environ['DIRECTORY_PATH'], netID))
    shortestPathsContainer = pickleFunc.load_obj(shortestPaths_filepath)
    
    sumolibnet = net.readNet(netFile_filepath)
    vehContainer = vehObj.vehObjContainer(sumolibnet, shortestPathsContainer, loop_ids, alpha)
    
    # SUMO Commands
    sumoBinary = os.environ["SUMO_BINARY"]
    traciPORT = checkPorts.getOpenPort() # Find a free port for Traci
    
    if guiOn: sumoBinary += "-gui" # Append the gui command if requested 
    
    sumoCommand = ("%s -n %s -a %s -r %s --step-length %.2f --tripinfo-output %s --vehroute-output %s --vehroute-output.last-route --vehroute-output.sorted --remote-port %d" % \
                   (sumoBinary, netFile_filepath, addFile_filepath, routeFile_filepath, stepLength, tripInfoOutput_filepath, vehRoutesOutput_filepath, traciPORT))
    sumoProcess = subprocess.Popen(sumoCommand, shell=True, stdout=sys.stdout, stderr=sys.stderr)
    print("Launched process: %s" % sumoCommand)
    
    # open up the traci port
    traci.init(traciPORT)
    print("Opened up traci on port %d" % (traciPORT))
    
    # initialise the step
    step = 0
    
    # run the simulation
    while step == 0 or traci.simulation.getMinExpectedNumber() > 0:
        traci.simulationStep()
        #timeNow = traci.simulation.getCurrentTime()
        vehContainer.updateVehicles()
        vehContainer.routerObj.updateEdgeOccupancies()
        vehContainer.updateVehicleRoutes()
        
        step += stepLength
    
    traci.close()
    sys.stdout.flush()
    sumoProcess.wait()

def travelTimeRouterMain(netID, stepLength, carGenRate, penetrationRate, run, updateInterval = 15, guiOn = False):
    
    # Input filepaths
    netFile_filepath = ("%s/netXMLFiles/%s.net.xml" % (os.environ['DIRECTORY_PATH'], netID))
    routeFile_filepath = ("%s/SUMO_Input_Files/routeFiles/%s-CGR-%.2f-PEN-0.00-%d.rou.xml" % (os.environ['DIRECTORY_PATH'], netID, carGenRate, run))
    
    # Output filepath
    tripInfoOutput_filepath = ("%s/SUMO_Output_Files/tripFiles/tripInfo-%s-CGR-%.2f-TTRR-PEN-%.2f-RUI-%d-%d.xml" % (os.environ['DIRECTORY_PATH'], netID, carGenRate, penetrationRate, int(updateInterval), run))
    vehRoutesOutput_filepath = ("%s/SUMO_Output_Files/vehRoutes/vehRoutes-%s-CGR-%.2f-TTRR-PEN-%.2f-RUI-%d-%d.rou.xml" % (os.environ['DIRECTORY_PATH'], netID, carGenRate, penetrationRate, int(updateInterval), run))
    
    sumoBinary = os.environ["SUMO_BINARY"]
    if guiOn: sumoBinary += "-gui"
    sumoCommand = ("%s -n %s -r %s --step-length %.2f --device.rerouting.probability %f --device.rerouting.period %d --device.rerouting.adaptation-interval %d --tripinfo-output %s --vehroute-output %s --vehroute-output.last-route --vehroute-output.sorted" \
    % (sumoBinary, netFile_filepath, routeFile_filepath, stepLength, penetrationRate, int(updateInterval), int(updateInterval), tripInfoOutput_filepath, vehRoutesOutput_filepath))
    
    sumoProcess = subprocess.Popen(sumoCommand, shell=True, stdout=sys.stdout)
    sumoProcess.wait()
    
def duaRouterIterativeMain(netID, stepLength, carGenRate, run):
    
    # Input filepaths
    netFile_filepath = ("%s/netXMLFiles/%s.net.xml" % (os.environ["DIRECTORY_PATH"], netID))
    routeFile_filepath = ("%s/SUMO_Input_Files/routeFiles/%s-CGR-%.2f-PEN-0.00-%d.rou.xml" % (os.environ["DIRECTORY_PATH"], netID, carGenRate, run))
    
    duaCommand = ("%s -n %s -r %s --disable-summary sumo--step-length %f" % (os.environ['DUAITERATE_PYTHON'], netFile_filepath, routeFile_filepath, stepLength))
                    
    duaIterateProcess = subprocess.Popen(duaCommand, shell=True, stdout=sys.stdout)
    duaIterateProcess.wait()
    
def shortestPathMain(netID, stepLength, carGenRate, run, guiOn = False):

    # Input filepaths
    netFile_filepath = ("%s/netXMLFiles/%s.net.xml" % (os.environ['DIRECTORY_PATH'], netID))
    routeFile_filepath = ("%s/SUMO_Input_Files/routeFiles/%s-CGR-%.2f-PEN-0.00-%d.rou.xml" % (os.environ['DIRECTORY_PATH'], netID, carGenRate, run))
    
    # Output filepath
    tripInfoOutput_filepath = ("%s/SUMO_Output_Files/tripFiles/tripInfo-%s-CGR-%.2f-SP-%d.xml" % (os.environ['DIRECTORY_PATH'], netID, carGenRate, run))
    vehRoutesOutput_filepath = ("%s/SUMO_Output_Files/vehRoutes/vehRoutes-%s-CGR-%.2f-SP-%d.rou.xml" % (os.environ['DIRECTORY_PATH'], netID, carGenRate, run))
     
    sumoBinary = os.environ["SUMO_BINARY"]
    
    if guiOn: sumoBinary += "-gui" # Append the gui command if requested 
    
    sumoCommand = ("%s -n %s -r %s --step-length %.2f --tripinfo-output %s --vehroute-output %s --vehroute-output.last-route --vehroute-output.sorted" % \
                   (sumoBinary, netFile_filepath, routeFile_filepath, stepLength, tripInfoOutput_filepath, vehRoutesOutput_filepath))
    sumoProcess = subprocess.Popen(sumoCommand, shell=True, stdout=sys.stdout, stderr=sys.stderr)
    sumoProcess.wait()
    