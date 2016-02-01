from __future__ import print_function
import os, sys, math
import xml.etree.ElementTree as ET

os.environ['DIRECTORY_PATH'] = os.getcwd()
directory_path = os.getcwd()
path_components = directory_path.split('/')
directory_name = path_components.pop()
os.environ['SUMO_PYTHON_MODULES'] = ("%s/_000_SUMO-PYTHON-MODULES_" % (os.path.dirname(directory_path)))
sys.path.append(os.environ['SUMO_PYTHON_MODULES'])

from sumoFileGen import sumoMains, pickleFunc

def allMiscDUAFiles(simulationDetails_filepath = "simulationDetails.xml"):
    
    """Executed within the directory, passed the simulationDetails.xml filepath if located elsewhere other than the main directory"""
    
    # Parse the simulation details XML file
    parse_simulationDetails = ET.parse(simulationDetails_filepath) # Use the XML parser to read the net XML file
    simDetails = parse_simulationDetails.getroot()
    
    # For every simulation
    for simulation in simDetails:
                
        # Extract the simulatino parameters
        netID = simulation.attrib["netID"]
        routingMethod = simulation.attrib["routingMethod"]
        carGenRate = float(simulation.attrib["carGenRate"])
        runs = int(simulation.attrib["runs"])
        
        # If the simulation is Coverage Based Routing
        if routingMethod == "DUA":
            for ii in range(0,runs):
                folderPath = ("%s/SUMO_Output_Files/%s-CGR-%.2f-DUA-%d" % (os.environ['DIRECTORY_PATH'], netID, carGenRate, ii))
                
                for jj in range(1,49):
                    files = [("dua.log"), ("tripinfo_%03d.xml" % (jj)), ("dua_dump_%03d.add.xml" % (jj)), ("dump_%03d_900.xml" % (jj)), ("%s-CGR-%01d_%03d.rou.xml" % (netID, carGenRate, jj)),
                             ("iteration_%03d.sumo.log" % (jj)), ("iteration_%03d.sumocfg" % (jj)), ("iteration_%03d_%s-CGR-%01d_%03d.duarcfg" % (jj, netID, carGenRate, (jj-1)))]
                    
                    for item in files:
                        remove_this_file = ("%s/%s" % (folderPath, item))
                        if os.path.isfile(remove_this_file) : os.remove(remove_this_file)
                        
                for jj in range(0,50):
                    files = [("%s-CGR-%01d_%03d.rou.alt.xml" % (netID, carGenRate, jj))]
                    
                    for item in files:
                        remove_this_file = ("%s/%s" % (folderPath, item))
                        if os.path.isfile(remove_this_file) : os.remove(remove_this_file)
            
def rmBluecrystalOutputShellFiles():
    """ Executed within the relevant directory """
    os.system('rm *.sh.o*')
    
def rmVehRouteAltFiles(vehRoutes_folder = "SUMO_Input_Files/routeFiles"):
    """ Executed within the relevant directory """
    os.chdir(vehRoutes_folder)
    os.system('rm *.rou.alt.xml')
    
def removeAllFilesFromSpecifiedDirectories(directories):
    
    for folder in directories:
        try:
            os.chdir(directory)
            allMiscDUAFiles()
            rmBluecrystalOutputShellFiles()
            rmVehRouteAltFiles()
        except 'OSError':
            print("%s not a directory?" % (folder))
    
def main():
    top_level_directory = os.getcwd()
    directories = ['_005_Grid-10x10_TLS', '_006_Bristol_TLS', '_007_Bristol_TLS_additionals', '_008_Scalefree-10x10_', 
                   '_009_Grid-10x10_', '_010_Grid-10x10_TLS', '_011_Scalefree-10x10_', '_012_Bristol', '_013_Bristol_2', '_015_Bristol_3_',
                   '_016_Grid-10x10_TLS_', '_017_Bristol_4_', '_018_Grid-10x10_TLS_', '_019_Scalefree-10x10_', '_021_Grid-32x32_TLS_']
    
    removeAllFilesFromSpecifiedDirectories(directories)
    
if __name__ == "__main__":
    main()