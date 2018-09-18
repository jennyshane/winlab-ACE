from __future__ import division
import os
import sys
import time
import struct
import threading
from observer import Flag

JS_MAX_ANALOG=32767
JS_MIN_ANALOG=-32768
JS_ANALOG_RANGE=65536
PAN_ANGLE_MIN=10
PAN_ANGLE_MAX=170
TILT_ANGLE_MIN=70
TILT_ANGLE_MAX=150

command_names={0: 'start_stream', 
        1: 'stop_stream',
        2: 'calib_start',
        3: 'calib_stop',
        4: 'calib_left',
        5: 'calib_right',
        6: 'dc_start',
        7: 'dc_stop'}

button_names={0:'A',
        1:'B',
        2:'X',
        3:'Y',
        4:'LB',
        5:'RB',
        6:'screen',
        7:'menu',
        8:'xbox'}

analog_names={0:'js1-x',
        1:'js1-y',
        2:'LT',
        3:'js2-x',
        4:'js2-y',
        5:'RT',
        6:'dpad-x',
        7:'dpad-y'}



class ControllerObject(object):

    def __init__(self, source=None):
        if source==None: 
            joystick_file='/dev/input/js0'
            self.source=open(joystick_file, 'rb') 
            print("opened joystick device file")
        else:
            self.source=source
        self.stop_event=threading.Event()
        self.proc_thread=threading.Thread(target=self.proc_thread)
        self.carlock=threading.Lock()
        self.camlock=threading.Lock()
        self.car_commands=[0, 90]
        self.cam_commands=[90, 90]

        self.handle_map={'js1-x':self.handleJS1_X, 'js1-y':None, 
                'js2-x':self.handleJS2_X, 'js2-y':self.handleJS2_Y,
                'LT':self.handleLT, 'RT':None, 'dpad-x':None, 'dpad-y':None, 
                'B':self.handleB, 'xbox':self.handleXbox, 'A':None, 'X':None,
                'Y':None, 'LB':None, 'RB':None, 'screen':None, 'menu':None}
        self.direction=True
        self.forceStop=False

    def start_thread(self):
        #start thread to read from source
        self.proc_thread.start()

    def proc_thread(self):
        #thread to read input from source
        while self.stop_event.isSet()==False:
            ev_buf=self.source.read(8)
            if ev_buf!=-1:
                time, value, in_type, in_id=struct.unpack('IhBB', ev_buf) #TODO FIXME
                if in_type==1 and self.handle_map[button_names[in_id]] is not None:
                    self.handle_map[button_names[in_id]](value)
                elif (in_type==2 and self.handle_map[analog_names[in_id]] is not None):
                    self.handle_map[analog_names[in_id]](value)
                elif in_type==3 and in_id in command_names.keys():
                    Flag(command_names[in_id], {})

    def stop_thread(self):
        #stops the thread. This must be called even if the thread terminates 
        self.stop_event.set()
        self.proc_thread.join()
            
    def carpoll(self):
        #returns a list with [thr, str] for car
        self.carlock.acquire()
        output=self.car_commands
        if self.forceStop==True:
            output[0]=0
            self.forceStop=False
        self.carlock.release()
        #print(output)
        return output

    def campoll(self):
        #returns a list with [pan, tilt] for camera
        self.camlock.acquire()
        output=self.cam_commands
        self.camlock.release()
        return output

    def registerFunction(self, input_name, function):
        if input_name in list(button_names.values()) or input_name in list(analog_names.values()):
            self.handle_map[input_name]=function
        else:
            print("failed to add callback for "+input_name)
    
    def analog_map(self, value, outmin, outmax):
        return ((value-JS_MIN_ANALOG)/JS_ANALOG_RANGE)*(outmax-outmin)+outmin

    def handleXbox(self, value):
        Flag("stop_stream", {})


    def handleB(self, value):
        if value==1:
            self.carlock.acquire()
            self.direction=(self.direction==False)
            self.car_commands[0]=0
            self.forceStop=True #shoot through protection? Not sure if needed
            self.carlock.release()

    def handleLT(self, value):
        mapped_val=self.analog_map(value, 0, 100)
        if abs(mapped_val)<10:
            thr=0
        else:
            thr=int(mapped_val) if self.direction else (-1)*int(mapped_val) 
        self.carlock.acquire()
        self.car_commands[0]=thr
        self.carlock.release()

    def handleJS1_X(self, value):
        mapped_val=self.analog_map(value, 50, 130)
        if abs(mapped_val-90)<3:
            mapped_val=90
        self.carlock.acquire()
        self.car_commands[1]=int(mapped_val)
        self.carlock.release()

    def handleJS2_X(self, value):
        mapped_val=self.analog_map(value, PAN_ANGLE_MIN, PAN_ANGLE_MAX)
        self.camlock.acquire()
        self.cam_commands[0]=PAN_ANGLE_MAX-int(mapped_val)+PAN_ANGLE_MIN
        self.camlock.release()

    def handleJS2_Y(self, value):
        mapped_val=self.analog_map(value, TILT_ANGLE_MIN, TILT_ANGLE_MAX)
        self.camlock.acquire()
        self.cam_commands[1]=int(mapped_val)
        self.camlock.release()

