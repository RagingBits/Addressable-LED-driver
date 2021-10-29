import subprocess
import os
import sys
import time
import queue
from subprocess import PIPE, Popen
from threading  import Thread
import io
import serial
import argparse
import os.path
from pathlib import Path
import sys


serial_in_thr = Thread
serial_out_thr = Thread
threads_run = False
thread_ser_in_active = False
thread_ser_out_active = False
serial_port = serial

def serial_in(port, input_q):
	global threads_run
	global thread_ser_in_active
	thread_ser_in_active = True
	print("Serial In daemon started")
	try:
		while(thread_ser_in_active == True and threads_run == True):
			if(port.isOpen() == True):
				temp_data = port.read(1) 
				try:
					data = temp_data.decode('utf-8')
					for item in data.split():
						input_q.put(item)
				except:
					data = temp_data
					input_q.put(data)
					pass
				
				#print(data)
			else:
				thread_ser_in_active = False
	except:
		pass
		
	print("Serial In daemon stopped")
	thread_ser_in_active = False
	threads_run = False
	
def serial_out(port, output_q):
	global thread_ser_out_active
	global threads_run
	thread_ser_out_active = True
	print("Serial Out daemon started")
	try:
		while(thread_ser_out_active == True and threads_run == True):
			if(port.isOpen() == True):
				if(not output_q.empty()):
					data_raw = output_q.get()
					
					try:
						data = bytes(data_raw,'UTF-8')
					except:
						data = data_raw
					
					port.write(data)
				else:
					time.sleep(0.005)
			else:
				thread_ser_out_active = False
	except:
		thread_ser_out_active = False
		
	print("Serial Out daemon stopped")
	thread_ser_out_active = False
	threads_run = False

def serial_start(port_name, input_queue, output_queue):
	global threads_run
	global thread_ser_in_active
	global thread_ser_out_active
	serial_port = serial.Serial()
	print("Start serial connection.")
	while(serial_port.isOpen() == False):	
		time.sleep(1)
		
		if(thread_ser_in_active == False and thread_ser_out_active == False):
			print("Attempt to open serial port...")
			try:
				serial_port = serial.Serial(
				port=port_name,
				baudrate=38400,
				parity=serial.PARITY_ODD,
				stopbits=serial.STOPBITS_ONE,
				bytesize=serial.EIGHTBITS,
				timeout=1)
				print("Serial port open.")
				time.sleep(1)
			except:
				print("Failed.")

		else:
			print("Serial daemons still active.")

	threads_run = True
	print("Start serial daemons.")
	serial_in_thr = Thread(target=serial_in, args=(serial_port, input_queue))
	serial_in_thr.daemon = True # thread dies with the program
	serial_in_thr.start()
	
	serial_out_thr = Thread(target=serial_out, args=(serial_port, output_queue))
	serial_out_thr.daemon = True # thread dies with the program
	serial_out_thr.start()
		
	return serial_port

def serial_stop():	
	global serial_in_thr
	global serial_out_thr
	global serial_port
	
	print("Close serial connection.")
	serial_port.close()
	print("Close serial daemons.")
	threads_run = False
	print("Waiting serial daemons to stop...")
	while(thread_ser_in_active == True or thread_ser_out_active == True):
		print(".")
		time.sleep(1)
		
	print("Serial daemons stopped.")
	
	
def effects_start(file):
	
	success = False
	
	run = True	
	while(run == True):
		data = file.readline()
		
		if (not data):
			run = False
		else:
			if(data[:5]	== "{anim"):
				success = True
				run = False
				
	return success	

	
def effects_get_next_array(file):
	
	number_of_leds = 0
	array = []	
	
	run = True	
	while(run == True):
		data = file.readline()
		
		if (not data):
			run = False
		else:
			array_ = data.split(':')	
	
			if(array_[0] == 'w'):
				number_of_leds = int(array_[1])
			elif(array_[0] == 'r'):
				array = array_[1].split(' ')
				if(number_of_leds == 0):
					number_of_leds = 1
				run = False
				
	return number_of_leds, array
	
def effects_get_info_from_array_item(item):
	
	r = 0
	g = 0
	b = 0
	try:
		b = int(item[:2], 16)
		r = int(item[2:4], 16)
		g = int(item[4:], 16)
	except:
		pass
		
	return g,r,b
		
	
