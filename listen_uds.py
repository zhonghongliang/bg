import MySQLdb as mdb
import os,sys
import prediction as pdt
import m_update as m_udt
import socket
import time
import json
import uds_client
import numpy as np
import random,string


def CreatToken(randomlength = 10):
    token = list(string.ascii_letters)
    random.shuttle(token)
    return ''.join(token[:randomlength])

server_address = '/tmp/bayclient.sock'
try:
    os.unlink(server_address)
except OSError:
    if os.path.exists(server_address):
        raise

sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
print >>sys.stderr, 'starting up on %s' %server_address
sock.bind(server_address)

sock.listen(1)

while True:
    print >>sys.stderr, 'waiting for a connection'
    connection, client_address = sock.accept()
    try:
        print >>sys.stderr, 'connection from', client_address
        
        while True:
            data = connection.recv(10000)
            print >>sys.stderr, 'received "%s"' %data
            if data:
                # TODO this part can make feedback to the server
                print >>sys.stderr,'sending data back to the client'
                connection.sendall(data)

                data_tmp = json.loads(data)
                BayGraphAct = data_tmp["BayGraphAct"]
                Boat_no = data_tmp["Velaliase"]
                Bay_no = data_tmp["ContainerPozISO"][0:2]
                stack_calib = int(data_tmp["ContainerPozISO"][2:4])
                tier_calib = int(data_tmp["ContainerPozISO"][4:6])
                container_size = data_tmp["ContainerSize"]
                if container_size == "20":
                    w = 2.35
                    h = 2.35
                    poids = 17.5
                elif container_size == "40":
                    w = 2.35
                    h = 2.35
                    poids = 22
                elif container_size == "45":
                    w = 2.35
                    h = 2.68
                    poids = 29
                else:
                    w = 2.35
                    h = 2.35
                    poids = 17.5
                Token = data_tmp["Token"]
                Timestamp = data_tmp["Timestamp"]
                
                db = mdb.connect('192.168.100.95','root','','BayInfo')
                cursor = db.cursor()
                sql_search_boat = "SELECT * FROM BayInfo.Bay_pdt WHERE Token = '%s'"%(Token)
                # if it can find the data from Weights_pdt, it means we have treat this container yet, then just to calib it
                # if not, we need to initiate it.
                try:
                    cursor.execute(sql_search_boat)
                    results = cursor.fetchone()
                    crane_no= results[2]
                    Boat_no = results[3]
                    Bay_no  = int(results[4][:])
                    Bay_type= results[5]
                    Bay_struct=results[6]
                    stack_pdt=int(results[7][:])
                    tier_pdt= int(results[8][:])
                    x = float(results[9][:])
                    y = float(results[10][:])
                    status = results[11]
                    sql_search_weight = "SELECT * FROM Weights_pdt WHERE Boat_no = '%s' AND Bay_no = '%s' "%(Boat_no,Bay_no)
                    try:
                        cursor.execute(sql_search_weight)
                        find_weight = cursor.fetchone()
                        Lower_tier_num = int(find_weight[3][:])
                        stack_num = int(find_weight[4][:])
                        center_ref = find_weight[5]
                        center_ref = json.loads(center_ref)

