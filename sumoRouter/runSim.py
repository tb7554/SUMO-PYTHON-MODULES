#!/usr/bin/env python
"""
@file    runSim.py
@author  Tim Barker
@date    20/06/2015

Function for executing a SUMO simulation using the sumoRouter package.

"""

from __future__ import print_function, division
import subprocess, sys, os
import tools
import traci
from sumoRouter import vehObj
from sumoFileGen import pickleFunc
from blueCrystalFuncs import checkPorts
from tools.sumolib import net
from sumocontrollib import controllers as ctrl
from sumocontrollib.intersection_controller import IntersectionControllerContainer

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


def q_learning_router_with_config_file(net_id, config_file, step_length, alpha, guiOn=False):

    # Input filepaths
    net_file_filepath = ("%s/Net_XML_Files/%s.net.xml" % (os.environ['DIRECTORY_PATH'], net_id))

    # Python objects
    inductionLoopsContainer_filepath = ("%s/netObjects/%s_inductionLoops" % (os.environ['DIRECTORY_PATH'], net_id))
    inductionLoopsContainer = pickleFunc.load_obj(inductionLoopsContainer_filepath)
    loop_ids = inductionLoopsContainer.getILids()

    shortestPaths_filepath = ("%s/netObjects/%s_shortestPaths" % (os.environ['DIRECTORY_PATH'], net_id))
    shortestPathsContainer = pickleFunc.load_obj(shortestPaths_filepath)

    sumolibnet = net.readNet(net_file_filepath)
    vehContainer = vehObj.vehObjContainer(sumolibnet, shortestPathsContainer, loop_ids, alpha)

    # SUMO Commands
    sumoBinary = os.environ["SUMO_BINARY"]
    traci_port = checkPorts.getOpenPort()  # Find a free port for Traci

    if guiOn: sumoBinary += "-gui"  # Append the gui command if requested

    sumoCommand = (
    "%s -c config_file --remote-port %d" % \
    (sumoBinary, config_file, traci_port))
    sumoProcess = subprocess.Popen(sumoCommand, shell=True, stdout=sys.stdout, stderr=sys.stderr)
    print("Launched process: %s" % sumoCommand)

    # open up the traci port
    traci.init(traci_port)
    print("Opened up traci on port %d" % (traci_port))

    # initialise the step
    step = 0

    # run the simulation
    while step == 0 or traci.simulation.getMinExpectedNumber() > 0:
        traci.simulationStep()

        vehContainer.updateVehicles()
        vehContainer.routerObj.updateEdgeOccupancies()
        vehContainer.updateVehicleRoutes()

        step += step_length

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

