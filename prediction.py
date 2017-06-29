# -*- coding:utf-8 -*-
#	This program is designed for the application of
#	Boat Graph. This part is the function for prediction.
#	Created on Thusday 15 Jun 2017 by Hugo
#------------------------------------------------#
#	TODO: to implement the API for requirement
#import MySQLdb as mdb
import os,sys
import m_update as m_udt
import numpy as np
#------------------------------------------------#

#------------------------------------------------#

#	part 10 to initiate the model
#	Bay_type = A(upper) or B(lower)
def toInit(Bay_type,Bay_struct, lower_tier_num, stack_init,tier_init,w,h,x,y):

	# there are two ways to get the info of structure, 1: read them from database directly from this part
	# 2: give them as parameters from the main function. It includes Boat_no, Bay_no, stack_num, Bay_type
	# lower_tier_num, upper_tier_num, 
	# for the x-axis center
	lower_tier_num = int(lower_tier_num)
	stack_init = int(stack_init)
	tier_init  = int(tier_init)
	if Bay_struct == 's': # to judge the stack type, if it is singular, distribution is 04 02 00 01 03
		if stack_init%2 == 1: # to judge stack_init is on the left or right of center, singular on right
			center_x = x - float(stack_init/2 + 1)*w
			#self.delta_x  = 0.0
		else:
			center_x = x + float(stack_init/2)*w
			#self.delta_x  = 0.0
	else : #distribution of stack no. is 04 02 01 03 Bay_struct = 'd'
		if int(stack_init)%2 == 1:
			center_x = x - float(stack_init/2 + 0.5)*w
			#self.delta_x  = 0.0
		else:
			center_x = x + float(stack_init/2 - 0.5)*w
			#self.delta_x  = 0.0
	delta_x = 0.0
	# for the y-axis upper center and lower center
	if Bay_type == 'A': # to judge whether the first container is posited above the board or not
		upper_center_y = y + float((tier_init-80)/2-1)*h+0.5*h
		#self.delta_upper_y  = 0.0
		lower_center_y = upper_center_y + float(lower_tier_num+1)*h
		#self.delta_lower_y  = 0.0
	else:
		lower_center_y = y + float(tier_init/2-1)*h+0.5*h
		#self.delta_lower_y  = 0.0
		upper_center_y = lower_center_y - float(lower_tier_num+1)*h
		#self.delta_lower_y  = 0.0
	# TODO 10-1 By the initiation, we should update the bias for next prediction
	delta_lower_y = 0.0
	delta_upper_y = 0.0
	weights_x = np.ones((1,4))
	weights_uy= np.ones((1,4))
	weights_ly= np.ones((1,4))
	tau = 0.01
	#center_ref = [center_x, lower_center_y, upper_center_y, delta_x, delta_lower_y, delta_upper_y, weights_x, weights_uy, weights_ly]
	center_ref = {}
	center_ref['center_x'] = center_x
	center_ref['lower_center_y'] = lower_center_y
	center_ref['upper_center_y'] = upper_center_y
	center_ref['delta_x'] = delta_x
	center_ref['delta_lower_y']= delta_lower_y
	center_ref['delta_upper_y']= delta_upper_y
	center_ref['weights_x'] = weights_x*tau
	center_ref['weights_uy'] =  weights_uy*tau
	center_ref['weights_ly'] =  weights_ly*tau
	return center_ref

