import cv2
import time
#print(cv2.__version__)

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

#camSet = ("raspivid -n -t 0 -rot 180 -w 1440 -h 720 -fps 30 -b 6000000 -o - | gst-launch-1.0 -e -vvvv fdsrc ! h264parse ! rtph264pay pt=96 config-interval=5 ! udpsink clients=169.254.203.43:5600")
cap= cv2.VideoCapture(0)
print("antes de testar o out")

if not cap.isOpened():
    print("não consegui inicar video")

camSet_out_teste_wifi = ' appsrc  ! video/x-raw,format=BGR ! videoconvert ! x264enc !  rtph264pay ! rtpjitterbuffer latency=0 ! application/x-rtp,media=video,encoding-name=H264 ! udpsink clients=169.254.203.43:5600'
#camSet_out_teste_wifi = ' appsrc emit-signals=True is-live=True ! video/x-raw ! queue ! videoconvert ! udpsink clients=169.254.203.43:5600'
#camSet_out_teste_wifi = "appsrc ! video/x-raw  ! udpsink clients=169.254.203.43:5600"
#camSet_out_teste_wifi = 'appsrc ! x264enc ! mpegtsmux ! udpsink host=localhost port=5000'
#camSet_out_teste_wifi = "appsrc ! videoconvert ! x264enc noise-reduction=10000 tune=zerolatency byte-stream=true ! h264parse ! mpegtsmux ! rtpmp2tpay ! udpsink  clients=169.254.203.43:5600"
#camSet_out_teste_wifi = 'appsrc ! queue ! videoconvert ! video/x-raw ! x264enc ! h264parse ! rtph264pay ! udpsink clients=169.254.203.43:5600 sync=false'
#camSet_out_teste_wifi = 'appsrc ! videoconvert ! x264enc tune=zerolatency noise-reduction=10000 bitrate=2048 speed-preset=superfast ! rtph264pay config-interval=1 pt=96 ! udpsink clients=169.254.203.43:5600'
#camSet_out_teste_wifi = 'appsrc ! decodebin ! videoconvert ! openh264enc ! rtph264pay name=pay0 pt=96 config-interval=1 ! udpsink clients=169.254.203.43:5600'
#teste_tcp = 'appsrc ! videoconvert ! v4l2h264enc ! video/x-h264,level=(string)4 ! h264parse ! matroskamux ! tcpserversink clients=169.254.203.43 port=5600'
#camSet_out_teste_wifi = ("appsrc ! videoconvert ! udpsink clients=169.254.203.43:5600 ")
fourcc = cv2.VideoWriter_fourcc(*'H264')
#out = cv2.VideoWriter(camSet_out_teste_wifi, cv2.CAP_GSTREAMER, 0, 30, (640,480), True)
out = cv2.VideoWriter(camSet_out_teste_wifi ,fourcc , 30, (640, 480), True)


if not out.isOpened():
    print("não consegui enviar video")

#cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
#cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
#cap.set(cv2.CAP_PROP_FPS, 40)

new_frame = 0
prev_frame = 0


while True:
    ret, frame = cap.read()
    #print("consegui dar camRead")
    new_frame = time.time()
    if frame is not None:
              
        fps = 1 / (new_frame - prev_frame)
        fps = str(round(fps, 1))
        #print(frame.shape[0])
        #print(frame.shape[1])
        #print(fps)
        cv2.putText(frame, fps, (565, 30), cv2.FONT_HERSHEY_SIMPLEX,1 , (0,0,255), 2 , cv2.LINE_AA)
        #cv2.imshow('nanoCam',frame)
        prev_frame = new_frame
        cv2.imshow("sender", frame)
        out.write(frame)
        
    if cv2.waitKey(1)==ord('q'):
        break
cap.release()
out.release()
cv2.destroyAllWindows()