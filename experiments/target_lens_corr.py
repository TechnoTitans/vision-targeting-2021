# target_lens_corr.py by Kaushal Sambanna created on 12/03/2021

import sensor
import image
import time
import math
import ustruct
from pyb import USB_VCP, CAN
import pyb

# Specify communication method: "print" "usb" "can"
COMMS_METHOD = "print"
TARGET_WIDTH = 39.25
TARGET_HEIGHT = 17.00

# make USB_VCP object
# this lets us know if targets are being
# detected without having to print it and
# we can see if the target is aligned as well
usb = USB_VCP()
red = pyb.LED(1)
green = pyb.LED(2)
blue = pyb.LED(3)

SCREEN_CENTERP = 160 # screen center (pixels) horizontal
VERTICAL_CENTERP = 120 # screen center (pixels) vertical


sensor.reset() # Initialize the camera sensor.
sensor.set_pixformat(sensor.RGB565) # or sensor.RGB565
sensor.set_framesize(sensor.QVGA) # or sensor.QVGA (or others)
sensor.skip_frames(time = 2000) # Let new settings take affect.
clock = time.clock()

# setting autoexposure automatically
KMAN = 0.065 # constant for exposure setting
autoExposureSum = 0
readExposureNum = 10
for i in range(readExposureNum):
    autoExposureSum += sensor.get_exposure_us()

autoExposure = autoExposureSum/readExposureNum
manualExposure = int(autoExposure * KMAN) # scale factor for decreasing autoExposure
sensor.set_auto_exposure(False,  manualExposure) # autoset exposures

values_history = [] # for median function

# LAB color space
thresholds = [(20, 100), (-128, -24), (-48, 51)] # green light



HFOV = 62.3 #70.8 # horizontal field of view
VFOV = 55.6 # vertical field of view

def drawScope(img, blob): # draws a circle and crosshair where the center calculations are
    # scope view
    img.draw_cross(blob.cx(), (int(blob.cy() - (blob.h()/2))), size = 5, thickness = 1)
    img.draw_circle(blob.cx(),  (int(blob.cy() - (blob.h()/2))), 5,  thickness = 2)

    # bounding box
    img.draw_rectangle(blob.x(), blob.y(),blob.w(), blob.h())

def getCenterX(blob): # getting the center value of the blob in x coordinates
    targetCX = blob.cx()
    return targetCX

def getCenterY(blob): # getting the center value of the blob in y coordinates
    targetCY = blob.cy() - (blob.h()/2)
    return targetCY

def getDistanceVFOV(wa, ha, blob): # gets the distance with the actual width/height of the target

    d_1 = ha / (2*(math.tan(math.radians(VFOV/2))))
    d_2 = img.height() / blob.h()
    verticle_distance = d_1 * d_2
    corrected_Vdistance = verticle_distance + ((verticle_distance * 0.22018465) - 10.68580068)
    return corrected_Vdistance

def getDistanceHFOV(wa, ha, blob):

    d_1 = wa / (2*(math.tan(math.radians(HFOV/2))))
    d_2 = img.width() / blob.w()
    horizontal_distance = d_1 * d_2
    corrected_Hdistance = horizontal_distance + ((horizontal_distance * 0.22018465) - 10.68580068)
    return horizontal_distance

def getAngleX(VFOV, targetCX): # gets the angle the turret needs to turn to be aligned with the target

    deltaX = float(SCREEN_CENTERP - targetCX)
    num_1 = (2.0 * deltaX) * (math.tan(math.radians(HFOV/2.0)))
    angleX = math.degrees(math.atan(num_1/img.width()))
    return angleX


def getAngleY(HVOV, targetCY):

    deltaY = float(VERTICAL_CENTERP - targetCY)
    num_1 = (2.0 * deltaY) * (math.tan(math.radians(VFOV/2.0)))
    angleY = math.degrees(math.atan(num_1/img.height()))
    return angleY


def getUnfilteredValues(wa, ha, img, i):
    blobs = img.find_blobs(thresholds, area_threshold = 8)

    for blob in blobs:
        # filtering based on aspect ratio
        aspectRatio = (blob.w() / blob.h())

        # filters pixels, aspect ratio
        if((blob.pixels() >= 17500) or
            (blob.density() <.1) or (blob.density() > 0.4) or
            (aspectRatio <= .4*2.84) or (aspectRatio >= 1.5*2.84)):
            continue

        # ===Bounding Box===
        drawScope(img, blob)

        # ==Centers===
        targetCX = getCenterX(blob)
        targetCY = getCenterY(blob)

        # ===Distance===
        dv = getDistanceVFOV(TARGET_WIDTH, TARGET_HEIGHT, blob)
        dh = getDistanceHFOV(TARGET_WIDTH, TARGET_HEIGHT, blob)

        # ===Angle===
        angleX = getAngleX(VFOV, targetCX)
        angleY = getAngleY(HFOV, targetCY)

        # returns the final values
        valuesRobot = dh #[targetCX, targetCY, dh, angleX, angleY, blob.w()]

        # deletes distance if greater than 22 ft.
        #if (valuesRobot[2]  >= 300):
            #return None
        return valuesRobot

def beam(values): # function that shines the LED on the camera
    if(((values[3] >= -5) and (values[3] <= 5)) and (values[3] != -1)):
        green.on()
    elif(values != [-1,-1,-1,-1,-1,-1]):
        blue.on()
    elif(values == [-1,-1,-1,-1,-1,-1]):
        red.on()

def create_decimal_list(start, stop, step):
    BIG_NUM = 10**4
    return [round(i/BIG_NUM, 2) for i in range(int(start*BIG_NUM), int(stop*BIG_NUM), int(step*BIG_NUM))]

for i in create_decimal_list(1, 2, 0.05):
    time.sleep(1)
    img_main = sensor.snapshot()
    img = img_main.lens_corr(strength = i)

    # params: width actual of target and height actual of target
    # returns: centerX, centerY, distance, angleX, angleY, blob width pixels
    values = getUnfilteredValues(TARGET_WIDTH, TARGET_HEIGHT , img, i)
    if(values == None):
        values = -1 #[-1,-1,-1,-1,-1,-1] # makes values this when there is no blob detected
    #beam(values)

    if(COMMS_METHOD == "print"):
            print(values)
    elif(COMMS_METHOD == "usb"): # sending the data via USB serial to the robot
        # values = memoryview(values)
        usb.send(ustruct.pack("d", values[0], values[1], values[2], values[3], values[4], values[5]))
    elif(COMMS_METHOD == "can"):
        pass
