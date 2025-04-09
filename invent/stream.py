import io
import logging
import socketserver
from http import server
from threading import Condition
import motion
import cv2
from picamera2 import Picamera2
import numpy as np
from picamera2.encoders import JpegEncoder
from picamera2.outputs import FileOutput
from PIL import Image

#http://10.38.64.42:5458

not_set = True
first_frame = None

def update_page(motion_detected):
    global PAGE
    if motion_detected:
        motion_message = "motion detected"
    else:
        motion_message = "no motion detected"

    PAGE = f"""
    <html>
    <head>
        <title>Inventing Bike Security</title>
    </head>
    <body style="background-color:rgb(161, 161, 187);">
        <h1 style="color:rgb(94, 56, 124); font-family:courier; font-size:200%; text-align:left;">Current Feed: </h1>
        <img src="stream.mjpg" width="640" height="480"/>
        <h2 style="color:rgb(94, 56, 124); font-family:courier; font-size:200%; text-align:right; vertical-align:top; "> {motion_message} </h2>
    </h1> 
    </body>
    </html>
    """

update_page(False)

class StreamingOutput(io.BufferedIOBase):
    def __init__(self):
        self.frame = None
        self.condition = Condition()

    def write(self, buf):
        with self.condition:
            self.frame = buf
            self.condition.notify_all()


class StreamingHandler(server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(301)
            self.send_header('Location', '/index.html')
            self.end_headers()
        elif self.path == '/index.html':
            print('html')
            content = PAGE.encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.send_header('Content-Length', len(content))
            self.end_headers()
            self.wfile.write(content)
        elif self.path == '/stream.mjpg':
            self.send_response(200)
            self.send_header('Age', 0)
            self.send_header('Cache-Control', 'no-cache, private')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Content-Type', 'multipart/x-mixed-replace; boundary=FRAME')
            self.end_headers()
            try:
                while True:
                    with output.condition:
                        output.condition.wait()
                        frame = output.frame
                        frame_arr = Image.open(io.BytesIO(frame))
                        frame_arr = np.asarray(frame_arr)
                        cv_frame = cv2.cvtColor(frame_arr, cv2.COLOR_BGR2GRAY)
                    if not_set == True:
                        first_frame = cv_frame
                    if motion.motion_detection(cv_frame, first_frame):
                        #print('motion????')
                        update_page(True)
                    else:
                        update_page(False)

                    content = PAGE.encode('utf-8')
                    self.send_header('Location', '/index.html')
                    self.send_header('Content-Type', 'text/html')
                    self.send_header('Content-Length', len(content))
                    self.end_headers()
                    self.wfile.write(content)

                    self.wfile.write(b'--FRAME\r\n')
                    self.send_header('Content-Type', 'image/jpeg')
                    self.send_header('Content-Length', len(frame))
                    self.end_headers()
                    self.wfile.write(frame)
                    self.wfile.write(b'\r\n')

            except Exception as e:
                logging.warning(
                    'Removed streaming client %s: %s',
                    self.client_address, str(e))
        else:
            self.send_error(404)
            self.end_headers()
                                                                                                                                                                                       

class StreamingServer(socketserver.ThreadingMixIn, server.HTTPServer):
    allow_reuse_address = True
    daemon_threads = True


picam2 = Picamera2()
picam2.configure(picam2.create_video_configuration(main={"size": (640, 480)}))
output = StreamingOutput()

picam2.start_recording(JpegEncoder(), FileOutput(output))

try:
    address = ('', 5458)
    server = StreamingServer(address, StreamingHandler)
    server.serve_forever()
finally:
    picam2.stop_recording()