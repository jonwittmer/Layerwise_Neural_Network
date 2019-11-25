#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Oct 23 13:35:17 2019

@author: hwan
"""
import tensorflow as tf
import numpy as np
import pandas as pd

import shutil # for deleting directories
import os
import time

import pdb #Equivalent of keyboard in MATLAB, just add "pdb.set_trace()"

###############################################################################
#                             Training Properties                             #
###############################################################################
def optimize(hyperp, run_options, file_paths, NN, data_loss, accuracy, data_and_labels_train, data_and_labels_val, data_and_labels_test, label_dimensions, num_batches_train):
    #=== Optimizer ===#
    optimizer = tf.keras.optimizers.Adam()
    reset_optimizer = tf.group([v.initializer for v in optimizer.variables()])
    
    #=== Define Metrics and Initialize Metric Storage Arrays ===#
    loss_train_batch_average = tf.keras.metrics.Mean()
    loss_val_batch_average = tf.keras.metrics.Mean()
    loss_test_batch_average = tf.keras.metrics.Mean()
    accuracy_train_batch_average = tf.keras.metrics.Mean()
    accuracy_val_batch_average = tf.keras.metrics.Mean()
    accuracy_test_batch_average = tf.keras.metrics.Mean()
    storage_loss_array = np.array([])
    storage_accuracy_array = np.array([])
    
    #=== Creating Directory for Trained Neural Network ===#
    if not os.path.exists(file_paths.NN_savefile_directory):
        os.makedirs(file_paths.NN_savefile_directory)
    
    #=== Tensorboard ===# Tensorboard: type "tensorboard --logdir=Tensorboard" into terminal and click the link
    if os.path.exists('../Tensorboard/' + file_paths.filename): # Remove existing directory because Tensorboard graphs mess up of you write over it
        shutil.rmtree('../Tensorboard/' + file_paths.filename)  
    summary_writer = tf.summary.create_file_writer('../Tensorboard/' + file_paths.filename)

###############################################################################
#                             Train Neural Network                            #
############################################################################### 
    loss_validation = 1e5
    trainable_hidden_layer_index = 2
    relative_number_zeros = 0
    storage_loss_array = []
    storage_accuracy_array = []
    storage_relative_number_zeros_array = []
    
    #####################################
    #   Training Current Architecture   #
    #####################################
    while loss_validation > hyperp.error_TOL and trainable_hidden_layer_index < hyperp.max_hidden_layers:    
        #=== Initial Loss and Accuracy ===#
        for batch_num, (data_train, labels_train) in data_and_labels_train.enumerate():
            output = NN(data_train)
            loss_train_batch = data_loss(output, labels_train, label_dimensions)
            loss_train_batch += sum(NN.losses)
            loss_train_batch_average(loss_train_batch) 
            accuracy_train_batch_average(accuracy(output, labels_train))
        for data_val, labels_val in data_and_labels_val:
            output_val = NN(data_val)
            loss_val_batch = data_loss(output_val, labels_val, label_dimensions)
            loss_val_batch += sum(NN.losses)
            loss_val_batch_average(loss_val_batch)
            accuracy_val_batch_average(accuracy(output_val, labels_val))
        for data_test, labels_test in data_and_labels_test:
            output_test = NN(data_test)
            loss_test_batch = data_loss(output_test, labels_test, label_dimensions)
            loss_test_batch += sum(NN.losses)
            loss_test_batch_average(loss_test_batch)
            accuracy_test_batch_average(accuracy(output_test, labels_test))
        storage_loss_array = np.append(storage_loss_array, loss_train_batch_average.result())
        storage_accuracy_array = np.append(storage_accuracy_array, accuracy_test_batch_average.result())
        print('Initial Losses:')
        print('Training Set: Loss: %.3e, Accuracy: %.3f' %(loss_train_batch_average.result(), accuracy_train_batch_average.result()))
        print('Validation Set: Loss: %.3e, Accuracy: %.3f' %(loss_val_batch_average.result(), accuracy_val_batch_average.result()))
        print('Test Set: Loss: %.3e, Accuracy: %.3f\n' %(loss_test_batch_average.result(), accuracy_test_batch_average.result()))
        
        #=== Begin Training ===#
        print('Beginning Training')
        for epoch in range(hyperp.num_epochs):
            print('================================')
            print('            Epoch %d            ' %(epoch))
            print('================================')
            print(file_paths.filename)
            print('Trainable Hidden Layer Index: %d' %(trainable_hidden_layer_index))
            print('GPU: ' + run_options.which_gpu + '\n')
            print('Optimizing %d batches of size %d:' %(num_batches_train, hyperp.batch_size))
            start_time_epoch = time.time()
            for batch_num, (data_train, labels_train) in data_and_labels_train.enumerate():
                with tf.GradientTape() as tape:
                    start_time_batch = time.time()
                    output = NN(data_train)
                    #=== Display Model Summary ===#
                    if batch_num == 0 and epoch == 0:
                        NN.summary()
                    loss_train_batch = data_loss(output, labels_train, label_dimensions)
                    loss_train_batch += sum(NN.losses)
                gradients = tape.gradient(loss_train_batch, NN.trainable_variables)
                optimizer.apply_gradients(zip(gradients, NN.trainable_variables))
                elapsed_time_batch = time.time() - start_time_batch
                if batch_num  == 0:
                    print('Time per Batch: %.2f' %(elapsed_time_batch))
                loss_train_batch_average(loss_train_batch) 
                accuracy_train_batch_average(accuracy(output, labels_train))
                                        
            #=== Computing Validation Metrics ===#
            for data_val, labels_val in data_and_labels_val:
                output_val = NN(data_val)
                loss_val_batch = data_loss(output_val, labels_val, label_dimensions)
                loss_val_batch += sum(NN.losses)
                loss_val_batch_average(loss_val_batch)
                accuracy_val_batch_average(accuracy(output_val, labels_val))
            
            #=== Computing Testing Metrics ===#
            for data_test, labels_test in data_and_labels_test:
                output_test = NN(data_test)
                loss_test_batch = data_loss(output_test, labels_test, label_dimensions)
                loss_test_batch += sum(NN.losses)
                loss_test_batch_average(loss_test_batch)
                accuracy_test_batch_average(accuracy(output_test, labels_test))
            
            #=== Track Training Metrics, Weights and Gradients ===#
            with summary_writer.as_default():
                tf.summary.scalar('loss_training', loss_train_batch_average.result(), step=epoch)
                tf.summary.scalar('accuracy_training', accuracy_train_batch_average.result(), step=epoch)
                tf.summary.scalar('loss_validation', loss_val_batch_average.result(), step=epoch)
                tf.summary.scalar('accuracy_validation', accuracy_val_batch_average.result(), step=epoch)
                tf.summary.scalar('loss_test', loss_test_batch_average.result(), step=epoch)
                tf.summary.scalar('accuracy_test', accuracy_test_batch_average.result(), step=epoch)
                storage_loss_array = np.append(storage_loss_array, loss_train_batch_average.result())
                storage_accuracy_array = np.append(storage_accuracy_array, accuracy_test_batch_average.result())
                for w in NN.weights:
                    tf.summary.histogram(w.name, w, step=epoch)
                l2_norm = lambda t: tf.sqrt(tf.reduce_sum(tf.pow(t, 2)))
                for gradient, variable in zip(gradients, NN.trainable_variables):
                    tf.summary.histogram("gradients_norm/" + variable.name, l2_norm(gradient), step = epoch)
                
            #=== Display Epoch Iteration Information ===#
            elapsed_time_epoch = time.time() - start_time_epoch
            print('Time per Epoch: %.2f\n' %(elapsed_time_epoch))
            print('Training Set: Loss: %.3e, Accuracy: %.3f' %(loss_train_batch_average.result(), accuracy_train_batch_average.result()))
            print('Validation Set: Loss: %.3e, Accuracy: %.3f' %(loss_val_batch_average.result(), accuracy_val_batch_average.result()))
            print('Test Set: Loss: %.3e, Accuracy: %.3f\n' %(loss_test_batch_average.result(), accuracy_test_batch_average.result()))
            print('Previous Layer Relative # of 0s: %.7f\n' %(relative_number_zeros))
            start_time_epoch = time.time()   
            
            #=== Reset Metrics ===#
            loss_validation = loss_val_batch_average.result()
            loss_train_batch_average.reset_states()
            loss_val_batch_average.reset_states()
            loss_test_batch_average.reset_states()
            accuracy_train_batch_average.reset_states()
            accuracy_val_batch_average.reset_states()
            accuracy_test_batch_average.reset_states()
                   
        ########################################################
        #   Updating Architecture and Saving Current Metrics   #
        ########################################################  
        print('================================')
        print('     Extending Architecture     ')
        print('================================')          
        #=== Saving Metrics ===#
        metrics_dict = {}
        metrics_dict['loss'] = storage_loss_array
        metrics_dict['accuracy'] = storage_accuracy_array
        df_metrics = pd.DataFrame(metrics_dict)
        df_metrics.to_csv(file_paths.NN_savefile_name + "_metrics_hl" + str(trainable_hidden_layer_index) + '.csv', index=False)
        
        #=== Sparsify Weights of Trained Layer ===#
        if run_options.use_L1 == 1:
            relative_number_zeros = NN.sparsify_weights_and_get_relative_number_of_zeros(hyperp.node_TOL)
            print('Relative Number of Zeros for Last Layer: %d\n' %(relative_number_zeros))
            storage_relative_number_zeros_array = np.append(storage_relative_number_zeros_array, relative_number_zeros)
        
        #=== Saving Relative Number of Zero Elements ===#
            relative_number_zeros_dict = {}
            relative_number_zeros_dict['rel_zeros'] = storage_relative_number_zeros_array
            df_relative_number_zeros = pd.DataFrame(relative_number_zeros_dict)
            df_relative_number_zeros.to_csv(file_paths.NN_savefile_name + "_relzeros" + '.csv', index=False)
       
        #=== Add Layer ===#
        trainable_hidden_layer_index += 1
        NN.add_layer(trainable_hidden_layer_index, freeze=True, add = True)
            
        #=== Preparing for Next Training Cycle ===#
        storage_loss_array = []
        storage_accuracy_array = []
        reset_optimizer   
        
    ########################
    #   Save Final Model   #
    ########################            
    #=== Saving Trained Model ===#          
    NN.save_weights(file_paths.NN_savefile_name)
    print('Final Model Saved') 
        

    
