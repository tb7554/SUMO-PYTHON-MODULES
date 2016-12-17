# -*- coding: utf-8 -*-
from __future__ import print_function, division
import numpy as np
import random, copy
import traci

class MinMaxGreenTimeController:
    
    def __init__(self, Tmin, Tmax):
        """ Controller that uses basic Tmin and Tmax to adjust green time """
        self._Tmin = Tmin
        self._Tmax = Tmax
        self._initialGreenTime = (Tmax+Tmin)/2
        
    def __repr__(self):
        return "Min/Max Green Time Controller"
        
    def get_initial_green_time(self):
        """ Calculates the intial green time that all lights start with """
        return self._initialGreenTime
        
    def get_new_green_time(self, IC):
        """ Takes the target number of vehicles to remove from the queue, compares withe the actual number. Returns updated green time."""

        target_number_cars_cleared = IC.get_a_compare()
        actual_number_cars_cleared = IC.get_b_compare()
        Gt_old = IC.get_current_green_time()

        # Increase green time if too few cars cleared. Decrease green time if too many cars cleared.
        if actual_number_cars_cleared > target_number_cars_cleared:
            Gt_new = (Gt_old + self._Tmin)/2
        elif actual_number_cars_cleared < target_number_cars_cleared:
            Gt_new = (Gt_old + self._Tmax)/2
        else:
            Gt_new = Gt_old

        return Gt_new
    
class PGreenTimeController:
    
    def __init__(self, K, G0, minValue=False, maxValue=False):
        """ Controller that uses an estimated error in the green to make adjustments """
        self._K = K
        self._initialGreenTime = G0

        if minValue:
            self._min = minValue
        else:
            self._min = 0

        if maxValue:
            self._max = maxValue
        else:
            maxValue = 3600

    def __repr__(self):
        return "Proportional Green Time Controller"
        
    def get_initial_green_time(self):
        """ Calculates the intial green time that all lights start with """
        return self._initialGreenTime
        
    def get_new_green_time(self, IC):
        """ Takes the target number of vehicles to remove from the queue, compares withe the actual number. Returns updated green time."""

        target_number_cars_cleared = IC.get_a_compare()
        actual_number_cars_cleared = IC.get_b_compare()
        Gt_old = IC.get_current_green_time()

        if target_number_cars_cleared:
            error = ((target_number_cars_cleared-actual_number_cars_cleared)/target_number_cars_cleared)*Gt_old
        else:
            error = 0

        Gt_new = Gt_old + self._K*error

        if Gt_new < self._min :
            Gt_new = self._min
        elif Gt_new > self._max:
            Gt_new = self._max
        else:
            pass

        return Gt_new

class ModelBasedGreenTimeController:

    def __init__(self, Tmin, Tmax):
        self._Tmin = Tmin
        self._Tmax = Tmax
        self._initialGreenTime = (Tmax+Tmin)/2

    def __repr__(self):
        return "Model Based Green Time"

    def get_initial_green_time(self):
        return self._initialGreenTime

    def get_new_green_time(self, IC):

        for phase_index, phase in enumerate(IC._phase_matrix_by_link_index):
            number_of_vehicles_to_remove_by_link_index = map(lambda x: x * IC._proportion_of_vehicles_to_remove, IC.get_queues())
            target_number_of_cars_to_clear = np.sum(np.multiply(number_of_vehicles_to_remove_by_link_index, phase))

            open_lanes = set([IC._incoming_lanes_by_index[index] for index, value in enumerate(phase) if value])

            mu = 0
            lam = 0

            for lane in open_lanes:
                mu += IC.get_mu(lane)
                lam += IC.get_lambda(lane)

            if target_number_of_cars_to_clear > 0:
                try:
                    modelBased_Gt = target_number_of_cars_to_clear/(mu-lam)
                except ZeroDivisionError:
                    modelBased_Gt = self._Tmax
            else:
                modelBased_Gt = self._Tmin

            if modelBased_Gt > self._Tmax : modelBased_Gt = self._Tmax
            elif modelBased_Gt < self._Tmin  : modelBased_Gt = self._Tmin

            IC._phase_green_times[phase_index] = modelBased_Gt

        return IC._phase_green_times[IC._current_phase_index]

