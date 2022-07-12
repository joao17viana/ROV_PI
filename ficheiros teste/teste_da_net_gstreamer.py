import cv2
import config
import time

def send():

    cap = cv2.VideoCapture(0) #open the camera
    
    fourcc = cv2.VideoWriter_fourcc(*'H264')
    out = cv2.VideoWriter('appsrc ! videoconvert ! x264enc tune=zerolatency noise-reduction=10000 bitrate=2048 speed-preset=superfast ! rtph264pay config-interval=1 pt=96 ! udpsink host=169.254.203.43 port=5600',fourcc,30, (640,480),True) #ouput GStreamer pipeline
    
    time.sleep(1)
    if not out.isOpened():
        print('VideoWriter not opened')
        exit(0)

    while cap.isOpened():
        ret,frame = cap.read()

        if ret:


            # Write to pipeline
            out.write(frame)

            if cv2.waitKey(1)&0xFF == ord('q'):
                break

    cap_send.release()
    out_send.release()

send()