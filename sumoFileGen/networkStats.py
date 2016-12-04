'''
Created on 9 Dec 2015

@author: tb7554
'''

from __future__ import division
import numpy as np
from tools.sumolib import net

def networkCV(nodeContainer):
    
    degrees = []
    
    for node in nodeContainer.container:
        degrees.append(len(nodeContainer.container[node].children))
        
    mean = np.mean(degrees)
    std = np.std(degrees)
    cv = std/mean
    
    print(mean, std, cv)
    
    return cv

class netStatsClass:
    
    def __init__(self, netfile_filepath):
        self._net = net.readNet(netfile_filepath)
        self._edges = self._net.getEdges()
        self._nodes = self._net.getNodes()
        
        self.edgeInOutDegrees()
        self.calcEdgeMeanDegree()
        self.calcEdgeCV()

        self.nodeInOutDegrees()
        self.calcNodeMeanDegree()
        self.calcNodeCV()

        self.printStats()
    
    def edgeInOutDegrees(self):
        
        self._edgeInDegrees = []
        self._edgeOutDegrees = []
        self._edgeDegrees = []
        
        for edge in self._edges:
            
            self._edgeDegrees.append(len(edge.getIncoming()) + len(edge.getOutgoing()))
            self._edgeInDegrees.append(len(edge.getIncoming()))
            self._edgeOutDegrees.append(len(edge.getOutgoing()))
            
    def calcEdgeMeanDegree(self):
        self._edgeInMeanDegree = np.mean(self._edgeInDegrees)
        self._edgeOutMeanDegree = np.mean(self._edgeOutDegrees)
        self._edgeMeanDegree = np.mean(self._edgeDegrees)
    
    def calcEdgeCV(self):
        
        self._edgeInCV = np.std(self._edgeInDegrees)/np.mean(self._edgeInDegrees)
        self._edgeOutCV = np.std(self._edgeOutDegrees)/np.mean(self._edgeOutDegrees)
        self._edgeCV = np.std(self._edgeDegrees)/np.mean(self._edgeDegrees)

    def nodeInOutDegrees(self):
        
        self._nodeInDegrees = []
        self._nodeOutDegrees = []
        self._nodeDegrees = []
        
        for node in self._nodes:
            self._nodeDegrees.append((len(node.getIncoming()) + len(node.getOutgoing()))/2)
            self._nodeInDegrees.append(len(node.getIncoming()))
            self._nodeOutDegrees.append(len(node.getOutgoing()))

    def calcNodeMeanDegree(self):
        self._nodeInMeanDegree = np.mean(self._nodeInDegrees)
        self._nodeOutMeanDegree = np.mean(self._nodeOutDegrees)
        self._nodeMeanDegree = np.mean(self._nodeDegrees)
        
    def calcNodeCV(self):
        
        self._nodeInCV = np.std(self._nodeInDegrees)/np.mean(self._nodeInDegrees)
        self._nodeOutCV = np.std(self._nodeOutDegrees)/np.mean(self._nodeOutDegrees)
        self._nodeCV = np.std(self._nodeDegrees)/np.mean(self._nodeDegrees)
        
    def printStats(self):
        
        print("Number of Nodes = %d\nNumber of Edges = %d" % (len(self._nodes), len(self._edges)))
        
        print("Edge Degrees\nIn mean: %.3f \nIn CV: %.3f \nOut mean: %.3f \nOut CV: %.3f \nMean: %.3f \nCV: %.3f" % 
              (self._edgeInMeanDegree, self._edgeInCV, self._edgeOutMeanDegree, self._edgeOutCV, self._edgeMeanDegree, self._edgeCV))
                            
        print("Node Degrees\nIn mean: %.3f \nIn CV: %.3f \nOut mean: %.3f \nOut CV: %.3f \nMean: %.3f \nCV: %.3f" % 
              (self._nodeInMeanDegree, self._nodeInCV, self._nodeOutMeanDegree, self._nodeOutCV, self._nodeMeanDegree, self._nodeCV))


if __name__ == "__main__":
    
    netStatsCalculator = netStatsClass("/Users/tb7554/PyCharmProjects/NetworkRestructuring/Smallworld-1-Lane-TLS.net.xml")
    netStatsCalculator.printStats()