class AdvancedModelBasedGreenTimeController:

    def __init__(self, T0, period):
        self._period = period #The time period the calculation is done over
        self._initialGreenTime = period/T0
    def __repr__(self):
        return "Calculates green time as a ratio of the inflow rates of the lanes assocaite with each phase"

    def get_initial_green_time(self):
        return self._initialGreenTime

    def get_new_green_time(self, IC):

        # get the cumulative lambda for each phase option
        cum_lambdas = []

        for phase_index, phase in enumerate(IC._phase_matrix_by_link_index):
            open_lanes = set([IC._incoming_lanes_by_index[index] for index, value in enumerate(phase) if value])

            lam = 0
            for lane in open_lanes:
                lam += IC.get_lambda(lane)

            cum_lambdas.append(lam)

        for phase_index, phase in enumerate(IC._phase_matrix_by_link_index):
            try:
                IC._phase_green_times[phase_index] = self._period*(cum_lambdas[phase_index]/sum(cum_lambdas))
            except ZeroDivisionError:
                IC._phase_green_times[phase_index] = self._period/len(IC._phase_matrix_by_link_index)

        return IC._phase_green_times[IC._current_phase_index]

class WaitTimeBasedLmaxQueueController:
    
    def __init__(self):
        """ Controller that maximises the total number of vehicles released at each phase, regardless of fairness """

    def __repr__(self):
        return "Max Queue Length Controller"

    def best_queue_set(self, intersection_controller):
        """Picks the best queue to release, based on total number of vehicles in non-conflicting queues"""
        phases = intersection_controller.get_phase_matrix_by_link_index()
        queues = intersection_controller.get_waiting_time_per_link_index()

        phases_queues_dot_product = np.dot(phases, queues)
        best_choices = np.nonzero(phases_queues_dot_product == np.amax(phases_queues_dot_product))[0]

        return random.choice(best_choices)

class LmaxQueueController:
    def __init__(self):
        """ Controller that maximises the total number of vehicles released at each phase, regardless of fairness """

    def __repr__(self):
        return "Max Queue Length Controller"

    def best_queue_set(self, intersection_controller, replacement_phases = np.empty([0])):
        """Picks the best queue to release, based on total number of vehicles in non-conflicting queues"""

        if replacement_phases.any():
            phases = replacement_phases
        else:
            phases = intersection_controller.get_phase_matrix_by_link_index()

        queues = intersection_controller.get_queues()

        phases_queues_dot_product = np.dot(phases, queues)
        best_choices = np.nonzero(phases_queues_dot_product == np.amax(phases_queues_dot_product))[0]

        return random.choice(best_choices)

class NormalConvexMaxQueueController:
    def __repr__(self):
        return "Max Queue Length Controller"

    def best_queue_set(self, intersection_controller, replacement_phases=np.empty([0])):
        """Picks the best queue to release, based on total number of vehicles in non-conflicting queues"""

        if replacement_phases.any():
            phases = replacement_phases
        else:
            phases = intersection_controller.get_phase_matrix_by_link_index()

        phase_benefit = []

        for phase in phases:
            open_lanes = set([intersection_controller._incoming_lanes_by_index[index] for index, value in enumerate(phase) if value])

            cumulative_convex_normalised_pressure = 0

            for lane in open_lanes:
                lane_occ = traci.lane.getLastStepOccupancy(lane)
                cumulative_convex_normalised_pressure += 4*(lane_occ**4)

            phase_benefit.append(cumulative_convex_normalised_pressure)

        best_choices = np.nonzero(phase_benefit == np.amax(phase_benefit))[0]

        return random.choice(best_choices)

