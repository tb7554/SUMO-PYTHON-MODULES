function setVehicleClass(typeID, clazz)
%setVehicleClass
%   setVehicleClass(TYPEID,CLASS) Sets the class of vehicles of this type.

%   Copyright 2015 Universidad Nacional de Colombia,
%   Politecnico Jaime Isaza Cadavid.
%   Authors: Andres Acosta, Jairo Espinosa, Jorge Espinosa.
%   $Id: setVehicleClass.m 20 2015-03-02 16:52:32Z afacostag $

import traci.constants
traci.sendStringCmd(constants.CMD_SET_VEHICLETYPE_VARIABLE, constants.VAR_VEHICLECLASS, typeID, clazz);