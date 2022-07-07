import time, math
import paho.mqtt.client as mqttClient
import serial
import threading
import var
import Definir
import Motores
from detetor_func import rotationMatrixToEulerAngles
import statistics
import ssl
import cv2 as cv
import numpy as np
from random import randint
from subprocess import call
from subprocess import run
#time.sleep(120)

#Flag de shutdown
exit_event= threading.Event()

vetor = "0 0 0 0 0 0"
depth = "000"
pressure = "0000.00"
altera = 0
client = 0
liga_lamp = 1
desliga_lamp = 0
var.rot_e = 0
var.rot_d = 0
var.w = 0
var.a = 0
var.d = 0
var.s = 0
var.profundidade_atual = 0
var.nova_profundidade = 0
var.altera = 0
var.velocidade = 0
var.luz = 0
var.sos = 0
var.x = "000"
var.y = "000"
var.mutex = 0
disconnect = 0
stop_connection = 0
var.Vprof = []


Motor = 0
var.Vprof = Definir.Vetor_prof()

class thread1(threading.Thread):
    def __init__(self):        
        threading.Thread.__init__(self)
        
    def run(self):
        global client
        Connected = False                                  #global variable for the state of the connection
         
        broker_address= "169.254.76.3"                  #Raspberry Pi IP
        #broker_address= "169.254.52.172"
        port = 1883                                        #Communication default MQTT port
        user = "username"                                  #MQTT broker username
        password = "123"                                   #MQTT broker password
         
        client = mqttClient.Client("Python")               #Create new instance
        client.username_pw_set(user, password=password)    #Set username and password
        client.on_connect= on_connect                      #Attach function to callback
        client.on_message = on_message
        client.connect(broker_address, port=port)          #Connect to broker
         
        client.loop_start()                                #Start the loop
        
        while True:
            read_arduino()                                 #Read sensors values from Arduino           
            if exit_event.is_set():
                client.disconnect()
                client.loop_stop()
                break
            
             
def read_arduino():
    global depth, pressure, client
    var.ser = serial.Serial('/dev/ttyUSB0', 9600, timeout=1)     #Stablish the serial communication
    var.ser.reset_input_buffer()                                 #Reset the input buffer
    time.sleep(2)
    while True:
        time.sleep(0.1)                                        
        if var.ser.in_waiting > 0 and var.mutex == 0:            #Verifies if there's something available on serial
            #time.sleep(1)
            line = var.ser.readline().decode('utf-8').rstrip()   #Read and decode what Arduino have sent to serial
            if(line == "Bar30 Failed"):
                line = "Bar30failed"
                print(line)
            else: 
                #var.x = str(randint(100,800))
                #var.y = str(randint(100,400))
                #print("Sending data from sensors")
                line = line[0:23]                                        #String "line" example: 0953.00/27.97/05.00/0/0/180/304/
                #print(line)
                if(len(line) == 22):
                    line = line[0:23] + var.x + "/" + var.y + "/"
                    #print(line)
                    #var.profundidade_atual = float(line[14:19]) * 100    #Update depth and convert to cm
                    #var.Vprof = Definir.Atualiza_Vetor_prof(var.profundidade_atual, var.Vprof)
                    #print(var.profundidade_atual)                                      
                    client.publish("test",line)                          #Send "line" to interface       
                    client.subscribe("motores")                          #Subscribe the topic where the interface is sending the inputs
            if exit_event.is_set():
                 break

     
def on_connect(client, userdata, flags, rc):
     
    if rc == 0:
     
        print("Connected to broker")
        client.subscribe("motores")                              #Subscribe the topic where the interface is sending the inputs                      
     
    else:
     
        print("Connection failed")                               #If connection fails the broker will try to reconnect automatically
            
    # Callback Function on Receiving the Subscribed Topic/Message
