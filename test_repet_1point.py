from cgi import test
import time
import datetime
import os
import csv
from turtle import down
import pyniryo as pn

import sys
import time
import logging
import usb


def usb_read_setup():
    global d
    global log

    log = logging.getLogger(__name__)
    d = usb.core.find(idVendor=0x0fe7, idProduct=0x4001)

    if d is None:
        log.error("No Mitutoyo device matching 0fe7:4001 found")
        sys.exit(1)

    if d.is_kernel_driver_active(0):
        d.detach_kernel_driver(0)
    #except usb.USBError as e:
    #    pass # kernel driver is already detached
    #    #log.warning(str(e))

    d.reset()
    d.set_configuration(1)
    c = d.get_active_configuration()
    global epin
    epin = d.get_active_configuration().interfaces()[0].endpoints()[0]
    bmRequestType=0x40 # Vendor Host-to-Device
    bRequest=0x01
    wValue=0xA5A5
    wIndex=0
    d.ctrl_transfer(bmRequestType, bRequest, wValue, wIndex)

    bmRequestType=0xC0 # Vendor Device-to-Host
    bRequest=0x02
    wValue=0
    wIndex=0
    length=1
    res1 = d.ctrl_transfer(bmRequestType, bRequest, wValue, wIndex, length)
    log.debug("Device Vendor resp: {}".format(res1))

usb_read_setup()

def mitu_get_val():
    bmRequestType=0x40 #0b01000000
    bRequest=0x03
    wValue=0
    wIndex=0
    data = b"1\r"

    d.ctrl_transfer(bmRequestType, bRequest, wValue, wIndex, data)

    MAX_PKT=64
    reading = epin.read(MAX_PKT)
    time.sleep(.1)
    str_val = reading.tostring()
    str_val = str_val[5:-1]
    val = float(str_val)
    return val


##################################################


ip_eth = "169.254.200.200"
ip_wifi = "192.168.1.26"
robot = pn.NiryoRobot(ip_wifi)
cwd = os.getcwd()



def make_test_poses():
    test_poses = [[0.30, 0.0, 0.145, 0.0, 0.695, 0.0]]
    return test_poses

def write_val(val, file_name):
    with open(cwd + '/'+ file_name, mode='a') as filepath_data:
        test_write = csv.writer(filepath_data, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        test_write.writerow([datetime.datetime.now().strftime("%H:%M:%S"), val])


def init_file(file_name):
    with open(cwd + '/'+ file_name, mode='a') as filepath_data:
        test_write = csv.writer(filepath_data, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        test_write.writerow(['Time', 'Value'])
    

def write_mitu_val(file_name):
    val = mitu_get_val()
    write_val(val, file_name+'.csv')


def press_down(down_pose, offset, file_name):
    up_pose = down_pose[:]
    up_pose[2] += offset

    robot.move_pose(up_pose)
    time.sleep(1)
    write_mitu_val(file_name)

    robot.set_arm_max_velocity(20) # move at 20% max speed before pressing down

    robot.move_linear_pose(down_pose)
    time.sleep(2) # wait 2s before regestering measurement to stabilise robot arm.
    write_mitu_val(file_name)

    robot.move_pose(up_pose)
    time.sleep(1)

    robot.set_arm_max_velocity(100)




def main():
    robot.set_arm_max_velocity(100)
    robot.calibrate_auto()
    robot.move_to_home_pose()
    offset = 0.02 # move of 2cm up from measurement position
    n_iter = 400 # do 400 measurements
    csv_file_name = 'test_repet_1point'

    test_poses = make_test_poses()

    init_file(csv_file_name)

    for i in range(n_iter):
        for j, pose in enumerate(test_poses):
            press_down(pose, offset, csv_file_name)

    robot.move_to_home_pose()

    robot.close_connection()

if __name__ == "__main__":
    main()