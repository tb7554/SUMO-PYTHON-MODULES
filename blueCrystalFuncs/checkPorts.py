# #!/usr/bin/env python
"""
@file   checkPorts.py
@author  Tim Barker
@date    10/07/2015

Checks if a port is free for use with the SUMO Traci API

"""

import socket

def getOpenPort():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("",0))
    s.listen(1)
    port = s.getsockname()[1]
    s.close()
    return port

def main():
    for ii in range(0,10):
        port = getOpenPort()
        print(port)
    
if __name__ == "__main__":
    main()