def main ():

	global serial_port
	
	
	
	parser = argparse.ArgumentParser(description='Xtms3Controller')
	parser.add_argument('-p', metavar='com_port', required=True, help='com port')
	
	parser.add_argument('-f', metavar='path', required=True, help='file of effects')
	
	args = parser.parse_args()

	port_name = args.p
	
	effects_file_name = args.f
	effects_file = Path(effects_file_name)
	
	if(effects_file.is_file() == False):
		print("Wrong file or path.")
		return
	
	
	effects_file = open(effects_file_name, "r")
	if(effects_start(effects_file) == False ):
		print("Invalid file.")
		return 
	total_number_leds, array = effects_get_next_array(effects_file)
	
	print("Strip length: ")
	print (total_number_leds)
	#print (array)
	
	red = [0] * total_number_leds
	green = [0] * total_number_leds
	blue = [0] * total_number_leds
	
	
	input_queue = queue.Queue()
	output_queue = queue.Queue()
	
	serial_port = serial_start(port_name,input_queue,output_queue)
	
	print("Start handshaking serial speed.")
	run = True
	while(run == True):
		output_queue.put("X")
		if(not input_queue.empty()):
			if(input_queue.get(1) == "X"):
				with output_queue.mutex:
					output_queue.queue.clear()
				run = False
		
		time.sleep(0.1)
		
	
	print("Setup LED strip length.")
	
	total_data_size = total_number_leds*3
	total_data_size_MSB,total_data_size_LSB = divmod(total_data_size, 256)
	temp_data = bytearray([total_data_size_MSB, total_data_size_LSB])
	print(total_data_size)
	output_queue.put('L')
	output_queue.put(temp_data)
	
	
	run = True
	while(run == True):
		if(not input_queue.empty()):
			if(input_queue.get() == 'Y'):
				with output_queue.mutex:
					output_queue.queue.clear()
				with input_queue.mutex:
					input_queue.queue.clear()
				run = False
		
		time.sleep(0.1)

	
	print("Running.")
	
			
	print_counter = 0
	
	while(1):
	
		#print (sys.stdin.read())
				
		if(threads_run == False):
			serial_port = serial_start(port_name,input_queue,output_queue)
			with output_queue.mutex:
				output_queue.queue.clear()
			with input_queue.mutex:
				input_queue.queue.clear()
			print("Running.")

		else:
		
			if(print_counter > 10):
				print(".")
				print_counter = 0
			else:
				print_counter = print_counter + 1

			r = 0
			g = 0
			b = 0
							
			counter = 0
			items_len = 0
			
			while(counter < total_number_leds):
				
				r,g,b = effects_get_info_from_array_item(array[counter])
				red[counter] = r&0x00FF
				green[counter] = g&0x00FF
				blue[counter] = b&0x00FF				
				temp_data=bytearray([red[counter],green[counter],blue[counter]])
				#print (temp_data)
				output_queue.put(temp_data)
				counter = counter+1
		
			num_items, array = effects_get_next_array(effects_file)
			
			if(not array):
				effects_file.close()
				effects_file = open(effects_file_name, "r")		
				if(effects_start(effects_file) == False ):
					print("Invalid file.")
					return 				
				num_items, array = effects_get_next_array(effects_file)
				
			
			run_this = threads_run
			counter = 101
			while(run_this != False and threads_run == True):
				#print("wait1")
				if(not input_queue.empty()):
					temp = input_queue.get(1)
					if(temp == "Y"):
						#print("y")
						run_this = False
				else:
					if(counter > 50):
						time.sleep(0.01)
						counter = counter - 1 
					elif(counter > 0):
						time.sleep(0.01)
						temp_data=bytearray([0])
						output_queue.put(temp_data)
						counter = counter - 1 
					else:
						run_this = False
						serial_stop()
						


			run_this = True
			counter = 101
			while(run_this == True and threads_run == True):
				#print("wait1")
				if(not input_queue.empty()):
					temp = input_queue.get(1)
					if(temp == "R" or temp == "Y"):
						#print("r")
						run_this = False
				else:
					if(counter > 0):
						time.sleep(0.01)
						counter = counter - 1 
					else:
						run_this = False
						serial_stop()
					
		
if __name__ == "__main__":
    main()

