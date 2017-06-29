# -*- coding:utf-8 -*-
#	This program is designed for the application of
#	Boat Graph. And this part to connect unix domain.
#	Created on Thusday 15 Jun 2017 by Hugo
#------------------------------------------------#
import json
import socket
import sys


def uds_client(BayGraphAct, Boat_no,Bay_no,stack_pdt,tier_pdt,ContainerSize,Token,Timestamp):
	# Create a UDS socket
	sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)

	# Connect the socket to the port where the server is listening
	server_address = '/tmp/bayclient.sock'
	print >>sys.stderr, 'connecting to %s' %server_address
	try:
		sock.connect(server_address)
	except socket.error,msg:
		print >>sys.stderr, msg
		sys.exit(1)

	try:
		# here to write the info into a format of xml and send it
		pdt_info = {}
		pdt_info["BayGraphAct"] = BayGraphAct
		pdt_info["Velaliase"] = Boat_no
		#print Bay_no,stack_pdt,tier_pdt
		Bay_no = "%02d"%(Bay_no)
		stack_pdt = "%02d"%(stack_pdt)
		tier_pdt = "%02d"%(tier_pdt)
		pdt_info["ContainerPozISO"] = Bay_no + stack_pdt + tier_pdt
		pdt_info["ContainerSize"] = ContainerSize
		pdt_info["Token"] = Token
		pdt_info["Timestamp"] = Timestamp
		message = json.dumps(pdt_info)
		#print >>sys.stderr, 'sending "%s"' %message
		sock.sendall(message)

		amount_received = 0
		amount_expected = len(message)

		while amount_received < amount_expected:
			data = sock.recv(10000)
			amount_received += len(data)
			print >>sys.stderr, 'received "%s"' %data

	finally:
		print >>sys.stderr, 'closing socket'
		sock.close()