function setProgram(tlsID, programID)
%setProgram
%   setProgram(TLSID,PROGRAMID)Sets the id of the current program.

%   Copyright 2015 Universidad Nacional de Colombia,
%   Politecnico Jaime Isaza Cadavid.
%   Authors: Andres Acosta, Jairo Espinosa, Jorge Espinosa.
%   $Id: setProgram.m 20 2015-03-02 16:52:32Z afacostag $

import traci.constants
traci.sendStringCmd(constants.CMD_SET_TL_VARIABLE,...
    constants.TL_PROGRAM, tlsID, programID);