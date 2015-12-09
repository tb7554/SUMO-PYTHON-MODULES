'''
Created on 9 Dec 2015

@author: tb7554
'''

from __future__ import division
import numpy as np

def networkCV(nodeContainer):
    
    degrees = []
    
    for node in nodeContainer.container:
        degrees.append(len(nodeContainer.container[node].children))
        
    mean = np.mean(degrees)
    std = np.std(degrees)
    cv = std/mean
    
    print(mean, std, cv)
    
    return cv