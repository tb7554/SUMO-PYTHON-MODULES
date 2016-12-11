# -*- coding: UTF-8 -*-
from __future__ import print_function, division
import numpy as np
from collections import defaultdict, Counter
import traci
import random
import tls_logic

class IntersectionController:
    def __init__(self, tls_id, inc_lanes_by_index, out_lanes_by_index, phase_matrix_by_link_index,
                 phase_strings, x_star, greenTimeController, queueController, link_index_to_turning_direction,
                 in_lane_and_out_edge_to_link_index, default_amber_phase_length, sim_step_length = 0.1,
                 time_window_for_mu_and_lambda = 600):
        """ Class which controls the lights at each intersection. This class keps track of properties such as
        the time elapsed since the last phase. The algorithm for determining green times and queues will be defined
        elsewhere and called by this function, in order to make it easy to switch algorithms """

        # Static properties of the intersection
        self._id = tls_id # id of the intersectoin controller
        self._num_queues = len(inc_lanes_by_index)  # The number of queues at this intersection (i.e. the number of combinations of in queue and out queue)

        self._incoming_lanes = set(inc_lanes_by_index) # The incoming lanes of this intersection
        self._incoming_lanes_by_index = inc_lanes_by_index # The outgoing lanes of this intersection
        self._indicies_by_incoming_lane = dict([(current_lane , [index for index, lane in enumerate(inc_lanes_by_index) if lane == current_lane])
                                                for current_lane in set(inc_lanes_by_index)])

        self._outgoing_lanes = set(out_lanes_by_index)
        self._outgoing_lanes_by_index = out_lanes_by_index
        self._indicies_by_outgoing_lane = dict([(current_lane, [index for index, lane in enumerate(out_lanes_by_index) if lane == current_lane])
                                                for current_lane in set(out_lanes_by_index)])

        self._link_index_to_turning_direction = link_index_to_turning_direction
        self._in_lane_and_out_edge_to_link_index = in_lane_and_out_edge_to_link_index

        self._default_amber_phase_length = default_amber_phase_length

        # These are the matrix L representations
        self._phase_matrix_by_link_index = np.array(phase_matrix_by_link_index) # Possible queue combinations for different phases
        #self._phase_matrix_by_lane = phase_matrix_by_lane
        self._phase_strings = phase_strings # Strings representing the light settings of each phase

        # Current values for dynamic properties
        self._current_phase_index = 0

        self._current_open_queues = self._phase_matrix_by_link_index[self._current_phase_index]
        self._current_open_indexes = np.nonzero(self._current_open_queues)[0]
        self._current_open_lanes = set([self._incoming_lanes_by_index[index] for index in self._current_open_indexes])
        self._current_phase_string = "".join(self._phase_strings[0])  # Initialise light settings as all red (will change in the first step of the simulation

        # Values to track important variables and state changes
        self._green_timer = greenTimeController.get_initial_green_time()  # Elapsed time since last phase
        self._amber_timer = 0
        self._state = False  # True means green state, False means amber state
        #self._queue_green_times = [greenTimeController.get_initial_green_time()] * self._num_queues
        self._phase_green_times = [greenTimeController.get_initial_green_time()] * len(self._phase_matrix_by_link_index)
        self._next_green_string = "".join(random.choice(self._phase_strings)) # Choose the initial green string at random

        self._queue_lengths_by_link_index = [0] * self._num_queues  #  The queue length for each index
        self._outgoing_lanes_queues_by_link_index = [0] * self._num_queues
        self._outgoing_lane_capacities_by_link_index = [999] * self._num_queues  # The capacity of the links each queue wishes to join

        # Algorithms used for picking queues and calculating green time
        self._timerControl = greenTimeController
        self._queueControl = queueController

        self._proportion_of_vehicles_to_remove = x_star # Proportion of vehicles to remove

        self._number_of_vehicles_to_remove_by_link_index = [0] * self._num_queues # Number of vehilces

        self._vehicles_to_remove_this_time_step_value_for_green_time_calculation = 0
        self._vehicles_removed_value_for_green_time_calculation = 0

        self._number_of_vehicles_to_remove_by_lane = defaultdict()

        self._vehicles_leaving_lane_per_time_step = defaultdict(list)
        self._vehicles_entering_lane_per_time_step = defaultdict(list)

        self._vehicles_at_start_of_timestep = defaultdict(list)
        self._vehicles_at_end_of_timestep = defaultdict(list)

        # Model based controller values
        self._sim_step_length = sim_step_length
        self._time_window_for_mu_and_lambda = time_window_for_mu_and_lambda
        self._step_window_for_mu_and_lambda = (1 / sim_step_length) * time_window_for_mu_and_lambda

        self._mu = defaultdict(int)
        self._lambda = defaultdict(int)

        # self._mu_G_minute = mus[0] # mean car exit rate
        # self._lambda_G_minute = lams[0] # mean car entry rate
        # self._mu_G_hour = mus[1]  # mean car exit rate
        # self._lambda_G_hour = lams[1]  # mean car entry rate
        # self._mu_G_year = mus[2]
        # self._lambda_G_year = lams[2]

        # Output
        self._OUTPUT_green_time_change_step = defaultdict(list)
        self._OUTPUT_green_time_setting = defaultdict(list)

    # Set property commands
    def set_queue_length_by_link_index(self, index, value):
        self._queue_lengths_by_link_index[index] = value

    def set_vehs_in_lane_at_start_of_step(self, lane, vehList):
        self._vehicles_at_start_of_timestep[lane] = vehList

    def set_vehs_in_lane_at_end_of_step(self, lane, vehList):
        self._vehicles_at_end_of_timestep[lane] = vehList

    def update_green_time_records_by_link_index(self, index, timeStep, Gt):
        lane = self.get_incoming_lane_from_index(index)

        self._OUTPUT_green_time_change_step[lane].append(timeStep)
        self._OUTPUT_green_time_setting[lane].append(Gt)

    def setCongestedLanes2Red(self):
        for ii in range(self._num_queues):
            if self._outgoing_lane_capacities_by_link_index[ii] < 1:
                self._next_green_string = self.set_queue_to_red(ii, self._next_green_string)

    def set_queue_to_red(self, queue, TLstring):
        TLstring = list(TLstring)
        TLstring[queue] = 'r'
        return "".join(TLstring)

    def set_queue_to_green(self, queue, TLstring):
        TLstring = list(TLstring)
        TLstring[queue] = 'g'
        return "".join(TLstring)

    # Main logic for updating the queues and the green time and sending it to SUMO

    def update_queues(self):
        """Updates the length of the queues"""
        link_index_to_queue_length = self.get_queue_length_per_link_index()
        queues = [0] * self._num_queues
        for index, length in link_index_to_queue_length.items():
            queues[index] = length
        self._queue_lengths_by_link_index = queues

    def update_queues_v2(self):
        """Updates the length of the queues using traci"""
        # The length of each queue is just the number of vehicles in it.
        # Get the list of all lanes incoming into the junction
        # For every lane, measure the number of vehicles in the queue
        for lane in self.get_incoming_lanes():
            queue_length = traci.lane.getLastStepVehicleNumber(lane)
            # For every linkIndex assigned to this lane, update link index as follows 'vehicles_in_lane / num_links'
            num_indexes_assigned_to_lane = len(self.get_indicies_of_incoming_lane(lane))
            value = queue_length / num_indexes_assigned_to_lane
            # Input into matrix X
            for index in self.get_indicies_of_incoming_lane(lane):
                self.set_queue_length_by_link_index(index, value)

    def update_capacities(self, min_gap=2.5):
        """Updates self._Cs with the capacity of the outgoing lanes"""
        for lane in self.get_outgoing_lanes_by_index_array():
            vehLength = traci.lane.getLastStepLength(lane)
            if vehLength:
                laneLength = int(traci.lane.getLength(lane))
                vehCount = traci.lane.getLastStepVehicleNumber(lane)
                spaces_total = int(laneLength / (vehLength + min_gap))
            else:
                laneLength = int(traci.lane.getLength(lane))
                vehCount = traci.lane.getLastStepVehicleNumber(lane)
                spaces_total = int(laneLength / (4 + (min_gap)))
            for index in self.get_indicies_of_outgoing_lane(lane):
                self._outgoing_lanes_queues_by_link_index[index] = vehCount
                remaining_capacity = spaces_total - vehCount
                if remaining_capacity < 0 : remaining_capacity = 0
                self._outgoing_lane_capacities_by_link_index[index] = remaining_capacity

    def update_b_compare(self):

        """Updates the actual number of vehicles removed from the queue"""
        # Identify only individual vehicles removed from the queue, that were there at the start
        # Compare the vehicles at the start to the vehicles at the end

        # Initialise a counter

        for lane in self._current_open_lanes:
            # Get the final count (current vehicles in the lane)
            endCount = traci.lane.getLastStepVehicleIDs(lane)
            # Get the number of vehicles at the start of the green time
            startCount = self._vehicles_at_start_of_timestep[lane]

            # if a vehicle there at the start is not longer there, then increase the count by 1
            b_per_step = 0
            lambda_per_step = 0
            for veh in startCount:
                if veh not in endCount:
                    self._vehicles_removed_value_for_green_time_calculation += 1
                    b_per_step += 1

            for veh in endCount:
                if veh not in startCount:
                    lambda_per_step += 1

            self._vehicles_leaving_lane_per_time_step[lane].append(b_per_step)
            if len(self._vehicles_leaving_lane_per_time_step[lane]) > self._step_window_for_mu_and_lambda:
                alpha_mu = self._vehicles_leaving_lane_per_time_step[lane].pop(0)
                omega_mu = b_per_step
                self._mu[lane] = self._mu[lane] + ((omega_mu - alpha_mu) / self._step_window_for_mu_and_lambda)
            else:
                self._mu[lane] = ((len(self._vehicles_leaving_lane_per_time_step[lane]) - 1) /
                                  len(self._vehicles_leaving_lane_per_time_step[lane])) * self._mu[lane] \
                                 + (1 / len(self._vehicles_leaving_lane_per_time_step[lane])) * b_per_step

            self._vehicles_entering_lane_per_time_step[lane].append(lambda_per_step)
            if len(self._vehicles_entering_lane_per_time_step) > self._step_window_for_mu_and_lambda:
                alpha_lam = self._vehicles_entering_lane_per_time_step[lane].pop(0)
                omega_lam = lambda_per_step
                self._lambda[lane] = self._lambda[lane] + ((omega_lam - alpha_lam) / self._step_window_for_mu_and_lambda)
            else:
                self._lambda[lane] = ((len(self._vehicles_entering_lane_per_time_step[lane]) - 1) / len(self._vehicles_entering_lane_per_time_step[lane])) * \
                                     self._lambda[lane] + 1 / len(self._vehicles_entering_lane_per_time_step[lane]) * lambda_per_step

            # Update the list of vehicles at the intersection to be compared next time.
            self._vehicles_at_start_of_timestep[lane] = endCount

    def reset_b(self):
        self._vehicles_removed_value_for_green_time_calculation = 0

    def update_green_time(self, step):
        """Updates the green time for the current queue
        (which will be used next time the queue receives a green light) using the timer algorithm"""
        Gt_new = self._timerControl.get_new_green_time(self)

        # Update the relevant green time
        self._phase_green_times[self._current_phase_index] = Gt_new

    def update_a(self):
        """Updates the target number of vehicles to remove from each queue"""
        # Set A by mapping the array of queues lengths (X) to a function that multiplies it by the fraction reduction
        self._number_of_vehicles_to_remove_by_link_index = (map(lambda x: x * self._proportion_of_vehicles_to_remove, self.get_queues()))
        self._vehicles_to_remove_this_time_step_value_for_green_time_calculation = np.sum(np.multiply(self._number_of_vehicles_to_remove_by_link_index, self._current_open_queues))

    def choose_queues_to_release(self):
        self._current_phase_index = self._queueControl.best_queue_set(self)
        self._current_open_queues = self._phase_matrix_by_link_index[self._current_phase_index]
        self._current_open_indexes = np.nonzero(self._current_open_queues)[0]
        self._current_open_lanes = []
        for index in self._current_open_indexes:
            lane = self.get_incoming_lane_from_index(index)
            if lane not in self._current_open_lanes: self._current_open_lanes.append(lane)

    def set_green_timer(self):
        self._green_timer = self._phase_green_times[self._current_phase_index]

    def set_green_string(self):
        self._next_green_string = "".join(self._phase_strings[self._current_phase_index])

    def set_amber_phase(self):
        """ Sets the intermediate phase between green times. Returns the phase duration and traffic light string. """
        amber_phase = []

        old_phase = list(self._current_phase_string)
        new_phase = list(self._next_green_string)

        if old_phase == new_phase:
            amber_phase_length = 1
            amber_phase = new_phase
        else:
            amber_phase_length = self._default_amber_phase_length
            for ii in range(0, len(old_phase)):
                if old_phase[ii] == 'r' and new_phase[ii] == 'r':
                    amber_phase.append('r')
                elif old_phase[ii] == 'r' and (new_phase[ii] == 'g' or new_phase[ii] == 'G'):
                    amber_phase.append('r')
                elif (old_phase[ii] == 'g' or old_phase[ii] == 'G') and (new_phase[ii] == 'r'):
                    amber_phase.append('y')
                elif (old_phase[ii] == 'g') and (new_phase[ii] == 'g'):
                    amber_phase.append('g')
                elif old_phase[ii] == 'G' and new_phase[ii] == 'G':
                    amber_phase.append('G')
                elif old_phase[ii] == 'g' and new_phase[ii] == 'G':
                    amber_phase.append('g')
                elif old_phase[ii] == 'G' and new_phase[ii] == 'g':
                    amber_phase.append('G')
                else:
                    print("Something wrong in amber phase logic. Old: %s, New: %s" % (old_phase[ii], new_phase[ii]))

        amberPhaseString = "".join(amber_phase)

        self._amber_timer = amber_phase_length
        self._current_phase_string = amberPhaseString

    def send_tls_settings_to_sumo(self):
        traci.trafficlights.setRedYellowGreenState(self._id, self._current_phase_string)

    # Main update function
    def update(self, step, step_length):

        # If the traffic light is in an amber phase and amber timer has reached zero. Go into the green phase.
        if not (self._state) and self._amber_timer <= 0:
            traci.trafficlights.setRedYellowGreenState(self._id, self._next_green_string)
            self._current_phase_string = self._next_green_string
            self._state = True

        # Else if in the amber phase but the amber timer has not reached zero, decrement the amber timer
        elif not (self._state) and self._amber_timer > 0:
            self._amber_timer -= step_length
        # Else if the traffic light is in the green phase and the green timer has reached zero. Update all variables
        # and calculate the new green time and phase. Then switch into the amber phase.
        elif self._state and self._green_timer <= 0:
            # ORDER IS IMPORTANT IN THIS SECTION. DO NOT REORDER WITHOUT FULL UNDERSTANDING OF THE CHANGES TO OBJECT PROPERTIES.
            # Update the queue lengths at each link
            self.update_queues()
            # Update the capacities of each exit lane
            self.update_capacities()
            # Update the number of vehicles which were cleared during the last green phase
            self.update_b_compare()
            # Update the green time for the links used in the last phase
            self.update_green_time(step)
            # Update the time step when the phase was changed
            # self._updateGtRecords_greenTime()
            # self.updateGtRecords_changeStep(step)

            # Update the queues to be set to green in the next phase
            self.choose_queues_to_release()
            # Update the target number of vehicles to be removed during the next phase
            self.update_a()

            # Update the green timer according to the queues to be unlocked
            self.set_green_timer()
            # Update the green string according to the queue
            self.set_green_string()

            # Set queues for which the outgoing lane is congested to red (discontinued due to poor performance)
            # self.setCongestedLanes2Red()   # Turned off the lane closing behaviour as it caused long queues at green lights

            # Set the amber phase according to the next green phase
            self.set_amber_phase()

            # Transmit the settings to SUMO
            self.send_tls_settings_to_sumo()

            # Set the state of the intersection to false, indicating the start of the amber phase
            self.reset_b()
            self._state = False

        # Else if the traffic light is in a green phase and the green timer is not finished, decrement the green timer
        elif self._state and self._green_timer > 0:
            self._green_timer -= step_length
            self.update_b_compare()
        # Catch all to check for logical errors
        else:
            print("Something wrong in update phase logic")

    def debug(self):
        pass
        # print(self._currentOpenLanes)
        # print(self._timerControl.getNewGreenTime(self))

    # Get functions

    def get_num_queues(self):
        return self._num_queues

    def get_phase_matrix_by_link_index(self, get_object_in_memory=False):
        if not get_object_in_memory:
            return self._phase_matrix_by_link_index.copy()
        else:
            print("WARNING: retreiving object in memory may result in accidental altering of contents (phase_matrix_by_link_index)")
            return self._phase_matrix_by_link_index

    def get_queues(self, get_object_in_memory=False):
        if not get_object_in_memory:
            return self._queue_lengths_by_link_index[:]
        else:
            print("WARNING: retreiving object in memory may result in accidental altering of contents (queues_by_link_index)")
            return self._queues_by_link_index

    def get_capacities(self, get_object_in_memory=False):
        if not get_object_in_memory:
            return self._outgoing_lane_capacities_by_link_index[:]
        else:
            print("WARNING: retreiving object in memory may result in accidental altering of contents (capacities_by_link_index)")
            return self._outgoing_lane_capacities_by_link_index

    def get_a_compare(self):
        return self._vehicles_to_remove_this_time_step_value_for_green_time_calculation

    def get_b_compare(self):
        return self._vehicles_removed_value_for_green_time_calculation

    def get_current_green_time(self):
        return self._phase_green_times[self._current_phase_index]

    def get_incoming_lanes(self):
        return self._incoming_lanes

    def get_incoming_lanes_by_index_array(self):
        return self._incoming_lanes_by_index

    def get_incoming_lane_from_index(self, index):
        return self._incoming_lanes_by_index[index]

    def get_indicies_of_incoming_lane(self, lane):
        return self._indicies_by_incoming_lane[lane]

    def get_outgoing_lanes(self):
        return self._outgoing_lanes

    def get_outgoing_lanes_by_index_array(self):
        return self._outgoing_lanes_by_index

    def get_outgoing_lane_from_index(self, index):
        return self._outgoing_lanes_by_index[index]

    def get_indicies_of_outgoing_lane(self, lane):
        return self._indicies_by_outgoing_lane[lane]

    def get_vehicles_at_start_of_time_step(self):
        return self._vehicles_at_start_of_timestep

    def get_vehicles_at_start_of_time_step_for_lane(self, lane):
        return self._vehicles_at_start_of_timestep[lane]

    def get_vehicles_at_end_of_timestep(self):
        return self._vehicles_at_end_of_timestep

    def get_vehicles_at_end_of_timestep_for_lane(self, lane):
        return self._vehicles_at_end_of_timestep[lane]

    def get_lambda(self, lane):
        return self._lambda[lane]

    def get_mu(self, lane):
        return self._mu[lane]

    def get_current_open_lanes(self):
        return self._current_open_lanes

    def get_destination(self, veh_id):
        route = traci.vehicle.getRoute(veh_id)
        return route.pop()

    def get_next_edge(self, veh_id):
        current_edge = traci.vehicle.getRoadID(veh_id)
        route = traci.vehicle.getRoute(veh_id)
        list_indicies = [list_index for list_index, edge in enumerate(route) if edge == current_edge]
        if len(list_indicies) > 1:
            print("Unable to determine next road due to duplicated edge in route. Ignoring vehicle.")
            return 0
        else:
            remaining_route = route[list_indicies[0]:]
            if len(remaining_route) == 1:
                return 0
            else:
                out_edge = remaining_route[1]
                return out_edge

    def get_veh_link_index(self, in_lane, veh_id):
        out_edge = self.get_next_edge(veh_id)
        if out_edge:
            try:
                index = self._in_lane_and_out_edge_to_link_index[in_lane][out_edge]
                return [index]
            except KeyError:
                for best_lane in traci.vehicle.getBestLanes(veh_id):
                    try:
                        index = self._in_lane_and_out_edge_to_link_index[best_lane[0]][out_edge]
                        return [index]
                    except KeyError:
                        pass
                return [-1]
        else:
            return self._in_lane_and_out_edge_to_link_index[in_lane].values()

    def get_veh_turning_direction(self, in_lane, veh_id):
        out_edge = self.get_next_edge(veh_id)
        return self._link_index_to_turning_direction[int(self._in_lane_and_out_edge_to_link_index[in_lane][out_edge])]

    def get_queue_length_per_link_index(self):
        veh_link_indexes = []
        for lane_id in self._incoming_lanes:
            veh_ids = traci.lane.getLastStepVehicleIDs(lane_id)
            new_indexes = [self.get_veh_link_index(lane_id, veh) for veh in veh_ids]
            if new_indexes :
                new_indexes_flattened = [item for sublist in new_indexes for item in sublist]
                veh_link_indexes.extend(new_indexes_flattened)
        index_count = Counter(veh_link_indexes)
        del index_count[-1]
        return index_count

    def get_waiting_time_per_link_index(self):
        waiting_times = [0] * self._num_queues

        for lane in self._incoming_lanes:
            for veh in traci.lane.getLastStepVehicleIDs(lane):
                self.get_veh_link_index(lane, veh)
                waiting_times[self.get_veh_link_index(lane, veh)[0]] += traci.vehicle.getWaitingTime(veh)

        return waiting_times


    def print_details(self):

        #print("Queues:", self._queue_lengths_by_link_index)
        #print("A:", self._number_of_vehicles_to_remove_by_link_index)
        print("Green Times:", self._phase_green_times)
        print("Timer:", self._green_timer)
        print("lambda", self._lambda)