class BackPressureQueueController:
    def __repr__(self):
        return "Back-pressure queue control"

    def best_queue_set(self, intersection_controller, replacement_phases=np.empty([0])):
        """Picks the best queue to release, based on total number of vehicles in non-conflicting queues"""

        if replacement_phases.any():
            phases = replacement_phases
        else:
            phases = intersection_controller.get_phase_matrix_by_link_index()

        phase_benefit = []

        for phase in phases:
            open_lanes = set([intersection_controller._incoming_lanes_by_index[index] for index, value in enumerate(phase) if value])



            for lane in open_lanes:
                lane_occ = traci.lane.getLastStepOccupancy(lane)
                cumulative_convex_normalised_pressure += 4*(lane_occ**4)

            phase_benefit.append(cumulative_convex_normalised_pressure)

        best_choices = np.nonzero(phase_benefit == np.amax(phase_benefit))[0]

        return random.choice(best_choices)

class CapacityAwareBackPressureQueueController:
    def __repr__(self):
        return "Back-pressure queue control"

    def best_queue_set(self, intersection_controller, replacement_phases=np.empty([0])):
        """Picks the best queue to release, based on total number of vehicles in non-conflicting queues"""

        if replacement_phases.any():
            phases = replacement_phases
        else:
            phases = intersection_controller.get_phase_matrix_by_link_index()

        phase_benefit = []

        for phase in phases:
            open_lanes = set([intersection_controller._incoming_lanes_by_index[index] for index, value in enumerate(phase) if value])

            cumulative_convex_normalised_pressure = 0

            for lane in open_lanes:
                lane_occ = traci.lane.getLastStepOccupancy(lane)
                cumulative_convex_normalised_pressure += 4*(lane_occ**4)

            phase_benefit.append(cumulative_convex_normalised_pressure)

        best_choices = np.nonzero(phase_benefit == np.amax(phase_benefit))[0]

        return random.choice(best_choices)

class NormalLinearMaxQueueController:
    def __repr__(self):
        return "Max Queue Length Controller"

    def best_queue_set(self, intersection_controller, replacement_phases=np.empty([0])):
        """Picks the best queue to release, based on total number of vehicles in non-conflicting queues"""

        if replacement_phases.any():
            phases = replacement_phases
        else:
            phases = intersection_controller.get_phase_matrix_by_link_index()

        phase_benefit = []

        for phase in phases:
            open_lanes = set([intersection_controller._incoming_lanes_by_index[index] for index, value in enumerate(phase) if value])

            cumulative_normalised_linear_pressure = 0

            for lane in open_lanes:
                lane_occ = traci.lane.getLastStepOccupancy(lane)
                cumulative_normalised_linear_pressure += lane_occ

            phase_benefit.append(cumulative_normalised_linear_pressure)

        best_choices = np.nonzero(phase_benefit == np.amax(phase_benefit))[0]

        return random.choice(best_choices)

class CongestionAwareLmaxQueueController:
    
    def __init__(self):
        pass

    def __repr__(self):
        return "Congestion Aware Max Queue Length Controller"
    
    def discount_congested_queues(self, phases, capacities):
        """Sets phase entry to 0 for queues which have nowhere to go"""
        for row, phase in enumerate(phases):
            for col, entry in enumerate(phase):
                if capacities[col] < 1 :
                    phases[row][col] = 0
        return phases
                 
    def best_queue_set(self, intersection_controller, replacement_phases = np.empty([0])):
        """Picks the best queue to release, based on total number of vehicles in non-conflicting queues"""

        if replacement_phases.any():
            phases = replacement_phases
        else:
            phases = intersection_controller.get_phase_matrix_by_link_index()

        queues = intersection_controller.get_queues()
        capacities = intersection_controller.get_capacities()

        phases_discounted = self.discount_congested_queues(phases, capacities)
        discounted_phases__queues_dot_product = np.dot(phases_discounted, queues)

        best_choices = np.nonzero(discounted_phases__queues_dot_product == np.amax(discounted_phases__queues_dot_product))[0]

        return random.choice(best_choices)

