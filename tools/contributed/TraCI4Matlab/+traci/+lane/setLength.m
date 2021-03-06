function setLength(laneID, len)
%setLength
%   setLength(LANEID,LENGTH) Sets the length of the lane in m.

%   Copyright 2015 Universidad Nacional de Colombia,
%   Politecnico Jaime Isaza Cadavid.
%   Authors: Andres Acosta, Jairo Espinosa, Jorge Espinosa.
%   $Id: setLength.m 20 2015-03-02 16:52:32Z afacostag $

import traci.constants
traci.sendDoubleCmd(constants.CMD_SET_LANE_VARIABLE, constants.VAR_LENGTH, laneID, len)