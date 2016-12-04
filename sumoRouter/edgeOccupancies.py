'''
Created on 11 Dec 2015

@author: tb7554
'''
from __future__ import division
import traci
import numpy as np


class edgeOccupanciesClass:
    def __init__(self, sumolibnet):
        self._net = sumolibnet
        self._edges = sumolibnet.getEdges()
        self._edgeOccupancies = {}
        self._edgeCriticalOccupancies = {}
        self._edgeLengths = {}
        self._shortEdges = []
        self._edgesDownstream = {}

        self.storeEdgeLengthsAndDownstreamEdges(minDistance=20)
        for edge in self._edges:
            self.storeEdgeCriticalOccupancy(edge.getID(), 0.2)

    def getEdges(self):
        return self._edges

    def calcEdgeOccupancy(self, edge):
        """ gets average of all lane occupancies for an edge """

        if edge.getID() in self._shortEdges:
            occ = self.calcEdgeOccupancyForMinDistance(edge.getID())
        else:
            occ = 0
            lanes = edge.getLanes()
            numlanes = len(lanes)
            for l in lanes:
                occ += traci.lane.getLastStepOccupancy(l.getID())
            occ /= numlanes

        self._edgeOccupancies[edge.getID()] = occ

    def calcEdgeOccupancyForMinDistance(self, edgeID):
        downstream = self._edgesDownstream[edgeID]
        occs = []
        lengths = []
        occs.append(self.getEdgeLengthByID(edgeID))
        lengths.append(self.getEdgeLengthByID(edgeID))

        for e in downstream:
            occs.append(self.getEdgeOccupancyByID(e))
            lengths.append(self.getEdgeLengthByID(e))
        total_length = np.sum(lengths)

        mean_occ = 0

        for ii in range(0, len(occs)):
            mean_occ += occs[ii] * (lengths[ii] / total_length)

        return mean_occ

    def updateAllEdgeOccupancies(self):
        """ updates the occupancies for all edges, recalculates occupancies for any edges found to be shorter than a minimum specified length """
        map(self.calcEdgeOccupancy, self._edges)
        map(self.calcEdgeOccupancyForMinDistance, self._shortEdges)

    def getEdgeOccupancyByID(self, edgeID):
        return self._edgeOccupancies[edgeID]

    def getEdgeCriticalOccupancyByID(self, edgeID):
        return self._edgeCriticalOccupancies[edgeID]

    def storeEdgeLengthsAndDownstreamEdges(self, minDistance=10, stopOnTLS=True):
        for edge in self._edges:
            self._edgeLengths.update({edge.getID(): edge._length})

            if edge._length < minDistance: self._shortEdges.append(edge.getID())

            self._edgesDownstream.update({edge.getID(): []})

            downstream = self._net.getDownstreamEdges(edge, minDistance, stopOnTLS)
            for e in downstream:
                self._edgesDownstream[edge.getID()].append(e[0].getID())

    def storeEdgeCriticalOccupancy(self, edgeID, criticalOccupancy):
        self._edgeCriticalOccupancies.update({edgeID: criticalOccupancy})

    def getEdgeLengthByID(self, edgeID):
        return self._edgeLengths[edgeID]

    def getShortEdges(self):
        return self._shortEdges

    def getEdgeOccupancies(self):
        return self._edgeOccupancies
            
    