def on_message( client, userdata, msg):
    # print the message received from the subscribed topic    
    vetor = str(msg.payload)                                     #Data received from interface
    print(vetor)
    var.w = int(vetor[2])                                        #Split the received string to the corresponding inputs
    var.a = int(vetor[4])
    var.d = int(vetor[6])
    var.s = int(vetor[8])
    var.nova_profundidade = int(vetor[10:13])
    var.altera = int(vetor[14])
    var.velocidade = int(vetor[16:18])
    var.luz = int(vetor[19])
    var.sos = int(vetor[21])
    var.rot_e = int(vetor[23])
    var.rot_d = int(vetor[25])
    #print("lampada " + str(var.luz))
    #print("rot_e " + str(var.rot_e))
    #time.sleep(0.5)

class thread2(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        
    def run(self):
        global Motor , vetor
        Motor = Definir.CarregaMotores() 
        #Definir.SetUp_Motores(Motor)
        Matriz = Definir.Cria_Matriz()
        #print("Estão criadas todas as condiçoes de trabalho")
        lamp = Definir.SetUp_Lampada()
        lamp_bool = 0
        while(1):
            if(var.altera == 1):
                var.profundidade_atual = 0
                while(1):
                    var.profundidade_atual = var.profundidade_atual + 2
                    time.sleep(0.5)
                    print(var.profundidade_atual)
                    if(var.profundidade_atual >= 180):
                        var.profundidade_atual = 0
                    
            time.sleep(0.5)            #Comentado pelo roberto
            Matriz, Motor = Motores.Matriz_Atc(Matriz,Motor)
            if(var.rot_e):
                Motor = Motores.Limpa_Matriz(Motor)
                Motor = Motores.Rotar_XY(Motor, (var.rot_e * -1))      ##O -1 é o parametro passado a função, só multiplico porque fica bontio
            if(var.rot_d):
                Motor = Motores.Limpa_Matriz(Motor)
                Motor = Motores.Rotar_XY(Motor, var.rot_d)  
            if(var.luz):
                if(lamp_bool == 0):
                    Definir.Controla_Lampada(liga_lamp, lamp)
                    lamp_bool = 1
            else:
                if(lamp_bool == 1):
                    Definir.Controla_Lampada(desliga_lamp, lamp)
                    lamp_bool = 0
            #print (vetor[11:14])
            if vetor[var.sos]== 1:
                call("sudo shutdown -h now",shell=True)
                
            
            
class thread3(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        
    def run(self):
        global Motor

        time.sleep(2)
        if Motor != 0:
            tempo = 0
            while(1):
                print(var.altera)
                while(var.altera == 0):
                    time.sleep(0.1)
                    aux = Definir.Det_Vetor_Medias(var.Vprof)
                    sentido = Definir.Det_tendencia(aux)
                    ## print(aux)
                    if(sentido != -1):
                        Motor = Motores.Manter_Profundidade(Motor, sentido)
                        tempo = time.time()
                        while(tempo + 1 > time.time()):                   ##Bussy Wait, 
                            if(altera == 1):break
                        Motor[0] = Motores.Desliga_Motor(Motor[0], 0)
                        Motor[1] = Motores.Desliga_Motor(Motor[1], 0)
                        tempo = time.time()
                        while(tempo + 1.2 > time.time()):                   ##Bussy Wait, espera que o vetor atualize 
                            if(altera == 1):break
                Motor = Motores.Altera_Profundidade(Motor, var.nova_profundidade)
                
                
                


class thread4(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        
    def run(self):
        # Main
        print("Entrei na thread da camera")
        # Vamos  definir variáveis e flags, nesta zona
        # Codigo da camera a partir daqui:

        marker_size = 16.8
        camera_width = 640
        camera_height = 480
        largura_tanque = 400
        comprimento_tanque = 800 

        # Vamos definir os Idsd

        id_fundo_esquerda = 5
        id_fundo_direita = 10 
        id_inicial_esquerda = 1
        id_inicial_direita = 6
        id_direita = 11
        id_esquerda  = 12
        list_ids = [id_fundo_esquerda,id_fundo_direita,id_inicial_esquerda,id_inicial_direita,id_direita,id_esquerda]

        # Vamos definir a rotacao de cada id
        deg_fundo = 0 
        deg_inicial = 180
        deg_direita = 90
        deg_esquerda = 270

        total_de_frames = 0
        N_frames_val = 15

        max_ids = 6
        linhas, colunas = ( (N_frames_val)+1,max_ids)
        n_ids = 0
        len_n_ids = 0
        aux_inicial = 0
        aux_inicial_2 = 0

        Pos_x = [[0 for i in range(linhas)] for y in range(colunas)]
        Pos_y = [[0 for i in range(linhas)] for y in range(colunas)]
        Pos_rot = [[0 for i in range(linhas)] for y in range(colunas)]

        for i in range(max_ids):
            Pos_x[i][0] = list_ids[i]
            Pos_y[i][0] =  list_ids[i]
            Pos_rot[i][0] = list_ids[i]






        # Define das localizacoes dos codigos
        class id_location:
            def __init__(self, x, y, id, deg):
                self.x = x
                self.y = y
                self.id = id
                self.deg = deg


        ids_paredes = []

        # Parede fundo

        ids_paredes.append(id_location(0,0,id_fundo_esquerda, deg_fundo))
        ids_paredes.append(id_location(0,largura_tanque,id_fundo_direita, deg_fundo))

        # Parede inical
        ids_paredes.append(id_location(comprimento_tanque, 0, id_inicial_esquerda, deg_inicial))
        ids_paredes.append(id_location(comprimento_tanque, largura_tanque, id_inicial_direita, deg_inicial))

        # Parede direita
        ids_paredes.append(id_location(largura_tanque/2,comprimento_tanque, id_direita, deg_direita))


        # Parede esquerda
        ids_paredes.append(id_location(largura_tanque/2,0, id_esquerda, deg_esquerda))
        
        with open('camera_cal.npy', 'rb') as f:
            camera_matrix = np.load(f)
            camera_distortion = np.load(f)
        
        flag_estima_pos = True
        
        
        
        #capSet = 'libcamerasrc !  videoconvert ! appsink'
        #capSet = 'libcamerasrc !      video/x-raw,colorimetry=bt709,format=NV12,width=1280,height=720,framerate=30/1 !      jpegenc ! multipartmux !      tcpserversink host=0.0.0.0 port=5000'


        #cap = cv.VideoCapture('libcamerasrc  !   video/x-raw,width=640,height=480,framerate=30/1 ! appsink')
        
        #cap = libcamerasrc ! h264parse ! rtph264pay pt=96 config-interval=5 ! udpsink clients=192.168.2.1:5000
        
        cap = cv.VideoCapture(0)
        print("arroz")
        
        # Nao podemos usar o cap.set quando usamos o gstreamer
        #cap.set(cv.CAP_PROP_FRAME_WIDTH, 640)
        #cap.set(cv.CAP_PROP_FRAME_HEIGHT, 480)
        #cap.set(cv.CAP_PROP_FPS, 40)

        # Check if the webcam is opened correctly
        if not cap.isOpened():
            raise IOError("Cannot open webcam")

        new_frame = 0
        prev_frame = 0

        while True:
            # Tamanho do frame -> 640x480
            ret, frame = cap.read()
            new_frame = time.time()
            if frame is not None:
                arucoFound = findArucoMarkers(frame)
                #print("aruco found")
                bbox = arucoFound[0]
                ids = arucoFound[1]

                #frame = cv.resize(frame, (960,720))
                fps = 1 / (new_frame - prev_frame)
                fps = int(fps)


                # Neste caso a distancia a parede vai ser o Pos[2] (o nosso Z) e distancia as laterais vai ser Pos[0] (o nosso x)
                if ids is not None:
                    if len_n_ids == len(ids):
                        aux_mudanca = 0
                        for i in range(len(ids)):
                            if(ids[i][0] == n_ids[i][0]):
                                aux_mudanca += 1
                        if aux_mudanca == len(ids):
                            total_de_frames += 1
                        else:
                            total_de_frames = 0
                            aux_inicial = 0
                            print("Apaguei")
                            Pos_x, Pos_y, Pos_rot = limpa_arrays(list_ids, linhas, colunas, max_ids)

                    else:
                        total_de_frames = 0
                        aux_inicial = 0
                        print("Apaguei")
                        Pos_x, Pos_y, Pos_rot = limpa_arrays(list_ids, linhas, colunas, max_ids)

                    if flag_estima_pos:
                        aux_inicial += 1
                        if(aux_inicial == 1):
                            total_de_frames += 1
                        n_ids = ids
                        len_n_ids = len(ids)
                        for aux in range(len(ids)):
                            Pos = estimaPos(frame, bbox[aux], ids[aux], camera_matrix, camera_distortion, marker_size)
                            #print("Pos x", Pos[2] )
                            #print("Pos y", Pos[0] )
                            
                            Pos_Tanque_aux = calcula_posicao_tanque(ids[aux], Pos[2], Pos[0], aux, ids_paredes, comprimento_tanque, largura_tanque)
                            #print("Pos x tanque", Pos_Tanque_aux[0])
                            #print("Pos x tanque", Pos_Tanque_aux[1])

                            i = encontra_id(ids[aux][0], max_ids, list_ids)

                            Pos_x[i][total_de_frames] = round(Pos_Tanque_aux[0], 4)
                            Pos_y[i][total_de_frames] = round(Pos_Tanque_aux[1], 4)
                            Pos_rot[i][total_de_frames] = round(Pos[3], 4)


                        # Vamos ter de analisar aqui as posições no tanque tendo em conta a validação
                        if (total_de_frames >= (N_frames_val - 1)):
                            Pos_tanque_final = Validacao_pos(ids, list_ids, N_frames_val, max_ids, Pos_x, Pos_y, Pos_rot)
                            aux_inicial_2 = 1
                            Pos_x, Pos_y, Pos_rot = limpa_arrays(list_ids, linhas, colunas, max_ids)
                            total_de_frames = 0

                    if aux_inicial_2 == 1:
                        tvec_str = "x=%4.0fcm  y=%4.0fcm"%(Pos_tanque_final[0],Pos_tanque_final[1])
                        rot_str = "Rotation=%4.0f "%(Pos_tanque_final[2])
                        cv.putText(frame, tvec_str, (20, 460), cv.FONT_HERSHEY_COMPLEX, 0.6, (0,0,255), 2, cv.LINE_AA)
                        cv.putText(frame, rot_str, (20, 400), cv.FONT_HERSHEY_COMPLEX, 0.6, (0,0,255), 2, cv.LINE_AA)



                #cv.putText(frame, str(fps) , (900, 25), cv.FONT_HERSHEY_PLAIN, 1.5, (255, 0 , 55),2)
                cv.putText(frame, str(fps) , (600, 25), cv.FONT_HERSHEY_PLAIN, 1.5, (255, 0 , 55),2)
                #print(fps)
                cv.imshow('Input', frame)

                prev_frame = new_frame

                key = cv.waitKey(1)
                if key == ord('q'):
                    break

        cap.release()
        cv.destroyAllWindows()
        
def encontra_id(id_aux, max_ids, list_ids):
    aux_i = 0
    for i in range(max_ids):
        if(id_aux == list_ids[i]):
            aux_i = i
    return aux_i                

def limpa_arrays(list_ids, linhas, colunas, max_ids):
    #print("fui chamado")
    Pos_x = [[0 for i in range(linhas)] for y in range(colunas)]
    Pos_y = [[0 for i in range(linhas)] for y in range(colunas)]
    Pos_rot = [[0 for i in range(linhas)] for y in range(colunas)]

    for i in range(max_ids):
        Pos_x[i][0] = list_ids[i]
        Pos_y[i][0] =  list_ids[i]
        Pos_rot[i][0] = list_ids[i]

    return Pos_x, Pos_y, Pos_rot

def calcula_posicao_tanque(id, dist_x_to_marker, dist_y_to_marker, aux, ids_paredes, comprimento_tanque, largura_tanque):
    
    indice_id_encontrado = 0

    for i in range(len(ids_paredes)):
        if(ids_paredes[i].id == id):
            indice_id_encontrado = i
            break

    if ids_paredes[indice_id_encontrado].x == 0:
        pos_x = ids_paredes[indice_id_encontrado].x + dist_x_to_marker

    elif  ids_paredes[indice_id_encontrado].x == comprimento_tanque:
        pos_x = ids_paredes[indice_id_encontrado].x - dist_x_to_marker

    if ids_paredes[indice_id_encontrado].y == 0:
        pos_y = ids_paredes[indice_id_encontrado].y + dist_y_to_marker

    elif ids_paredes[indice_id_encontrado].y == largura_tanque:
        pos_y = ids_paredes[indice_id_encontrado].y - dist_y_to_marker
    
    
    return [pos_x, pos_y]


def estimaPos(frame, bbox, ids, camera_matrix, camera_distortion, marker_size):
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


    return [realworld_tvec[0],realworld_tvec[1],realworld_tvec[2],math.degrees(roll)]

def findArucoMarkers(frame, matrix_dict =5, totalMarkers =1000, draw=True):
    
    with open('camera_cal.npy', 'rb') as f:
        camera_matrix = np.load(f)
        camera_distortion = np.load(f)
        
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

def Validacao_pos(ids, list_ids, N_frames_val, max_ids, Pos_x, Pos_y, Pos_rot):

    # Sera que a media é a melhor forma de validar resultados?
    # Teremos de verificar se não há um valor com um desvio muito grande
    desvio_padrao_x = [0,0,0,0,0,0]
    desvio_padrao_y = [0,0,0,0,0,0]
    desvio_padrao_rot = [0,0,0,0,0,0]
    media_x = [0,0,0,0,0,0]
    media_y = [0,0,0,0,0,0]
    media_rot = [0,0,0,0,0,0]
    desvio_total = [0,0,0]

    Pos_x_final = 0
    Pos_y_final = 0
    Pos_rot_final = 0

    desvio_aux_x = 0
    desvio_aux_y = 0
    desvio_aux_rot = 0

    if(len(ids) == 1):
        indice = encontra_id(ids[0][0], max_ids, list_ids)
        #print(indice)


        for i in range(N_frames_val - 1):
            Pos_x_final += Pos_x[indice][i]
            Pos_y_final += Pos_y[indice][i]
            Pos_rot_final += Pos_rot[indice][i]

        Pos_x_final = Pos_x_final / N_frames_val
        Pos_y_final = Pos_y_final / N_frames_val
        Pos_rot_final = Pos_rot_final / N_frames_val

    if(len(ids) > 1):
        for i in range(len(ids)):
            indice = encontra_id(ids[i][0], max_ids, list_ids)
            desvio_padrao_x[i] = statistics.stdev(Pos_x[indice][1:N_frames_val])
            desvio_padrao_y[i] = statistics.stdev(Pos_y[indice][1:N_frames_val])
            desvio_padrao_rot[i] = statistics.stdev(Pos_rot[indice][1:N_frames_val])
            media_x[i] = statistics.mean(Pos_x[indice][1:N_frames_val])
            media_y[i] = statistics.mean(Pos_y[indice][1:N_frames_val])
            media_rot[i] = statistics.mean(Pos_rot[indice][1:N_frames_val])

            
        desvio_total[0] =  sum(desvio_padrao_x)
        desvio_total[1] =  sum(desvio_padrao_y)
        desvio_total[2] =  sum(desvio_padrao_rot)

        for y in range(len(ids)):
            for u in range(len(ids)): 
                if(u != y):
                    desvio_aux_x += desvio_padrao_x[u]
                    desvio_aux_y += desvio_padrao_y[u]
                    desvio_aux_rot += desvio_padrao_rot[u]
                Pos_x_final += (media_x[y] * desvio_aux_x / desvio_total[0])
                Pos_y_final += (media_y[y] * desvio_aux_y / desvio_total[1])
                Pos_rot_final += (media_rot[y] * desvio_aux_rot / desvio_total[2])


    return [Pos_x_final, Pos_y_final, Pos_rot_final]
        

        
            

t1 = thread1()
t1.start()
t2 = thread2()
t2.start()
t3 = thread3()
t3.start()
t4 = thread4()
#t4.start()
#call("raspivid -n -t 0 -rot 180 -w 1440 -h 720 -fps 30 -b 6000000 -o - | gst-launch-1.0 -e -vvvv fdsrc ! h264parse ! rtph264pay pt=96 config-interval=5 ! udpsink clients=169.254.203.43:5600", shell = True)

#threadli0st.append(Thread(target=thread3))
