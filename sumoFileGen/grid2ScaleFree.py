#!/usr/bin/env python
"""
@file    parseXML.py
@author  Tim Barker
@date    09/01/2015

Functions for parsing XML files into python objects for use in routing algorithms

"""
from __future__ import print_function, division
import os, sys, random, math, subprocess, math

directory_path = os.getcwd()
os.environ['DIRECTORY_PATH'] = directory_path
path_components = directory_path.split('/')
directory_name = path_components.pop()

from sumoRouter import netObjects, netObjFuncs
from sumoFileGen import pickleFunc

def getKey(item):
    return item[1]

class newNodeObj():
    
    def __init__(self, id, x, y):
        self.id = id
        self.x = x
        self.y = y
        self.degree = 0
        self.preferedNodes = None
        self.neighbours = []
    
    def __str__(self):
        return ("ID: %s\nLoc: (%d,%d)\nDeg: %d\nRemEdges: %d\nPrefNod: %s\nNeighbours: %s" % (self.id, self.x, self.y, self.degree, self.remainingEdges, self.preferedNodes, self.neighbours))
    
    def degreeIncrement(self):
        self.degree += 1
        
    def addNeighbour(self, neighbour):
        self.neighbours.append(neighbour)
    
    def preferedNodesCreator(self, nodeContainer, L):
        preferedNodes = []
        
        for node in nodeContainer:
            xDistance = self.x - nodeContainer[node].x
            yDistance = self.y - nodeContainer[node].y
            
            distance =  math.sqrt(xDistance**2 + yDistance**2)

            nodeAndDistanceTuple = (nodeContainer[node].id, distance)
            
            if distance <= L and not(distance==0) and node not in self.neighbours:
                preferedNodes.append(nodeAndDistanceTuple)
        
        self.preferedNodes = preferedNodes
        random.shuffle(self.preferedNodes)
        
#         notPreferedNodes = []
#         
#         for node in nodeContainer:
#             xDistance = self.x - nodeContainer[node].x
#             yDistance = self.y - nodeContainer[node].y
#             
#             distance =  math.sqrt(xDistance**2 + yDistance**2)
# 
#             nodeAndDistanceTuple = (nodeContainer[node].id, distance)
#             
#             if distance > L and not(distance==0):
#                 notPreferedNodes.append(nodeAndDistanceTuple)
#                 
#         extension = sorted(notPreferedNodes, key=getKey)
#         
#         self.preferedNodes.extend(extension)
        
        #self.preferedNodes = sorted(preferedNodes, key=lambda node: node[1])
        #self.preferedNodes.pop(0)

