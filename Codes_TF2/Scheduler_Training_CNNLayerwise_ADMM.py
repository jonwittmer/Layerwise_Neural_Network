#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Sep 18 20:53:06 2019

@author: Jon Wittmer
"""

import subprocess
from mpi4py import MPI
import copy
from Utilities.get_hyperparameter_permutations import get_hyperparameter_permutations
from Utilities.schedule_and_run import schedule_runs
from Training_Driver_CNNLayerwise_ADMM import Hyperparameters
import pdb #Equivalent of keyboard in MATLAB, just add "pdb.set_trace()"

class FLAGS:
    RECEIVED = 1
    RUN_FINISHED = 2
    EXIT = 3
    NEW_RUN = 4

###############################################################################
#                                   Executor                                  #
###############################################################################
if __name__ == '__main__':
                    
    # To run this code "mpirun -n 4 ./Scheduler_Training_CNNLayerwise_ADMM.py" in command line
    
    # mpi stuff
    comm   = MPI.COMM_WORLD
    nprocs = comm.Get_size()
    rank   = comm.Get_rank()
    
    # By running "mpirun -n <number> ./scheduler.py", each process is cycled through by their rank
    if rank == 0: # This is the master processes' action 
        #########################
        #   Get Scenarios List  #
        #########################   
        hyperp = Hyperparameters() # Assign instance attributes below, DO NOT assign an instance attribute to GPU
        
        # assign instance attributes for hyperp
        hyperp.max_hidden_layers = [8]
        hyperp.filter_size       = [3] # Indexing includes input and output layer with input layer indexed by 0
        hyperp.num_filters       = [128]
        hyperp.regularization    = [0.001]
        hyperp.penalty           = [1, 5, 10, 20, 100]
        hyperp.node_TOL          = [1e-4]
        hyperp.error_TOL         = [1e-4]
        hyperp.batch_size        = [1000]
        hyperp.num_epochs        = [30]
        
        permutations_list, hyperp_keys = get_hyperparameter_permutations(hyperp) 
        print('permutations_list generated')
        
        # Convert each list in permutations_list into class attributes
        scenarios_class_instances = []
        for scenario_values in permutations_list: 
            hyperp_scenario = Hyperparameters()
            for i in range(0, len(scenario_values)):
                setattr(hyperp_scenario, hyperp_keys[i], scenario_values[i])
            scenarios_class_instances.append(copy.deepcopy(hyperp_scenario))

        # Schedule and run processes
        schedule_runs(scenarios_class_instances, nprocs, comm)  
        
    else:  # This is the worker processes' action
        while True:
            status = MPI.Status()
            data = comm.recv(source=0, status=status)
            
            if status.tag == FLAGS.EXIT:
                break
            
            proc = subprocess.Popen(['./Training_Driver_CNNLayerwise_ADMM.py', f'{data.max_hidden_layers}', f'{data.filter_size}', f'{data.num_filters}', f'{data.regularization}', f'{data.penalty:.4f}', f'{data.node_TOL:.4e}', f'{data.error_TOL:.4e}', f'{data.batch_size}', f'{data.num_epochs}',  f'{data.gpu}'])
            proc.wait() # without this, the process will detach itself once the python code is done running
            
            req = comm.isend([], 0, FLAGS.RUN_FINISHED)
            req.wait() # without this, the message sent by comm.isend might get lost when this process hasn't been probed. With this, it essentially continues to message until its probe
    
    print('All scenarios computed')