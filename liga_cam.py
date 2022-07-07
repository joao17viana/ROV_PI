import cv2 as cv
import time



# gst-launch-1.0 libcamerasrc ! 'video/x-raw,width=1280,height=720' ! \glimagesink
#str = ('videotestsrc ! videoconvert ! appsink')
#str = ("libcamerasrc ! 'video/x-raw,width=1280,height=720' ! \glimagesink")
str_pipe = "v4l2src ! videoconvert ! appsink"
cap = cv.VideoCapture(str_pipe)

cap.set(cv.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv.CAP_PROP_FRAME_HEIGHT, 480)
cap.set(cv.CAP_PROP_FPS, 40)

# Check if the webcam is opened correctly
if not cap.isOpened():
    raise IOError("Cannot open webcam")

new_frame = 0
prev_frame = 0

while True:
    ret, frame = cap.read()
    if frame is None:
        print("Não estou a capturar video")
    new_frame = time.time()

    cv.imshow('Input', frame)

    fps = 1 / (new_frame - prev_frame)
    fps = int(fps)
    frame = cv.flip(frame, 1)
    cv.putText(frame, str(fps) , (600, 25), cv.FONT_HERSHEY_PLAIN, 1.5, (255, 0 , 55),2)
    cv.imshow('Input', frame)

    prev_frame = new_frame
    key = cv.waitKey(1)
    if key == ord('q'):
        break

cap.release()
cv.destroyAllWindows()