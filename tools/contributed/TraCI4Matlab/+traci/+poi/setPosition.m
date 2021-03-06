function setPosition(poiID, x, y)
%setPosition
%   setPosition(POIID,X,Y) Sets the position coordinates of the poi.

%   Copyright 2015 Universidad Nacional de Colombia,
%   Politecnico Jaime Isaza Cadavid.
%   Authors: Andres Acosta, Jairo Espinosa, Jorge Espinosa.
%   $Id: setPosition.m 20 2015-03-02 16:52:32Z afacostag $

import traci.constants
global message
traci.beginMessage(constants.CMD_SET_POI_VARIABLE, constants.VAR_POSITION, poiID, 1+8+8);
message.string = [message.string uint8(sscanf(constants.POSITION_2D,'%x')) traci.packInt64([y x])];
traci.sendExact();