class IntersectionControllerContainer:

    def __str__(self):
        """Container object for all the traffic light controlled intesections in the network.
        Provides methods for automatically creating the intersection objects from net file and updating them
        simultaneously during a simulation"""

    def __init__(self):
        self._intersection_controller_container = defaultdict(IntersectionController)

    def add_intersection_controller(self,
                                    tls_id, inc_lanes_by_index, out_lanes_by_index,
                                    phase_matrix_by_link_index, phase_strings, x_star,
                                    green_time_controller, queue_controller, TLS_dirs, TLS_lane2index, step_length,
                                    default_amber_phase_length = 4):

        new_ic = IntersectionController(tls_id, inc_lanes_by_index, out_lanes_by_index,
                                        phase_matrix_by_link_index, phase_strings, x_star, green_time_controller,
                                        queue_controller, TLS_dirs, TLS_lane2index, default_amber_phase_length, sim_step_length=step_length)

        self._intersection_controller_container[tls_id] = new_ic

    def add_intersection_controllers_from_net_file(self, net_file, x_star, green_time_controller, queue_controller, step_length, default_amber_phase_length=4, exclude=[]):
        """Read a net file and create intersection controllers for every traffic light controlled intersection
        add a green time controller and a queue controller for each traffic light"""

        [TLS_L, TLS_phases] = tls_logic.get_compatible_lanes_matrix_and_phases_from_net_file(net_file)
        [TLS_in_lanes, TLS_out_lanes] = tls_logic.get_in_out_lanes_to_index(net_file)
        [TLS_dirs, TLS_lane2index] = tls_logic.get_connection_to_turn_defs(net_file)

        TLS_IDs = TLS_L.keys()

        for tls_id in TLS_IDs:
            if tls_id not in exclude:
                inc_lanes_by_index = TLS_in_lanes[tls_id]
                out_lanes_by_index = TLS_out_lanes[tls_id]
                phase_matrix_by_link_index = TLS_L[tls_id]
                phase_strings = TLS_phases[tls_id]
                dirs = TLS_dirs[tls_id]
                lane2index = TLS_lane2index[tls_id]

                self.add_intersection_controller(tls_id, inc_lanes_by_index, out_lanes_by_index,
                                                 phase_matrix_by_link_index, phase_strings, x_star,
                                                 green_time_controller, queue_controller, dirs, lane2index, step_length, default_amber_phase_length=default_amber_phase_length)

    def update_intersection_controllers(self, step, step_length):
        for intersection_controller in self._intersection_controller_container.itervalues():
            intersection_controller.update(step, step_length)

    def print_details(self, tls_id):

        self._intersection_controller_container[tls_id].print_details()

