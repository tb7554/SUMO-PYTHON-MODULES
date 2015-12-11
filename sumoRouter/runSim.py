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
from sumoRouter import netObjects, vehObj
from sumoFileGen import pickleFunc
from blueCrystalFuncs import checkPorts

# Define the path for the environment variable SUMO_HOME
directory_path = os.getcwd()
path_components = directory_path.split('/')
directory_name = path_components.pop()

def covBasedRoutingMain(netID, stepLength, carGenRate, penetrationRate, run, alpha, guiOn = False):
    
    #Object filepaths
    shortestPaths_filepath = ("%s/netObjects/%s_shortestPaths" % (directory_path, netID))
    loopIDs_filepath = ("%s/netObjects/%s_loopIDs" % (directory_path, netID)) 
    
    # Input filepaths
    netFile_filepath = ("%s/netXMLFiles/%s.net.xml" % (directory_path, netID))
    routeFile_filepath = ("%s/SUMO_Input_Files/routeFiles/%s-CGR-%.2f-PEN-%.2f-%d.rou.xml" % (directory_path, netID, carGenRate, penetrationRate, run))
    addFile_filepath = ("%s/SUMO_Input_Files/additionalFiles/%s-CGR-%.2f-PEN-%.2f-%d.add.xml" % (directory_path, netID, carGenRate, penetrationRate, run))
    
    # Output filepath
    tripInfoOutput_filepath = ("%s/SUMO_Output_Files/tripFiles/tripInfo-%s-CGR-%.2f-CBR-PEN-%.2f-ALPHA-%.2f-%d.xml" % (directory_path, netID, carGenRate, penetrationRate, alpha, run))
    vehRoutesOutput_filepath = ("%s/SUMO_Output_Files/vehRoutes/vehRoutes-%s-CGR-%.2f-CBR-PEN-%.2f-ALPHA-%.2f-%d.rou.xml" % (directory_path, netID, carGenRate, penetrationRate, alpha, run))
    summaryOutput_filepath = ("%s/SUMO_Output_Files/summary/summary-%s-CGR-%.2f-CBR-PEN-%.2f-ALPHA-%.2f-%d.xml" % (directory_path, netID, carGenRate, penetrationRate, alpha, run))
     
    #Load the edgeContainer and juncContainer objects, and the loop IDs
    shortestPaths = pickleFunc.load_obj(shortestPaths_filepath)
    loop_ids = pickleFunc.load_obj(loopIDs_filepath)
    
    # Create a container for vehicle objects
    vehContainer = vehObj.vehObjContainer(edgeContainer, juncContainer, loop_ids, alpha)
    
    # Find a free port for Traci
    traciPORT = checkPorts.getOpenPort()
    # Start a sumo simulation as a subprocess
    sumoBinary = os.environ["SUMO_BINARY"]
    if guiOn: sumoBinary += "-gui" # Append the gui command if requested 
    
    #configfilepath = ("%s/SUMO_Input_Files/configurationFiles/test.sumocfg" % (directory_path))
    #sumoCommand = ("%s -c %s" % (sumoBinary, configfilepath))
    sumoCommand = ("%s -n %s -a %s -r %s --step-length %.2f --tripinfo-output %s --vehroute-output %s --vehroute-output.last-route --vehroute-output.sorted --remote-port %d" % \
                   (sumoBinary, netFile_filepath, addFile_filepath, routeFile_filepath, stepLength, tripInfoOutput_filepath, vehRoutesOutput_filepath, traciPORT))
    #sumoCommand = [sumoBinary, "-n", netFile_filepath, "-a", addFile_filepath, "-r", routeFile_filepath, "--step-length", str(stepLength), "--tripinfo-output", tripInfoOutput_filepath, \
    #               "--vehroute-output", vehRoutesOutput_filepath, "--vehroute-output.last-route", "--vehroute-output.sorted", "--summary-output", summaryOutput_filepath, "--remote-port", str(traciPORT)]
    sumoProcess = subprocess.Popen(sumoCommand, shell=True, stdout=sys.stdout, stderr=sys.stderr)
    
    # open up the traci port
    traci.init(traciPORT)
    
    # initialise the step
    step = 0
     
    # run the simulation
    while step == 0 or traci.simulation.getMinExpectedNumber() > 0:
        traci.simulationStep()
        #timeNow = traci.simulation.getCurrentTime()
        
        # Update the vehicle container vehicles
        vehContainer.updateVehicles(step)
        
        # Update the edge container occupancies
        vehContainer.routerObj.updateEdgeOccupancies()
        
        # update vehicle routes
        vehContainer.updateVehicleRoutes()
        
        step += stepLength
    
    traci.close()
    sys.stdout.flush()
    sumoProcess.wait()

def travelTimeRouterMain(netID, stepLength, carGenRate, penetrationRate, run, updateInterval = 15, guiOn = False):
    
    # Input filepaths
    netFile_filepath = ("%s/netXMLFiles/%s.net.xml" % (directory_path, netID))
    routeFile_filepath = ("%s/SUMO_Input_Files/routeFiles/%s-CGR-%.2f-PEN-0.00-%d.rou.xml" % (directory_path, netID, carGenRate, run))
    
    # Output filepath
    tripInfoOutput_filepath = ("%s/SUMO_Output_Files/tripFiles/tripInfo-%s-CGR-%.2f-TTRR-PEN-%.2f-RUI-%d-%d.xml" % (directory_path, netID, carGenRate, penetrationRate, int(updateInterval), run))
    vehRoutesOutput_filepath = ("%s/SUMO_Output_Files/vehRoutes/vehRoutes-%s-CGR-%.2f-TTRR-PEN-%.2f-RUI-%d-%d.rou.xml" % (directory_path, netID, carGenRate, penetrationRate, int(updateInterval), run))
    summaryOutput_filepath = ("%s/SUMO_Output_Files/summary/summary-%s-CGR-%.2f-TTRR-PEN-%.2f-RUI-%d-%d.xml" % (directory_path, netID, carGenRate, penetrationRate, int(updateInterval), run))
    
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