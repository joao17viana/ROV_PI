import cv2 as cv
import numpy as np
import os
import sys, time, math
from tkinter import *
import random


# Copyright (c) 2016 Satya Mallick <spmallick@learnopencv.com>
# All rights reserved. No warranty, explicit or implicit, provided.

# Checks if a matrix is a valid rotation matrix.
def isRotationMatrix(R) :
    Rt = np.transpose(R)
    shouldBeIdentity = np.dot(Rt, R)
    I = np.identity(3, dtype = R.dtype)
    n = np.linalg.norm(I - shouldBeIdentity)
    return n < 1e-6


# Calculates rotation matrix to euler angles
# The result is the same as MATLAB except the order
# of the euler angles ( x and z are swapped ).
def rotationMatrixToEulerAngles(R) :

    assert(isRotationMatrix(R))
    
    sy = math.sqrt(R[0,0] * R[0,0] +  R[1,0] * R[1,0])
    
    singular = sy < 1e-6

    if  not singular :
        x = math.atan2(R[2,1] , R[2,2])
        y = math.atan2(-R[2,0], sy)
        z = math.atan2(R[1,0], R[0,0])
    else :
        x = math.atan2(-R[1,2], R[1,1])
        y = math.atan2(-R[2,0], sy)
        z = 0

    return np.array([x, y, z])

# Calculates Rotation Matrix given euler angles.
def eulerAnglesToRotationMatrix(theta) :
    
    R_x = np.array([[1,         0,                  0                   ],
                    [0,         math.cos(theta[0]), -math.sin(theta[0]) ],
                    [0,         math.sin(theta[0]), math.cos(theta[0])  ]
                    ])
        
        
                    
    R_y = np.array([[math.cos(theta[1]),    0,      math.sin(theta[1])  ],
                    [0,                     1,      0                   ],
                    [-math.sin(theta[1]),   0,      math.cos(theta[1])  ]
                    ])
                
    R_z = np.array([[math.cos(theta[2]),    -math.sin(theta[2]),    0],
                    [math.sin(theta[2]),    math.cos(theta[2]),     0],
                    [0,                     0,                      1]
                    ])
                    
                    
    R = np.dot(R_z, np.dot( R_y, R_x ))

    return R




def findArucoMarkers(frame, markerSize =5, totalMarkers =1000, draw=True):
    frame_bw = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)

    # Temos de definir o dicionario que estamos a usar, neste caso, 5x5
    # Formato - arucoDict = aruco.Dictionary_get(aruco.DICT_5X5_100)
    # Contudo, para ser costumizavel pelos atributos, vamos recorrer a strings
    key = getattr(cv.aruco, f'DICT_{markerSize}X{markerSize}_{totalMarkers}')
    arucoDict = cv.aruco.Dictionary_get(key)

    # Apos definir o dicionario vamos recolher os parametros
    arucoParam = cv.aruco.DetectorParameters_create()

    # Passamos então à deteção dos markers
    # Temos como return as bounding boxes, os ids dos respetivos markers e os markers rejeitados sem ids
    bbox, ids, rejected = cv.aruco.detectMarkers(frame_bw, arucoDict, parameters = arucoParam)

    # Vamos imprimir ids para verificar quais foram detetados
    # print(ids)

    # Caso seja para desenhar, o aruco ja possui uma função para desenhar
    if draw:
        cv.aruco.drawDetectedMarkers(frame, bbox) 

    # Vamos retornar as bbox e os respetivos ids
    return [bbox, ids]

# Nesta funcao vamos calcular a distancia ao centro do frame caso este se encontre entre os markers