class IntersectionControllerContainer_discountedIfGivingWay:

    def __str__(self):
        """Container object for all the traffic light controlled intesections in the network.
        Provides methods for automatically creating the intersection objects from net file and updating them
        simultaneously during a simulation"""

    def __init__(self):
        self._intersection_controller_container = defaultdict(IntersectionController)

    def add_intersection_controller(self,
                                    tls_id, inc_lanes_by_index, out_lanes_by_index,
                                    phase_matrix_by_link_index, phase_strings, x_star,
                                    green_time_controller, queue_controller, TLS_dirs, TLS_lane2index, step_length,
                                    default_amber_phase_length=4):

        new_ic = IntersectionController(tls_id, inc_lanes_by_index, out_lanes_by_index,
                                        phase_matrix_by_link_index, phase_strings, x_star, green_time_controller,
                                        queue_controller, TLS_dirs, TLS_lane2index, default_amber_phase_length, sim_step_length=step_length)

        self._intersection_controller_container[tls_id] = new_ic

    def add_intersection_controllers_from_net_file(self, net_file, x_star, green_time_controller, queue_controller, step_length, default_amber_phase_length = 4, exclude=[]):
        """Read a net file and create intersection controllers for every traffic light controlled intersection
        add a green time controller and a queue controller for each traffic light"""

        [TLS_L, TLS_phases] = tls_logic.get_compatible_lanes_matrix_and_phases_with_giveway_discount_from_net_file(net_file)
        [TLS_in_lanes, TLS_out_lanes] = tls_logic.get_in_out_lanes_to_index(net_file)
        [TLS_dirs, TLS_lane2index] = tls_logic.get_connection_to_turn_defs(net_file)

        TLS_IDs = TLS_L.keys()

        for tls_id in TLS_IDs:
            if tls_id not in exclude:
                inc_lanes_by_index = TLS_in_lanes[tls_id]
                out_lanes_by_index = TLS_out_lanes[tls_id]
                phase_matrix_by_link_index = TLS_L[tls_id]
                phase_strings = TLS_phases[tls_id]
                dirs = TLS_dirs[tls_id]
                lane2index = TLS_lane2index[tls_id]

                self.add_intersection_controller(tls_id, inc_lanes_by_index, out_lanes_by_index,
                                                 phase_matrix_by_link_index, phase_strings, x_star,
                                                 green_time_controller, queue_controller, dirs, lane2index, step_length, default_amber_phase_length)

    def update_intersection_controllers(self, step, step_length):
        for intersection_controller in self._intersection_controller_container.itervalues():
            intersection_controller.update(step, step_length)

    def print_details(self, tls_id):

        self._intersection_controller_container[tls_id].print_details()