# toCalib(Bay_type, Bay_struct, center_ref, lower_tier_num, stack_pdt, stack_calib, tier_pdt, tier_calib, w, h, x, y, poids)
                        center_ref_cab = pdt.toCalib(Bay_type, Bay_struct, center_ref, Lower_tier_num, stack_pdt,stack_calib,\
                                                     stack_pdt, tier_calib,w,h,x,y,poids)
                        center_ref_cab = json.dumps(center_ref_cab)
                        
                        sql_update_w = "UPDATE Weights_pdt SET center_ref = '%s' WHERE Boat_no = '%s' AND Bay_no = '%s' "\
                                       %(center_ref_cab, Boat_no, Bay_no)
                        try:
                            cursor.execute(sql_update_w)
                            db.commit()
                        except:
                            print "There is something wrong with update for table Weights_pdt"
                        
                        sql_update_b = "UPDATE BayInfo.Bay_pdt SET stack = '%s', tier = '%s', Bay_type = '%s',Bay_struct = 's,status = 'cab' WHERE Token = '%s' "\
                                       %(stack_calib,tier_calib,Bay_type,Bay_struct,Token)
                        try:
                            cursor.execute(sql_update_b)
                            db.commit()
                        except:
                            print "There is something wrong with update for table Bay_pdt"    

                    except:
                        print "can't find anything from Table Weights with this boat and bay number."
                        pass

                except:
                    sql_search_crane = "SELECT * FROM BayInfo.CranePos WHERE velaliase = '%s' AND bay = '%s' " % (Boat_no, Bay_no)
                    try:
                        cursor.execute(sql_search_crane)
                        crane_no_result = cursor.fetchone()
                        crane_no = crane_no_result[0]
                    except:
                        print "can't find the crane_no from database: cranePos"
                        continue

                    sql_search_plc = "SELECT * FROM BayInfo.PLC WHERE crane_no = '%s' " % (crane_no)
                    try:
                        cursor.excute(sql_search_plc)
                        plc_result = cursor.fetchone()
                        x = float(plc_result[2][:])
                        y = float(plc_result[3][:])
                        container_size_plc = plc_result[7]
                        if tier_calib < 80:
                            Bay_type = 'B'
                        else:
                            Bay_type = 'A'

                        sql_search_stacknum = "SELECT max(CAST(iso_stack as signed)) FROM VesselCellRaw WHERE velaliase = '%s' and iso_bay = '%s' " % (Boat_no, Bay_no)
                        try:
                            cursor.execute(sql_search_stacknum)
                            Stack_num = cursor.fetchone()
                            Stack_num = int(Stack_num)
                            if int(Stack_num) % 2 == 1:
                                Bay_struct = 's'
                            else:
                                Bay_struct = 'd'
                        except:
                            print "can't find any information from Table VesselCellRaw for Bay_struct"
                            continue

                        sql_search_lowertier = "SELECT max(CAST(iso_tier as signed)) FROM VesselCellRaw WHERE velaliase ='%s' and iso_bay = '%s' and type_a = 'B' " % (Boat_no, Bay_no)
                        try:
                            cursor.execute(sql_search_lowertier)
                            Lower_tier_num = cursor.fetchone()
                            Lower_tier_num = int(Lower_tier_num)
                        except:
                            print "can't find the lower tier number from VesselCellRaw Table"
                            continue
                        center_ref = pdt.toInit(Bay_type, Bay_struct, Lower_tier_num, stack_calib, tier_calib, w, h, x, y)
                        center_ref = json.dumps(center_ref)
                        sql_insert_w = "INSERT INTO BayInfo.Weights_pdt(Boat_no,Bay_no,Lower_tier_num,Stack_num,Center_ref) VALUES('%s','%s','%s','%s','%s')" % (Boat_no, Bay_no, Lower_tier_num, Stack_num, center_ref)
                        Token = CreatToken(randomlength=10)
                        try:
                            cursor.execute(sql_insert_w)
                        except:
                            print "can' insert anything into the table Weights_pdt"
                            pass

                        sql_insert_b = "INSERT INTO BayInfo.Bay_pdt(crane_no,Boat_no,Bay_no, Bay_type, Bay_struct, stack,tier,x,y,status,Token) VALUES('%s','%s','%s','%s','%s','%s','%s','%s','%s','init','%s')" %(crane_no, Boat_no, Bay_no, Bay_type, Bay_struct, stack_calib, tier_calib, x, y, Token)
                        try:
                            cursor.execute(sql_insert_b)
                        except:
                            print "can' insert anything into the table Bay_pdt"
                            pass
                    except:
                        print "can't find anything from table PLC with crane number"
                        continue

                uds_client.uds_client(BayGraphAct,Boat_no,Bay_no,stack_calib,tier_calib,container_size,Token,time.time())
            else:
                print >>sys.stderr, 'no more data from', client_address
            break

    finally:
            connection.close()
