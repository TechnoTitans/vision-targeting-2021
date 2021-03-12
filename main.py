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

HFOV = 62.3  # 70.8 # horizontal field of view
VFOV = 55.6  # vertical field of view

SCREEN_CENTERP = 160  # screen center (pixels) horizontal
VERTICAL_CENTERP = 120  # screen center (pixels) vertical

THRESHOLDS = [(20, 100), (-128, -24), (-48, 51)]  # LAB Color space, green light

# make USB_VCP object
# this lets us know if targets are being
# detected without having to print it and
# we can see if the target is aligned as well
usb = USB_VCP()
red = pyb.LED(1)
green = pyb.LED(2)
blue = pyb.LED(3)

sensor.reset()  # Initialize the camera sensor.
sensor.set_pixformat(sensor.RGB565)  # or sensor.RGB565
sensor.set_framesize(sensor.QVGA)  # or sensor.QVGA (or others)
sensor.skip_frames(time=2000)  # Let new settings take affect.
clock = time.clock()

# TODO: See if we even need this
# setting autoexposure automatically
KMAN = 0.065  # constant for exposure setting
autoExposureSum = 0
readExposureNum = 10
for i in range(readExposureNum):
    autoExposureSum += sensor.get_exposure_us()

autoExposure = autoExposureSum / readExposureNum
manualExposure = int(autoExposure * KMAN)  # scale factor for decreasing autoExposure
sensor.set_auto_exposure(False, manualExposure)  # autoset exposures


def drawScope(img, blob):  # draws a circle and crosshair where the center calculations are
    # scope view
    img.draw_cross(blob.cx(), (int(blob.cy() - (blob.h() / 2))), size=5, thickness=1)
    img.draw_circle(blob.cx(), (int(blob.cy() - (blob.h() / 2))), 5, thickness=2)

    # bounding box
    img.draw_rectangle(blob.x(), blob.y(), blob.w(), blob.h())


def getCenterX(blob):  # getting the center value of the blob in x coordinates
    targetCX = blob.cx()
    return targetCX


def getCenterY(blob):  # getting the center value of the blob in y coordinates
    targetCY = blob.cy() - (blob.h() / 2)
    return targetCY


def getDistanceVFOV(blob):  # gets the distance with the actual width/height of the target
    constant_term = (TARGET_HEIGHT * img.height()) / (2 * (math.tan(math.radians(VFOV / 2))))
    vertical_distance = constant_term / blob.h()
    # TODO: Get vertical correction values
    corrected_V_distance = vertical_distance + ((vertical_distance * 0.22018465) - 10.68580068)
    return corrected_V_distance


def getDistanceHFOV(blob):
    constant_term = (TARGET_WIDTH * img.height()) / (2 * (math.tan(math.radians(HFOV / 2))))
    horizontal_distance = constant_term / blob.w()
    corrected_H_distance = horizontal_distance + ((horizontal_distance * 0.22018465) - 10.68580068)
    return corrected_H_distance


def getAngleX(targetCX):  # gets the angle the turret needs to turn to be aligned with the target
    deltaX = float(SCREEN_CENTERP - targetCX)
    constant_term = (2.0 * (math.tan(math.radians(HFOV / 2.0))))/img.width()
    angleX = math.degrees(math.atan(constant_term * deltaX))
    return angleX


def getAngleY(targetCY):
    deltaY = float(SCREEN_CENTERP - targetCY)
    constant_term = (2.0 * (math.tan(math.radians(VFOV / 2.0))))/img.height()
    angleY = math.degrees(math.atan(constant_term * deltaY))
    return angleY


def getUnfilteredValues(img):
    blobs = img.find_blobs(THRESHOLDS, area_threshold=8)

    for blob in blobs:
        # filtering based on aspect ratio
        aspectRatio = (blob.w() / blob.h())

        # filters pixels, aspect ratio
        if ((blob.pixels() >= 17500) or
                (blob.density() < 0.1) or (blob.density() > 0.4) or
                (aspectRatio <= .4 * 2.84) or (aspectRatio >= 1.5 * 2.84)):
            continue

        # ===Bounding Box===
        drawScope(img, blob)

        # ==Centers===
        targetCX = getCenterX(blob)
        targetCY = getCenterY(blob)

        # ===Distance===
        dv = getDistanceVFOV(blob)
        dh = getDistanceHFOV(blob)

        # ===Angle===
        angleX = getAngleX(targetCX)
        angleY = getAngleY(targetCY)

        # returns the final values
        valuesRobot = [targetCX, targetCY, dh, angleX, angleY, blob.w()]

        return valuesRobot

    return [-1, -1, -1, -1, -1, -1]


def beam(values):  # function that shines the LED on the camera
    if ((values[3] >= -5) and (values[3] <= 5)) and (values[3] != -1):
        green.on()
    elif values != [-1, -1, -1, -1, -1, -1]:
        blue.on()
    elif values == [-1, -1, -1, -1, -1, -1]:
        red.on()


while True:
    img_main = sensor.snapshot()
    img = img_main.lens_corr(strength=1.1)

    # params: image
    # returns: centerX, centerY, distance, angleX, angleY, blob width pixels
    values = getUnfilteredValues(img)

    beam(values)

    if COMMS_METHOD == "print":
        print(values)
    elif COMMS_METHOD == "usb":  # sending the data via USB serial to the robot
        # values = memoryview(values)
        usb.send(ustruct.pack("d", values[0], values[1], values[2], values[3], values[4], values[5]))
    elif COMMS_METHOD == "can":
        pass
