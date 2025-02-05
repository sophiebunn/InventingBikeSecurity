from picamera2 import Picamera2
import cv2
import numpy as np
import time

picam2 = Picamera2()
picam2.start_and_record_video("cv.mp4", duration=5)
time.sleep(1)
cap = cv2.VideoCapture('cv.mp4')

def motion_detection(frame):
    # Convert the frame to grayscale
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Apply background subtraction

    thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 11, 2)

    # Find contours
    _, contours = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    print(contours)
    # Iterate through contours
    for contour in contours:
        # Calculate the area of the contour
        area = cv2.contourArea(contour)

        # Ignore small contours
        if area < 100:
            continue

        # Draw a rectangle around the contour
        x, y, w, h = cv2.boundingRect(contour)
        cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)

    return frame

# Combine motion detection
while True:
    # Read a frame from the video
    ret, frame = cap.read()

    # Apply motion detection
    frame = motion_detection(frame)

    # Display the frame
    cv2.imshow('Frame', frame)

    # Exit on key press
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cv2.waitKey(0)
cv2.destroyAllWindows()
