#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Sep 15 14:29:36 2019

@author: hwan
"""

import tensorflow as tf
import numpy as np
import pandas as pd
import pdb #Equivalent of keyboard in MATLAB, just add "pdb.set_trace()"

tf.set_random_seed(1234)

class Layerwise:
    def __init__(self, hyper_p, data_dimension, labels_dimension, weight_list_counter, savefilepath):
        
###############################################################################
#                    Constuct Neural Network Architecture                     #
###############################################################################        
        # Initialize placeholders
        self.data_tf = tf.placeholder(tf.float32, shape=[None, data_dimension], name = "data_tf")
        self.labels_tf = tf.placeholder(tf.float32, shape=[None, labels_dimension], name = "labels_tf") # This is needed for batching during training, else can just use state_data
                           
        # Initialize weights and biases storage
        self.layers = [data_dimension] + [data_dimension]*(weight_list_counter+1) + [labels_dimension]
        print(self.layers)
        self.weights = [] # This will be a list of tensorflow variables
        self.biases = [] # This will be a list of tensorflow variables
        num_layers = len(self.layers)  
        
        ############################
        #   Initial Architecture   #
        ############################
        # If first iteration, initialize output layer
        with tf.variable_scope("NN") as scope: 
            if weight_list_counter == 0: 
                for l in range(0, 2):
                    W = tf.get_variable("W" + str(l+1), dtype = tf.float32, shape = [self.layers[l], self.layers[l + 1]], initializer = tf.random_normal_initializer())
                    b = tf.get_variable("b" + str(l+1), dtype = tf.float32, shape = [1, self.layers[l + 1]], initializer = tf.constant_initializer(0))                                  
                    tf.summary.histogram("weights" + str(l+1), W)
                    tf.summary.histogram("biases" + str(l+1), b)
                    self.weights.append(W)
                    self.biases.append(b)
        
        ##############################
        #   Extending Architecture   #
        ##############################   
        if weight_list_counter > 0: 
            with tf.variable_scope("NN") as scope: 
                # Load pre-trained weights and biases
                for l in range(0, weight_list_counter):
                    df_trained_weights = pd.read_csv(savefilepath + "_W" + str(l+1) + '.csv')
                    df_trained_biases = pd.read_csv(savefilepath + "_b" + str(l+1) + '.csv')
                    restored_W = df_trained_weights.values.reshape([self.layers[l], self.layers[l + 1]])
                    restored_b = df_trained_biases.values.reshape([1, self.layers[l + 1]])
                    W = tf.get_variable("W" + str(l+1), dtype = tf.float32, shape = [self.layers[l], self.layers[l + 1]], initializer = tf.constant_initializer(restored_W), trainable = False)
                    b = tf.get_variable("b" + str(l+1), dtype = tf.float32, shape = [1, self.layers[l + 1]], initializer = tf.constant_initializer(restored_b), trainable = False)                                  
                    self.weights.append(W)
                    self.biases.append(b)
                
                # Initialize new hidden layer weights and biases as 0           
                l = weight_list_counter
                W = tf.get_variable("W" + str(l+1), dtype = tf.float32, shape = [self.layers[l], self.layers[l + 1]], initializer = tf.constant_initializer(0))
                b = tf.get_variable("b" + str(l+1), dtype = tf.float32, shape = [1, self.layers[l + 1]], initializer = tf.constant_initializer(0))                                  
                tf.summary.histogram("weights" + str(l+1), W)
                tf.summary.histogram("biases" + str(l+1), b)
                self.weights.append(W)
                self.biases.append(b)
                    
                # Load pre-trained output layer weights and biases. Note these can be trained again
                l = weight_list_counter + 1
                df_trained_weights = pd.read_csv(savefilepath + "_Woutput" + '.csv')
                df_trained_biases = pd.read_csv(savefilepath + "_boutput" + '.csv')
                restored_W = df_trained_weights.values.reshape([self.layers[l], self.layers[l + 1]])
                restored_b = df_trained_biases.values.reshape([1, self.layers[l + 1]])
                W = tf.get_variable("W" + str(l+1), dtype = tf.float32, shape = [self.layers[l], self.layers[l + 1]], initializer = tf.constant_initializer(restored_W))
                b = tf.get_variable("b" + str(l+1), dtype = tf.float32, shape = [1, self.layers[l + 1]], initializer = tf.constant_initializer(restored_b))                                  
                tf.summary.histogram("weights" + str(l+1), W)
                tf.summary.histogram("biases" + str(l+1), b)
                self.weights.append(W)
                self.biases.append(b)
        
###############################################################################
#                           Network Propagation                               #
###############################################################################                  
        self.prediction = self.forward_prop(self.data_tf, num_layers)                
        self.classify = tf.argmax(self.prediction, 1)
        
###############################################################################
#                                Methods                                      #
############################################################################### 
    def forward_prop(self, X, num_layers):  
        with tf.variable_scope("fwd_prop") as scope:
            for l in range(0, num_layers-2):
                current_input = X
                W = self.weights[l]
                b = self.biases[l]
                X = current_input + tf.nn.relu(tf.add(tf.matmul(X, W), b))
                #tf.summary.histogram("activation" + str(l+1), X)
            W = self.weights[-1]
            b = self.biases[-1]
            output = tf.add(tf.matmul(X, W), b)
            return output
    