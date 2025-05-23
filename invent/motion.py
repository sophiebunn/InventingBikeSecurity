from picamera2 import Picamera2

import cv2
import numpy as np
import time

def motion_detection(frame, ctrl):  
    mtn = False

    #making image black & white, NECESSARY for thresholding and contouring
    #gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gray = frame
    #increase the Gaussian blur to decrease the amount of arbitrary noise between frames
    gray = cv2.GaussianBlur(gray, (51,51), 0)
    
    #comparing the control frame to the current frame
    frameDelta = cv2.absdiff(ctrl, gray)
    
    #make the threshold according to the difference between frames
    #this will return an image made black and white where white is the movement
    thresh = cv2.threshold(frameDelta, 25, 255, cv2.THRESH_BINARY)[1]
    thresh = cv2.dilate(thresh, None, iterations=2)    
    
    #find the contours (shapes) that are changing between frames
    cnts = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[0]
        
    for contour in cnts:
        area = cv2.contourArea(contour)

        #yes, this is a less than sign
        #making area less than EXCLUDES small contours
        if area < 100000:
            mtn = True
            continue

        #drawing a green rectangle around the moving objects in our original frame
        x, y, w, h = cv2.boundingRect(contour)
        cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)

    return mtn
