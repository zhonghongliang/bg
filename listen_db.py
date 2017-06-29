# -*- coding:utf-8 -*-
#    This program is designed for the application of
#    Boat Graph. And this part is the main function.
#    Created on Thusday 15 Jun 2017 by Hugo

#    -------------------------------------------------#
#    TODO: to implement the API for requirement
import MySQLdb as mdb
import os,sys
import prediction as pdt
import m_update as m_udt
import time
import json
import random,string
import uds_client
#    ------------------------------------------------#

#    ------------------------------------------------#
#    This is the main entry for this program, it
#    listens the port of PLC or something else,
#    when it gets some info, it will take some
#    decision to do, for example: to init a model,
#    to predict the row and col of container or to
#    calibrate the model by manuel intervention
#    TODO 1: listen to the port of Unix domain socket
#    or get the new info from DB
#    ------------------------------------------------#

#    ------------------------------------------------#
#    When you get the information of boat and bay,
#    the first thing is to check it in the database
#    whether you have treated this bay.
#    TODO 2: check whether there is a model for this
#    bay.
#    If there is a model in the database,
#    TODO 3: reload this model
#    If not,
#    TODO 4: init a model for this bay, and store it
#    in the database
#    ------------------------------------------------#

#    ------------------------------------------------#
#    After get the model, you need to listen the
#    port of PLC, you can get the information of
#    what you need, for example: crane_no, lock_stat
#    , container_size, x: xiaoche, y: uplocation,
#    stack_init: the first container's stack,
#    tier_init: the first container's tier,
#    stack_calib: the calibration of the container's
#    stack by user, tier_calib: the calibration of
#    the container's tier by user.
#    To get some useful info from PLC
#    ------------------------------------------------#

#    listen to DB changement, if there is a lately insert
#    check whether it exists stack_pdt and tier_pdt

#    This definition needs to change by the true value
def CreatToken(randomlength = 10):
    a = list(string.ascii_letters)
    random.shuffle(a)
    return ''.join(a[:randomlength])

Bay_type = 'A'
while True:
    time.sleep(2)
    db = mdb.connect("192.168.100.95","root","","BayInfo")
    cursor = db.cursor()
    sql_search_plc = "SELECT * FROM BayInfo.PLC ORDER BY timestamp DESC LIMIT 1;"
    try:
        cursor.execute(sql_search_plc)
        results = cursor.fetchone()
        crane_no = results[1]
        x = float(results[2][:])
        y = float(results[3][:])
        lock_stat = results[5]
        container_size = results[7]
        if container_size == '20':
            w = 2.35
            h = 2.35
            poids = 17.5
        elif container_size == '40':
            w = 2.35
            h = 2.35
            poids = 22
        elif container_size == '45':
            w = 2.35
            h = 2.68
            poids = 29
        else:
            w = 2.35
            h = 2.35
            poids = 17.5
    except:
        print "There is something wrong with sql search,"
        print " or there is no feedback from sql."
        continue
#    print "Get the lastest notice from PLC is :" + results[1]


    sql_search_bay = "SELECT * FROM CranePoz WHERE crane_no = '%s'" %(crane_no)
    try:
        cursor.execute(sql_search_bay)
        results = cursor.fetchone()
        Boat_no = results[2]
        Bay_no  = results[3]

    except:
        print "There is no crane working with this boat and this bay!"
        continue

#    here to search the max 'B' Bay tier num and max stack num
    sql_search_tier = "SELECT max(CAST(iso_tier AS signed))  FROM VesselStackRaw WHERE velaliase = '%s' and isobay = '%s' and type_a = 'B' " %(Boat_no,Bay_no)
    try:
        cursor.execute(sql_search_tier)
        results = cursor.fetchall()
        Lower_tier_num = int(results[:])
    except:
        print "There is no info of tier_lower_num for this boat and this bay!"
        continue
    
    sql_search_stack = "SELECT max(CAST(iso_stack AS signed)) FROM VesselStackRaw WHERE velaliase = '%s' and isobay = '%s' " %(Boat_no,Bay_no)
    try:
        cursor.execute(sql_search_stack)
        results = cursor.fetchall()
        Stack_num = int(results[:])
        if Stack_num%2 == 1:
            Bay_struct = 's'
        else:
            Bay_struct = 'd'
    except:
        print "There is no info of stack_num for this boat and this bay!"
        continue

    sql_search_bay = "SELECT * FROM Weights_pdt WHERE velaliase = '%s' and isobay = '%s'" %(Boat_no,Bay_no)
    try:
        cursor.execute(sql_search_bay)
        results = cursor.fetchone()
        center_ref = json.loads(results[6]) # can't get Bay_type,w,h
        
        stack_pdt,tier_pdt,center_ref = pdt.toPdt(Bay_struct,Bay_type,center_ref,w,h,x,y,poids,Lower_tier_num)
        VesselCraneBay = "ContainerPoz"
        Token = CreatToken(randomlength=10)
        timestamp = time.time()
#BayGraphAct,Boat_no,Bay_no,stack_calib,tier_calib,container_size,Token,time.time()
        uds_client.uds_client("ContainerPoz",Boat_no,Bay_no,stack_pdt,tier_pdt,container_size,Token,time.time())
        sql_insert_b = "INSERT INTO BayInfo.Bay_pdt(crane_no,Boat_no,Bay_no, Bay_type, Bay_struct, stack,tier,x,y,status,Token) VALUES('%s','%s','%s','%s','%s','%s','%s','%s','%s','pdt','%s')" %(crane_no, Boat_no, Bay_no, Bay_type, Bay_struct, stack_pdt, tier_pdt, x, y, Token)
        try:
            cursor.execute(sql_insert_b)
        except:
            print "can' insert anything into the table Bay_pdt"
            pass
    except:
        print "There is no data for this boat and bay, it needs to calibrate manuelly for this boat and this bay!"
        continue
    
    db.close()