class newNetObjContainer():
    
    def __init__(self, newJuncData, num_edges, L):
        self.maxEdgeLength = L
        self.nodeContainer = {}
        self.edgeContainer = []
        self.tupleNodes = []
        self.listOfNodes = []
        self.unnattachedEdges = 0
        self.desiredEdges = num_edges
        
        for junc in newJuncData:
            self.addNewNodeObj(junc,newJuncData[junc]["x"],newJuncData[junc]["y"])
            self.tupleNodes.append((junc, newJuncData[junc]["x"],newJuncData[junc]["y"]))
            
        for node in self.nodeContainer:
            self.nodeContainer[node].preferedNodesCreator(self.nodeContainer, L)
            if self.nodeContainer[node].preferedNodes:
                self.listOfNodes.append(self.nodeContainer[node].id)
            print(self.nodeContainer[node].preferedNodes)
        
        print(self.listOfNodes)
        
        
    def addNewNodeObj(self, id, x, y):
        self.nodeContainer.update({id:newNodeObj(id, x, y)})
        
    def checkEdgeIntersection(self, edge_proposed):
        
        # True/False response to be returned by the function
        conflict = False
        
        # Extract the nodes which form the edge being checked    
        node_a1 = edge_proposed[0]
        node_a2 = edge_proposed[1]
        
        # New edge co-ordinates
        x_a1 = self.nodeContainer[node_a1].x
        y_a1 = self.nodeContainer[node_a1].y
        
        x_a2 = self.nodeContainer[node_a2].x
        y_a2 = self.nodeContainer[node_a2].y
        
        # If x_a1 == x_a2, then we have a vertical line with an infinite gradient
        if x_a1 == x_a2:
            
            # To check this vertical line against all other lines we set constant c_a equal to x_a1 (= x_a2)
            c_a = x_a1
            
            # We can then analyse for every line in the edge container to see if they intersect this vertical line
            for edge in self.edgeContainer:
                
                # Extract the nodes which form the line being checked
                node_b1 = edge[0]
                node_b2 = edge[1]
                
                # Extract the co-ordinates of the line being checked
                x_b1 = self.nodeContainer[node_b1].x
                y_b1 = self.nodeContainer[node_b1].y

                x_b2 = self.nodeContainer[node_b2].x
                y_b2 = self.nodeContainer[node_b2].y
                
                # Check to see if this is also a vertical line, in which case, they can never cross
                if x_b2 == x_b1:
                    None
                
                # If the line is not vertical, find the equation of the line being checked (y_b = m_b*x_b + c_b)                
                else:
                    m_b = (y_b2 - y_b1)/(x_b2 - x_b1)
                    c_b = y_b1 - m_b*x_b1
                    
                    # Find the intersection point if the two lines do meet (y* = m_b*c_a + c_b)
                    y_intersect = m_b*c_a + c_b
                    
                    # The lines intersect if BOTH lines pass through the intersection point.
                    # Check if y_intersect lies between the y-coordinates of both nodes. If it lies outside of either line, they cannot conflict.
                    if ((y_a1 < y_intersect < y_a2) or (y_a1 > y_intersect > y_a2)) and ((y_b1 < y_intersect < y_b2) or (y_b1 > y_intersect > y_b2)):
                        # If this condition holds, we have a conflict and the edge should not be included
                        conflict = True
        
        # If the first line was not vertical, so we find the equation of this line
        else:
            
            m_a = (y_a2 - y_a1)/(x_a2 - x_a1) # New edge gradient
            c_a = y_a1 - m_a*x_a1 # New edge y-intersect
        
            # Check against every edge currently in the system
            for edge in self.edgeContainer:
                
                # Extract the nodes which form the edge to be checked
                node_b1 = edge[0]
                node_b2 = edge[1]
                
                # Extract node coordinates
                x_b1 = self.nodeContainer[node_b1].x
                y_b1 = self.nodeContainer[node_b1].y

                x_b2 = self.nodeContainer[node_b2].x
                y_b2 = self.nodeContainer[node_b2].y
                
                # If x_b1 == x_b2 then this edge is a vertical line
                if x_b1 == x_b2:
                
                    # Set c_b = x_b1 as it is a constant
                    c_b = x_b1
                    
                    # Calculate the y-coordinate at which the lines would intersect
                    y_intersect = m_a*c_b + c_a
                    
                    # The lines intersect if BOTH lines pass through the intersection point.
                    # Check if y_intersect lies between the y-coordinates of both nodes. If it lies outside of either line, they cannot conflict.
                    if ((y_a1 < y_intersect < y_a2) or (y_a1 > y_intersect > y_a2)) and ((y_b1 < y_intersect < y_b2) or (y_b1 > y_intersect > y_b2)):
                        conflict = True
                
                # In this case, neither line is vertical. We can continue checking intersection the usual fashion, using the equations for both lines
                else:
                    
                    m_b = (y_b2 - y_b1)/(x_b2 - x_b1)
                    c_b = y_b1 - m_b*x_b1
                    
                    # If the lines are parallel, they cannot intersect assuming they do not lie on the same constant (incl. if the gradient is 0 for both and the lines are horizontal)
                    if m_a == m_b:
                        # Check to see if the lines have the exactsame equation, in which case we should check to see if they overlap
                        if (c_a == c_b):
                            # See if either line has one of its nodes lying within the other line (only needs to be checked for one line)
                            if (x_a1 < x_b1 < x_a2) or (x_a1 > x_b1 > x_a2) or (x_a1 < x_b2 < x_a2) or (x_a1 > x_b2 > x_a2):
                                conflict = True                           
                    
                    # If the lines are not parallel, we need to check if both lines cross the intersection point. We can calculate this. 
                    else:
                        
                        x_intersect = (c_b - c_a)/(m_a - m_b)
                        
                        if ((x_a1 < x_intersect < x_a2) or (x_a1 > x_intersect > x_a2)) and ((x_b1 < x_intersect < x_b2) or (x_b1 > x_intersect > x_b2)):
                            conflict = True
                        
            return conflict
    
    def checkNodeIntersection(self, edge_proposed):
        
        conflict = False
        
        node_1 = edge_proposed[0]
        node_2 = edge_proposed[1]
        
        # New edge properties
        x_1 = self.nodeContainer[node_1].x
        y_1 = self.nodeContainer[node_1].y
        
        x_2 = self.nodeContainer[node_2].x
        y_2 = self.nodeContainer[node_2].y
        
        if x_1 == x_2:
            
            for node in self.nodeContainer:
            
                x_node = self.nodeContainer[node].x
                y_node = self.nodeContainer[node].y
            
                x_edge = x_1
                
                if x_node == x_edge:
                    if node == node_1:
                        conflic = False
                    elif node == node_2:
                        conflict = False
                    else:
                       conflict = True
                       #print("Edge from %s to %s conflicts with node at (%d, %d)" % (node_1, node_2, x_node, y_node))                
                else:
                    None
                    
        else:
            m = (y_2 - y_1)/(x_2 - x_1) # New edge gradient    
            c = y_1 - m*x_1 # New edge y-intersect
            
            for node in self.nodeContainer:
                
                x_node = self.nodeContainer[node].x
                y_node = self.nodeContainer[node].y
            
                y_edge = m*x_node
                
                if (y_node == y_edge) and ((y_1 < y_node and y_2 > y_node) or (y_1 > y_node and y_2 < y_node)):
                    conflict = True
                   # print("Edge from %s to %s conflicts with node at (%d, %d)" % (node_1, node_2, x_node, y_node))
                else:
                    None
                
        return conflict
        
    def refreshTupleNodes(self):
        
        newTupleNodes = []
        
        for node in self.nodeContainer:
            id = self.nodeContainer[node].id
            x = self.nodeContainer[node].x
            y = self.nodeContainer[node].y
            preferedNodes = self.nodeContainer[node].preferedNodes
            remainingNodes = self.nodeContainer[node].remainingEdges
        
            if preferedNodes and remainingNodes:
                newTupleNodes.append((id, x, y, remainingNodes))
        
        self.tupleNodes = newTupleNodes
        
    
    def checkDegreeIncreaseProb(self, proposed_edge):
        
        node_1 = proposed_edge[0]
        node_2 = proposed_edge[1]
        addEdge = False

        degree_1 = self.nodeContainer[node_1].degree
        degree_2 = self.nodeContainer[node_2].degree
        
        try:
            degreeIncreaseProb = 1/((degree_1**2)*(degree_2**2))
        except ZeroDivisionError:
            degreeIncreaseProb = 1
            
        randomInt = random.random()
        if randomInt < degreeIncreaseProb: addEdge = True         
        
        return addEdge
            
        
    def firstPass(self):
        
        nodes = self.listOfNodes[:]
        
        while nodes:
        
            node_1 = nodes[0]
            
            [node_2, distance] = self.nodeContainer[node_1].preferedNodes.pop()
            if not(self.nodeContainer[node_1].preferedNodes):
                self.listOfNodes.pop(0)
                nodes.pop(0)
            
            proposed_edge = [node_1, node_2]
            reverse_edge = [node_2, node_1]
    
            if proposed_edge not in self.edgeContainer:        
                if not self.checkEdgeIntersection(proposed_edge):
                    #if not self.checkNodeIntersection(proposed_edge):
                    self.nodeContainer[node_1].degreeIncrement()
                    self.nodeContainer[node_2].degreeIncrement()
                    self.edgeContainer.append(proposed_edge)
                    self.edgeContainer.append(reverse_edge)
                    self.nodeContainer[node_1].addNeighbour(node_2)
                    self.nodeContainer[node_2].addNeighbour(node_1)
                    
                    nodes.pop(0)
                    
                    print("Edge from %s to %s, of length %d" % (node_1, node_2, distance))
    
    def createEdge(self):
        
        random.shuffle(self.listOfNodes)
        #print(self.listOfNodes)
        
        node_1 = False
        node_2 = False
        
        while not(node_2):
            try: 
                node_1 = self.listOfNodes[0]
            except IndexError:
                break
            try:
                [node_2, distance] = self.nodeContainer[node_1].preferedNodes.pop()
            except IndexError:
                self.listOfNodes.pop(0)
        
        if node_1 and node_2:
        
            proposed_edge = [node_1, node_2]
            reverse_edge = [node_2, node_1]
    
            if proposed_edge not in self.edgeContainer:        
                if not self.checkEdgeIntersection(proposed_edge):
                    if self.checkDegreeIncreaseProb(proposed_edge):
                    #if not self.checkNodeIntersection(proposed_edge):
                        self.nodeContainer[node_1].degreeIncrement()
                        self.nodeContainer[node_2].degreeIncrement()
                        self.edgeContainer.append(proposed_edge)
                        self.edgeContainer.append(reverse_edge)
                        self.nodeContainer[node_1].addNeighbour(node_2)
                        self.nodeContainer[node_2].addNeighbour(node_1)
                
                        print("Edge from %s to %s, of length %d" % (node_1, node_2, distance))            
    
    def addAllEdges(self):
        
        self.firstPass()
        

        while (len(self.edgeContainer) < self.desiredEdges):

            while self.listOfNodes:
                            
            #for node in self.nodeContainer:
                #print(self.nodeContainer[node].preferedNodes)
                self.createEdge()
            
            self.maxEdgeLength*=1.5
            for node in self.nodeContainer:
                self.listOfNodes.append(node)
                self.nodeContainer[node].preferedNodesCreator(self.nodeContainer, self.maxEdgeLength)
            
            
            #print(self.edgeContainer)

