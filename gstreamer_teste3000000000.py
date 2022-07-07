import cv2
import time
print(cv2.__version__)

# Verificar o seguinte código
#https://forums.developer.nvidia.com/t/streaming-videos-from-opencv-to-gstreamer-on-udp-sink/140471

# codigos raspivid
#https://gstreamer.freedesktop.org/documentation/rpicamsrc/index.html?gi-language=c

# Cam properties
fps = 30.
frame_width = 1920
frame_height = 1080



dispW=640
dispH=480
flip=2

coordinate = (200,200)

#Uncomment These next Two Line for Pi Camera

# Nao funcionam
#camSet = ('videotestsrc pattern=snow ! videoconvert ! appsink')
#camSet = ('libcamerasrc ! video/x-raw width=640 height=480 framerate= 30 ! videoconvert ! appsink')
#camSet = ('libcamerasrc ! video/x-raw,width=480,height=640 ! glimagesink')

# Funciona
#camSet = ('libcamerasrc ! videoconvert ! appsink')
camSet = ('libcamerasrc ! videoconvert ! appsink')
#camSet = ("raspivid -n -t 0 -rot 180 -w 1440 -h 720 -fps 30 -b 6000000 -o - | gst-launch-1.0 -e -vvvv fdsrc ! h264parse ! rtph264pay pt=96 config-interval=5 ! udpsink clients=169.254.203.43:5600")

print("consegui dar camset")

camSet = ("raspivid -n -t 0 -rot 180 -w 1440 -h 720 -fps 30 -b 6000000 -o - | gst-launch-1.0 -e -vvvv fdsrc ! h264parse ! rtph264pay pt=96 config-interval=5 ! udpsink clients=169.254.203.43:5600")
cap= cv2.VideoCapture(0)

if not cap.isOpened():
    print("não consegui inicar video")

camSet_out = ("appsrc ! video/x-raw,format=BGR ! queue ! videoconvert ! h264parse ! rtph264pay ! udpsink host=169.254.203.43 port=5600 auto-multicast=0")
out = cv2.VideoWriter(camSet_out, cv2.CAP_GSTREAMER, 0, float(52), (1440,720), True)

if not out.isOpened():
    print("não consegui enviar video")

#cam.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
#cam.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
#cam.set(cv2.CAP_PROP_FPS, 40)

new_frame = 0
prev_frame = 0


while True:
    ret, frame = cap.read()
    #print("consegui dar camRead")
    new_frame = time.time()
    if frame is not None:
              
        fps = 1 / (new_frame - prev_frame)
        fps = str(round(fps, 1))
        #print(fps)
        cv2.putText(frame, fps, (560, 30), cv2.FONT_HERSHEY_SIMPLEX,1 , (0,0,255), 2 , cv2.LINE_AA)
        #cv2.imshow('nanoCam',frame)
        prev_frame = new_frame
        out.write(frame)
        cv2.imshow("sender", frame)
        
    if cv2.waitKey(1)==ord('q'):
        break
cap.release()
cv2.destroyAllWindows()