#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Author: Tim Barker
Created: 15/05/2015
Modified: 15/05/2015

Functions relating to saving and analysing results from SUMO

"""

from __future__ import print_function, division

import matplotlib
from matplotlib import pyplot as plt
import os, sys, math, time, re, random

import numpy as np
from sumoFileGen import pickleFunc
from sumoRouter import netObjects
import xml.etree.ElementTree as ET

directory_path = os.getcwd()
os.environ['DIRECTORY_PATH'] = os.getcwd()
path_components = directory_path.split('/')
directory_name = path_components.pop()

if __name__=="__main__":
    directory_path = os.path.dirname(os.getcwd())
    sys.path.append(directory_path)

def dictAdd(dict1, dict2):
    
    for element in dict1:
        dict1[element] += dict2[element]
    
    return dict1

def dictDiv(dict1, dict2):
    
    for element in dict1:
        dict1[element] /= dict2[element]
        
    return dict1

def carsInNetworkOverTime(tripFile_filepath):
    
    # This function takes a trip file and outputs an array containing the cumulative number of finished journeys at each time step
    tripData = ET.parse(tripFile_filepath) # Use the XML parser to read the net XML file
    trips = tripData.getroot()
    
    totalSimTime = 0
    for trip in trips:
        if int(float(trip.attrib["arrival"])) > totalSimTime : totalSimTime = int(float(trip.attrib["arrival"]))
    totalSimTime += 1
    
    carsInNetwork = [0] * totalSimTime
        
    for trip in trips:
        arrivalTime = int(float(trip.attrib["arrival"]))
        departTime = int(float(trip.attrib["depart"]))
        carsInNetwork[departTime] += 1
        carsInNetwork[arrivalTime] -= 1
    
    return np.cumsum(carsInNetwork)

def carsInNetworkOverTimeMultiRun(carsOverTimeArray):
    
    runs = len(carsOverTimeArray)
     
    maxTime = 0
    for run in carsOverTimeArray:
        if maxTime < len(run) : maxTime = len(run)
    maxTime += 1
    
    carsOverTime_mean = [] * maxTime
    carsOverTime_stdDev = [] * maxTime
    
    for t in range(0, maxTime):
        data = [] * runs
        for run in carsOverTimeArray:
            try:
                data.append(run[t])
            except IndexError:
                data.append(0)
                
        carsOverTime_mean.append(np.mean(data))
        carsOverTime_stdDev.append(np.std(data))
        
    return carsOverTime_mean, carsOverTime_stdDev

def extractTravelTimeStats(tripFile_filepath, withDepartDelays = True):
    
    tripData = ET.parse(tripFile_filepath) # Use the XML parser to read the net XML file
    trips = tripData.getroot()
    
    travelTimes = []
    
    for trip in trips:
        departDelay = float(trip.attrib["departDelay"])
        travelDuration = float(trip.attrib["duration"])
        
        if withDepartDelays : travelDuration += departDelay
        
        travelTimes.append(travelDuration)
        
    mean_travelTime = np.mean(travelTimes)
    stdDev_travelTime = np.std(travelTimes)
        
    return mean_travelTime, stdDev_travelTime

def extractVehicleIDList(routeFile_filepath):
    routeData = ET.parse(routeFile_filepath) # Use the XML parser to read the net XML file
    vehicleRoutes = routeData.getroot()
    
    vehIDs = []
    
    for vehicle in vehicleRoutes:
        if vehicle.tag == 'vehicle':
            vehID = vehicle.attrib['id']
            
            vehIDs.append(vehID)
            
    return vehIDs

def extractVehicleExpectedTravelTimesFromRouteFile(routeFile_filepath):
    # This function takes the path to an alt.rou.xml file and extracts the route cost for each vehicle.
    # It returns a dictionary with vehicle names as the key, and expected travel time as the attribute.
    
    routeData = ET.parse(routeFile_filepath) # Use the XML parser to read the net XML file
    vehicleRoutes = routeData.getroot()
    
    vehRoute_costs = {}
    
    for vehicle in vehicleRoutes:
        if vehicle.tag == 'vehicle':
            vehID = vehicle.attrib['id']
            for routeDistribution in vehicle:
                for route in routeDistribution:
                    cost = float(route.attrib['cost'])
                
            vehRoute_costs.update({vehID:cost})
        
    return vehRoute_costs

def extractVehicleActualTravelTimesFromTripFile(tripFile_filepath):
    # This function takes the filepath to a trip output file from SUMO and extracts the trip duration for each vehicle.
    # It returns a dictionary with vehicle names as the key, and the trip duration as the attribute.
    
    tripData =  ET.parse(tripFile_filepath)
    trips = tripData.getroot()
    
    trip_durations = {}
    
    for veh in trips:
        vehID = veh.attrib['id']
        travelTime = float(veh.attrib['duration'])
        
        trip_durations.update({vehID : travelTime})

    return trip_durations

def calculateTripDelayStats(tripFile_filepath, routeFile_filepath):
    
    trip_delays = []
    
    vehIDs = extractVehicleIDList(routeFile_filepath)
    veh_TravelTimes = extractVehicleActualTravelTimesFromTripFile(tripFile_filepath)
    vehRoute_costs = extractVehicleExpectedTravelTimesFromRouteFile(routeFile_filepath)
    
    for veh in vehIDs:
        delay = veh_TravelTimes[veh] - vehRoute_costs[veh]
        trip_delays.append(delay)

    mean_delay = np.mean(trip_delays)
    stdDev_delay = np.std(trip_delays)
        
    return mean_delay, stdDev_delay

def delayAsFractionOfTravelTime(tripFile_filepath, routeFile_filepath):
     
    trip_delaysOverTravelTime = []
    
    vehIDs = extractVehicleIDList(routeFile_filepath)
    veh_TravelTimes = extractVehicleActualTravelTimesFromTripFile(tripFile_filepath)
    vehRoute_costs = extractVehicleExpectedTravelTimesFromRouteFile(routeFile_filepath)
    
    for veh in vehIDs:
        delay = veh_TravelTimes[veh] - vehRoute_costs[veh]
        delayOverTravelTime = delay/veh_TravelTimes[veh]
        
        trip_delaysOverTravelTime.append(delayOverTravelTime)
        
    mean_delayOverTravelTime = np.mean(trip_delaysOverTravelTime)
    stdDev_delayOverTravelTime = np.std(trip_delaysOverTravelTime)
        
    return mean_delayOverTravelTime, stdDev_delayOverTravelTime

def delayAsFractionOfExpectedTravelTime(tripFile_filepath, routeFile_filepath):
     
    trip_delaysOverExpectedTravelTime = []
    
    vehIDs = extractVehicleIDList(routeFile_filepath)
    veh_TravelTimes = extractVehicleActualTravelTimesFromTripFile(tripFile_filepath)
    vehRoute_costs = extractVehicleExpectedTravelTimesFromRouteFile(routeFile_filepath)
    
    for veh in vehIDs:
        delay = veh_TravelTimes[veh] - vehRoute_costs[veh]
        delayOverExpectedTravelTime = delay/vehRoute_costs[veh]
        
        trip_delaysOverExpectedTravelTime.append(delayOverExpectedTravelTime)
        
    mean_delayOverExpectedTravelTime = np.mean(trip_delaysOverExpectedTravelTime)
    stdDev_delayOverExpectedTravelTime = np.std(trip_delaysOverExpectedTravelTime)
        
    return mean_delayOverExpectedTravelTime, stdDev_delayOverExpectedTravelTime

def extractVehTypeFromTripFile(tripFile_filepath):
    # This function takes the filepath to a trip output file from SUMO and extracts the vehicle type (namely, the routing algorithm type)
    # It returns a dictionary with vehicle names as the key, and the wait time as the attribute.
    
    tripData =  ET.parse(tripFile_filepath)
    trips = tripData.getroot()
    
    trip_vTypes = {}
    
    for veh in trips:
        vehID = veh.attrib['id']
        vType = veh.attrib['vType']
        vehDevices = veh.attrib['devices']
        
        if vType == "HumanCoverageRouted":
            trip_vTypes.update({vehID : 'Coverage Based Routing'})
        elif vType == "HumanStandard" or vType == "DEFAULT_VEHTYPE":
            routingDeviceName = ("routing_%s" % (vehID))
            if re.search(routingDeviceName, vehDevices):
                trip_vTypes.update({vehID : 'Travel Time Re-Router'})
            else:
                trip_vTypes.update({vehID : 'No Dynamic Routing'})

    return trip_vTypes

def splitVehDataByVehType(veh_dataDict, veh_typeDict):
    
    vehTypes = []
    veh_dataDict_split = {}
    
    for veh in veh_typeDict:
        vType = veh_typeDict[veh]
        if vType not in vehTypes: vehTypes.append(vType)
    
    veh_dataDict_split.update({"vTypes":vehTypes})
    for veh in vehTypes:
        veh_dataDict_split.update({veh:{}})
    
    for veh in veh_dataDict:
        data = veh_dataDict[veh]
        vType = veh_typeDict[veh]
        veh_dataDict_split[vType].update({veh:data})
        
    return veh_dataDict_split
    
def convertCarDataAndTimeData2TimeDict(veh_dataDict, veh_timeDict):
    
    dataByTime_dict = {}
    simEndTime = 0;
    
    for veh in veh_timeDict:
        if veh_timeDict[veh] > simEndTime : simEndTime = int(veh_timeDict[veh])
    
    dataByTime_dict.update({'simEndTime':simEndTime})
    
    for ii in range(0,simEndTime+1):
        dataByTime_dict.update({ii:[]})
    
    for veh in veh_timeDict:
        time = int(veh_timeDict[veh])
        if veh in veh_dataDict : dataByTime_dict[time].append(veh_dataDict[veh])

    return dataByTime_dict

def convertCarDataOverTime2MovingAverage(dataByTime_dict, timeWindow=False): 
    # Takes one dictionary organised by vehicle ID, with some data value, and another dict iving a time references (e.g. insertion/arrival), and simulation Length (int)
    # Outputs a list obect with the moving average over time for the data
    
    simEndTime = dataByTime_dict['simEndTime']
    if not(timeWindow):
        timeWindow = simEndTime
    
    data_window = np.array([])
    
    data_movingAverage = [0]*simEndTime
    data_movingStdDev = [0]*simEndTime
    
    for ii in range(0, simEndTime):
        if ii <= timeWindow:
            data_window = np.append(data_window, dataByTime_dict[ii], axis=0)
        else:
            data_window = np.delete(data_window, 0, axis=0)
            data_window = np.append(data_window, dataByTime_dict[ii], axis=0)
        
        average = np.mean(data_window)
        stdDev = np.std(data_window, dtype=np.float64)
        
        if math.isnan(average) : average = 0
        if math.isnan(stdDev) : stdDev = 0
        
        data_movingAverage[ii] = average
        data_movingStdDev[ii] = stdDev
        
        higher_bound = np.add(data_movingAverage, data_movingStdDev)
        lower_bound = np.subtract(data_movingAverage, data_movingStdDev)
        
    return np.array([data_movingAverage, higher_bound, lower_bound])

def retrieveColourScheme(schemeName):
    
    from matplotlib.colors import LinearSegmentedColormap
    
    if schemeName == "meanData":
        scheme = [[(31, 119, 180), (174, 199, 232), (174, 199, 232)],
                  [(148, 103, 189), (197, 176, 213), (197, 176, 213)], 
                  [(227, 119, 194), (247, 182, 210), (247, 182, 210)],
                  [(255, 127, 14), (255, 187, 120), (255, 187, 120)], 
                  [(44, 160, 44), (152, 223, 138), (152, 223, 138)],
                  [(214, 39, 40), (255, 152, 150), (255, 152, 150)],    
                  [(140, 86, 75), (196, 156, 148), (196, 156, 148)],
                  [(127, 127, 127), (199, 199, 199), (199, 199, 199)],
                  [(188, 189, 34), (219, 219, 141), (219, 219, 141)],
                  [(23, 190, 207), (158, 218, 229), (158, 218, 229)]]
        for ii in range(len(scheme)):
            for jj in range(0,3):
                r, g, b = scheme[ii][jj]
                scheme[ii][jj] = (r / 255., g / 255., b / 255.)  
        
    if schemeName == "parula":
        cm_data = [[0.2081, 0.1663, 0.5292], [0.2116238095, 0.1897809524, 0.5776761905], 
         [0.212252381, 0.2137714286, 0.6269714286], [0.2081, 0.2386, 0.6770857143], 
         [0.1959047619, 0.2644571429, 0.7279], [0.1707285714, 0.2919380952, 
          0.779247619], [0.1252714286, 0.3242428571, 0.8302714286], 
         [0.0591333333, 0.3598333333, 0.8683333333], [0.0116952381, 0.3875095238, 
          0.8819571429], [0.0059571429, 0.4086142857, 0.8828428571], 
         [0.0165142857, 0.4266, 0.8786333333], [0.032852381, 0.4430428571, 
          0.8719571429], [0.0498142857, 0.4585714286, 0.8640571429], 
         [0.0629333333, 0.4736904762, 0.8554380952], [0.0722666667, 0.4886666667, 
          0.8467], [0.0779428571, 0.5039857143, 0.8383714286], 
         [0.079347619, 0.5200238095, 0.8311809524], [0.0749428571, 0.5375428571, 
          0.8262714286], [0.0640571429, 0.5569857143, 0.8239571429], 
         [0.0487714286, 0.5772238095, 0.8228285714], [0.0343428571, 0.5965809524, 
          0.819852381], [0.0265, 0.6137, 0.8135], [0.0238904762, 0.6286619048, 
          0.8037619048], [0.0230904762, 0.6417857143, 0.7912666667], 
         [0.0227714286, 0.6534857143, 0.7767571429], [0.0266619048, 0.6641952381, 
          0.7607190476], [0.0383714286, 0.6742714286, 0.743552381], 
         [0.0589714286, 0.6837571429, 0.7253857143], 
         [0.0843, 0.6928333333, 0.7061666667], [0.1132952381, 0.7015, 0.6858571429], 
         [0.1452714286, 0.7097571429, 0.6646285714], [0.1801333333, 0.7176571429, 
          0.6424333333], [0.2178285714, 0.7250428571, 0.6192619048], 
         [0.2586428571, 0.7317142857, 0.5954285714], [0.3021714286, 0.7376047619, 
          0.5711857143], [0.3481666667, 0.7424333333, 0.5472666667], 
         [0.3952571429, 0.7459, 0.5244428571], [0.4420095238, 0.7480809524, 
          0.5033142857], [0.4871238095, 0.7490619048, 0.4839761905], 
         [0.5300285714, 0.7491142857, 0.4661142857], [0.5708571429, 0.7485190476, 
          0.4493904762], [0.609852381, 0.7473142857, 0.4336857143], 
         [0.6473, 0.7456, 0.4188], [0.6834190476, 0.7434761905, 0.4044333333], 
         [0.7184095238, 0.7411333333, 0.3904761905], 
         [0.7524857143, 0.7384, 0.3768142857], [0.7858428571, 0.7355666667, 
          0.3632714286], [0.8185047619, 0.7327333333, 0.3497904762], 
         [0.8506571429, 0.7299, 0.3360285714], [0.8824333333, 0.7274333333, 0.3217], 
         [0.9139333333, 0.7257857143, 0.3062761905], [0.9449571429, 0.7261142857, 
          0.2886428571], [0.9738952381, 0.7313952381, 0.266647619], 
         [0.9937714286, 0.7454571429, 0.240347619], [0.9990428571, 0.7653142857, 
          0.2164142857], [0.9955333333, 0.7860571429, 0.196652381], 
         [0.988, 0.8066, 0.1793666667], [0.9788571429, 0.8271428571, 0.1633142857], 
         [0.9697, 0.8481380952, 0.147452381], [0.9625857143, 0.8705142857, 0.1309], 
         [0.9588714286, 0.8949, 0.1132428571], [0.9598238095, 0.9218333333, 
          0.0948380952], [0.9661, 0.9514428571, 0.0755333333], 
         [0.9763, 0.9831, 0.0538]]
        
        parula_map = LinearSegmentedColormap.from_list('parula', cm_data)
        # For use of "viscm view"
        scheme = parula_map
        
    if schemeName == 'viridis':
        cm_data = [[0.267004, 0.004874, 0.329415],
         [0.268510, 0.009605, 0.335427],
         [0.269944, 0.014625, 0.341379],
         [0.271305, 0.019942, 0.347269],
         [0.272594, 0.025563, 0.353093],
         [0.273809, 0.031497, 0.358853],
         [0.274952, 0.037752, 0.364543],
         [0.276022, 0.044167, 0.370164],
         [0.277018, 0.050344, 0.375715],
         [0.277941, 0.056324, 0.381191],
         [0.278791, 0.062145, 0.386592],
         [0.279566, 0.067836, 0.391917],
         [0.280267, 0.073417, 0.397163],
         [0.280894, 0.078907, 0.402329],
         [0.281446, 0.084320, 0.407414],
         [0.281924, 0.089666, 0.412415],
         [0.282327, 0.094955, 0.417331],
         [0.282656, 0.100196, 0.422160],
         [0.282910, 0.105393, 0.426902],
         [0.283091, 0.110553, 0.431554],
         [0.283197, 0.115680, 0.436115],
         [0.283229, 0.120777, 0.440584],
         [0.283187, 0.125848, 0.444960],
         [0.283072, 0.130895, 0.449241],
         [0.282884, 0.135920, 0.453427],
         [0.282623, 0.140926, 0.457517],
         [0.282290, 0.145912, 0.461510],
         [0.281887, 0.150881, 0.465405],
         [0.281412, 0.155834, 0.469201],
         [0.280868, 0.160771, 0.472899],
         [0.280255, 0.165693, 0.476498],
         [0.279574, 0.170599, 0.479997],
         [0.278826, 0.175490, 0.483397],
         [0.278012, 0.180367, 0.486697],
         [0.277134, 0.185228, 0.489898],
         [0.276194, 0.190074, 0.493001],
         [0.275191, 0.194905, 0.496005],
         [0.274128, 0.199721, 0.498911],
         [0.273006, 0.204520, 0.501721],
         [0.271828, 0.209303, 0.504434],
         [0.270595, 0.214069, 0.507052],
         [0.269308, 0.218818, 0.509577],
         [0.267968, 0.223549, 0.512008],
         [0.266580, 0.228262, 0.514349],
         [0.265145, 0.232956, 0.516599],
         [0.263663, 0.237631, 0.518762],
         [0.262138, 0.242286, 0.520837],
         [0.260571, 0.246922, 0.522828],
         [0.258965, 0.251537, 0.524736],
         [0.257322, 0.256130, 0.526563],
         [0.255645, 0.260703, 0.528312],
         [0.253935, 0.265254, 0.529983],
         [0.252194, 0.269783, 0.531579],
         [0.250425, 0.274290, 0.533103],
         [0.248629, 0.278775, 0.534556],
         [0.246811, 0.283237, 0.535941],
         [0.244972, 0.287675, 0.537260],
         [0.243113, 0.292092, 0.538516],
         [0.241237, 0.296485, 0.539709],
         [0.239346, 0.300855, 0.540844],
         [0.237441, 0.305202, 0.541921],
         [0.235526, 0.309527, 0.542944],
         [0.233603, 0.313828, 0.543914],
         [0.231674, 0.318106, 0.544834],
         [0.229739, 0.322361, 0.545706],
         [0.227802, 0.326594, 0.546532],
         [0.225863, 0.330805, 0.547314],
         [0.223925, 0.334994, 0.548053],
         [0.221989, 0.339161, 0.548752],
         [0.220057, 0.343307, 0.549413],
         [0.218130, 0.347432, 0.550038],
         [0.216210, 0.351535, 0.550627],
         [0.214298, 0.355619, 0.551184],
         [0.212395, 0.359683, 0.551710],
         [0.210503, 0.363727, 0.552206],
         [0.208623, 0.367752, 0.552675],
         [0.206756, 0.371758, 0.553117],
         [0.204903, 0.375746, 0.553533],
         [0.203063, 0.379716, 0.553925],
         [0.201239, 0.383670, 0.554294],
         [0.199430, 0.387607, 0.554642],
         [0.197636, 0.391528, 0.554969],
         [0.195860, 0.395433, 0.555276],
         [0.194100, 0.399323, 0.555565],
         [0.192357, 0.403199, 0.555836],
         [0.190631, 0.407061, 0.556089],
         [0.188923, 0.410910, 0.556326],
         [0.187231, 0.414746, 0.556547],
         [0.185556, 0.418570, 0.556753],
         [0.183898, 0.422383, 0.556944],
         [0.182256, 0.426184, 0.557120],
         [0.180629, 0.429975, 0.557282],
         [0.179019, 0.433756, 0.557430],
         [0.177423, 0.437527, 0.557565],
         [0.175841, 0.441290, 0.557685],
         [0.174274, 0.445044, 0.557792],
         [0.172719, 0.448791, 0.557885],
         [0.171176, 0.452530, 0.557965],
         [0.169646, 0.456262, 0.558030],
         [0.168126, 0.459988, 0.558082],
         [0.166617, 0.463708, 0.558119],
         [0.165117, 0.467423, 0.558141],
         [0.163625, 0.471133, 0.558148],
         [0.162142, 0.474838, 0.558140],
         [0.160665, 0.478540, 0.558115],
         [0.159194, 0.482237, 0.558073],
         [0.157729, 0.485932, 0.558013],
         [0.156270, 0.489624, 0.557936],
         [0.154815, 0.493313, 0.557840],
         [0.153364, 0.497000, 0.557724],
         [0.151918, 0.500685, 0.557587],
         [0.150476, 0.504369, 0.557430],
         [0.149039, 0.508051, 0.557250],
         [0.147607, 0.511733, 0.557049],
         [0.146180, 0.515413, 0.556823],
         [0.144759, 0.519093, 0.556572],
         [0.143343, 0.522773, 0.556295],
         [0.141935, 0.526453, 0.555991],
         [0.140536, 0.530132, 0.555659],
         [0.139147, 0.533812, 0.555298],
         [0.137770, 0.537492, 0.554906],
         [0.136408, 0.541173, 0.554483],
         [0.135066, 0.544853, 0.554029],
         [0.133743, 0.548535, 0.553541],
         [0.132444, 0.552216, 0.553018],
         [0.131172, 0.555899, 0.552459],
         [0.129933, 0.559582, 0.551864],
         [0.128729, 0.563265, 0.551229],
         [0.127568, 0.566949, 0.550556],
         [0.126453, 0.570633, 0.549841],
         [0.125394, 0.574318, 0.549086],
         [0.124395, 0.578002, 0.548287],
         [0.123463, 0.581687, 0.547445],
         [0.122606, 0.585371, 0.546557],
         [0.121831, 0.589055, 0.545623],
         [0.121148, 0.592739, 0.544641],
         [0.120565, 0.596422, 0.543611],
         [0.120092, 0.600104, 0.542530],
         [0.119738, 0.603785, 0.541400],
         [0.119512, 0.607464, 0.540218],
         [0.119423, 0.611141, 0.538982],
         [0.119483, 0.614817, 0.537692],
         [0.119699, 0.618490, 0.536347],
         [0.120081, 0.622161, 0.534946],
         [0.120638, 0.625828, 0.533488],
         [0.121380, 0.629492, 0.531973],
         [0.122312, 0.633153, 0.530398],
         [0.123444, 0.636809, 0.528763],
         [0.124780, 0.640461, 0.527068],
         [0.126326, 0.644107, 0.525311],
         [0.128087, 0.647749, 0.523491],
         [0.130067, 0.651384, 0.521608],
         [0.132268, 0.655014, 0.519661],
         [0.134692, 0.658636, 0.517649],
         [0.137339, 0.662252, 0.515571],
         [0.140210, 0.665859, 0.513427],
         [0.143303, 0.669459, 0.511215],
         [0.146616, 0.673050, 0.508936],
         [0.150148, 0.676631, 0.506589],
         [0.153894, 0.680203, 0.504172],
         [0.157851, 0.683765, 0.501686],
         [0.162016, 0.687316, 0.499129],
         [0.166383, 0.690856, 0.496502],
         [0.170948, 0.694384, 0.493803],
         [0.175707, 0.697900, 0.491033],
         [0.180653, 0.701402, 0.488189],
         [0.185783, 0.704891, 0.485273],
         [0.191090, 0.708366, 0.482284],
         [0.196571, 0.711827, 0.479221],
         [0.202219, 0.715272, 0.476084],
         [0.208030, 0.718701, 0.472873],
         [0.214000, 0.722114, 0.469588],
         [0.220124, 0.725509, 0.466226],
         [0.226397, 0.728888, 0.462789],
         [0.232815, 0.732247, 0.459277],
         [0.239374, 0.735588, 0.455688],
         [0.246070, 0.738910, 0.452024],
         [0.252899, 0.742211, 0.448284],
         [0.259857, 0.745492, 0.444467],
         [0.266941, 0.748751, 0.440573],
         [0.274149, 0.751988, 0.436601],
         [0.281477, 0.755203, 0.432552],
         [0.288921, 0.758394, 0.428426],
         [0.296479, 0.761561, 0.424223],
         [0.304148, 0.764704, 0.419943],
         [0.311925, 0.767822, 0.415586],
         [0.319809, 0.770914, 0.411152],
         [0.327796, 0.773980, 0.406640],
         [0.335885, 0.777018, 0.402049],
         [0.344074, 0.780029, 0.397381],
         [0.352360, 0.783011, 0.392636],
         [0.360741, 0.785964, 0.387814],
         [0.369214, 0.788888, 0.382914],
         [0.377779, 0.791781, 0.377939],
         [0.386433, 0.794644, 0.372886],
         [0.395174, 0.797475, 0.367757],
         [0.404001, 0.800275, 0.362552],
         [0.412913, 0.803041, 0.357269],
         [0.421908, 0.805774, 0.351910],
         [0.430983, 0.808473, 0.346476],
         [0.440137, 0.811138, 0.340967],
         [0.449368, 0.813768, 0.335384],
         [0.458674, 0.816363, 0.329727],
         [0.468053, 0.818921, 0.323998],
         [0.477504, 0.821444, 0.318195],
         [0.487026, 0.823929, 0.312321],
         [0.496615, 0.826376, 0.306377],
         [0.506271, 0.828786, 0.300362],
         [0.515992, 0.831158, 0.294279],
         [0.525776, 0.833491, 0.288127],
         [0.535621, 0.835785, 0.281908],
         [0.545524, 0.838039, 0.275626],
         [0.555484, 0.840254, 0.269281],
         [0.565498, 0.842430, 0.262877],
         [0.575563, 0.844566, 0.256415],
         [0.585678, 0.846661, 0.249897],
         [0.595839, 0.848717, 0.243329],
         [0.606045, 0.850733, 0.236712],
         [0.616293, 0.852709, 0.230052],
         [0.626579, 0.854645, 0.223353],
         [0.636902, 0.856542, 0.216620],
         [0.647257, 0.858400, 0.209861],
         [0.657642, 0.860219, 0.203082],
         [0.668054, 0.861999, 0.196293],
         [0.678489, 0.863742, 0.189503],
         [0.688944, 0.865448, 0.182725],
         [0.699415, 0.867117, 0.175971],
         [0.709898, 0.868751, 0.169257],
         [0.720391, 0.870350, 0.162603],
         [0.730889, 0.871916, 0.156029],
         [0.741388, 0.873449, 0.149561],
         [0.751884, 0.874951, 0.143228],
         [0.762373, 0.876424, 0.137064],
         [0.772852, 0.877868, 0.131109],
         [0.783315, 0.879285, 0.125405],
         [0.793760, 0.880678, 0.120005],
         [0.804182, 0.882046, 0.114965],
         [0.814576, 0.883393, 0.110347],
         [0.824940, 0.884720, 0.106217],
         [0.835270, 0.886029, 0.102646],
         [0.845561, 0.887322, 0.099702],
         [0.855810, 0.888601, 0.097452],
         [0.866013, 0.889868, 0.095953],
         [0.876168, 0.891125, 0.095250],
         [0.886271, 0.892374, 0.095374],
         [0.896320, 0.893616, 0.096335],
         [0.906311, 0.894855, 0.098125],
         [0.916242, 0.896091, 0.100717],
         [0.926106, 0.897330, 0.104071],
         [0.935904, 0.898570, 0.108131],
         [0.945636, 0.899815, 0.112838],
         [0.955300, 0.901065, 0.118128],
         [0.964894, 0.902323, 0.123941],
         [0.974417, 0.903590, 0.130215],
         [0.983868, 0.904867, 0.136897],
         [0.993248, 0.906157, 0.143936]]
        
        viridis_map = LinearSegmentedColormap.from_list('viridis', cm_data)
        # For use of "viscm view"
        scheme = viridis_map
        
    if schemeName == 'colourBlind':
        scheme = [[(0, 107, 164), (163, 200, 236), (163, 200, 236)], 
                  [(255, 128, 14),(255, 188, 121), (255, 188, 121)],
                  [(89, 89, 89), (171, 171, 171), (171, 171, 171)],
                  [(137, 137, 137), (207, 207, 207), (207, 207, 207)],
                  [(200, 82, 0), (95, 158, 209), (95, 158, 209)]]
                
        for ii in range(len(scheme)):
            for jj in range(0,3):
                r, g, b = scheme[ii][jj]
                scheme[ii][jj] = (r / 255., g / 255., b / 255.)
        
    return scheme



def plotMeanData(meanDelayData, labelOffsets, plotName, stdDev=True):
    
    # Set matplotlib default font
    font = {'family' : 'Times New Roman',
            'weight' : 'normal',
            'size'   : 8}
    
    matplotlib.rc('font', **font)
    
    maxSimLength = 0
    maxYvalue = 0
    
    labels = []
    
    for simRun in meanDelayData:
        for vType in meanDelayData[simRun]:
            labels.append(simRun + "-" + vType)
            possMaxYvalue = int(math.ceil(meanDelayData[simRun][vType].max()*10))
            if possMaxYvalue > maxYvalue : maxYvalue = possMaxYvalue

    colour_scheme = retrieveColourScheme('meanData')
      
    # You typically want your plot to be ~1.33x wider than tall. This plot is a rare    
    # exception because of the number of lines being plotted on it.    
    # Common sizes: (10, 7.5) and (12, 9)    
    plt.figure(figsize=(4, 3))
    
    # Remove the plot frame lines. They are unnecessary chartjunk.    
    ax = plt.subplot(111)    
    ax.spines["top"].set_visible(False)    
    ax.spines["bottom"].set_visible(False)    
    ax.spines["right"].set_visible(False)    
    ax.spines["left"].set_visible(False)
    
    # Ensure that the axis ticks only show up on the bottom and left of the plot.    
    # Ticks on the right and top of the plot are generally unnecessary chartjunk.    
    ax.get_xaxis().tick_bottom()    
    ax.get_yaxis().tick_left()    
    
    if stdDev:
        jj_range = 3
    else:
        jj_range = 1
    
    ii = -1
    for simRun in meanDelayData:
        for vType in meanDelayData[simRun]:
            ii += 1
            results = meanDelayData[simRun][vType] 
            
            for jj in range(0,jj_range):
        # Plot each line separately with its own color, using the Tableau 20    
        # color set in order.
                time_values = range(0, results.shape[1])
                simLength = time_values[-1]
                if simLength > maxSimLength : maxSimLength = simLength
                
                if jj > 0:
                    plt.plot(time_values,    
                             results[jj][:],
                             lw=2.5, color=colour_scheme[ii][jj], hold=True)
                    
                else:
                    plt.plot(time_values,    
                             results[jj][:],
                             lw=2.5, color=colour_scheme[ii][jj], hold=True)
            
            # Add a text label to the right end of every line. Most of the code below    
            # is adding specific offsets y position because some labels overlapped.    
                y_pos = results[jj][simLength]
                     
            # Again, make sure that all labels are large enough to be easily read    
            # by the viewer.


    plotNumber = 0
    for simRun in meanDelayData:
        for vType in meanDelayData[simRun]:
            plt.text(maxSimLength + 10, maxYvalue - ((plotNumber+1)*0.1), simRun, color=colour_scheme[plotNumber][0])
                
             
    
    # Limit the range of the plot to only where the data is.    
    # Avoid unnecessary whitespace.    
    plt.ylim(0, maxYvalue/10)    
    plt.xlim(0, maxSimLength) 
    
    # Make sure your axis ticks are large enough to be easily read.    
    # You don't want your viewers squinting to read your plot.    
    plt.yticks([x*0.1 for x in range(0,maxYvalue)], [str(x*0.1) for x in range(0, maxYvalue)])
    
    if maxSimLength < 3600:
        xTickLocs = [x for x in range(0, maxSimLength, 900)]
        xTickLabels = [x/60 for x in range(0, maxSimLength, 900)]
        plt.xlabel('Minutes')
    else:
        xTickLocs = [x for x in range(0, maxSimLength, 3600)]
        xTickLabels = [x/3600 for x in range(0, maxSimLength, 3600)]
        plt.xlabel('Hours')
     
    plt.xticks(xTickLocs, xTickLabels)
    
    # Provide tick lines across the plot to help your viewers trace along    
    # the axis ticks. Make sure that the lines are light and small so they    
    # don't obscure the primary data lines.    
    for y in [x*0.1 for x in range(0, 11)]:   
        plt.plot(range(0, maxSimLength), [y] * len(range(0, maxSimLength)), "--", lw=0.5, color="black", alpha=0.3)    
      
    # Remove the tick marks; they are unnecessary with the tick lines we just plotted.    
    plt.tick_params(axis="both", which="both", bottom="off", top="off",    
                    labelbottom="on", left="off", right="off", labelleft="on")
    
    # matplotlib's title() call centers the title on the plot, but not the graph,    
    # so I used the text() call to customize where the title goes.    
      
    # Make the title big enough so it spans the entire plot, but don't make it    
    # so big that it requires two lines to show.    
      
    # Note that if the title is descriptive enough, it is unnecessary to include    
    # axis labels; they are self-evident, in this plot's case.    
    #plt.text(1995, 93, "Percentage of Bachelor's degrees conferred to women in the U.S.A."    
    #       ", by major (1970-2012)", fontsize=17, ha="center")    
      
    # Always include your data source(s) and copyright notice! And for your    
    # data sources, tell your viewers exactly where the data came from,    
    # preferably with a direct link to the data. Just telling your viewers    
    # that you used data from the "U.S. Census Bureau" is completely useless:    
    # the U.S. Census Bureau provides all kinds of data, so how are your    
    # viewers supposed to know which data set you used?    
    #plt.text(1966, -8, "Data source: nces.ed.gov/programs/digest/2013menu_tables.asp"    
    #       "\nAuthor: Randy Olson (randalolson.com / @randal_olson)"    
    #       "\nNote: Some majors are missing because the historical data "    
    #       "is not available for them", fontsize=10)    
      
    # Finally, save the figure as a PNG.    
    # You can also save it as a PDF, JPEG, etc.    
    # Just change the file extension in this call.    
    # bbox_inches="tight" removes all the extra whitespace on the edges of your plot.    
    #plt.savefig("../../_004_Grid-10x10_/test.png", bbox_inches="tight")  
    plt.savefig(("plots/%s.pdf" % (plotName)), bbox_inches="tight")
    plt.savefig(("/Users/tb7554/University Cloud/Image Repository/SUMO Results/%s.pdf" % (plotName)), bbox_inches="tight")
 
    plt.show()
    
def convertFile2movingAverageDelay(routeFile_filepath, tripFile_filepath, timeWindow=900):
    
    veh_delayOverTravelTime = delayAsFractionOfTravelTime(routeFile_filepath, tripFile_filepath)
    veh_departTimes = extractDepartTimesFromTripFile(tripFile_filepath)
    veh_vTypes = extractVehTypeFromTripFile(tripFile_filepath)
    veh_delayOverTravelTime_split = splitVehDataByVehType(veh_delayOverTravelTime, veh_vTypes)
    
    veh_delayOverTravelTime_split_timeSeries = {}

    vTypes =  veh_delayOverTravelTime_split['vTypes']
    
    for vType in vTypes:
        dataTime_dict = convertCarDataAndTimeData2TimeDict(veh_delayOverTravelTime_split[vType], veh_departTimes)
        veh_delayOverTravelTime_split_timeSeries.update({vType:convertCarDataOverTime2MovingAverage(dataTime_dict)})
    
    return veh_delayOverTravelTime_split_timeSeries

def extractSummary(summaryFile_filepath):
    
    parse_simulationSummary = ET.parse(summaryFile_filepath) # Use the XML parser to read the net XML file
    summaryData = parse_simulationSummary.getroot()
    
    time = []
    carsInserted = []
    carsRunning = []
    carsWaiting = []    
    
    for timeStep in summaryData:
        time.append(float(timeStep.attrib["time"]))
        carsInserted.append(int(timeStep.attrib["inserted"]))
        carsRunning.append(int(timeStep.attrib["running"]))
        carsWaiting.append(int(timeStep.attrib["waiting"]))

    dictFormat = {"timeSteps" : time, "carsInserted" : carsInserted, "carsRunning" : carsRunning, "carsWaiting" : carsWaiting}
    
    return dictFormat

def plotCarsInNetwork(summaryData, labelOffsets, plotName):
    
    # Set matplotlib default font
    font = {'family' : 'Times New Roman',
            'weight' : 'normal',
            'size'   : 8}
    
    matplotlib.rc('font', **font)
    
    maxSimLength = 0
    maxYvalue = 0
    
    labels = []
    
    for simRun in summaryData:
        labels.append(simRun)
        possMaxYvalue = max(summaryData[simRun]["carsRunning"])
        if possMaxYvalue > maxYvalue : maxYvalue = possMaxYvalue

    colour_scheme = retrieveColourScheme('meanData')
    
    # Scale the RGB values to the [0, 1] range, which is the format matplotlib accepts.    
    for ii in range(len(colour_scheme)):
        for jj in range(0,3):
            r, g, b = colour_scheme[ii][jj]
            colour_scheme[ii][jj] = (r / 255., g / 255., b / 255.)    
      
    # You typically want your plot to be ~1.33x wider than tall. This plot is a rare    
    # exception because of the number of lines being plotted on it.    
    # Common sizes: (10, 7.5) and (12, 9)    
    plt.figure(figsize=(4, 3))
    
    # Remove the plot frame lines. They are unnecessary chartjunk.    
    ax = plt.subplot(111)    
    ax.spines["top"].set_visible(False)    
    ax.spines["bottom"].set_visible(False)    
    ax.spines["right"].set_visible(False)    
    ax.spines["left"].set_visible(False)
    
    # Ensure that the axis ticks only show up on the bottom and left of the plot.    
    # Ticks on the right and top of the plot are generally unnecessary chartjunk.    
    ax.get_xaxis().tick_bottom()    
    ax.get_yaxis().tick_left()    
    
    plotNumber = 0
    for simRun in summaryData:

        results = summaryData[simRun]["carsRunning"] 
        time_values = summaryData[simRun]["timeSteps"]
        simLength = time_values[-1]
        if simLength > maxSimLength : maxSimLength = simLength
                
        plt.plot(time_values,    
                 results,
                 lw=2.5, color=colour_scheme[plotNumber][0], hold=True)
             
    # Add a text label to the right end of every line. Most of the code below    
    # is adding specific offsets y position because some labels overlapped.    
        y_pos = results[-1]           
        
        plotNumber += 1
    
    plotNumber = 0 
    for simRun in summaryData:
        plt.text(maxSimLength + 10, maxYvalue - ((plotNumber+1)*200), simRun, color=colour_scheme[plotNumber][0])
        plotNumber += 1
        
    # Limit the range of the plot to only where the data is.    
    # Avoid unnecessary whitespace.
    plt.ylim(0, maxYvalue/10)    
    plt.xlim(0, maxSimLength) 
    
    # Make sure your axis ticks are large enough to be easily read.    
    # You don't want your viewers squinting to read your plot.    
    plt.yticks([x for x in range(0,maxYvalue,500)], [str(x) for x in range(0, maxYvalue,500)], fontsize=8)
    
    if maxSimLength < 3600:
        xTickLocs = [x for x in range(0, int(maxSimLength), 900)]
        xTickLabels = [x/60 for x in range(0, int(maxSimLength), 900)]
        plt.xlabel('Minutes', fontsize=10)
    else:
        xTickLocs = [x for x in range(0, int(maxSimLength), 3600)]
        xTickLabels = [x/3600 for x in range(0, int(maxSimLength), 3600)]
        plt.xlabel('Hours', fontsize=10)
     
    plt.xticks(xTickLocs, xTickLabels, fontsize=8)
    
    # Provide tick lines across the plot to help your viewers trace along    
    # the axis ticks. Make sure that the lines are light and small so they    
    # don't obscure the primary data lines.    
    for y in [x for x in range(0, maxYvalue,500)]:   
        plt.plot(range(0, int(maxSimLength)), [y] * len(range(0, int(maxSimLength))), "--", lw=0.5, color="black", alpha=0.3)    
    
    plt.ylabel("Cars in the network", fontsize=10)
    
    # Remove the tick marks; they are unnecessary with the tick lines we just plotted.    
    plt.tick_params(axis="both", which="both", bottom="off", top="off",    
                    labelbottom="on", left="off", right="off", labelleft="on")
    
    # matplotlib's title() call centers the title on the plot, but not the graph,    
    # so I used the text() call to customize where the title goes.    
      
    # Make the title big enough so it spans the entire plot, but don't make it    
    # so big that it requires two lines to show.    
      
    # Note that if the title is descriptive enough, it is unnecessary to include    
    # axis labels; they are self-evident, in this plot's case.    
    #plt.text(1995, 93, "Percentage of Bachelor's degrees conferred to women in the U.S.A."    
    #       ", by major (1970-2012)", fontsize=17, ha="center")    
      
    # Always include your data source(s) and copyright notice! And for your    
    # data sources, tell your viewers exactly where the data came from,    
    # preferably with a direct link to the data. Just telling your viewers    
    # that you used data from the "U.S. Census Bureau" is completely useless:    
    # the U.S. Census Bureau provides all kinds of data, so how are your    
    # viewers supposed to know which data set you used?    
    #plt.text(1966, -8, "Data source: nces.ed.gov/programs/digest/2013menu_tables.asp"    
    #       "\nAuthor: Randy Olson (randalolson.com / @randal_olson)"    
    #       "\nNote: Some majors are missing because the historical data "    
    #       "is not available for them", fontsize=10)    
      
    # Finally, save the figure as a PNG.    
    # You can also save it as a PDF, JPEG, etc.    
    # Just change the file extension in this call.    
    # bbox_inches="tight" removes all the extra whitespace on the edges of your plot.    
    plt.savefig(("plots/%s.pdf" % (plotName)), bbox_inches="tight")
    plt.savefig(("/Users/tb7554/University Cloud/Image Repository/SUMO Results/%s.pdf" % (plotName)), bbox_inches="tight")
    
    plt.show()
    
def configFigure(figHandle, height, width):
    
    # Set matplotlib default font
    font = {'family' : 'Times New Roman',
            'weight' : 'normal',
            'size'   : 8}
    
    matplotlib.rc('font', **font)
          
    # You typically want your plot to be ~1.33x wider than tall. This plot is a rare    
    # exception because of the number of lines being plotted on it.    
    # Common sizes: (10, 7.5) and (12, 9)
    plt.figure(figsize=(width*4, height*3))
    
    # Remove the plot frame lines. They are unnecessary chartjunk.    
    for sub in range(1,height*width+1):
        index = ("%d%d%d" % (height, width, sub))
        ax = plt.subplot(int(index))
        ax.spines["top"].set_visible(False)    
        ax.spines["bottom"].set_visible(False)    
        ax.spines["right"].set_visible(False)    
        ax.spines["left"].set_visible(False)

     
def plotCarsInNetworkOverTime(simulationsList, plotName):
    
    #numSims = len(simulationsList)

    # Set matplotlib default font
    font = {'family' : 'Times New Roman',
            'weight' : 'normal',
            'size'   : 8}
    
    matplotlib.rc('font', **font)
    
    colour_scheme = retrieveColourScheme('meanData')
       
    # You typically want your plot to be ~1.33x wider than tall. This plot is a rare    
    # exception because of the number of lines being plotted on it.    
    # Common sizes: (10, 7.5) and (12, 9)    
    plt.figure("carsInNetwork", figsize=(4, 3))
    # Remove the plot frame lines. They are unnecessary chartjunk.    
    ax = plt.subplot(111) 
    ax.spines["top"].set_visible(False)
    ax.spines["bottom"].set_visible(False)    
    ax.spines["right"].set_visible(False)    
    ax.spines["left"].set_visible(False)
    
    # Ensure that the axis ticks only show up on the bottom and left of the plot.    
    # Ticks on the right and top of the plot are generally unnecessary chartjunk.    
    ax.get_xaxis().tick_bottom()    
    ax.get_yaxis().tick_left()    
    
    plt.figure("carsInNetworkStdDev", figsize=(4, 3))
    # Remove the plot frame lines. They are unnecessary chartjunk.    
    ax = plt.subplot(111) 
    ax.spines["top"].set_visible(False)
    ax.spines["bottom"].set_visible(False)    
    ax.spines["right"].set_visible(False)    
    ax.spines["left"].set_visible(False)
    
    # Ensure that the axis ticks only show up on the bottom and left of the plot.    
    # Ticks on the right and top of the plot are generally unnecessary chartjunk.    
    ax.get_xaxis().tick_bottom()    
    ax.get_yaxis().tick_left()    
    
    maxTime = 0
    maxCars = 0
    maxDev = 0
    titles = []
    subplot = 0
    
    for batchID in simulationsList:
        
        dataContainer_filepath = ("%s/evaluatedResultsFiles/%s" % (os.environ['DIRECTORY_PATH'], batchID))
        dataContainer = pickleFunc.load_obj(dataContainer_filepath)
        
        routingMethod = dataContainer.keys()[0]
        
        if routingMethod == "CBR":
            penRate = dataContainer[routingMethod].keys()[0]
            alpha = dataContainer[routingMethod][penRate].keys()[0]
            carsOverTimeStats = dataContainer[routingMethod][penRate][alpha]['carsOverTime']
            title = ("Coverage Based Routing - alpha = %.2f, penetration rate = %d%%" % (alpha, int(penRate*100)))
        elif routingMethod == "TTRR":
            penRate = dataContainer[routingMethod].keys()[0]
            RUI = dataContainer[routingMethod][penRate].keys()[0]
            carsOverTimeStats = dataContainer[routingMethod][penRate][RUI]['carsOverTime']
            title = ("Travel Time Routing - update interval = %d, penetration rate = %d%%" % (int(RUI), int(penRate*100)))
        elif routingMethod == "DUA":
            carsOverTimeStats = dataContainer[routingMethod]['carsOverTime']
            title = ("Dynamic User Assignment")
        
        numCars = carsOverTimeStats[0]
        stdDev = carsOverTimeStats[1]
        
        time = len(numCars)
        if time > maxTime : maxTime = time
        carsPeak = int(max(numCars))
        if carsPeak > maxCars : maxCars = carsPeak
        devPeak = int(max(stdDev))
        if devPeak > maxDev : maxDev = devPeak
         
        time_axis = range(0, time)
        
        plt.figure("carsInNetwork")
        plt.plot(time_axis,    
                 numCars,
                 lw=2.5, color=colour_scheme[subplot][0], hold=True)

        plt.figure("carsInNetworkStdDev")
        plt.plot(time_axis,    
                 stdDev,
                 lw=2.5, color=colour_scheme[subplot][0], hold=True)
        
        titles.append(title)
        
        subplot += 1
        
    plt.figure("carsInNetwork")
    # Limit the range of the plot to only where the data is.    
    # Avoid unnecessary whitespace.
    plt.ylim(0, maxCars)    
    plt.xlim(0, maxTime) 
    
    # Make sure your axis ticks are large enough to be easily read.    
    # You don't want your viewers squinting to read your plot.    
    plt.yticks([x for x in range(0,maxCars,int(math.ceil(maxCars/(10*100))*100))], [str(x) for x in range(0, maxCars,int(math.ceil(maxCars/(10*100))*100))], fontsize=8)
    
    if maxTime < 3600:
        xTickLocs = [x for x in range(0, int(maxTime), 900)]
        xTickLabels = [x/60 for x in range(0, int(maxTime), 900)]
        plt.xlabel('Minutes', fontsize=10)
    else:
        xTickLocs = [x for x in range(0, int(maxTime), 3600)]
        xTickLabels = [x/3600 for x in range(0, int(maxTime), 3600)]
        plt.xlabel('Hours', fontsize=10)
     
    plt.xticks(xTickLocs, xTickLabels, fontsize=8)
    
    # Provide tick lines across the plot to help your viewers trace along    
    # the axis ticks. Make sure that the lines are light and small so they    
    # don't obscure the primary data lines.    
    for y in [x for x in range(0, maxCars,int(math.ceil(maxCars/(10*100))*100))]:   
        plt.plot(range(0, int(maxTime)), [y] * len(range(0, int(maxTime))), "--", lw=0.5, color="black", alpha=0.3)    
    
    plt.ylabel("Cars in the network", fontsize=10)
    
    # Remove the tick marks; they are unnecessary with the tick lines we just plotted.    
    plt.tick_params(axis="both", which="both", bottom="off", top="off",    
                    labelbottom="on", left="off", right="off", labelleft="on")
    
    for ii in range(0, len(titles)):
        plt.text(maxTime, maxCars-((ii+1)*0.1*maxCars),titles[ii], color=colour_scheme[ii][0], horizontalalignment='left', verticalalignment='center')
      
    plt.savefig(("plots/%s_carsOverTime.pdf" % (plotName)), bbox_inches="tight")
    
    plt.figure("carsInNetworkStdDev")
    # Limit the range of the plot to only where the data is.    
    # Avoid unnecessary whitespace.
    plt.ylim(0, maxDev)    
    plt.xlim(0, maxTime) 
    
    # Make sure your axis ticks are large enough to be easily read.    
    # You don't want your viewers squinting to read your plot. 
    if maxDev == 0 : maxDev = 1  
    plt.yticks([x for x in range(0,maxDev,int(math.ceil(maxDev/(10*100))*100))], [str(x) for x in range(0, maxDev,int(math.ceil(maxDev/(10*100))*100))], fontsize=8)
    
    if maxTime < 3600:
        xTickLocs = [x for x in range(0, int(maxTime), 900)]
        xTickLabels = [x/60 for x in range(0, int(maxTime), 900)]
        plt.xlabel('Minutes', fontsize=10)
    else:
        xTickLocs = [x for x in range(0, int(maxTime), 3600)]
        xTickLabels = [x/3600 for x in range(0, int(maxTime), 3600)]
        plt.xlabel('Hours', fontsize=10)
     
    plt.xticks(xTickLocs, xTickLabels, fontsize=8)
    
    # Provide tick lines across the plot to help your viewers trace along    
    # the axis ticks. Make sure that the lines are light and small so they    
    # don't obscure the primary data lines.    
    for y in [x for x in range(0, maxDev,int(math.ceil(maxDev/(10*100))*100))]:   
        plt.plot(range(0, int(maxTime)), [y] * len(range(0, int(maxTime))), "--", lw=0.5, color="black", alpha=0.3)    
    
    plt.ylabel("Standard Deviation Between Simulation Runs", fontsize=10)
    
    # Remove the tick marks; they are unnecessary with the tick lines we just plotted.    
    plt.tick_params(axis="both", which="both", bottom="off", top="off",    
                     labelbottom="on", left="off", right="off", labelleft="on")

    for ii in range(0, len(titles)):
        plt.text(maxTime, maxDev-((ii+1)*0.1*maxDev),titles[ii], color=colour_scheme[ii][0], horizontalalignment='left', verticalalignment='center')

    plt.savefig(("plots/%s_devBetweenRuns.pdf" % (plotName)), bbox_inches="tight")
    
    plt.show()
        
def plotPenetrationRateEffect(gridID, routingMethod, CGR, penRates, alpha=None, RUI=None):
    
    travelTimeMean = []
    travelTimeStdDev = []
    travelTimeMean_runsStdDev = []
    travelTimeStdDev_runsStdDev = []
    
    delayMean = []
    delayStdDev = []
    delayMean_runsStdDev = []
    delayStdDev_runsStdDev = []
    
    for rate in penRates:
        if routingMethod == "CBR":
            dataContainer_filepath = ("%s/evaluatedResultsFiles/%s-CGR-%.2f-CBR-PEN-%.2f-ALPHA-%.2f" % (os.environ['DIRECTORY_PATH'], gridID, CGR, rate, alpha))
            dataContainer = pickleFunc.load_obj(dataContainer_filepath)
            pen = dataContainer[routingMethod].keys()[0]
            alpha = dataContainer[routingMethod][pen].keys()[0]
            data = dataContainer[routingMethod][pen][alpha]
        elif routingMethod == "TTRR":
            dataContainer_filepath = ("%s/evaluatedResultsFiles/%s-CGR-%.2f-TTRR-PEN-%.2f-RUI-%d" % (os.environ['DIRECTORY_PATH'], gridID, CGR, rate, RUI))
            dataContainer = pickleFunc.load_obj(dataContainer_filepath)
            pen = dataContainer[routingMethod].keys()[0]
            RUI = dataContainer[routingMethod][pen].keys()[0]
            data = dataContainer[routingMethod][pen][RUI]
            
        travelTimeMean.append(data["travelTime"][0])
        travelTimeStdDev.append(data["travelTime"][1])
        travelTimeMean_runsStdDev.append(data["travelTime"][2])
        travelTimeStdDev_runsStdDev.append(data["travelTime"][3])
        
        delayMean.append(data["delay"][0])
        delayStdDev.append(data["delay"][1])
        delayMean_runsStdDev.append(data["delay"][2])
        delayStdDev_runsStdDev.append(data["delay"][3])
        
    # Set matplotlib default font
    font = {'family' : 'Times New Roman',
            'weight' : 'normal',
            'size'   : 8}
    
    matplotlib.rc('font', **font)
    
    colour_scheme = retrieveColourScheme('meanData')
    if routingMethod == "CBR":
        colourIndex = 0
    elif routingMethod == "TTRR":
        colourIndex = 1
    else:
        colourIndex = 2
    
    plt.figure("stats", figsize=(8, 9))
    for plot in range(311,314):
        # Remove the plot frame lines. They are unnecessary chartjunk.    
        ax = plt.subplot(plot) 
        ax.spines["top"].set_visible(False)
        ax.spines["bottom"].set_visible(False)    
        ax.spines["right"].set_visible(False)    
        ax.spines["left"].set_visible(False)
        # Ensure that the axis ticks only show up on the bottom and left of the plot.    
        # Ticks on the right and top of the plot are generally unnecessary chartjunk.    
        ax.get_xaxis().tick_bottom()    
        ax.get_yaxis().tick_left()
    
    plt.subplot(311)
    plt.plot(penRates, travelTimeMean, lw=2.5, color=colour_scheme[colourIndex][0], hold=True)
    
    higherBound = []
    lowerBound = []

    for ii in range(0, len(travelTimeMean)):
        higherBound.append(travelTimeMean[ii] + travelTimeStdDev[ii])
        if travelTimeMean[ii] - travelTimeStdDev[ii] >= 0:
            lowerBound.append(travelTimeMean[ii] - travelTimeStdDev[ii])
        else:
            lowerBound.append(0)
    
    plt.plot(penRates, higherBound, lw=2.5, color=colour_scheme[colourIndex][1], hold=True)
    plt.plot(penRates, lowerBound, lw=2.5, color=colour_scheme[colourIndex][1], hold=True)
    
    # Limit the range of the plot to only where the data is.    
    # Avoid unnecessary whitespace.
    plt.ylim(0, max(higherBound))    
    plt.xlim(0, 1) 
    # Make sure your axis ticks are large enough to be easily read.    
    # You don't want your viewers squinting to read your plot. 
    xTickLocs = penRates
    xTickLabels = [str(x) for x in penRates]
    plt.xlabel('Penetration Rate', fontsize=10)

    if max(higherBound) > 3600:
        plt.yticks([x for x in range(0,int(max(higherBound)),1800)], [str(x/3600) for x in range(0, int(max(higherBound)),1800)], fontsize=8)
        plt.ylabel("Mean  Travel Time (hours)", fontsize=10)
    elif max(higherBound) > 1800:
        plt.yticks([x for x in range(0,int(max(higherBound)),300)], [str(x/60) for x in range(0, int(max(higherBound)),300)], fontsize=8)
        plt.ylabel("Mean Travel Time (mins)", fontsize=10)
    else:
        plt.yticks([x for x in range(0,int(max(higherBound)),120)], [str(x/60) for x in range(0, int(max(higherBound)),120)], fontsize=8)
        plt.ylabel("Mean Travel Time (mins)", fontsize=10)
    
    plt.xticks(xTickLocs, xTickLabels, fontsize=8)
    # Provide tick lines across the plot to help your viewers trace along    
    # the axis ticks. Make sure that the lines are light and small so they    
    # don't obscure the primary data lines.
    for y in [x for x in range(0, int(max(higherBound)),int(math.ceil(max(higherBound)/(10*100))*100))]:   
        plt.plot([x*0.1 for x in range(0,11)], [y] * (len(penRates)+1), "--", lw=0.5, color="black", alpha=0.3)
    # Remove the tick marks; they are unnecessary with the tick lines we just plotted.    
    plt.tick_params(axis="both", which="both", bottom="off", top="off",    
                    labelbottom="on", left="off", right="off", labelleft="on")
    
    plt.subplot(312)
    plt.plot(penRates, delayMean, lw=2.5, color=colour_scheme[colourIndex][0], hold=True)
    
    higherBound = []
    lowerBound = []

    for ii in range(0, len(travelTimeMean)):
        higherBound.append(delayMean[ii] + delayStdDev[ii])
        if delayMean[ii] - delayStdDev[ii] >= 0:
            lowerBound.append(delayMean[ii] - delayStdDev[ii])
        else:
            lowerBound.append(0)
    
    plt.plot(penRates, higherBound, lw=2.5, color=colour_scheme[colourIndex][1], hold=True)
    plt.plot(penRates, lowerBound, lw=2.5, color=colour_scheme[colourIndex][1], hold=True)
    
    # Limit the range of the plot to only where the data is.    
    # Avoid unnecessary whitespace.
    plt.ylim(0, max(higherBound))    
    plt.xlim(0, 1) 
    # Make sure your axis ticks are large enough to be easily read.    
    # You don't want your viewers squinting to read your plot. 
    xTickLocs = penRates
    xTickLabels = [str(x) for x in penRates]
    plt.xlabel('Penetration Rate', fontsize=10)
    
    if max(higherBound) > 3600:
        plt.yticks([x for x in range(0,int(max(higherBound)),1800)], [str(x/3600) for x in range(0, int(max(higherBound)),1800)], fontsize=8)
        plt.ylabel("Mean Delay (hours)", fontsize=10)
    elif max(higherBound) > 1800:
        plt.yticks([x for x in range(0,int(max(higherBound)),300)], [str(x/60) for x in range(0, int(max(higherBound)),300)], fontsize=8)
        plt.ylabel("Mean Delay (mins)", fontsize=10)
    else:
        plt.yticks([x for x in range(0,int(max(higherBound)),120)], [str(x/60) for x in range(0, int(max(higherBound)),120)], fontsize=8)
        plt.ylabel("Mean Delay (mins)", fontsize=10)

    plt.xticks(xTickLocs, xTickLabels, fontsize=8)
    # Provide tick lines across the plot to help your viewers trace along    
    # the axis ticks. Make sure that the lines are light and small so they    
    # don't obscure the primary data lines.    
    for y in [x for x in range(0, int(max(higherBound)),int(math.ceil(max(higherBound)/(10*100))*100))]:   
        plt.plot([x*0.1 for x in range(0,11)], [y] * (len(penRates)+1), "--", lw=0.5, color="black", alpha=0.3)    
        
    # Remove the tick marks; they are unnecessary with the tick lines we just plotted.    
    plt.tick_params(axis="both", which="both", bottom="off", top="off",    
                    labelbottom="on", left="off", right="off", labelleft="on")
    
    plt.subplot(313)
    plt.plot(penRates, delayOverTravelTimeMean, lw=2.5, color=colour_scheme[colourIndex][0], hold=True)
    
    higherBound = []
    lowerBound = []

    for ii in range(0, len(travelTimeMean)):
        higherBound.append(delayOverTravelTimeMean[ii] + delayOverTravelTimeStdDev[ii])
        if delayOverTravelTimeMean[ii] - delayOverTravelTimeStdDev[ii] >= 0:
            lowerBound.append(delayOverTravelTimeMean[ii] - delayOverTravelTimeStdDev[ii])
        else:
            lowerBound.append(0)
    
    plt.plot(penRates, higherBound, lw=2.5, color=colour_scheme[colourIndex][1], hold=True)
    plt.plot(penRates, lowerBound, lw=2.5, color=colour_scheme[colourIndex][1], hold=True)
    
    # Limit the range of the plot to only where the data is.    
    # Avoid unnecessary whitespace.
    plt.ylim(0, max(higherBound))    
    plt.xlim(0, 1) 
    # Make sure your axis ticks are large enough to be easily read.    
    # You don't want your viewers squinting to read your plot. 
    xTickLocs = penRates
    xTickLabels = [str(x) for x in penRates]
    plt.xlabel('Penetration Rate', fontsize=10)
    if max(higherBound) > 1:
        plt.yticks([x*0.1 for x in range(0,int(max(higherBound)*10)+1)], [str(x*0.1) for x in range(0, int(max(higherBound)*10))], fontsize=8)
        for y in [x*0.1 for x in range(0, (int(max(higherBound)*10)+1))]:   
            plt.plot([x*0.1 for x in range(0,11)], [y] * (len(penRates)+1), "--", lw=0.5, color="black", alpha=0.3)
    else:
        plt.yticks([x*0.1 for x in range(0,11)], [str(x*0.1) for x in range(0, 11)], fontsize=8)
        for y in [x*0.1 for x in range(0, 11)]:   
            plt.plot([x*0.1 for x in range(0,11)], [y] * (len(penRates)+1), "--", lw=0.5, color="black", alpha=0.3)  
        
    plt.xticks(xTickLocs, xTickLabels, fontsize=8)
    # Provide tick lines across the plot to help your viewers trace along    
    # the axis ticks. Make sure that the lines are light and small so they    
    # don't obscure the primary data lines.      
    plt.ylabel("Ratio of Delay to Total Travel Time", fontsize=10)
    # Remove the tick marks; they are unnecessary with the tick lines we just plotted.    
    plt.tick_params(axis="both", which="both", bottom="off", top="off",    
                    labelbottom="on", left="off", right="off", labelleft="on")
    
    plt.savefig(("plots/%s-CGR-%.2f-%s_stats.pdf" % (gridID, CGR, routingMethod)), bbox_inches="tight")
    
    plt.show()
    
def plotAlphaEffect(gridID, routingMethod, CGR, alphas, penRate=1):
    
    travelTimeMean = []
    travelTimeStdDev = []
    travelTimeMean_runsStdDev = []
    travelTimeStdDev_runsStdDev = []
    
    delayMean = []
    delayStdDev = []
    delayMean_runsStdDev = []
    delayStdDev_runsStdDev = []
    
    delayOverExpectedTravelTimeMean = []
    delayOverExpectedTravelTimeStdDev = []
    delayOverExpectedTravelTimeMean_runsStdDev = []
    delayOverExpectedTravelTimeStdDev_runsStdDev = []
    
    for alpha in alphas:
        dataContainer_filepath = ("%s/evaluatedResultsFiles/%s-CGR-%.2f-CBR-PEN-%.2f-ALPHA-%.2f" % (os.environ['DIRECTORY_PATH'], gridID, CGR, penRate, alpha))
        dataContainer = pickleFunc.load_obj(dataContainer_filepath)
        pen = dataContainer[routingMethod].keys()[0]
        alpha = dataContainer[routingMethod][pen].keys()[0]
        data = dataContainer[routingMethod][pen][alpha]
            
        travelTimeMean.append(data["travelTime"][0])
        travelTimeStdDev.append(data["travelTime"][1])
        travelTimeMean_runsStdDev.append(data["travelTime"][2])
        travelTimeStdDev_runsStdDev.append(data["travelTime"][3])
        
        delayMean.append(data["delay"][0])
        delayStdDev.append(data["delay"][1])
        delayMean_runsStdDev.append(data["delay"][2])
        delayStdDev_runsStdDev.append(data["delay"][3])
        
        delayOverExpectedTravelTimeMean.append(data["delayOverExpectedTravelTime"][0])
        delayOverExpectedTravelTimeStdDev.append(data["delayOverExpectedTravelTime"][1])
        delayOverExpectedTravelTimeMean_runsStdDev.append(data["delayOverExpectedTravelTime"][2])
        delayOverExpectedTravelTimeStdDev_runsStdDev.append(data["delayOverExpectedTravelTime"][3])
    
    # Set matplotlib default font
    font = {'family' : 'Times New Roman',
            'weight' : 'normal',
            'size'   : 8}
    
    matplotlib.rc('font', **font)
    
    colour_scheme = retrieveColourScheme('meanData')
    if routingMethod == "CBR":
        colourIndex = 0
    elif routingMethod == "TTRR":
        colourIndex = 1
    else:
        colourIndex = 2
    
    plt.figure("stats", figsize=(8, 9))
    for plot in range(311,314):
        # Remove the plot frame lines. They are unnecessary chartjunk.    
        ax = plt.subplot(plot) 
        ax.spines["top"].set_visible(False)
        ax.spines["bottom"].set_visible(False)    
        ax.spines["right"].set_visible(False)    
        ax.spines["left"].set_visible(False)
        # Ensure that the axis ticks only show up on the bottom and left of the plot.    
        # Ticks on the right and top of the plot are generally unnecessary chartjunk.    
        ax.get_xaxis().tick_bottom()    
        ax.get_yaxis().tick_left()
    
    plt.subplot(311)
    plt.plot(alphas, travelTimeMean, lw=2.5, color=colour_scheme[colourIndex][0], hold=True)
    
    higherBound = []
    lowerBound = []

    for ii in range(0, len(travelTimeMean)):
        higherBound.append(travelTimeMean[ii] + travelTimeStdDev[ii])
        if travelTimeMean[ii] - travelTimeStdDev[ii] >= 0:
            lowerBound.append(travelTimeMean[ii] - travelTimeStdDev[ii])
        else:
            lowerBound.append(0)
    
    plt.plot(alphas, higherBound, lw=2.5, color=colour_scheme[colourIndex][1], hold=True)
    plt.plot(alphas, lowerBound, lw=2.5, color=colour_scheme[colourIndex][1], hold=True)
    
    # Limit the range of the plot to only where the data is.    
    # Avoid unnecessary whitespace.
    plt.ylim(0, max(higherBound))    
    plt.xlim(0, 1) 
    # Make sure your axis ticks are large enough to be easily read.    
    # You don't want your viewers squinting to read your plot. 
    xTickLocs = alphas
    xTickLabels = [str(x) for x in alphas]
    plt.xlabel('Alpha', fontsize=10)

    if max(higherBound) > 3600:
        plt.yticks([x for x in range(0,int(max(higherBound)),3600)], [str(x/3600) for x in range(0, int(max(higherBound)),3600)], fontsize=8)
        plt.ylabel("Mean  Travel Time (hours)", fontsize=10)
    else:
        plt.yticks([x for x in range(0,int(max(higherBound)),60)], [str(x/60) for x in range(0, int(max(higherBound)),60)], fontsize=8)
        plt.ylabel("Mean Travel Time (mins)", fontsize=10)
    
    plt.xticks(xTickLocs, xTickLabels, fontsize=8)
    # Provide tick lines across the plot to help your viewers trace along    
    # the axis ticks. Make sure that the lines are light and small so they    
    # don't obscure the primary data lines.
    for y in [x for x in range(0, int(max(higherBound)),int(math.ceil(max(higherBound)/(10*100))*100))]:  
        plt.plot(alphas, [y] * (len(alphas)), "--", lw=0.5, color="black", alpha=0.3)
    # Remove the tick marks; they are unnecessary with the tick lines we just plotted.    
    plt.tick_params(axis="both", which="both", bottom="off", top="off",    
                    labelbottom="on", left="off", right="off", labelleft="on")
    
    plt.subplot(312)
    plt.plot(alphas, delayMean, lw=2.5, color=colour_scheme[colourIndex][0], hold=True)
    
    higherBound = []
    lowerBound = []

    for ii in range(0, len(travelTimeMean)):
        higherBound.append(delayMean[ii] + delayStdDev[ii])
        if delayMean[ii] - delayStdDev[ii] >= 0:
            lowerBound.append(delayMean[ii] - delayStdDev[ii])
        else:
            lowerBound.append(0)
    
    plt.plot(alphas, higherBound, lw=2.5, color=colour_scheme[colourIndex][1], hold=True)
    plt.plot(alphas, lowerBound, lw=2.5, color=colour_scheme[colourIndex][1], hold=True)
    
    # Limit the range of the plot to only where the data is.    
    # Avoid unnecessary whitespace.
    plt.ylim(0, max(higherBound))    
    plt.xlim(0, 1) 
    # Make sure your axis ticks are large enough to be easily read.    
    # You don't want your viewers squinting to read your plot. 
    xTickLocs = alphas
    xTickLabels = [str(x) for x in alphas]
    plt.xlabel('Alpha', fontsize=10)
    
    if max(higherBound) > 3600:
        plt.yticks([x for x in range(0,int(max(higherBound)),3600)], [str(x/3600) for x in range(0, int(max(higherBound)),3600)], fontsize=8)
        plt.ylabel("Mean Delay (hours)", fontsize=10)
    else:
        plt.yticks([x for x in range(0,int(max(higherBound)),60)], [str(x/60) for x in range(0, int(max(higherBound)),60)], fontsize=8)
        plt.ylabel("Mean Delay (mins)", fontsize=10)

    plt.xticks(xTickLocs, xTickLabels, fontsize=8)
    # Provide tick lines across the plot to help your viewers trace along    
    # the axis ticks. Make sure that the lines are light and small so they    
    # don't obscure the primary data lines.    
    for y in [x for x in range(0, int(max(higherBound)),int(math.ceil(max(higherBound)/(10*100))*100))]:   
        plt.plot(alphas, [y] * (len(alphas)), "--", lw=0.5, color="black", alpha=0.3)    
        
    # Remove the tick marks; they are unnecessary with the tick lines we just plotted.    
    plt.tick_params(axis="both", which="both", bottom="off", top="off",    
                    labelbottom="on", left="off", right="off", labelleft="on")
    
    plt.subplot(313)
    plt.plot(alphas, delayOverTravelTimeMean, lw=2.5, color=colour_scheme[colourIndex][0], hold=True)
    
    higherBound = []
    lowerBound = []

    for ii in range(0, len(travelTimeMean)):
        higherBound.append(delayOverTravelTimeMean[ii] + delayOverTravelTimeStdDev[ii])
        if delayOverTravelTimeMean[ii] - delayOverTravelTimeStdDev[ii] >= 0:
            lowerBound.append(delayOverTravelTimeMean[ii] - delayOverTravelTimeStdDev[ii])
        else:
            lowerBound.append(0)
    
    plt.plot(alphas, higherBound, lw=2.5, color=colour_scheme[colourIndex][1], hold=True)
    plt.plot(alphas, lowerBound, lw=2.5, color=colour_scheme[colourIndex][1], hold=True)
    
    # Limit the range of the plot to only where the data is.    
    # Avoid unnecessary whitespace.
    plt.ylim(0, max(higherBound))    
    plt.xlim(0, 1) 
    # Make sure your axis ticks are large enough to be easily read.    
    # You don't want your viewers squinting to read your plot. 
    xTickLocs = alphas
    xTickLabels = [str(x) for x in alphas]
    plt.xlabel('Alpha', fontsize=10)   
    plt.yticks([x*0.1 for x in range(0,int(max(higherBound)*10))], [str(x*0.1) for x in range(0, int(max(higherBound)*10))], fontsize=8)
    plt.xticks(xTickLocs, xTickLabels, fontsize=8)
    # Provide tick lines across the plot to help your viewers trace along    
    # the axis ticks. Make sure that the lines are light and small so they    
    # don't obscure the primary data lines.    
    for y in [x for x in range(0, int(max(higherBound)),int(math.ceil(max(higherBound)/(10*100))*100))]:   
        plt.plot(alphas, [y] * (len(alphas)), "--", lw=0.5, color="black", alpha=0.3)    
    plt.ylabel("Ratio of Delay to Total Travel Time", fontsize=10)
    # Remove the tick marks; they are unnecessary with the tick lines we just plotted.    
    plt.tick_params(axis="both", which="both", bottom="off", top="off",    
                    labelbottom="on", left="off", right="off", labelleft="on")
    
    plt.savefig(("plots/%s-CGR-%.2f-%s_alphaStats.pdf" % (gridID, CGR, routingMethod)), bbox_inches="tight")
    
    plt.show()
    
def plotAlphaVsCarGenRateMeanDelay(netID, carGenRange, alphaRange, penRate, axis_title_font_size, axis_labels_font_size, figNum=1):
    
    heightWidthRatio = (max(carGenRange)-min(carGenRange))/(max(alphaRange)-min(alphaRange))
    
    avcgrd_fig = plt.figure(num=figNum, dpi=300, frameon=False)
    mean_delays_matrix = []
    
    iterations = len(carGenRange)*len(alphaRange)
    index = 0
    
    for carGen in carGenRange:
        
        mean_delays = []
        
        for alpha in alphaRange:
            
            results_data_path = ("%s/evaluatedResultsFiles/%s-CGR-%.2f-CBR-PEN-%.2f-ALPHA-%.2f" % (os.environ['DIRECTORY_PATH'], netID, carGen, penRate, alpha))
            alpha=float("{0:.2f}".format(alpha))
            
            try:
                results = pickleFunc.load_obj(results_data_path)
                meanDelay = results["CBR"][penRate][alpha]['delay'][0]
                mean_delays.append(meanDelay)
            except IOError:
                print("Cannot find data for alpha=%f and carGen=%f" % (alpha, carGen))
                mean_delays = prevMeanDelays
                break
        
            index+= 1
            print("%.2f %%" % ((index/iterations)*100))
        
        prevMeanDelays = mean_delays
        mean_delays_matrix.append(mean_delays)
    
    [x,y] = np.meshgrid(alphaRange, carGenRange)
    
    z = np.matrix(mean_delays_matrix)
    z_min = z.min()
    z_max = z_min+300
    
    if z_max > 3600:
        z_min = int(math.floor(z_min/1800)*1800)
        z_max = int(math.ceil(z_max/1800)*1800)
        cax = plt.imshow(z, vmin=z_min, vmax=z_max, extent=[x.min(), x.max(), y.min(), y.max()], interpolation='bicubic', origin='lower', cmap=retrieveColourScheme('viridis'))
        cbar = plt.colorbar(cax, ticks=[z_min, (z_min+z_max)/2 , z_max])
        cbar.ax.set_yticklabel([str(z_min/3600), str((z_min+z_max)/7200), str(z_max/3600)])
    else:
        z_min = int(math.floor(z_min/300)*300)
        z_max = int(math.ceil(z_max/300)*300)
        cax = plt.imshow(z, vmin=z_min, vmax=z_max, extent=[x.min(), x.max(), y.min(), y.max()], interpolation='bicubic', origin='lower', cmap=retrieveColourScheme('viridis'))
        cbar = plt.colorbar(cax, ticks=[z_min, (z_min+z_max)/2 , z_max])
        cbar.ax.set_yticklabels([str(z_min/60), str((z_min+z_max)/120), '> ' + str(z_max/60)])
    
    formatGraph(axis_labels_font_size)

    #pp.title(r'$\alpha$' + ' Plotted Against\nCar Generation Rate\nand Associated Mean Delay', fontsize=10)
    plt.xlabel(r'$\alpha$', fontsize=axis_title_font_size)
    plt.ylabel(r'Car Generation Rate ($\lambda$)', fontsize=axis_title_font_size)
    save_to = ('%s/plots/%s_avcgrd.pdf' % (os.environ['DIRECTORY_PATH'], netID))
    plt.savefig(save_to, bbox_inches='tight')
    #fig_num += 1
    
    plt.show()

def plotMeanDelayVsCarGenRate(netID, carGenRateRange, axis_title_font_size, axis_labels_font_size, routingMethods = ["CBR", "DUA_000"], alpha=None, RUI=None, penRate=None):
    
    plt.figure("meanDelayVsCarGenRate", figsize=(3.4,1.7))
    colour_scheme = retrieveColourScheme('colourBlind')
    
    
    higherBound = 0
    plot_num = 0    
    
    for method in routingMethods:
        
        mean_delays = []
        
        for rate in carGenRateRange:
            
            if method == "CBR":
                results_data_path = ("%s/evaluatedResultsFiles/%s-CGR-%.2f-%s-PEN-%.2f-ALPHA-%.2f" % (os.environ['DIRECTORY_PATH'], netID, rate, method, penRate, alpha))
                results = pickleFunc.load_obj(results_data_path)
                meanDelay = results["CBR"][penRate][alpha]['delay'][0]
            elif method == "TTRR":
                results_data_path = ("%s/evaluatedResultsFiles/%s-CGR-%.2f-%s-PEN-%.2f-RUI-%d" % (os.environ['DIRECTORY_PATH'], netID, rate, method, penRate, RUI))
                results = pickleFunc.load_obj(results_data_path)
                meanDelay = results["TTRR"][penRate][RUI]['delay'][0]
            else:
                results_data_path = ("%s/evaluatedResultsFiles/%s-CGR-%.2f-%s" % (os.environ['DIRECTORY_PATH'], netID, rate, method))
                results = pickleFunc.load_obj(results_data_path)
                meanDelay = results["DUA"]['delay'][0]
                
            mean_delays.append(meanDelay)
            if meanDelay > higherBound : higherBound = meanDelay
            
        plt.plot(carGenRateRange, mean_delays, lw=2.5, color=colour_scheme[plot_num][0], hold=True)
        plot_num += 1
    
    formatGraph(axis_labels_font_size)
    
    if higherBound > 3600:
        plt.yticks([x for x in range(0,int(higherBound),3600)], [str(x/3600) for x in range(0, int(higherBound),3600)])
        plt.ylabel("Mean Delay (Hours)", fontsize=axis_title_font_size)
    else:
        plt.yticks([x for x in range(0,int(higherBound),600)], [str(x/60) for x in range(0, int(higherBound),600)])
        plt.ylabel("Mean Delay (Mins)", fontsize=axis_title_font_size)

    plt.xticks([x for x in range(int(min(carGenRateRange)), int(max(carGenRateRange))+1)], [str(x) for x in range(int(min(carGenRateRange)), int(max(carGenRateRange))+1)] )
    plt.xlabel(r'Car Generation Rate ($\lambda$)',fontsize=axis_title_font_size)

    plt.axis([min(carGenRateRange),max(carGenRateRange),-100,higherBound])
    
    save_to = ('%s/plots/%s_rmd.pdf' % (os.environ['DIRECTORY_PATH'], netID))
    plt.savefig(save_to, bbox_inches='tight')
    plt.show()

def plotMeanDelayVsPenetrationRate(netID, penRateRange, carGenRates, routingMethods, axis_title_font_size, axis_labels_font_size, alpha=None, RUI=None):
    
    plt.figure("meanDelayVsPenRate", figsize=(3.4,1.7))
    colour_scheme = retrieveColourScheme('colourBlind')
    
    higherBound = 0
    plot_num = 0
    
    for method in routingMethods:
        
        for carGenRate in carGenRates:
        
            mean_delays = []
            
            for penRate in penRateRange:
                penRate=float("{0:.2f}".format(penRate))
                
                if method == "CBR":
                    results_data_path = ("%s/evaluatedResultsFiles/%s-CGR-%.2f-%s-PEN-%.2f-ALPHA-%.2f" % (os.environ['DIRECTORY_PATH'], netID, carGenRate, method, penRate, alpha))
                    results = pickleFunc.load_obj(results_data_path)
                    meanDelay = results["CBR"][penRate][alpha]['delay'][0]
                elif method == "TTRR":
                    results_data_path = ("%s/evaluatedResultsFiles/%s-CGR-%.2f-%s-PEN-%.2f-RUI-%d" % (os.environ['DIRECTORY_PATH'], netID, carGenRate, method, penRate, RUI))
                    results = pickleFunc.load_obj(results_data_path)
                    meanDelay = results["TTRR"][penRate][RUI]['delay'][0]
                else:
                    results_data_path = ("%s/evaluatedResultsFiles/%s-CGR-%.2f-%s" % (os.environ['DIRECTORY_PATH'], netID, carGenRate, method))
                    results = pickleFunc.load_obj(results_data_path)
                    meanDelay = results["DUA"]['delay'][0]
                    
                mean_delays.append(meanDelay)
                if meanDelay > higherBound : higherBound = meanDelay
                
            plt.plot(penRateRange, mean_delays, lw=2.5, color=colour_scheme[plot_num][0], hold=True)
            plot_num += 1
            
    formatGraph(axis_labels_font_size)
    
    if higherBound > 3600:
        plt.yticks([x for x in range(0,int(higherBound),3600)], [str(x/3600) for x in range(0, int(higherBound),3600)])
        plt.ylabel("Mean Delay (Hours)", fontsize=axis_title_font_size)
    else:
        plt.yticks([x for x in range(0,int(higherBound),600)], [str(x/60) for x in range(0, int(higherBound),600)])
        plt.ylabel("Mean Delay (Mins)", fontsize=axis_title_font_size)

    plt.xticks([x*0.01 for x in range(0, int(max(penRateRange)*100)+1,20)], [str(x) for x in range(0, int(max(penRateRange)*100)+1, 20)] )
    plt.axis([0,1,-100,higherBound])
    plt.xlabel('Penetration Rate (%)', fontsize=axis_title_font_size)
    
    save_to = ('%s/plots/%s_pmd.pdf' % (os.environ['DIRECTORY_PATH'], netID))
    plt.savefig(save_to, bbox_inches='tight')
    plt.show()

def plotDelayOverExpectedTravlTimeVsCarGenRate(netID, carGenRateRange, routingMethods = ["CBR", "DUA_000"], alpha=None, RUI=None, penRate=None):
    
    plt.figure(1, figsize=(3.4,1.7))
    colour_scheme = retrieveColourScheme('colourBlind')
    
    plot_num = 0
    
    for method in routingMethods:
        
        mean_delay_over_expected_travel_time = []
        
        for rate in carGenRateRange:
            print(rate)
            if method == "CBR":
                results_data_path = ("%s/evaluatedResultsFiles/%s-CGR-%.2f-%s-PEN-%.2f-ALPHA-%.2f" % (os.environ['DIRECTORY_PATH'], netID, rate, method, penRate, alpha))
                results = pickleFunc.load_obj(results_data_path)
                meanDelayOverExpectedTravelTime = results["CBR"][penRate][alpha]['delay'][1]
            elif method == "TTRR":
                results_data_path = ("%s/evaluatedResultsFiles/%s-CGR-%.2f-%s-PEN-%.2f-RUI-%d" % (os.environ['DIRECTORY_PATH'], netID, rate, method, penRate, RUI))
                results = pickleFunc.load_obj(results_data_path)
                meanDelayOverExpectedTravelTime = results["TTRR"][penRate][RUI]['delay'][1]
            else:
                results_data_path = ("%s/evaluatedResultsFiles/%s-CGR-%.2f-%s" % (os.environ['DIRECTORY_PATH'], netID, rate, method))
                results = pickleFunc.load_obj(results_data_path)
                meanDelayOverExpectedTravelTime = results["DUA"]['delay'][1]
                
            mean_delay_over_expected_travel_time.append(meanDelayOverExpectedTravelTime)
            
        plt.plot(carGenRateRange, mean_delay_over_expected_travel_time, lw=2.5, color=colour_scheme[plot_num][0], hold=True)
        plot_num += 1
    
    formatGraph()
    
    plt.xlabel(r'$\lambda$', fontsize=10)
    plt.ylabel("Standard Deviation in Delay", fontsize=10)
    
    save_to = ('%s/plots/%s_sddott.pdf' % (os.environ['DIRECTORY_PATH'], netID))
    plt.savefig(save_to, bbox_inches='tight')
    plt.show()
  
def plotMeanDelayVsCarGenRate_CBRonly(netID, carGenRateRange, alphasRange, penRate, axis_title_font_size, axis_labels_font_size):
    
    plt.figure("meanDelayVsCarGenRate_CBRonly", figsize=(3.4,1.7))
    colour_scheme = retrieveColourScheme('colourBlind')
    
    plot_num = 0
    
    higherBound = 0
    
    for rate in carGenRateRange:
        
        mean_delays = []
        
        for alpha in alphasRange:
            
            alpha=float("{0:.2f}".format(alpha))
            results_data_path = ("%s/evaluatedResultsFiles/%s-CGR-%.2f-CBR-PEN-%.2f-ALPHA-%.2f" % (os.environ['DIRECTORY_PATH'], netID, rate, penRate, alpha))
            results = pickleFunc.load_obj(results_data_path)
            meanDelay = results["CBR"][penRate][alpha]['delay'][0]
            mean_delays.append(meanDelay)
            if float(meanDelay) > higherBound : higherBound = float(meanDelay)
            
        plt.plot(alphasRange, mean_delays, lw=2.5, color=colour_scheme[plot_num][0], hold=True)
        plot_num += 1
    
    formatGraph(axis_labels_font_size)
    
    if higherBound > 3600:
        plt.yticks([x for x in range(0,int(higherBound),3600)], [str(x/3600) for x in range(0, int(higherBound),3600)])
        plt.ylabel("Mean Delay (Hours)", fontsize=axis_title_font_size)
    else:
        plt.yticks([x for x in range(0,int(higherBound),300)], [str(x/60) for x in range(0, int(higherBound),300)])
        plt.ylabel("Mean Delay (Mins)", fontsize=axis_title_font_size)
    
    plt.xlabel(r"$\alpha$", fontsize=axis_title_font_size)
    
    plt.axis([min(alphasRange),max(alphasRange),-100,higherBound])
    
    save_to = ('%s/plots/%s_amd.pdf' % (os.environ['DIRECTORY_PATH'], netID))
    plt.savefig(save_to, bbox_inches='tight')
    plt.show()

def formatGraph(axis_labels_font_size, fontFamily='Times New Roman', fontWeight='normal' ):
    
    # Set matplotlib default font
    font = {'family' : fontFamily,
            'weight' : fontWeight,
            'size'   : axis_labels_font_size}
    
    matplotlib.rc('font', **font)
    
    # Remove the plot frame lines. They are unnecessary chartjunk.    
    ax = plt.subplot(111) 
    ax.spines["top"].set_visible(False)
    ax.spines["bottom"].set_visible(False)    
    ax.spines["right"].set_visible(False)    
    ax.spines["left"].set_visible(False)
    # Ensure that the axis ticks only show up on the bottom and left of the plot.    
    # Ticks on the right and top of the plot are generally unnecessary chartjunk.    
    ax.get_xaxis().tick_bottom()    
    ax.get_yaxis().tick_left()

def checkTripFilesCanBeRead():
    for file in os.listdir("SUMO_Output_Files/tripFiles"):
        tripFile_filepath = "SUMO_Output_Files/tripFiles/" + file
        tripData =  ET.parse(tripFile_filepath)
        trips = tripData.getroot()
    print("Success")

def printKeyStatistics(simulationsList):
        
    travelTimeMean = []
    travelTimeStdDev = []
    travelTimeMean_runsStdDev = []
    travelTimeStdDev_runsStdDev = []
    
    delayMean = []
    delayStdDev = []
    delayMean_runsStdDev = []
    delayStdDev_runsStdDev = []
    
    delayOverTravelTimeMean = []
    delayOverTravelTimeStdDev = []
    delayOverTravelTimeMean_runsStdDev = []
    delayOverTravelTimeStdDev_runsStdDev = []
        
    for batchID in simulationsList:
    
        dataContainer_filepath = ("%s/evaluatedResultsFiles/%s" % (os.environ['DIRECTORY_PATH'], batchID))
        dataContainer = pickleFunc.load_obj(dataContainer_filepath)
        
        routingMethod = dataContainer.keys()[0]
        
        if routingMethod == "CBR":
            penRate = dataContainer[routingMethod].keys()[0]
            alpha = dataContainer[routingMethod][penRate].keys()[0]
            title = ("Coverage Based Routing - alpha = %.2f, penetration rate = %d%%" % (alpha, int(penRate*100)))
            data = dataContainer[routingMethod][penRate][alpha]
        elif routingMethod == "TTRR":
            penRate = dataContainer[routingMethod].keys()[0]
            RUI = dataContainer[routingMethod][penRate].keys()[0]
            title = ("Travel Time Routing - update interval = %d, penetration rate = %d%%" % (int(RUI), int(penRate*100)))
            data = dataContainer[routingMethod][penRate][RUI]
        elif routingMethod == "DUA":
            carsOverTimeStats = dataContainer[routingMethod]['carsOverTime']
            title = ("Dynamic User Assignment")
            data = dataContainer[routingMethod]
                                
        travelTimeMean.append(data["travelTime"][0])
        travelTimeStdDev.append(data["travelTime"][1])
        travelTimeMean_runsStdDev.append(data["travelTime"][2])
        travelTimeStdDev_runsStdDev.append(data["travelTime"][3])
        
        delayMean.append(data["delay"][0])
        delayStdDev.append(data["delay"][1])
        delayMean_runsStdDev.append(data["delay"][2])
        delayStdDev_runsStdDev.append(data["delay"][3])
        
        delayOverTravelTimeMean.append(data["delayOverTravelTime"][0])
        delayOverTravelTimeStdDev.append(data["delayOverTravelTime"][1])
        delayOverTravelTimeMean_runsStdDev.append(data["delayOverTravelTime"][2])
        delayOverTravelTimeStdDev_runsStdDev.append(data["delayOverTravelTime"][3])
    
    print("Travel Time Mean", [int(x/60) for x in travelTimeMean])
    print("Travel Time Stadard Deviation", [int(x/60) for x in travelTimeStdDev])
    print("Travel Time Mean Standard Deviation Between Runs", [int(x/60) for x in travelTimeMean_runsStdDev])
    print("Travel Time Standard Deviation in Standard Deviation Between Runs", [int(x/60) for x in travelTimeStdDev_runsStdDev])
    print("Mean Delay", [int(x/60) for x in delayMean])
    print("Delay Standard Deviation", [int(x/60) for x in delayStdDev])
    print("Mean Delay Standard Deviation Between Runs", [int(x/60) for x in delayMean_runsStdDev])
    print("Standard Deviation in Standard Deviation Between Runs", [int(x/60) for x in delayStdDev_runsStdDev])
    print("Mean Delay Over Travel Time", [int(x*1000)/1000 for x in delayOverTravelTimeMean])
    print("Standard Deviation in Delay Over Travel Time", [int(x*1000)/1000 for x in delayOverTravelTimeStdDev])
    print("Standard Deviation in Mean Delay Over Travel Time Between Runs", [int(x*1000)/1000 for x in delayOverTravelTimeMean_runsStdDev])
    print("Standard Deviation in Standard Deviation in Delay Over Travel Time Between Runs", [int(x*1000)/1000 for x in delayOverTravelTimeStdDev_runsStdDev])      
         
def extractMeanDataFromMultipleRuns(overwritePrevious=False):
    
    # Parse the simulation details XML file
    simulationDetails_filepath = ("%s/simulationDetails.xml" % (directory_path))
    parse_simulationDetails = ET.parse(simulationDetails_filepath) # Use the XML parser to read the net XML file
    simDetails = parse_simulationDetails.getroot()
    
    # {Routing Method: {{1:{Details : {alpha: #, penRate: #}, travelTime (all runs) : [ meanTravelTime, stdDevTravelTime , stdDeBetweenRuns] }, 2: {}}
    
    # For every simulation
    for simulation in simDetails:
                
        # Extract the simulatino parameters
        batchID = simulation.attrib["batchID"]
        netID = simulation.attrib["netID"]
        routingMethod = simulation.attrib["routingMethod"]
        carGenRate = float(simulation.attrib["carGenRate"])
        runs = int(simulation.attrib["runs"])
        
        # If the simulation is Coverage Based Routing
        if routingMethod == "CBR":
            for batch in simulation:
                # Create a dictionary to store results
                results = {}
                results.update({routingMethod:{}})
                save=False

                penetrationRate = float(batch.attrib["PenetrationRate"])
                alpha = float(batch.attrib["alpha"])
                
                results[routingMethod].update({penetrationRate:{alpha:{}}})
                results_filepath = ("%s/evaluatedResultsFiles/%s-CGR-%.2f-CBR-PEN-%.2f-ALPHA-%.2f" % (os.environ['DIRECTORY_PATH'], netID, carGenRate, penetrationRate, alpha))
                
                if not(os.path.isfile(results_filepath + ".pkl")) or overwritePrevious:
                
                    runs_eval = 0
                    mean_travelTimes = []
                    stdDev_travelTimes = []
                    mean_delay = []
                    stdDev_delay = []
                    mean_delayOverExpectedTravelTime = []
                    stdDev_delayOverExpectedTravelTime = []
                    
                    carsOverTime = []
    
                    for run in range(0,runs):
                        resultsIdentifier = ("%s-CGR-%.2f-CBR-PEN-%.2f-ALPHA-%.2f-%d" % (netID, carGenRate, penetrationRate, alpha, run))
                        inputsIdentifer = ("%s-CGR-%.2f-PEN-%.2f-%d" % (netID, carGenRate, penetrationRate, run))
                        
                        routeFile_filepath = ("%s/SUMO_Input_Files/routeFiles/%s.rou.alt.xml" % (directory_path, inputsIdentifer))
                        tripFile_filepath = ("%s/SUMO_Output_Files/tripFiles/tripInfo-%s.xml" % (directory_path, resultsIdentifier))
                        
                        if os.path.isfile(tripFile_filepath):
                            try:
                                ET.parse(tripFile_filepath)
                                fileValidity = True
                            except ET.ParseError:
                                fileValidity = False
                                print("%s is incomplete" % tripFile_filepath)
                        
                            if fileValidity:
                                carsOverTime_run = carsInNetworkOverTime(tripFile_filepath)
                                carsOverTime.append(carsOverTime_run)
                                
                                [mean_travelTime_run, stdDev_travelTime_run] = extractTravelTimeStats(tripFile_filepath)
                                mean_travelTimes.append(mean_travelTime_run)
                                stdDev_travelTimes.append(stdDev_travelTime_run)
                                
                                [mean_delay_run, stdDev_delay_run] = calculateTripDelayStats(tripFile_filepath, routeFile_filepath)
                                mean_delay.append(mean_delay_run)
                                stdDev_delay.append(stdDev_delay_run)
                                
                                [mean_delayOverExpectedTravelTime_run, stdDev_delayOverExpectedTravelTime_run] = delayAsFractionOfExpectedTravelTime(tripFile_filepath, routeFile_filepath)
                                mean_delayOverExpectedTravelTime.append(mean_delayOverExpectedTravelTime_run)
                                stdDev_delayOverExpectedTravelTime.append(stdDev_delayOverExpectedTravelTime_run)
                                
                                runs_eval += 1
                            else:
                                print("%s not found" % resultsIdentifier)
                        
                    if runs_eval > 0:                    
                        print("%d runs evaluated, calculating statistics..." % runs_eval)
                        print("Cars in network over time...")
                        carsInNetworkOverTimeStats = carsInNetworkOverTimeMultiRun(carsOverTime)
                        print("Travel time statistics...")
                        travelTimeStats = [np.mean(mean_travelTimes), np.mean(stdDev_travelTimes),np.std(mean_travelTimes), np.std(stdDev_travelTimes)]
                        print("Delay statistics...")
                        delayStats = [np.mean(mean_delay), np.mean(stdDev_delay), np.std(mean_delay), np.std(stdDev_delay)]
                        print("Delay over expected travel time statistics...")
                        delayOverExpectedTravelTimeStats = [np.mean(mean_delayOverExpectedTravelTime), np.mean(stdDev_delayOverExpectedTravelTime), np.std(mean_delayOverExpectedTravelTime), np.std(stdDev_delayOverExpectedTravelTime)]
                        print("Adding to dictionary...")
                        results[routingMethod][penetrationRate][alpha].update({'carsOverTime' : carsInNetworkOverTimeStats,'travelTime' :  travelTimeStats, 'delay' : delayStats,
                                                                               'delayOverExpectedTravelTime' : delayOverExpectedTravelTimeStats})
                        
                        save = True
                        
                    else:
                        print("No runs to evaluated for %s - ALPHA = %.2f - PEN = %.2f" % (batchID, alpha, penetrationRate))
                    
                    if save:
                        print("Saving results for %s" % results_filepath)
                        pickleFunc.save_obj(results, results_filepath)
                    else:
                        print("Results empty, not saving")
        
        elif routingMethod == "TTRR":
            
            results = {}
            results.update({routingMethod:{}})
            save=False
            
            for batch in simulation:
                batchNo = 1
                penetrationRate = float(batch.attrib["PenetrationRate"])
                RUI = int(float(batch.attrib["UpdateInterval"]))
                
                results[routingMethod].update({penetrationRate:{RUI:{}}})
                results_filepath = ("%s/evaluatedResultsFiles/%s-CGR-%.2f-TTRR-PEN-%.2f-RUI-%d" % (os.environ['DIRECTORY_PATH'], netID, carGenRate, penetrationRate, RUI))
                
                if not(os.path.isfile(results_filepath + ".pkl")) or overwritePrevious:
                
                    runs_eval = 0
                    mean_travelTimes = []
                    stdDev_travelTimes = []
                    mean_delay = []
                    stdDev_delay = []
                    mean_delayOverExpectedTravelTime = []
                    stdDev_delayOverExpectedTravelTime = []
                    
                    carsOverTime = []
    
                    for run in range(0,runs):
                    
                        resultsIdentifier = ("%s-CGR-%.2f-TTRR-PEN-%.2f-RUI-%d-%d" % (netID, carGenRate, penetrationRate, RUI, run))
                        inputsIdentifer = ("%s-CGR-%.2f-PEN-%.2f-%d" % (netID, carGenRate, penetrationRate, run))
                        
                        routeFile_filepath = ("%s/SUMO_Input_Files/routeFiles/%s.rou.alt.xml" % (directory_path, inputsIdentifer))
                        tripFile_filepath = ("%s/SUMO_Output_Files/tripFiles/tripInfo-%s.xml" % (directory_path, resultsIdentifier))
                        
                        if os.path.isfile(tripFile_filepath):
                            carsOverTime_run = carsInNetworkOverTime(tripFile_filepath)
                            carsOverTime.append(carsOverTime_run)
                            
                            [mean_travelTime_run, stdDev_travelTime_run] = extractTravelTimeStats(tripFile_filepath)
                            mean_travelTimes.append(mean_travelTime_run)
                            stdDev_travelTimes.append(stdDev_travelTime_run)
                            
                            [mean_delay_run, stdDev_delay_run] = calculateTripDelayStats(tripFile_filepath, routeFile_filepath)
                            mean_delay.append(mean_delay_run)
                            stdDev_delay.append(stdDev_delay_run)
                            
                            [mean_delayOverExpectedTravelTime_run, stdDev_delayOverExpectedTravelTime_run] = delayAsFractionOfExpectedTravelTime(tripFile_filepath, routeFile_filepath)
                            mean_delayOverExpectedTravelTime.append(mean_delayOverExpectedTravelTime_run)
                            stdDev_delayOverExpectedTravelTime.append(stdDev_delayOverExpectedTravelTime_run)
                            
                            runs_eval += 1
                        else:
                            print("%s not found" % resultsIdentifier)
                        
                    if runs_eval > 0:                    
                        print("%d runs evaluated, calculating statistics..." % runs_eval)
                        print("Cars in network over time...")
                        carsInNetworkOverTimeStats = carsInNetworkOverTimeMultiRun(carsOverTime)
                        print("Travel time statistics...")
                        travelTimeStats = [np.mean(mean_travelTimes), np.mean(stdDev_travelTimes),np.std(mean_travelTimes), np.std(stdDev_travelTimes)]
                        print("Delay statistics...")
                        delayStats = [np.mean(mean_delay), np.mean(stdDev_delay), np.std(mean_delay), np.std(stdDev_delay)]
                        print("Delay over expected travel time statistics...")
                        delayOverExpectedTravelTimeStats = [np.mean(mean_delayOverExpectedTravelTime), np.mean(stdDev_delayOverExpectedTravelTime), np.std(mean_delayOverExpectedTravelTime), np.std(stdDev_delayOverExpectedTravelTime)]
                        print("Adding to dictionary...")
                        results[routingMethod][penetrationRate][RUI].update({'carsOverTime' : carsInNetworkOverTimeStats,'travelTime' :  travelTimeStats, 'delay' : delayStats,
                                                                               'delayOverExpectedTravelTime' : delayOverExpectedTravelTimeStats})                        
                        save=True
                        
                    else:
                        print("No runs to evaluated for %s - RUI = %d - PEN = %.2f" % (batchID, RUI, penetrationRate))
            
                    if save:
                        print("Saving results for %s" % results_filepath)
                        pickleFunc.save_obj(results, results_filepath)
                    else:
                        print("Results empty, not saving")
    
        elif routingMethod == "DUA":
            
            results_049 = {}
            results_049.update({routingMethod:{}})
            results_000 = {}
            results_000.update({routingMethod:{}})
            
            results_filepath_049 = ("%s/evaluatedResultsFiles/%s-CGR-%.2f-DUA_049" % (os.environ['DIRECTORY_PATH'], netID, carGenRate))
            results_filepath_000 = ("%s/evaluatedResultsFiles/%s-CGR-%.2f-DUA_000" % (os.environ['DIRECTORY_PATH'], netID, carGenRate))
            
            if not(os.path.isfile(results_filepath_000 + ".pkl")) or not(os.path.isfile(results_filepath_049 + ".pkl")) or overwritePrevious:
            
                save=False
                
                for batch in simulation:
                    
                    runs_eval = 0
                    mean_travelTimes_049 = []
                    stdDev_travelTimes_049 = []
                    mean_delay_049 = []
                    stdDev_delay_049 = []
                    mean_delayOverExpectedTravelTime_049 = []
                    stdDev_delayOverExpectedTravelTime_049 = []         
                    carsOverTime_049 = []
                    
                    mean_travelTimes_000 = []
                    stdDev_travelTimes_000 = []
                    mean_delay_000 = []
                    stdDev_delay_000 = []
                    mean_delayOverExpectedTravelTime_000 = []
                    stdDev_delayOverExpectedTravelTime_000 = []
                    carsOverTime_000 = []
    
                    for run in range(0,runs):
                    
                        resultsIdentifier = ("%s-CGR-%.2f-DUA-%d" % (netID, carGenRate, run))
                        inputsIdentifer = ("%s-CGR-%.2f-PEN-%.2f-%d" % (netID, carGenRate, penetrationRate, run))
                        
                        routeFile_filepath = ("%s/SUMO_Input_Files/routeFiles/%s.rou.alt.xml" % (directory_path, inputsIdentifer))
                        tripFile_filepath_049 = ("%s/SUMO_Output_Files/%s/tripinfo_049.xml" % (directory_path, resultsIdentifier))
                        tripFile_filepath_000 = ("%s/SUMO_Output_Files/%s/tripinfo_000.xml" % (directory_path, resultsIdentifier))
                        
                        if os.path.isfile(tripFile_filepath_049):
                            carsOverTime_run_049 = carsInNetworkOverTime(tripFile_filepath_049)
                            carsOverTime_049.append(carsOverTime_run_049)
                            
                            [mean_travelTime_run_049, stdDev_travelTime_run_049] = extractTravelTimeStats(tripFile_filepath_049)
                            mean_travelTimes_049.append(mean_travelTime_run_049)
                            stdDev_travelTimes_049.append(stdDev_travelTime_run_049)
                            
                            [mean_delay_run_049, stdDev_delay_run_049] = calculateTripDelayStats(tripFile_filepath_049, routeFile_filepath)
                            mean_delay_049.append(mean_delay_run_049)
                            stdDev_delay_049.append(stdDev_delay_run_049)
                            
                            [mean_delayOverExpectedTravelTime_run_049, stdDev_delayOverExpectedTravelTime_run_049] = delayAsFractionOfExpectedTravelTime(tripFile_filepath_049, routeFile_filepath)
                            mean_delayOverExpectedTravelTime_049.append(mean_delayOverExpectedTravelTime_run_049)
                            stdDev_delayOverExpectedTravelTime_049.append(stdDev_delayOverExpectedTravelTime_run_049)
                            
                            carsOverTime_run_000 = carsInNetworkOverTime(tripFile_filepath_000)
                            carsOverTime_000.append(carsOverTime_run_000)
                            
                            [mean_travelTime_run_000, stdDev_travelTime_run_000] = extractTravelTimeStats(tripFile_filepath_000)
                            mean_travelTimes_000.append(mean_travelTime_run_000)
                            stdDev_travelTimes_000.append(stdDev_travelTime_run_000)
                            
                            [mean_delay_run_000, stdDev_delay_run_000] = calculateTripDelayStats(tripFile_filepath_000, routeFile_filepath)
                            mean_delay_000.append(mean_delay_run_000)
                            stdDev_delay_000.append(stdDev_delay_run_000)
                            
                            [mean_delayOverExpectedTravelTime_run_000, stdDev_delayOverExpectedTravelTime_run_000] = delayAsFractionOfExpectedTravelTime(tripFile_filepath_000, routeFile_filepath)
                            mean_delayOverExpectedTravelTime_000.append(mean_delayOverExpectedTravelTime_run_000)
                            stdDev_delayOverExpectedTravelTime_000.append(stdDev_delayOverExpectedTravelTime_run_000)
                            
                            runs_eval += 1
                        else:
                            print("%s not found" % resultsIdentifier)
                    
                    if runs_eval > 0:                    
                        print("%d runs evaluated, calculating statistics..." % runs_eval)
                        print("Cars in network over time...")
                        carsInNetworkOverTimeStats_049 = carsInNetworkOverTimeMultiRun(carsOverTime_049)
                        carsInNetworkOverTimeStats_000 = carsInNetworkOverTimeMultiRun(carsOverTime_000)
                        print("Travel time statistics...")
                        travelTimeStats_049 = [np.mean(mean_travelTimes_049), np.mean(stdDev_travelTimes_049),np.std(mean_travelTimes_049), np.std(stdDev_travelTimes_049)]
                        travelTimeStats_000 = [np.mean(mean_travelTimes_000), np.mean(stdDev_travelTimes_000),np.std(mean_travelTimes_000), np.std(stdDev_travelTimes_000)]
                        print("Delay statistics...")
                        delayStats_049 = [np.mean(mean_delay_049), np.mean(stdDev_delay_049), np.std(mean_delay_049), np.std(stdDev_delay_049)]
                        delayStats_000 = [np.mean(mean_delay_000), np.mean(stdDev_delay_000), np.std(mean_delay_000), np.std(stdDev_delay_000)]
                        print("Delay over expected travel time statistics...")
                        delayOverExpectedTravelTimeStats_049 = [np.mean(mean_delayOverExpectedTravelTime_049), np.mean(stdDev_delayOverExpectedTravelTime_049), np.std(mean_delayOverExpectedTravelTime_049),
                                                        np.std(stdDev_delayOverExpectedTravelTime_049)]
                        delayOverExpectedTravelTimeStats_000 = [np.mean(mean_delayOverExpectedTravelTime_000), np.mean(stdDev_delayOverExpectedTravelTime_000), np.std(mean_delayOverExpectedTravelTime_000),
                                                        np.std(stdDev_delayOverExpectedTravelTime_000)]
                        print("Adding to dictionary...")
                        results_049[routingMethod].update({'carsOverTime' : carsInNetworkOverTimeStats_049,'travelTime' :  travelTimeStats_049, 'delay' : delayStats_049,
                                                           'delayOverExpectedTravelTime' : delayOverExpectedTravelTimeStats_049})
                        results_000[routingMethod].update({'carsOverTime' : carsInNetworkOverTimeStats_000,'travelTime' :  travelTimeStats_000, 'delay' : delayStats_000,
                                                           'delayOverExpectedTravelTime' : delayOverExpectedTravelTimeStats_000})
                        
                        save=True
                        
                    else:
                        print("No runs to evaluate for %s" % (batchID))
            
                if save:
                    print("Saving results for %s and %s" % (results_filepath_049, results_filepath_000))
                    pickleFunc.save_obj(results_049, results_filepath_049)
                    pickleFunc.save_obj(results_000, results_filepath_000)
    
                else:
                    print("Results empty, not saving")

def main(reanalyse=False):
    
    directory_path = os.getcwd()
    simulationDetails_filepath = ("%s/simulationDetails.xml" % (directory_path))
    parse_simulationDetails = ET.parse(simulationDetails_filepath) # Use the XML parser to read the net XML file
    simDetails = parse_simulationDetails.getroot()

    for simulation in simDetails:
        netID = simulation.attrib["id"]
        stepLength = float(simulation.attrib["stepLength"])
        carGenRate = float(simulation.attrib["carGenRate"])
        runs = int(simulation.attrib["runs"])
        for run in range(0,runs):
            for batch in simulation:
                routingMethod = batch.attrib["routingMethod"]
                if routingMethod == "CBR":
                    
                    penetrationRate = float(batch.attrib["PenetrationRate"])
                    alpha = float(batch.attrib["alpha"])
                    
                    resultsIdentifier = ("%s-CGR-%.2f-CBR-PEN-%.2f-ALPHA-%.2f-%d" % (netID, carGenRate, penetrationRate, alpha, run))
                    inputsIdentifer = ("%s-CGR-%.2f-PEN-%.2f-%d" % (netID, carGenRate, penetrationRate, run))
                    
                    routeFile_filepath = ("%s/SUMO_Input_Files/routeFiles/%s.rou.alt.xml" % (directory_path, inputsIdentifer))
                    tripFile_filepath = ("%s/SUMO_Output_Files/tripFiles/tripInfo-%s.xml" % (directory_path, resultsIdentifier))
                    analysedResults_filepath = ("%s/analysedData/movingAverageDelay-%s" % (directory_path, resultsIdentifier))
                    
                elif routingMethod == "TravelTimeRouter":
                    
                    penetrationRate = float(batch.attrib["PenetrationRate"])
                    updateInterval = int(float(batch.attrib["UpdateInterval"]))
                
                    resultsIdentifier = ("%s-CGR-%.2f-TTRR-PEN-%.2f-RUI-%d-%d" % (netID, carGenRate, penetrationRate, updateInterval, run))
                    inputsIdentifer = ("%s-CGR-%.2f-PEN-%.2f-%d" % (netID, carGenRate, penetrationRate, run))
                    
                    routeFile_filepath = ("%s/SUMO_Input_Files/routeFiles/%s.rou.alt.xml" % (directory_path, inputsIdentifer))
                    tripFile_filepath = ("%s/SUMO_Output_Files/tripFiles/tripInfo-%s.xml" % (directory_path, resultsIdentifier))
                    analysedResults_filepath = ("%s/analysedData/movingAverageDelay-%s" % (directory_path, resultsIdentifier))
                
                elif routingMethod == "DUA":
                    
                    penetrationRate = 0
                    
                    resultsIdentifier = ("%s-CGR-%.2f-DUA-%d" % (netID, carGenRate, run))
                    inputsIdentifer = ("%s-CGR-%.2f-%d" % (netID, carGenRate, run))
                    
                    routeFile_filepath = ("%s/SUMO_Input_Files/routeFiles/%s.rou.alt.xml" % (directory_path, inputsIdentifer))
                    tripFile_filepath = ("%s/SUMO_Output_Files/%s/tripinfo_000.xml" % (directory_path, resultsIdentifier))
                    analysedResults_filepath = ("%s/analysedData/movingAverageDelay-%s" % (directory_path, resultsIdentifier))
                
                if not(os.path.isfile(analysedResults_filepath + ".pkl")) or reanalyse:
                    try:
                        movingAverageDelay = convertFile2movingAverageDelay(routeFile_filepath, tripFile_filepath)
                        pickleFunc.save_obj(movingAverageDelay, analysedResults_filepath)
                    except IOError:
                        print("%s --> no results file" % (resultsIdentifier))
    
    print("Finished")
    
    #reprocess = False
    
    #if os.path.isfile("/Users/tb7554/lbox/lbox_workspace/_004_Grid-10x10_/analysedData/movingAverageDelay-Grid-10x10-CGR-10.00-CBR-PEN-0.75-ALPHA-0.95-0.pkl") and not(reprocess):
    #    movingAverageDelay = pickleFunc.load_obj("/Users/tb7554/lbox/lbox_workspace/_004_Grid-10x10_/analysedData/movingAverageDelay-Grid-10x10-CGR-10.00-CBR-PEN-0.75-ALPHA-0.95-0")
    #else:
    #    movingAverageDelay = convertFile2movingAverageDelay(routeFile_filepath, tripFile_filepath)
    #    pickleFunc.save_obj(movingAverageDelay, "/Users/tb7554/lbox/lbox_workspace/_004_Grid-10x10_/analysedData/movingAverageDelay-Grid-10x10-CGR-10.00-CBR-PEN-0.75-ALPHA-0.95-0")

    #plotMeanData(movingAverageDelay)
    
    #delayOverTraveTime_movingAverage = convertCarData2MovingAverage(veh_delayOverTravelTime, veh_departTimes)
    #delayOverTraveTime_movingAverage = np.multiply(delayOverTraveTime_movingAverage, 100)
    #print(max(delayOverTraveTime_movingAverage))
    #plotData(delayOverTraveTime_movingAverage, ['Moving Average\nCoverage Based Routing\n(100% Penetration)'])
    
    #plotArrayAgainstTime(delayOverTraveTime_movingAverage)
    #vehIDs = extractVehicleIDList(routeFile_filepath)
    #vehRoute_costs = extractVehicleExpectedTravelTimesFromRouteFile(routeFile_filepath)
    #simEndTime = calculateTotalSimTime(tripFile_filepath)
    
    #veh_travelTimes_1 = extractVehicleActualTravelTimesFromTripFile(tripFile_filepath_1)
    #veh_departDelays_1 = extractDepartDelaysFromTripFile(tripFile_filepath_1)
    #veh_arrivalTimes_1 = extractArrivalTimesFromTripFile(tripFile_filepath_1)
    #trip_delays_1 = calculateTripDelays(vehIDs, veh_travelTimes_1, vehRoute_costs)
    #trip_delays_1 = dictAdd(trip_delays_1, veh_departDelays_1)
       
    #veh_travelTimes_2 = extractVehicleActualTravelTimesFromTripFile(tripFile_filepath_2)
    #veh_departDelays_2 = extractDepartDelaysFromTripFile(tripFile_filepath_2)
    #veh_arrivalTimes_2 = extractArrivalTimesFromTripFile(tripFile_filepath_2)
    #veh_departTimes_2 = extractDepartTimesFromTripFile(tripFile_filepath_2)
    #trip_delays_2 = calculateTripDelays(vehIDs, veh_travelTimes_2, vehRoute_costs)
    #trip_delays_2 = dictAdd(trip_delays_2, veh_departDelays_2)
    
    #delays_movingAverage_1 = tripDelayMovingAverageVersion1(vehIDs, trip_delays, veh_arrivalTimes)
    #delays_movingAverage_1, delays_movingStandardDeviation_1, delays_maximum_1 = tripDelayMovingAverageVersion2(vehIDs, trip_delays_1, veh_arrivalTimes_1, veh_departTimes_1, 100)
    #[delays_movingAverage_2, delays_movingStandardDeviation_2, delays_maximum_2] = tripDelayMovingAverageVersion2(vehIDs, trip_delays_2, veh_arrivalTimes_2, veh_departTimes_2, 100)
    #travelTime_movingAverage, travelTime_movingStandardDeviation = travelTimeMovingAverage(vehIDs, veh_travelTimes, veh_arrivalTimes)
    
    #fig = pp.figure()
    #time = range(0, len(delays_movingAverage_1))
    #pp.plot(time, delays_maximum_1, hold=True)
    #time = range(0, len(delays_movingAverage_1))
    #pp.plot(time, delays_movingAverage_1)
    #pp.plot(time, std_dev)
    #pp.show()
    
if __name__ == "__main__":
    extractKeyDataFromTripFile("/Users/tb7554/UniversityCloud/Home/workspace/_009_Grid-10x10_/SUMO_Output_Files/tripFiles/tripInfo-Grid-10x10-CGR-3.00-CBR-PEN-0.10-ALPHA-0.95-0.xml")