def main(seed_identifer, output_identifier, grid_spacing=25, node_joining_radius=150, directory=os.environ['DIRECTORY_PATH']):
        
    # Load the edge and junc containers of the original seed net
    edgeobj_file = ("%s/netObjects/%s_edgeContainer" % (directory, seed_identifer))
    juncobj_file = ("%s/netObjects/%s_juncContainer" % (directory, seed_identifer))
    
    edgeContainer = pickleFunc.load_obj(edgeobj_file)
    juncContainer = pickleFunc.load_obj(juncobj_file)         
    
    # Define the path to the new node, edge and net files for the scalefree graph. The gexf file allows for checking of the network in force atlas.
    node_filepath = ("%s/netXMLFiles/%s.nod.xml" % (directory, output_identifier))
    edge_filepath = ("%s/netXMLFiles/%s.edg.xml" % (directory, output_identifier))
    net_filepath = ("%s/netXMLFiles/%s.net.xml" % (directory, output_identifier))
    gexf_filepath = ("%s/netXMLFiles/%s.gexf" % (directory, output_identifier))
    
    newJuncData = {} # This will be updated with a dictionary for each adjusted node {ID: x, y}
    old_layout = [] # Seed net junction co-ordinates
    new_layout = [] # Adjusted co-ordinates for the scalefree net
    
    # Add all junc co-ordinates to old_layout array
    for junc in juncContainer.container:
        x = juncContainer.container[junc].x
        y = juncContainer.container[junc].y
        point = [x,y]
        old_layout.append(point)    
    
    #  For each junction in the junction container, adjust the co-ordiantes by a random number between 0 and grid_spacing in any direction, Append result to a dictionary.
    for junc in juncContainer.container:
    
        x_change = random.randint(-grid_spacing, grid_spacing)
        y_change = random.randint(-grid_spacing, grid_spacing)
        
        current_x = juncContainer.container[junc].x
        current_y = juncContainer.container[junc].y
        
        new_x = current_x + x_change
        new_y = current_y + y_change
        
        newJuncData.update({junc:{"x" : new_x, "y" :new_y}})
        new_layout.append([new_x, new_y])
    
    junc_array_index_to_junc_ID = {}
    index = 0
    for junc in juncContainer.container:
        junc_array_index_to_junc_ID.update({junc:index})
        index += 1
    
    # Count the number of edges
    num_juncs = index
    index = 0
    for edge in edgeContainer.container:
        index += 1
    num_edges = index
    
    # Create arrays to store the degree of all junctions, and the number of edges left to assign to the network
    junc_degree = []
    edges_left = num_edges
    
    # Give all junctions at least a degree of 1
    for ii in range(0,num_juncs):
        junc_degree.append(2)
        edges_left -= 1
    
    # Create a new net object container. Run .addAllEdges() to assign the rest of the edges in a scale free distribution
    netContainer = newNetObjContainer(newJuncData, num_edges, node_joining_radius)
    netContainer.addAllEdges()
    
    # Open the new edge file to print with the new edge details
    EDGEFILE = open(edge_filepath, 'w')
    
    print("<edges>", file=EDGEFILE)
    
    for edge in netContainer.edgeContainer:
        frm = edge[0]
        to = edge[1]
        print('<edge id="%sto%s" from="%s" to="%s" priority="-1"/>' % (frm,to,frm,to), file=EDGEFILE)
            
    print("</edges>", file=EDGEFILE)
    
    EDGEFILE.close()
    
    # Open the new node file to print with new node details
    NODEFILE = open(node_filepath, "w")
    
    print("<nodes>", file=NODEFILE)
    
    for node in netContainer.nodeContainer:
        id = netContainer.nodeContainer[node].id
        x = netContainer.nodeContainer[node].x
        y = netContainer.nodeContainer[node].y
        print('\t<node id="%s" x="%d" y="%d" type="priority"/>' % (id,x,y), file=NODEFILE)
                
    print("</nodes>", file=NODEFILE)
    
    NODEFILE.close()
    
    # Open and print details to a gexf file
    GEXFFILE = open(gexf_filepath, 'w')
    
    print('<?xml version="1.0" encoding="UTF-8"?>', file=GEXFFILE)
    print('<gexf xmlns="http://www.gexf.net/1.2draft" version="1.2">', file=GEXFFILE)
    print('\t<meta lastmodifieddate="2009-03-20">', file=GEXFFILE)
    print('\t\t<creator>Gexf.net</creator>', file=GEXFFILE)
    print('\t\t<description>A hello world! file</description>', file=GEXFFILE)
    print('\t</meta>', file=GEXFFILE)
    print('\t<graph mode="static" defaultedgetype="directed">', file=GEXFFILE)
    print('\t\t<nodes>', file=GEXFFILE)
    
    node_counter = 0
    for node in netContainer.nodeContainer:
        id = netContainer.nodeContainer[node].id
        print('\t\t\t<node id="%s" label="%s" />' % (id, id), file=GEXFFILE)
        node_counter += 1
        
    print('\t\t</nodes>', file=GEXFFILE)
    print('\t\t<edges>', file=GEXFFILE)
    
    edge_counter = 0
    for edge in netContainer.edgeContainer:
        frm = edge[0]
        to = edge[1]
        print('\t\t\t<edge id="%sto%s" source="%s" target="%s" />' % (frm,to,frm,to), file=GEXFFILE)
    
    print('\t\t</edges>', file=GEXFFILE)
    print('\t</graph>', file=GEXFFILE)
    print('</gexf>', file=GEXFFILE)
    
    # Use netconvert to generate the network    
    netconvertCommand = ("%s -n %s -e %s -o %s --lefthand --geometry.remove --roundabouts.guess --ramps.guess --junctions.join --tls.guess-signals --tls.discard-simple --tls.join" 
                         % (os.environ['NETCONVERT_BINARY'], node_filepath, edge_filepath, net_filepath))
    netconvertProcess = subprocess.Popen(netconvertCommand, shell=True, stdout=sys.stdout, stderr=sys.stderr)
    netconvertProcess.wait()

if __name__ == "__main__":
    os.environ['NETCONVERT_BINARY'] = '/usr/local/bin/netconvert'
    main("Grid-10x10", "Scalefree-10x10", grid_spacing=0, node_joining_radius=150, directory="/Users/tb7554/UniversityCloud/Home/workspace/_009_Grid-10x10_")