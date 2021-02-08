import sensor
import image
import time
import math
import ustruct
from pyb import USB_VCP, CAN
import pyb

# Specify communication method: "print" "usb" "can"
COMMS_METHOD = "usb"
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



HFOV = 70.8 # horizontal field of view
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
    d3 = ((ha/2.0)*img.height())
    d4 = 2.0*(blob.h()/2.0)*math.tan(math.radians(VFOV/2.0))
    dv = (d3/d4)
    dv =1.35*dv # fudge factor calcs 1.25 in front of init line
    return dv

def getDistanceHFOV(wa, ha, blob):
    d1 = ((wa/2.0)*img.width())
    d2 = 2.0*(blob.w()/2.0)*math.tan(math.radians(HFOV/2.0))
    dh = (d1/d2)
    dh = 1.35*dh # fudge factor calcs 1.35 behind init line
    return dh

def getAngleX(VFOV, targetCX, dv): # gets the angle the turret needs to turn to be aligned with the target
    thetaV = math.radians(VFOV/2.0)
    differenceC1 = SCREEN_CENTERP - targetCX
    a1 = 2*dv*math.tan(thetaV)
    angleDelta1 = (differenceC1*(a1))/(160.0) # angle delta for x
    anglex = math.degrees(math.atan(angleDelta1/dv)) # angle x degrees change needed
    return anglex

def getAngleY(HVOV, targetCY, dh):
    thetaH = math.radians(HFOV/2.0)
    differenceC2 = VERTICAL_CENTERP - targetCY
    a2 = 2*dh*math.tan(thetaH)
    angleDelta2 = (differenceC2*(a2))/(120.0) # angle delta for y
    angley = math.degrees(math.atan(angleDelta2/dh)) # angle y degrees change needed
    return angley


def getUnfilteredValues(wa, ha, img):
    blobs = img.find_blobs(thresholds, area_threshold = 10)

    for blob in blobs:
        # filtering based on aspect ratio
        aspectRatio = (blob.w() / blob.h())

        # filters pixels, aspect ratio
        if((blob.pixels() >= 17500) or
            (blob.density() <.15) or (blob.density() > 0.35) or
            (aspectRatio <= .45*2.84) or (aspectRatio >= 1.3*2.84)):
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
        angleX = getAngleX(VFOV, targetCX, dv)
        angleY = getAngleY(HFOV, targetCY, dh)

        # returns the final values
        valuesRobot = [targetCX, targetCY, dh, angleX, angleY, blob.w()]

        # deletes distance if greater than 22 ft.
        if (valuesRobot[2]  >= 300):
            return None
        return valuesRobot

def beam(values): # function that shines the LED on the camera 
    if(((values[3] >= -5) and (values[3] <= 5)) and (values[3] != -1)):
        green.on()
    elif(values != [-1,-1,-1,-1,-1,-1]):
        blue.on()
    elif(values == [-1,-1,-1,-1,-1,-1]):
        red.on()


while(True):
    img = sensor.snapshot()

    # params: width actual of target and height actual of target
    # returns: centerX, centerY, distance, angleX, angleY, blob width pixels
    values = getUnfilteredValues(TARGET_WIDTH, TARGET_HEIGHT , img)
    if(values == None):
        values = [-1,-1,-1,-1,-1,-1] # makes values this when there is no blob detected
    beam(values)

    if(COMMS_METHOD == "print"):
            print(values)
    elif(COMMS_METHOD == "usb"): # sending the data via USB serial to the robot
        # values = memoryview(values)
        usb.send(ustruct.pack("d", values[0], values[1], values[2], values[3], values[4], values[5]))
    elif(COMMS_METHOD == "can"):
        pass