def calcula_distancia_v2(bbox):

    marker_size = 7.4
    w_frame = 640
    l_frame = 480

    
    # Vamos agora definir os 4 quantos da bbox
    tl = bbox[0][0][0] , bbox[0][0][1]
    tr = bbox[0][1][0] , bbox[0][1][1]
    br = bbox[0][2][0] , bbox[0][2][1]
    bl = bbox[0][3][0] , bbox[0][3][1]


    # calculo do tamanho da folha em pixeis
    dist_t_x = tr[0] - tl[0]
    dist_t_x_y = abs(tr[1] - tl[1])
    dist_b_x = br[0] - bl[0]
    dist_b_x_y = abs(br[1] - bl[1])
    dist_t_w = math.sqrt((dist_t_x * dist_t_x) + (dist_t_x_y * dist_t_x_y))
    dist_b_w = math.sqrt((dist_b_x * dist_b_x) + (dist_b_x_y * dist_b_x_y))
    dist_w = (dist_t_w + dist_b_w)/2

    dist_r_y = br[1] - tr[1]
    dist_r_y_x = abs(tr[0] - br[0])
    dist_l_y = bl[1] - tl[1]
    dist_l_y_x = abs(tl[1] - bl[1])
    dist_r_l = math.sqrt((dist_r_y * dist_r_y) + (dist_r_y_x * dist_r_y_x))
    dist_l_l = math.sqrt((dist_l_y * dist_l_y) + (dist_l_y_x * dist_l_y_x))
    dist_l = (dist_r_l + dist_l_l)/2
    

    # Calculo do Focal Length
    # Realizando um ensaio com 6 amostras em linha reta, onde F = PxD/W
    # P - tamanho em pixeis, neste caso, dist_w
    # D - distância Real ao objeto (20,35,45,55,65,75) !!! INCHES !!!
    # D - distância Real ao objeto (50.8/88.9/114.3/139.7/165.1/190.5) !!! Cm !!!
    # W - tamanho real do objeto
    # Obtemos: media de F é 187.12 em inches (x2.54 para ter em cm)
    # Podemos então definir D
    Focal_Length = 187.12*2.54
    Dist_real = Focal_Length * marker_size / dist_w


    # Vamos calcular a distancia de um pixel (em cm)
    w_pixel = dist_w / marker_size
    l_pixel = dist_l / marker_size
    


    # Vamos calcular o centro do marker e do frame em x e em y
    center_marker_x = (dist_t_x/2 + dist_b_x/2)/2
    center_frame_x = w_frame/2

    center_marker_y = (dist_r_y/2 + dist_l_y/2)/2
    center_frame_y = l_frame/2

    
    # Vamos calcular a distancia em x e em y
    distancia_em_y_pixel = abs(center_frame_y - center_marker_y)
    distancia_em_y = l_pixel * distancia_em_y_pixel

    distancia_em_x_pixel = abs(center_frame_x - center_marker_x)
    distancia_em_x = w_pixel * distancia_em_x_pixel


    # Vamos calcular as distancias entre centros
    distancia_centros = math.sqrt((distancia_em_x * distancia_em_x) + (distancia_em_y * distancia_em_y))


    # distancia a parede
    distancia_parede = math.sqrt((distancia_centros * distancia_centros) + (Dist_real * Dist_real))


    return distancia_parede, distancia_em_y


def calcula_distancia_v1(bbox):
    marker_size = 25
    
    # Vamos agora definir os 4 quantos da bbox
    tl = bbox[0][0][0] , bbox[0][0][1]
    tr = bbox[0][1][0] , bbox[0][1][1]
    br = bbox[0][2][0] , bbox[0][2][1]
    bl = bbox[0][3][0] , bbox[0][3][1]


    # calculo do tamanho da folha em pixeis
    dist_t_x = tr[0] - tl[0]
    dist_t_y = tr[1] - tl[1]
    dist_b_x = br[0] - bl[0]
    dist_b_y = br[1] - bl[1]
    dist_t_w = math.sqrt(dist_t_x * dist_t_x) + (dist_t_y * dist_t_y)
    dist_b_w = (math.sqrt(dist_b_x * dist_b_x) + (dist_b_y * dist_b_y))
    dist_w = (dist_t_w + dist_b_w)/2

    # Calculo do Focal Length
    # Realizando um ensaio com 6 amostras em linha reta, onde F = PxD/W
    # P - tamanho em pixeis, neste caso, dist_w
    # D - distância Real ao objeto (20,35,45,55,65,75) !!! INCHES !!!
    # D - distância Real ao objeto (50.8/88.9/114.3/139.7/165.1/190.5) !!! Cm !!!
    # W - tamanho real do objeto
    # Obtemos: media de F é 187.12 em inches (x2.54 para ter em cm)
    # Podemos então definir D
    Focal_Length = 187.12*2.54
    Dist_real = Focal_Length * marker_size / dist_w

    return Dist_real

def AugmentAruco(bbox, id, img, imgAug, drawImg = True, drawId = True):

    # Vamos agora definir os 4 quantos da bbox
    tl = bbox[0][0][0] , bbox[0][0][1]
    tr = bbox[0][1][0] , bbox[0][1][1]
    br = bbox[0][2][0] , bbox[0][2][1]
    bl = bbox[0][3][0] , bbox[0][3][1]
    
    if drawImg:
        # Vamos agora calcuular o tamanho da imagem a dar Augment
        h,w,c = imgAug.shape

        # Warping - Exemplo: tl, neste caso, tem de ser o ponto (0,0)
        pts1 = np.array([tl, tr, br, bl])
        pts2 = np.float32([[0,0], [w,0], [w,h], [0,h]])

        # Criamos a matriz que nos vai ajudar na warp perspective
        matrix, _ = cv.findHomography(pts2, pts1)

        # Damos warp na imagem, ou seja, a nossa imgAug acompanha a distorção do código 
        imgOut = cv.warpPerspective(imgAug, matrix, (img.shape[1], img.shape[0]))

        # Vamos remover da imagem original a porção ocupada pelo codigo
        cv.fillConvexPoly(img, pts1.astype(int), (0,0,0))

        # Vamos combinar agora as duas imagens
        imgOut = img + imgOut

        if drawId:
            cv.putText(imgOut, str(id), (int(tl[0]), int(tl[1])), cv.FONT_HERSHEY_PLAIN, 2, (255,0,255),2)

        return imgOut
    
    if drawId:
        cv.putText(img, str(id), (int(tl[0]), int(tl[1])), cv.FONT_HERSHEY_COMPLEX, 2, (255,0,255), 2)

    return img