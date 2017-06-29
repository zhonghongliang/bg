# -*- coding:utf-8 -*-
#	This program is designed for the application of
#	Boat Graph. This part is the function for update
#	the position different between current and 
#	original center point
#	Created on Thusday 15 Jun 2017 by Hugo
#------------------------------------------------#
#	TODO: to implement the API for requirement
import MySQLdb as mdb
import os,sys
import numpy as np
#------------------------------------------------#

#------------------------------------------------#
#	this function is used to ameliorate the model 
#	who can predict the changement of the bias
#	tau is the learning rate	
#	here, we use an online machine learning algorithm
#	to predict the bias. it needs several parameters:
#	W the learning weights; x the all input parameters
#	y the delta_tmp we calculate temporally and epsilon
#	we previewed.
#	The first thing is to get the predict y_hat
#	y_hat = w*x
#	then, calculate the loss l:
#	l:= 0 if |w*x-y|<=epsilon, else |w*x-y|-epsilon
#	after that, to update the weights W
#	W_{t+1} = W_t + sign(y-y_hat)*x*loss/(norm(x)^2) 

#delta_lower_y, tier_pdt_tr, poids, tier_calib_tr,center_ref
#center_ref = [center_x, lower_center_y, upper_center_y, delta_x, delta_lower_y, delta_upper_y, weights_x, weights_uy, weights_ly]

def update_delta_x(delta_x, stack_pdt_tr, poids, stack_calib_tr,center_ref,w):
	#[center_x, lower_center_y, upper_center_y, delta_x, delta_lower_y, delta_upper_y, weights_x, weights_uy, weights_ly] = center_ref
	instance = np.array([stack_pdt_tr, poids, stack_calib_tr-stack_pdt_tr, 1])
	instance.shape = (1,4)
	delta_x_tmp  = np.dot(center_ref['weights_x'],instance.T)
	if abs(delta_x-delta_x_tmp)<=w:
		center_ref['delta_x'] = delta_x_tmp
		loss = 0.0
	else:
		center_ref['delta_x'] = delta_x
		loss = abs(delta_x-delta_x_tmp)-w
	center_ref['weights_x'] = center_ref['weights_x'] + np.sign(delta_x-delta_x_tmp)*loss*instance/np.dot(instance,instance.T)

	return center_ref['delta_x'], center_ref['weights_x']

def update_delta_upper_y(delta_upper_y, tier_pdt_tr, poids, tier_calib_tr,center_ref,h):
	#[center_x, lower_center_y, upper_center_y, delta_x, delta_lower_y, delta_upper_y, weights_x, weights_uy, weights_ly] = center_ref
	instance = np.array([tier_pdt_tr, poids, tier_calib_tr-tier_pdt_tr, 1])
	instance.shape=(1,4)
	delta_upper_y_tmp = np.dot(center_ref['weights_uy'],instance.T)
	if abs(delta_upper_y-delta_upper_y_tmp)<=h:
		center_ref['delta_upper_y'] = delta_upper_y_tmp
		loss = 0.0
	else:
		center_ref['delta_upper_y'] = center_ref['delta_upper_y']
		loss = abs(delta_upper_y-delta_upper_y_tmp) - h
	center_ref['weights_uy'] = center_ref['weights_uy'] + np.sign(delta_upper_y-delta_upper_y_tmp)*loss*instance/np.dot(instance,instance.T)

	return center_ref['delta_upper_y'], center_ref['weights_uy']

def update_delta_lower_y(delta_lower_y, tier_pdt_tr, poids, tier_calib_tr,center_ref,h):
	#[center_x, lower_center_y, upper_center_y, delta_x, delta_lower_y, delta_upper_y, weights_x, weights_uy, weights_ly] = center_ref
	instance = np.array([tier_pdt_tr, poids, tier_calib_tr-tier_pdt_tr, 1])
	instance.shape = (1,4)
	delta_lower_y_tmp = np.dot(center_ref['weights_ly'],instance.T)
	if abs(delta_lower_y-delta_lower_y_tmp)<=h:
		center_ref['delta_lower_y'] = delta_lower_y_tmp
		loss = 0.0
	else:
		center_ref['delta_lower_y'] = delta_lower_y
		loss = abs(delta_lower_y-delta_lower_y_tmp) - h
	weights_ly = center_ref['weights_ly'] + np.sign(delta_lower_y-delta_lower_y_tmp)*loss*instance/np.dot(instance,instance.T)

	return center_ref['delta_lower_y'], center_ref['weights_ly']
#------------------------------------------------#