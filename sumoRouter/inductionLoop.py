'''
Created on 3 Feb 2016

@author: tb7554
'''

class inductionLoopClass():
    '''
    Class for individual inductance loop
    '''

    def __init__(self, ILid, lane, pos, freq):
        '''
        Constructor
        '''
        self._id = ILid
        self._lane = lane
        self._pos = pos
        self._freq = freq
        
    def getID(self):
        return self._id
    
    def getLane(self):
        return self._lane
    
    def getPos(self):
        return self._pos
    
    def getFreq(self):
        return self._freq
        
class inductionLoopContainerClass():
    '''
    Class for a collection of inductance loops
    '''
    
    def __init__(self):
        
        self._ILs = []
        self._id2IL = {}
        self._ids = []
    
    def addIL(self, ILid, lane, pos, freq):
        IL = inductionLoopClass(ILid, lane, pos, freq)
        self._ILs.append(IL)
        self._id2IL.update({ILid:IL})
        self._ids.append(ILid)
        
    def getAllIL(self):
        return self._ILs
      
    def getIL(self, ILid):
        return self._id2IL[ILid]
    
    def getILids(self):
        return self._ids
    
    
        