if __name__ == "__main__":

    import sys, os, subprocess
    from sumocontrollib import controllers as ctrl
    from  blueCrystalFuncs import checkPorts

    os.environ['SUMO_HOME'] = '/sumo'

    queue_controller = "MaxBoundedQueue"
    green_time_controller = "Proportional"
    step_length = 0.1

    net_file_filepath = "/Users/tb7554/PyCharmProjects/_607_Smallworld_/Net_XML_Files/Smallworld_edited.net.xml"

    kwargs = {'tmin':5, 'tmax':25, 't_start':15, 'proportional_gain':0.15}
    target_frac = 1

    end_step = 7200

    project_directory = ""

    if queue_controller == "MaxBoundedQueue":
        queue_control = ctrl.CongestionDemandOptimisingQueueController()
    elif queue_controller == "CongestionAware":
        queue_control = ctrl.CongestionAwareLmaxQueueController()
    elif queue_controller == "CapacityAware":
        queue_control = ctrl.CongestionAwareLmaxQueueController()
    else:
        print("Unknown queue controller. Update code options in runSim.py")

    if green_time_controller == "MinMax":
        tmin = kwargs['tmin']
        tmax = kwargs['tmax']
        timer = ctrl.MinMaxGreenTimeController(tmin, tmax)
    elif green_time_controller == "Proportional":
        proportional_gain = kwargs['proportional_gain']
        t_start = kwargs['t_start']
        tmin = kwargs['tmin']
        tmax = kwargs['tmax']
        timer = ctrl.PGreenTimeController(proportional_gain, t_start, minValue=tmin, maxValue=tmax)
    elif green_time_controller == 'ModelBased':
        tmin = kwargs['tmin']
        tmax = kwargs['tmax']
        timer = ctrl.ModelBasedGreenTimeController(tmin, tmax)
    else:
        print("Uknown green time controller. Update code options in runSim.py")

    traci_port = checkPorts.getOpenPort()

    sumoCommand = ("sumo-gui -n %s -r /Users/tb7554/PyCharmProjects/_607_Smallworld_/SUMO_Input_Files/Trips/Smallworld-10x10-1-Lane-TLS-CGR-2.00-PEN-0.00-0.trip.xml -a /Users/tb7554/PyCharmProjects/_607_Smallworld_/SUMO_Input_Files/Trips/vtypes.add.xml --remote-port %d --step-length %.2f"
    % (net_file_filepath, traci_port, step_length))

    sumoProcess = subprocess.Popen(sumoCommand, shell=True, stdout=sys.stdout, stderr=sys.stderr)
    print("Launched process: %s" % sumoCommand)

    # initialise the step
    step = 0

    intersection_controller_container = IntersectionControllerContainer()
    intersection_controller_container.add_intersection_controllers_from_net_file(net_file_filepath, target_frac, timer,
                                                                                 queue_control, step_length, default_amber_phase_length = 4)

    # Open up traci on a free port
    traci.init(traci_port)
    print("port opened")
    # run the simulation
    while step <= end_step and traci.simulation.getMinExpectedNumber() > 0:
        traci.simulationStep()

        intersection_controller_container.update_intersection_controllers(step, step_length)

        step += step_length

    for ii in range(int(1 / step_length)):
        traci.simulationStep()

    for vehicle in traci.vehicle.getIDList():
        traci.vehicle.remove(vehicle)

    traci.close()
    sys.stdout.flush()

    sumoProcess.wait()