def controlled_intersections_main(batch_id, net_id, begin_step, end_step, step_length, car_gen_rate, run, queue_controller, green_time_controller, target_frac, guiOn=False, **kwargs):

    if queue_controller == "MaxBoundedQueue":
        queue_control = ctrl.CongestionDemandOptimisingQueueController()
    else:
        print("Unknown queue controller. Update code options in runSim.py")

    if green_time_controller == "MinMax":
        tmin = kwargs['tmin']
        tmax = kwargs['tmax']
        timer = ctrl.MinMaxGreenTimeController(tmin, tmax)
    elif green_time_controller == "Proportional":
        proportional_gain = kwargs['proportional_gain']
        t_start = kwargs['t_start']
        timer = ctrl.PGreenTimeController(proportional_gain, t_start)
    elif green_time_controller == 'ModelBased':
        tmin = kwargs['tmin']
        tmax = kwargs['tmax']
        timer = ctrl.ModelBasedGreenTimeController(tmin, tmax)
    else:
        print("Uknown green time controller. Update code options in runSim.py")

    sumoBinary = os.environ["SUMO_BINARY"]
    if guiOn: sumoBinary += "-gui"

    # Input filepaths
    net_file_filepath = ("%s/Net_XML_Files/%s.net.xml" % (os.environ['DIRECTORY_PATH'], net_id))
    route_file_filepath = ("%s/SUMO_Input_Files/Routes/%s-CGR-%.2f-PEN-0.00-%d.rou.xml" % (
    os.environ['DIRECTORY_PATH'], net_id, car_gen_rate, run))

    # Output filepath
    trip_info_output_filepath = ("%s/SUMO_Output_Files/Trip_Info/TripInfo-%s-%d.xml" % (
    os.environ['DIRECTORY_PATH'], batch_id, run))

    summary_output_filepath = ("%s/SUMO_Output_Files/Summary/Summary-%s-%d.xml" % (
    os.environ['DIRECTORY_PATH'], batch_id, run))

    traci_port = checkPorts.getOpenPort()
    sumoCommand = ("%s -n %s -r %s -b %d -e %d --step-length %.2f --remote-port %d --verbose --time-to-teleport -1 --tripinfo-output %s --summary %s" % \
    (sumoBinary, net_file_filepath, route_file_filepath, begin_step, end_step, step_length, traci_port, trip_info_output_filepath, summary_output_filepath))

    sumoProcess = subprocess.Popen(sumoCommand, shell=True, stdout=sys.stdout, stderr=sys.stderr)
    print("Launched process: %s" % sumoCommand)

    # initialise the step
    step = 0

    intersection_controller_container = IntersectionControllerContainer()
    intersection_controller_container.add_intersection_controllers_from_net_file(net_file_filepath, target_frac, timer,
                                                                                 queue_control)

    # Open up traci on a free port
    traci.init(traci_port)
    print("port opened")
    # run the simulation
    while step < end_step and traci.simulation.getMinExpectedNumber() > 0:
        traci.simulationStep()

        intersection_controller_container.update_intersection_controllers(step, step_length)

        step += step_length

    traci.close()
    sys.stdout.flush()

    sumoProcess.wait()

    intersection_controller_object_save_location = (
    "%s/SUMO_Output_Files/Intersection_Controller_Objects/Intersection_Controller-%s-%d" % (os.environ['DIRECTORY_PATH'], batch_id, run))
    pickleFunc.save_obj(intersection_controller_container, intersection_controller_object_save_location)

def uncontrolled_intersections_main(batch_id, net_id, begin_step, end_step, step_length, car_gen_rate, run, guiOn=False):
    # Input filepaths
    net_file_filepath = ("%s/Net_XML_Files/%s.net.xml" % (os.environ['DIRECTORY_PATH'], net_id))
    route_file_filepath = ("%s/SUMO_Input_Files/Routes/%s-CGR-%.2f-PEN-0.00-%d.rou.xml" % (
    os.environ['DIRECTORY_PATH'], net_id, car_gen_rate, run))

    # Output filepath
    trip_info_output_filepath = ("%s/SUMO_Output_Files/Trip_Info/TripInfo-%s-%d.xml" % (
    os.environ['DIRECTORY_PATH'], batch_id, run))

    summary_output_filepath = ("%s/SUMO_Output_Files/Summary/Summary-%s-%d.xml" % (
    os.environ['DIRECTORY_PATH'], batch_id, run))

    sumoBinary = os.environ["SUMO_BINARY"]

    if guiOn: sumoBinary += "-gui"  # Append the gui command if requested

    sumoCommand = ("%s -n %s -r %s -b %d -e %d --step-length %.2f --verbose --time-to-teleport -1 --tripinfo-output %s --summary %s" % \
    (sumoBinary, net_file_filepath, route_file_filepath, begin_step, end_step, step_length, trip_info_output_filepath, summary_output_filepath))
    sumoProcess = subprocess.Popen(sumoCommand, shell=True, stdout=sys.stdout, stderr=sys.stderr)
    sumoProcess.wait()