class CongestionDemandOptimisingQueueController:

    def __repr__(self):
        return """Bounded Queue Length Max Queue Length Controller"""

    def get_L_matrix_from_phase(self, phase):
        L = []
        for row_index, row_status in enumerate(phase):
            L.append([])
            for other_index, col_status in enumerate(phase):
                if row_status and col_status:
                    L[row_index].append(1)
                else:
                    L[row_index].append(0)

        return L

    def bounded_demand(self, x_tilda, capacity_vec):
        return [min(val) for val in zip(x_tilda,capacity_vec)]

    def demand_per_queue(self, combined_out_flows_and_L_matrix, x_bounded):

        return [(queue_bounded/np.sum(combined_out_flows_and_L_matrix[ii][:])) if np.sum(combined_out_flows_and_L_matrix[ii][:]) != 0 else 0 for ii, queue_bounded in enumerate(x_bounded)]

    def phase_selection(self, phases, receiving_lanes_index, queues, capacities):

        phase_benefit = []

        for phase in phases:
            L = self.get_L_matrix_from_phase(phase)
            combined_out_flows_and_L_matrix = np.multiply(receiving_lanes_index, L)
            x_tilda = np.dot(combined_out_flows_and_L_matrix, queues)

            x_bounded = self.bounded_demand(x_tilda, capacities)
            x_bounded_per_queue = self.demand_per_queue(combined_out_flows_and_L_matrix, x_bounded)

            total_demand_bounded_by_capacity = np.dot(phase, x_bounded_per_queue)

            phase_benefit.append(total_demand_bounded_by_capacity)

        best_choices = np.nonzero(phase_benefit == np.amax(phase_benefit))[0]

        return random.choice(best_choices)

    def best_queue_set(self, intersection_controller, replacement_phases = np.empty([0])):

        # extract the relevant data from the intersection controller
        if replacement_phases.any():
            phases = replacement_phases
        else:
            phases = intersection_controller.get_phase_matrix_by_link_index()

        receiving_lanes_index = [[1 if ii in intersection_controller.get_indicies_of_outgoing_lane(intersection_controller.get_outgoing_lane_from_index(jj))
                                else 0
                                for ii in range(intersection_controller.get_num_queues())]
                                for jj in range(intersection_controller.get_num_queues())]
        queues = intersection_controller.get_queues()
        capacities = intersection_controller.get_capacities()

        best_phase = self.phase_selection(phases, receiving_lanes_index, queues, capacities)

        return best_phase

class MaxWaitTimeDeadlockDetectingController:

    def __repr__(self):
        queue_controller_string = str(self._queue_controller)
        return """MaxWaitTimeDeadlockDetectingController + """ + queue_controller_string

    def __init__(self, max_wait_time, queue_controller):
        self._queue_controller = queue_controller()
        self._max_allowable_wait_time = max_wait_time

    def deadlock_detection(self, IC):
        largest_wait_time_this_cycle = 0 # The longest any vehicle has to wait
        veh_queue_index = None # The queue index of said vehicle
        for lane in IC._incoming_lanes:
            for veh in traci.lane.getLastStepVehicleIDs(lane):
                wait_time = traci.vehicle.getWaitingTime(veh)
                if wait_time > self._max_allowable_wait_time and wait_time > largest_wait_time_this_cycle:
                    largest_wait_time_this_cycle = wait_time
                    veh_queue_index = IC.get_veh_link_index(lane, veh)

        return veh_queue_index

    def best_deadlocked_phase(self, veh_queue_index, IC):

        # Find the phases which unlock the relevant queue, then create a new phase matrix which sets other phases to all 0
        best_phases = [index for index, phase in enumerate(IC._phase_matrix_by_link_index) if phase[veh_queue_index]]
        phases_copy = copy.copy(IC._phase_matrix_by_link_index)

        for index, phase in enumerate(phases_copy):
            if index not in best_phases : phases_copy[index] = [0]*len(phase)

        best_phase = self._queue_controller.best_queue_set(IC, replacement_phases = phases_copy)

        return best_phase

    def best_queue_set(self, intersection_controller):
        deadlocked_queue = self.deadlock_detection(intersection_controller)

        if deadlocked_queue == None:
            return self._queue_controller.best_queue_set(intersection_controller)
        else:
            return self.best_deadlocked_phase(deadlocked_queue, intersection_controller)

class AlternatingPhasesQueueController:

    def __repr__(self):
        return """Cycles through each phase in order"""

    def best_queue_set(self, IC):
        last_phase = len(IC._phase_strings) - 1
        current_phase = IC._current_phase_index

        if current_phase == last_phase:
            return 0
        else:
            return current_phase + 1
