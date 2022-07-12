import cv2 as cv
import time



cap = cv.VideoCapture(0)

cap.set(cv.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv.CAP_PROP_FRAME_HEIGHT, 480)
cap.set(cv.CAP_PROP_FPS, 40)

# Check if the webcam is opened correctly
if not cap.isOpened():
    raise IOError("Cannot open webcam")

new_frame = 0
prev_frame = 0

frame_count = 0
cal_img_count = 0
fileName = "cal"

while True:
    ret, frame = cap.read()
    new_frame = time.time()

    frame_count += 1
    if frame_count == 30:
        cv.imwrite("%s%d.jpg"%(fileName, cal_img_count), frame)
        cal_img_count += 1
        frame_count = 0

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