#	part 11 to predict the position of this container
#	Input:x,y,Boat_no, Bay_no, Bay_type, stack_num,
#	Output:stack_pdt,tier_pdt
def toPdt(Bay_struct,Bay_type,center_ref,w,h,x,y,poids,lower_tier_num):
	#center_x = center_ref[0]
	#lower_center_y = center_ref[1]
	#upper_center_y = center_ref[2]
	#delta_x = center_ref[3]
	#delta_lower_y = center_ref[4]
	#delta_upper_y = center_ref[5]
	#weights_x = center_ref[6]
	#weights_uy = center_ref[7]
	#weights_ly = center_ref[8]
	lower_tier_num = int(lower_tier_num)
	# for stack
	if Bay_struct == 's':
		if (x>=center_ref['center_x']):
			stack_tmp = int((x-center_ref['center_x']-center_ref['delta_x'])/w+0.5)
			if (stack_tmp >=1): 
				stack_pdt = stack_tmp*2-1
			else:
				stack_pdt = 0
			delta_x_tmp = x-center_ref['center_x']-stack_tmp*w
		else:
			stack_tmp = int((x-center_ref['center_x']-center_ref['delta_x'])/w-0.5)
			stack_pdt = -stack_tmp*2
			delta_x_tmp = x-center_ref['center_x']-stack_tmp*w
	else:
		if (x>=center_ref['center_x']):
			stack_tmp = int((x-center_ref['center_x']-center_ref['delta_x'])/w)
			stack_pdt = stack_tmp*2+1
			delta_x_tmp = x-center_ref['center_x']-stack_tmp*w-0.5*w
		else:
			stack_tmp = int((x-center_ref['center_x']-center_ref['delta_x'])/w)
			stack_pdt = -(stack_tmp+1)*2
			delta_x_tmp = x-center_ref['center_x']-stack_tmp*w+0.5*w
	# TODO temp to verify the update function
	center_ref['delta_x'],center_ref['weights_x'] = m_udt.update_delta_x(delta_x_tmp, stack_tmp, poids, stack_tmp,center_ref,w)

	# for tier
	if Bay_type == 'A':
		tier_tmp = int((center_ref['upper_center_y']+center_ref['delta_upper_y']-y)/h)
		tier_pdt = 80+(tier_tmp+1)*2
		delta_upper_y_tmp = y + float(tier_tmp)*h - center_ref['upper_center_y'] + 0.5*h
		# TODO temp to verify the update function
		center_ref['delta_upper_y'],center_ref['weights_uy'] = m_udt.update_delta_upper_y(delta_upper_y_tmp, tier_tmp+1+lower_tier_num,poids,tier_tmp+1+lower_tier_num,center_ref,h)

	else:
		tier_tmp = int((center_ref['lower_center_y']+center_ref['delta_lower_y']-y)/h)
		tier_pdt = (tier_tmp+1)*2
		delta_lower_y_tmp = y + float(tier_tmp)*h - center_ref['lower_center_y'] + 0.5*h
		# TODO temp to verify the update function
		center_ref['delta_lower_y'],center_ref['weights_ly'] = m_udt.update_delta_lower_y(delta_lower_y_tmp, tier_tmp, poids, tier_tmp,center_ref,h)

	# TODO 11-1 as same as 10-2 to restore the bay_ref_info into db

	# TODO 11-3 to update the difference's model
	# self.delta_x,self.delta_upper_y,self.delta_lower_y = m_udt.update_model(self.stack_pdt, delta_x, tier_pdt, delta_upper_y,delta_lower_y)
	stack_pdt = "%02d"%(stack_pdt)
	tier_pdt = "%02d"%(tier_pdt)
	return stack_pdt,tier_pdt, center_ref

#	TODO 12 to calibrate the difference of original point
#	Input: Boat_no, Bay_no, Bay_type, stack_num
#	Output: nothing
def toCalib(Bay_type, Bay_struct, center_ref, lower_tier_num, stack_pdt, stack_calib,tier_pdt, tier_calib,w,h,x,y,poids):
	# to judge the Boat_num and Bay_num is as same as it has initiate
	# if not, it should reload the Bay_ref_info from db
	lower_tier_num = int(lower_tier_num)
	stack_calib = int(stack_calib)
	tier_calib  = int(tier_calib)
	stack_pdt   = int(stack_pdt)
	tier_pdt    = int(tier_pdt)
	# for stack
	if Bay_struct == 's':
		if stack_calib%2 == 1:
			delta_x_tmp = x - float((stack_calib+1)/2)*w - center_ref['center_x']
		else:
			delta_x_tmp = x + float(stack_calib/2)*w - center_ref['center_x']
	else:
		if stack_calib%2 == 1:
			delta_x_tmp = x - float((stack_calib+1)/2)*w + 0.5*w - center_ref['center_x']
		else:
			delta_x_tmp = x + float(stack_calib/2)*w -0.5*w - center_ref['center_x']
	center_ref['center_x'] = delta_x_tmp
	# TODO verify the update function
	if stack_pdt%2==1:
		stack_pdt_tr = (stack_pdt+1)/2
	else:
		stack_pdt_tr = -stack_pdt/2
	if stack_calib%2==1:
		stack_calib_tr=(stack_calib+1)/2
	else:
		stack_calib_tr=-stack_calib/2

	center_ref['delta_x'],center_ref['weights_x'] = m_udt.update_delta_x(delta_x_tmp, stack_pdt_tr, poids, stack_calib_tr,center_ref,w)
	
	# for tier
	if Bay_type == "A":
		tier_pdt_tr = (tier_pdt-80)/2 + lower_tier_num + 1
		tier_calib_tr = (tier_calib-80)/2 + lower_tier_num + 1
		delta_upper_y_tmp = y + float((tier_calib-80)/2-0.5)*h - center_ref['upper_center_y']
		center_ref['delta_upper_y'] = delta_upper_y_tmp
		center_ref['delta_upper_y'],center_ref['weights_uy'] = m_udt.update_delta_upper_y(delta_upper_y_tmp, tier_pdt_tr, poids, tier_calib_tr,center_ref,h)

	else:
		delta_lower_y_tmp = y +float(tier_calib/2-0.5)*h -center_ref['lower_center_y']
			# TODO verify the update function
		tier_pdt_tr = (tier_pdt/2)
		tier_calib_tr = (tier_calib/2)
		center_ref['delta_lower_y'] = delta_lower_y_tmp
		center_ref['delta_lower_y'],center_ref['weights_ly'] = m_udt.update_delta_lower_y(delta_lower_y_tmp, tier_pdt_tr, poids, tier_calib_tr,center_ref,h)

	# part 11-3 to update the difference's model
	# self.delta_x,self.delta_upper_y,self.delta_lower_y = m_udt.update_model(self.stack_pdt, delta_x, tier_pdt, delta_upper_y,delta_lower_y)
	return center_ref
#------------------------------------------------# 