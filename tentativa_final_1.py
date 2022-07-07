import cv2 as cv
import numpy as np
import os
import time, math
from tkinter import *
from detetor_func import rotationMatrixToEulerAngles

# Vamos  definir variáveis e flags, nesta zona
marker_size = 16.8
camera_width = 640
camera_height = 480

with open('camera_cal.npy', 'rb') as f:
    camera_matrix = np.load(f)
    camera_distortion = np.load(f)

flag_estima_pos = True

# Vamos definir aqui as funções a utilizar
def estimaPos(frame, bbox, ids):
        # rvec - Vetores de rotação
        # tvec - Vetores de translação

        # rvec diz-nos quanto temos que rodar num plano 3D para ficar paralelo ao aruco
        # tvec diz-nos quanto temos que andar para a frente e para os lados para centrar o aruco com o frame da camera

        # Usando estes dois vetores é possivel estimar facilmente a posição do ROV

    rvec_list, tvec_list, _objtPoints = cv.aruco.estimatePoseSingleMarkers(bbox, marker_size, camera_matrix, camera_distortion)

    for marker in range(len(ids)):
        #cv.aruco.drawAxis(frame, camera_matrix, camera_distortion, rvec_list[marker], tvec_list[marker], 60)

                # A diferenca entre as coordenadas Reais e as coordenadas da camera, prende-se pela orientação dos eixos
                # x_real -> z_camera
                # z_real -> y_camera
                # y_real -> x_camera

                # Para fazer esta conversão de orientação vamos recorrer a uma função existente em python
                
        rvec_flipped =  rvec_list[0][0] * -1    # Primeiro elemento da lista de vetores de rotação
        tvec_flipped =  tvec_list[0][0] * -1    # Primeiro elemento da lista de vetores de translação

        rotation_matrix, jacobian = cv.Rodrigues(rvec_flipped)  # Obtemos a matrix de rotação
        realworld_tvec = np.dot(rotation_matrix, tvec_flipped)   # Aplicamos a matrix para alterar a orientação dos eixos

                # Vamos então recorrer a uma matriz de rotação para descobrir o angulo de Euler de rotação atraves de uma conversão (código não original!)
                # Mais informação sobre este processo pode ser encontrada em: https://learnopencv.com/rotation-matrix-to-euler-angles/

        pitch, roll, yaw = rotationMatrixToEulerAngles(rotation_matrix)

                # Vamos agora escrever as distancias ao objeto nos eixos certos


    return [realworld_tvec[0],realworld_tvec[1],realworld_tvec[2],math.degrees(roll),math.degrees(pitch)]

    # -> função de deteção dos arucos

def findArucoMarkers(frame, matrix_dict =5, totalMarkers =1000, draw=True):
    frame_bw = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)

    # Temos de definir o dicionario que estamos a usar, neste caso, 5x5
    # Formato - arucoDict = aruco.Dictionary_get(aruco.DICT_5X5_100)
    # Contudo, para ser costumizavel pelos atributos, vamos recorrer a strings
    key = getattr(cv.aruco, f'DICT_{matrix_dict}X{matrix_dict}_{totalMarkers}')
    arucoDict = cv.aruco.Dictionary_get(key)

    # Apos definir o dicionario vamos recolher os parametros
    arucoParam = cv.aruco.DetectorParameters_create()

    # Passamos então à deteção dos markers
    # Temos como return as bounding boxes, os ids dos respetivos markers e os markers rejeitados sem ids
    bbox, ids, rejected = cv.aruco.detectMarkers(frame_bw, arucoDict, camera_matrix, camera_distortion)

    # Vamos imprimir ids para verificar quais foram detetados
    # print(ids)

    # Caso seja para desenhar, o aruco ja possui uma função para desenhar
    if ids is not None:
        cv.aruco.drawDetectedMarkers(frame, bbox) 
            


    # Vamos retornar as bbox e os respetivos ids
    return [bbox, ids]





# Main

cap = cv.VideoCapture(0)

cap.set(cv.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv.CAP_PROP_FRAME_HEIGHT, 480)
cap.set(cv.CAP_PROP_FPS, 40)

# Check if the webcam is opened correctly
if not cap.isOpened():
    raise IOError("Cannot open webcam")

new_frame = 0
prev_frame = 0

while True:
    # Tamanho do frame -> 640x480
    ret, frame = cap.read()
    new_frame = time.time()
    arucoFound = findArucoMarkers(frame)
    bbox = arucoFound[0]
    ids = arucoFound[1]

    #frame = cv.resize(frame, (960,720))
    fps = 1 / (new_frame - prev_frame)
    fps = int(fps)

    # Neste caso a distancia a parede vai ser o Pos[2] (o nosso Z) e distancia as laterais vai ser Pos[0] (o nosso x)
    if ids is not None and flag_estima_pos:
        Pos = estimaPos(frame, bbox, ids)
        tvec_str = "x=%4.0fcm  z=%4.0fcm"%(Pos[0],Pos[2])
        rot_str = "Rotation=%4.0f   Pitch=%4.0f"%(Pos[3],Pos[4])
        cv.putText(frame, tvec_str, (20, 460), cv.FONT_HERSHEY_COMPLEX, 0.6, (0,0,255), 2, cv.LINE_AA)
        cv.putText(frame, rot_str, (20, 400), cv.FONT_HERSHEY_COMPLEX, 0.6, (0,0,255), 2, cv.LINE_AA)


    #cv.putText(frame, str(fps) , (900, 25), cv.FONT_HERSHEY_PLAIN, 1.5, (255, 0 , 55),2)
    cv.putText(frame, str(fps) , (600, 25), cv.FONT_HERSHEY_PLAIN, 1.5, (255, 0 , 55),2)
    cv.imshow('Input', frame)

    prev_frame = new_frame

    key = cv.waitKey(1)
    if key == ord('q'):
        break

cap.release()
cv.destroyAllWindows()