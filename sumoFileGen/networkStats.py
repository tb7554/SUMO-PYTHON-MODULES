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
        
        
        
        self.printStats()
    
    def edgeInOutDegrees(self):
        
        self._edgeInDegrees = []
        self._edgeOutDegrees = []
        
        for edge in self._edges:
            
            self._edgeInDegrees.append(len(edge.getIncoming()))
            self._edgeOutDegrees.append(len(edge.getOutgoing()))
            
        self._edgeDegrees = []
        self._edgeDegrees.extend(self._edgeInDegrees)
        self._edgeDegrees.extend(self._edgeOutDegrees)
            
    def calcEdgeMeanDegree(self):
        self._edgeInMeanDegree = np.mean(self._edgeInDegrees)
        self._edgeOutMeanDegree = np.mean(self._edgeOutDegrees)
        self._edgeMeanDegree = np.mean(self._edgeDegrees)
    
    def calcEdgeCV(self):
        
        self._edgeInCV = np.std(self._edgeInDegrees)/np.mean(self._edgeInDegrees)
        self._edgeoutCV = np.std(self._edgeOutDegrees)/np.mean(self._edgeOutDegrees)
        self._CV = np.std(self._edgeDegrees)/np.mean(self._edgeDegrees)
        
    def nodeInOutDegrees(self):
        
        self._nodeInDegrees = []
        self._nodeOutDegrees = []
        
        for node in self._nodes:
            self._nodeInDegrees.append(node.getIncoming())
            self._nodeOutDegrees.append(node.getOutgoing())
            
        self._nodeDegrees = []
        self._nodeDegrees.extend(self._nodeInDegrees)
        self._nodeDegrees.extend(self._nodeOutDegrees)

    def calcNodeMeanDegree(self):
        self._nodeInnMeanDegree = np.mean(self._nodeInDegrees)
        self._nodeOutMeanDegree = np.mean(self._nodeOutDegrees)
        self._nodeMeanDegree = np.mean(self._nodeDegrees)
        
    def calcNodeCV(self):
        
        self._inCV = np.std(self._edgeInDegrees)/np.mean(self._edgeInDegrees)
        self._outCV = np.std(self._edgeOutDegrees)/np.mean(self._edgeOutDegrees)
        self._CV = np.std(self._edgeDegrees)/np.mean(self._edgeDegrees)
        
    def printStats(self):
        
        print("Edge Degress\nIn mean: %.3f \nIn CV: %.3f \nOut mean: %.3f \nOut CV: %.3f \nMean: %.3f \nCV: %.3f" % 
              (self._edgeInMeanDegree, self._inCV, self._edgeOutMeanDegree, self._outCV, self._edgeMeanDegree, self._CV))
                            

if __name__ == "__main__":
    
    netStatsCalculator = netStatsClass("/Users/tb7554/workspace/_013_Bristol_2/netXMLFiles/Bristol.net.xml")
    
    netStatsCalculator.printStats()