def controlled_intersections_main_with_sumocfg_file(batch_id, run, net_id, end_step, step_length, queue_controller, green_time_controller, target_frac, guiOn=False, exclude=[], sumo_options=[], **kwargs):

    if queue_controller == "MaxBoundedQueue":
        queue_control = ctrl.CongestionDemandOptimisingQueueController()
    elif queue_controller == "CongestionAware":
        queue_control = ctrl.CongestionAwareLmaxQueueController()
    elif queue_controller == "CapacityAware":
        queue_control = ctrl.CongestionDemandOptimisingQueueController()
    else:
        print("Unknown queue controller. Update code options in runSim.py")

    if green_time_controller == "MinMax":
        tmin = kwargs['tmin']
        tmax = kwargs['tmax']
        timer = ctrl.MinMaxGreenTimeController(tmin, tmax)
    elif green_time_controller == "Proportional":
        proportional_gain = kwargs['proportional_gain']
        t_start = kwargs['t_start']
        timer = ctrl.PGreenTimeController(proportional_gain, t_start)
    elif green_time_controller == 'ModelBased':
        tmin = kwargs['tmin']
        tmax = kwargs['tmax']
        timer = ctrl.ModelBasedGreenTimeController(tmin, tmax)
    else:
        print("Uknown green time controller. Update code options in runSim.py")

    sumoBinary = os.environ["SUMO_BINARY"]
    if guiOn: sumoBinary += "-gui"

    # Input filepaths
    sumo_config_file = ("%s/SUMO_Input_Files/Config/%s-%d.sumocfg" % (os.environ['DIRECTORY_PATH'], batch_id, run))
    net_file_filepath = ("%s/Net_XML_Files/%s.net.xml" % (os.environ['DIRECTORY_PATH'], net_id))

    traci_port = checkPorts.getOpenPort()
    sumoCommand = ("%s -c %s --remote-port %d" % \
    (sumoBinary, sumo_config_file, traci_port))

    for option in sumo_options:
        sumoCommand += " "
        sumoCommand += str(option)

    sumoProcess = subprocess.Popen(sumoCommand, shell=True, stdout=sys.stdout, stderr=sys.stderr)
    print("Launched process: %s" % sumoCommand)

    # initialise the step
    step = 0

    intersection_controller_container = IntersectionControllerContainer()
    intersection_controller_container.add_intersection_controllers_from_net_file(net_file_filepath, target_frac, timer,
                                                                                 queue_control, step_length, exclude=exclude)

    # Open up traci on a free port
    traci.init(traci_port)
    print("port opened")
    # run the simulation
    while step <= end_step and traci.simulation.getMinExpectedNumber() > 0:
        traci.simulationStep()

        intersection_controller_container.update_intersection_controllers(step, step_length)

        step += step_length

    for ii in range(int(1/step_length)):
        traci.simulationStep()

    for vehicle in traci.vehicle.getIDList():
        traci.vehicle.remove(vehicle)

    traci.close()
    sys.stdout.flush()

    sumoProcess.wait()

    tripinfo_file = ("%s/SUMO_Output_Files/Trip_Info/TripInfo-%s-%d.xml" % (os.environ['DIRECTORY_PATH'], batch_id, run))
    xml2csv_tripinfo_command = ("%s -x %s -s , %s" % (os.environ['XML2CSV_PYTHON'], os.environ['XML_SCHEMA_TRIPINFO'], tripinfo_file))
    xml2csv_process = subprocess.Popen(xml2csv_tripinfo_command, shell=True, stdout=sys.stdout, stderr=sys.stderr)
    xml2csv_process.wait()

    remove_tripinfo_command = ("rm %s" % (tripinfo_file))
    removal_process = subprocess.Popen(remove_tripinfo_command, shell=True, stdout=sys.stdout, stderr=sys.stderr)
    removal_process.wait()

    summary_file = ("%s/SUMO_Output_Files/Summary/Summary-%s-%d.xml" % (os.environ['DIRECTORY_PATH'], batch_id, run))
    xml2csv_summary_command = ("%s -x %s -s , %s" % (os.environ['XML2CSV_PYTHON'], os.environ['XML_SCHEMA_SUMMARY'], summary_file))
    xml2csv_process = subprocess.Popen(xml2csv_summary_command, shell=True, stdout=sys.stdout, stderr=sys.stderr)
    xml2csv_process.wait()

    remove_summary_command = ("rm %s" % (summary_file))
    removal_process = subprocess.Popen(remove_summary_command, shell=True, stdout=sys.stdout, stderr=sys.stderr)
    removal_process.wait()

    edge_file = ("%s/SUMO_Output_Files/Edges/Edge-%s-%d.xml" % (os.environ['DIRECTORY_PATH'], batch_id, run))
    xml2csv_edge_command = ("%s -s , %s" % (os.environ['XML2CSV_PYTHON'], edge_file))
    xml2csv_process = subprocess.Popen(xml2csv_edge_command, shell=True, stdout=sys.stdout, stderr=sys.stderr)
    xml2csv_process.wait()

    intersection_controller_object_save_location = \
        ("%s/SUMO_Output_Files/Intersection_Controller_Objects/Intersection_Controller-%s-%d"
         % (os.environ['DIRECTORY_PATH'], batch_id, run))
    pickleFunc.save_obj(intersection_controller_container, intersection_controller_object_save_location)

