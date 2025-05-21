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
notUpdated = True


def update_page(motion_detected):
    global PAGE

    PAGE = """
    <html>
    <style>

.slidecontainer{
        width: 100%; 
        display: flex;
        flex-direction: row;
        justify-content:center;
        margin-top: 35px;
        align-items: center;
        }
    
        /*track*/
        .slider{
        -webkit-appearance: none; 
        appearance: none; 
        width:50%; 
        height: 10px;
        border-radius: 50px;
        background: #b6b6b6;
        outline: none;
        opacity: .6;
        -webkit-transitiion: .2s;
        
        transition: opacity .2;
        
        
    
        /*FIX OPACITY*/
    
        /*centering*/
        display: block; /* Make the image a block-level element */
        margin-left: 10px; /* Distribute left margin to the left side */
        margin-right: 10px; /* Distribute right margin to the right side */
        }
    
        .slider:hover{
            opacity: .8;
            
        }
    
        /*slider thumb (little circle)*/
        .slider::-webkit-slider-thumb{
            -webkit-appearance: none;
            appearance: none;
            width: 25px;
            height: 25px;
         
            border-radius: 100%;
            border-width: 100px;
            background: rgb(1, 150, 187);
    
            cursor: pointer;
    
        }
    
        p{
            margin-top: 100px;
            font-size: 25px;
            text-align: center;
            font-family: Arial;
            font-weight: bold;
    
        }
    /*create different file*/
    .centered {
    display: block; /* Make the image a block-level element */
    margin-left: auto; /* Distribute left margin to the left side */
    margin-right: auto; /* Distribute right margin to the right side */
}

.rounded-centered-video {
    border-radius: 30px; /* Adjust the value for desired roundness */
    /*width: 100%;  Make the video responsive */
    /*height: 100*/
    display: block; /* Make the image a block-level element */
    margin-left: auto; /* Distribute left margin to the left side */
    margin-right: auto; /* Distribute right margin to the right side */
}

/*padding??*/
.header {
  position: sticky;
  top: 0;
  color: #ffffff; /*use????*/
  background: #ffffff;
  margin-top: -8px; /*needed to use units!!*/
  margin-right: -8px;
  margin-left: -8px;

  margin-bottom: 1.5em;
}

.rectangle {
font-family: Arial;
font-weight: bold;
  height: 75px;
  width: 80%;
  color:white;
  background-color: rgb(255, 255, 255);
  border-radius:15px;
  text-align:center;
  justify-content:center;
  align-items: center;
  display: block; /* Make the image a block-level element */
    margin-left: auto; /* Distribute left margin to the left side */
    margin-right: auto; /* Distribute right margin to the right side */
    margin-bottom: 1.5em;
    margin-top: 1.5em;
    display: flex;
    color: rgb(42, 42, 42) /* how do we know this is referring to text?*/
}


.rectangle1 {
font-family: Arial;
font-weight: bold;
  height: 150px;
  width: 80%;
  color:white;
  background-color: rgb(255, 255, 255);
  border-radius:15px;
  text-align:center;
  flex-direction: column;
  justify-content:center;
  align-items: center;
  display: block; /* Make the image a block-level element */
    margin-left: auto; /* Distribute left margin to the left side */
    margin-right: auto; /* Distribute right margin to the right side */
    margin-bottom: 1.5em;
    margin-top: 1.5em;
    display: flex;
    color: rgb(42, 42, 42) /* how do we know this is referring to text?*/
}



.header-link{
    display: inline-flexbox; /*dif between inline flex and inline flexbox???*/
    margin-top: 45px;
    margin-left: 50px; /*REMEMBER to put px*/
    color: rgb(42, 42, 42);
    text-decoration: none;
    font-family: Arial;
    font-weight: bold;
}

/*add in font, font size, etc for all lables*/
.label-low{
    margin-left: 60px;
    margin-right: 10px;
    font-size: 15px;
    color: #6b6b6b;

}

.label-high{
    margin-left: 10px;
    margin-right: 60px;
    font-size: 15px;
    color: #6b6b6b;}



/*can make things obey two dif classes by just putting a space between (look at bookmarked button example)*/


    </style>
    <head>
        <title> BOK </title>
        
       
   </head>

   <!--Header-->
   <div class="header" style="display: flex">
    <img src="~/Documents/invent/icon.png" width="auto" height="100" alt ="image"> <!-- why did it stretch accross pg w width=100??-->
    <a class="header-link" href="stream.mjpg"> Configure </a>
    <a class="header-link" href="stream.mjpg"> History </a>
  </div>

   <body style="background-color:rgb(233, 234, 234);">
    <img class= "rounded-centered-video" src="stream.mjpg" width="80%" height="600"/>
   </body>

    <div class="rectangle">
        Motion variable place holder
    </div>
        <head>
            <title> Configure My BOK </title>
        </head>
        <div class = "rectangle1">
            Motion Detection Sensitivity
        <div class="slidecontainer">
            <div class="label-low">
            Low
            </div>
            <input type="range" min="1" max="100" value="50" class = "slider" id="m_Range">
            <div class="label-high">
            High  
        </div>
        </div>
    </div>
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
        #print(self)
        if self.path == '/':
            self.send_response(301)
            self.send_header('Location', '/index.html')
            self.end_headers()
            
        elif self.path == '/index.html':

            content = PAGE.encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.send_header('Content-Length', len(content))
            self.end_headers()
            self.wfile.write(content)

        elif self.path == '/stream.mjpg':
            global notUpdated
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

                    if motion.motion_detection(cv_frame, first_frame) and notUpdated == True:
                        #print('motion')
                        update_page(True)
                        self.updateWeb()
                        notUpdated = False
                    else:
                        update_page(False)
                        #self.updateWeb()

                    #self.path = '/stream.mjpg'
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
    
    def updateWeb(self):
        content = PAGE.encode('utf-8')
        self.send_header('Content-Type', 'text/html')
        self.send_header('Content-Length', len(content))
        self.end_headers()
        self.wfile.write(content)
                                                                                                                                                                                    
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