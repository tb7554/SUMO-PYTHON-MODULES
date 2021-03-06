function setColor(poiID, color)
%setColor
%   setColor(POIID,COLOR) Sets the rgba color of the poi. COLOR is a
%   four-element vector whose elements range from 0 to 255, they represent
%   the R, G, B and Alpha (unused) components of the color.

%   Copyright 2015 Universidad Nacional de Colombia,
%   Politecnico Jaime Isaza Cadavid.
%   Authors: Andres Acosta, Jairo Espinosa, Jorge Espinosa.
%   $Id: setColor.m 20 2015-03-02 16:52:32Z afacostag $

import traci.constants
global message
traci.beginMessage(constants.CMD_SET_POI_VARIABLE, constants.VAR_COLOR, poiID, 1+1+1+1+1);
message.string = [message.string uint8([sscanf(constants.TYPE_COLOR,'%x') color])];
traci.sendExact();