def uncontrolled_intersections_main_with_sumo_config_file(batch_id, run, end_step, step_length=0.1, guiOn=False):
    # Input filepaths
    # Input filepaths
    sumo_config_file = ("%s/SUMO_Input_Files/Config/%s-%d.sumocfg" % (os.environ['DIRECTORY_PATH'], batch_id, run))

    # Output filepath
    sumoBinary = os.environ["SUMO_BINARY"]

    if guiOn: sumoBinary += "-gui"  # Append the gui command if requested

    traci_port = checkPorts.getOpenPort()
    sumoCommand = ("%s -c %s --remote-port %d" % \
    (sumoBinary, sumo_config_file, traci_port))

    print("Launched process: %s" % sumoCommand)
    sumoProcess = subprocess.Popen(sumoCommand, shell=True, stdout=sys.stdout, stderr=sys.stderr)

    # initialise the step
    step = 0
    # Open up traci on a free port
    traci.init(traci_port)
    print("port opened")
    # run the simulation
    while step <= end_step and traci.simulation.getMinExpectedNumber() > 0:
        traci.simulationStep()
        step += step_length

    for ii in range(int(1 / step_length)):
        traci.simulationStep()

    for vehicle in traci.vehicle.getIDList():
        traci.vehicle.remove(vehicle)

    traci.close()
    sys.stdout.flush()

    sumoProcess.wait()

    tripinfo_file = ("%s/SUMO_Output_Files/Trip_Info/TripInfo-%s-%d.xml" % (os.environ['DIRECTORY_PATH'], batch_id, run))
    xml2csv_tripinfo_command = ("%s -x %s -s , %s" % (os.environ['XML2CSV_PYTHON'], os.environ['XML_SCHEMA_TRIPINFO'], tripinfo_file))
    xml2csv_process = subprocess.Popen(xml2csv_tripinfo_command, shell=True, stdout=sys.stdout, stderr=sys.stderr)
    xml2csv_process.wait()

    remove_tripinfo_command = ("rm %s" % (tripinfo_file))
    removal_process = subprocess.Popen(remove_tripinfo_command, shell=True, stdout=sys.stdout, stderr=sys.stderr)
    removal_process.wait()

    summary_file = ("%s/SUMO_Output_Files/Summary/Summary-%s-%d.xml" % (os.environ['DIRECTORY_PATH'], batch_id, run))
    xml2csv_summary_command = ("%s -x %s -s , %s --" % (os.environ['XML2CSV_PYTHON'], os.environ['XML_SCHEMA_SUMMARY'], summary_file))
    xml2csv_process = subprocess.Popen(xml2csv_summary_command, shell=True, stdout=sys.stdout, stderr=sys.stderr)
    xml2csv_process.wait()

    remove_summary_command = ("rm %s" % (summary_file))
    removal_process = subprocess.Popen(remove_summary_command, shell=True, stdout=sys.stdout, stderr=sys.stderr)
    removal_process.wait()

    edge_file = ("%s/SUMO_Output_Files/Edges/Edge-%s-%d.xml" % (os.environ['DIRECTORY_PATH'], batch_id, run))
    xml2csv_edge_command = ("%s -s , %s" % (os.environ['XML2CSV_PYTHON'], edge_file))
    xml2csv_process = subprocess.Popen(xml2csv_edge_command, shell=True, stdout=sys.stdout, stderr=sys.stderr)
    xml2csv_process.wait()


