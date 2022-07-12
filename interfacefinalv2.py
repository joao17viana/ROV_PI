from tkinter import CENTER, EW, ttk, Label, Listbox, Scrollbar, Tk, messagebox, Canvas, Entry
from tkinter import font
from tkinter.font import Font
from tkinter import E, SE, SW, NW, NE, NSEW, S, W
from ttkthemes import ThemedTk

from threading import Thread
import paho.mqtt.client as mqtt
from datetime import datetime, timedelta
import logging
import time
import cv2 as cv
import numpy as np
import math
import time
import statistics
from detecao_funcoes import rotationMatrixToEulerAngles, encontra_id, limpa_arrays, calcula_posicao_tanque, estimaPos, findArucoMarkers, Validacao_pos, filtro_amosta, write_on_file
from PIL import Image, ImageTk
from random import randint

import matplotlib
import matplotlib.dates as mdates
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

matplotlib.use("TkAgg")


pressure = "1000.00"
temperature = 25.00
depth = "00.00"
leak = "0"
client = 0

input = "0 0 0 0 000 0 00 0 0 0 0"
#[0 0 0 0 ...] - w a d s
#[... 000 0 ...] - define a profundidade, o outro bit transmite se alteramos a profundidade (só é 1 na função de alterar a prof)
#[... 00 ...] - percentagem da potência a que funcionam os motores
#[... 0 0 ...] - bits para ligar a luz e desligar o rpi, respectivamente
#[... 0 0] - rotação anti horaria e horaria
 

now = datetime.now()
dt_string = now.strftime("%H:%M:%S")


def thread1():
    # variáveis da camera
    global prev_frame, new_frame, marker_size, camera_width, camera_height, largura_tanque, comprimento_tanque, id_fundo_direita, id_fundo_esquerda, id_inicial_direita, id_inicial_esquerda
    global id_direita, id_esquerda, list_ids, deg_fundo, deg_inicial, deg_direita, deg_esquerda, total_de_frames, N_frames_val, max_ids, linhas, colunas
    global n_ids, len_n_ids, aux_inicial, aux_inicial_2, Pos_rot, Pos_x, Pos_y, ids_paredes, flag_estima_pos, Pos_tanque_final
    Pos_tanque_final = [0,0]

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

    new_frame = 0
    prev_frame = 0
    #Definir variaveis globais e inicializar a janela
    global pressure, temperature, depth, leak, strProf, strPerc, is_on, valorx, valory
    strProf= "000"
    strPerc = "00"
    is_on = "0"
    valorx = 0
    valory = 0
    window = ThemedTk(theme="breeze")

    #Definir uma font
    FONTE = Font(size=14)
    FontePeq = Font(size=10)

    #Define o titulo e dimensões da janela
    window.title("Painel Controlo ROV")
    #window.state("zoomed")

    # Muda o icon para o emoji de sereia
    #window.iconbitmap('C:\\Users\\jbmor\\OneDrive\\Ambiente de Trabalho\\mermaid_icon.ico') 

    #Configurar grid
    tabs = ttk.Notebook(window)
    tabs.grid()
    frame1 = ttk.Frame(tabs)
    frame2 = ttk.Frame(tabs)
    tabs.add(frame1, text="Main")
    tabs.add(frame2, text="Inputs")
    width = window.winfo_screenwidth()
    height = window.winfo_screenheight()
    print(width)
    print(height)

    #Configurar dimensões e posições dos quadradinhos
    camera = ttk.Frame(frame1, borderwidth=4, relief="ridge", width=width*3/4, height=height*8.7/13)
    profundidade = ttk.Frame(frame1, borderwidth=4, relief="ridge", width=width/4, height=height*3.2/13)
    dados = ttk.Frame(frame1, borderwidth=4, relief="ridge", width=width/4, height=height*2.6/13)
    lugar = ttk.Frame(frame1, borderwidth=4, relief="ridge", width=width/4, height=height*4.4/13)
    controlo = ttk.Frame(frame1, borderwidth=4, relief="ridge", width=width*3/4, height=height*1.5/13)
    lampada = ttk.Frame(frame1, borderwidth=4, relief="ridge", width=width/10, height=height*1.5/13)
    lampada.columnconfigure(0, weight=1)
    exit = ttk.Frame(frame1, borderwidth=4, relief="ridge", width=width/10, height=height*1.5/13)
    exit.columnconfigure(0, weight=1)
    sos = ttk.Frame(frame1, borderwidth=4, relief="ridge", width=width/10, height=height*1.5/13)
    sos.columnconfigure(0, weight=1)

    #Cada retângulo
    tabs.grid(column=0, row=0, sticky=NSEW)
    camera.grid(column=0, row=0, columnspan=3, rowspan=3, sticky=NSEW)
    controlo.grid(column=0, row=3, columnspan=3, sticky=NSEW)
    profundidade.grid(column=3, row=0, sticky=NE)
    dados.grid(column=3, row=1, sticky=E)
    lugar.grid(column=3, row=2, rowspan=2, sticky=SE)
    lampada.grid(column=1, row=4, sticky=E)
    exit.grid(column=2, row=4, columnspan=2, sticky=E)
    sos.grid(column=0,row=4,columnspan=2,sticky=W)

    #Supostamente permitia mudar os widgets conforme o tamanho da janela
    camera.grid_propagate(0)
    controlo.grid_propagate(0)
    profundidade.grid_propagate(0)
    dados.grid_propagate(0)
    lugar.grid_propagate(0)
    lampada.grid_propagate(0)
    exit.grid_propagate(0)
    sos.grid_propagate(0)
    
    #Lista Inputs
    lista= Listbox(frame2,height=50,selectmode="extended")

    #Tecla Premida
    def key_pressed(event):
        global input, w, a, d, s, q, e, z, c, client
        if event.char == "w":
            w="1"
            input = w +" 0 0 0 000 0 " + strPerc + " "+is_on+" 0 0 0"
            client.publish("motores",input)
            print(input)
        elif event.char == "s":
            s="1"
            input ="0 0 0 " + s +" 000 0 " + strPerc + " "+is_on+" 0 0 0"
            client.publish("motores",input)
            print(input)
        elif event.char == "a":
            a="1"
            input = "0 " + a +" 0 0 000 0 " + strPerc + " "+is_on+" 0 0 0"
            client.publish("motores",input)
            print(input)
        elif event.char == "d":
            d="1"
            input = "0 0 " + d + " 0 000 0 " + strPerc + " "+is_on+" 0 0 0"
            client.publish("motores",input)
            print(input)
        elif event.char == "q":
            q="1 1"
            input = q+ " 0 0 000 0 " + strPerc + " "+is_on+" 0 0 0"
            client.publish("motores",input)
            print(input)
        elif event.char == "e":
            e="1 0 1"
            input = e + " 0 000 0 " + strPerc + " "+is_on+" 0 0 0"
            client.publish("motores",input)
            print(input)
        elif event.char == "z":
            z="1 0 1"
            input = "0 " + z +" 000 0 " + strPerc + " "+is_on+" 0 0 0"
            client.publish("motores",input)
            print(input)
        elif event.char == "c":
            c="1 1"
            input = "0 0 " + c +" 000 0 " + strPerc + " "+is_on+" 0 0 0"
            client.publish("motores",input)
            print(input)
        elif event.char == "p":
            input = "0 0 0 0 000 0 00 "+is_on+" 0 0 0"
            client.publish("motores",input)
            print(input)
        elif event.char == "r":
            input ="0 0 0 0 000 0 " + strPerc + " "+is_on+" 0 1 0"
            client.publish("motores",input)
            print(input)
        elif event.char == "t":
            input ="0 0 0 0 000 0 " + strPerc + " "+is_on+" 0 0 1"
            client.publish("motores",input)
            print(input)

        #print(event.char)
        for i in range(0,1):
            if event.char != lista.get(i):
                lista.insert(i,event.char)
        

    window.bind('<KeyPress>', key_pressed)
    scroll = Scrollbar(frame2,orient="vertical",command=lista.yview)
    scroll.grid(column=2, columnspan=3)
    scroll.config(command = lista.yview)
    lista.config(yscrollcommand = scroll.set)
    lista.grid()


    #Aviso Leak
    def AvisoLeak(leak):
        global input, client
        if leak==1:                                           #Quando há leak sobe até à superficie e desliga tudo               
            messagebox.showerror("ERRO", "Leak no Cilindro")
            input ="0 0 0 0 000 1 50 0 0 0 0"
            client.publish("motores",input)
            if depth == 0:
                input="0 0 0 0 000 0 00 0 1 0 0"
                client.publish("motores",input)


    #Profundidade
    class GraphPage(ttk.Frame):
        def __init__(self,profundidade,nbpoints):
            ttk.Frame.__init__(self, profundidade)
            self.figPr = Figure(figsize=(4.8,2.6), dpi=100)         #define o gráfico e o seu tamanho
            self.ax = self.figPr.add_subplot(111)

            myFmt = mdates.DateFormatter("%S")                      
            self.ax.xaxis.set_major_formatter(myFmt)

            dateTimeObj = datetime.now() + timedelta(seconds=-nbpoints)
            self.x_data = [dateTimeObj + timedelta(seconds=i) for i in range(nbpoints)]     #insere o tempo (nº definido pelo user)
            self.y_data = [0 for i in range(nbpoints)]
            self.plot = self.ax.plot(self.x_data, self.y_data, label='Profundidade')[0]
            self.ax.set_ylim(0, 180)                                                         #range da escala do y
            self.ax.set_xlim(self.x_data[0], self.x_data[-1])

            self.canvas = FigureCanvasTkAgg(self.figPr, master=profundidade)                #colocar o gráfico no sítio certo
            self.canvas.get_tk_widget().grid()

        def animate(self):
            # append new data point to the x and y data
            self.x_data.append(datetime.now())
            self.y_data.append(int(float(depth)*100))
            # remove oldest data point
            self.x_data = self.x_data[1:]
            self.y_data = self.y_data[1:]
            #  update plot data
            self.plot.set_xdata(self.x_data)
            self.plot.set_ydata(self.y_data)
            self.ax.set_xlim(self.x_data[0], self.x_data[-1])
            self.canvas.draw_idle()  # redraw plot
            self.after(1000, self.animate)  # repeat after 1s


    #Indicadores de valores (Temperatura, Pressão, Profundidade)
    labProf = Label(profundidade, text="Profundidade")
    labProf.place(relx=0.88,rely=0.13,anchor=NW)

    labTemp = Label(dados, text="Temperatura = ", font=FONTE, fg="black")
    valTemp = Label(dados, text=f"{temperature} ºC", font=FONTE, fg="#800080")
    labTemp.place(relx=0.24,rely=0.18)
    valTemp.place(relx=0.59,rely=0.18)
    
    labPres = Label(dados, text="Pressão = ", font=FONTE, fg="black")
    valPres = Label(dados, text=f"{pressure} mbar", font=FONTE, fg="#800080")
    labPres.place(relx=0.24,rely=0.43)
    valPres.place(relx=0.475,rely=0.43)

    labProfV = Label(dados, text="Profundidade = ", font=FONTE, fg="black")
    valProfV = Label(dados, text = f"{depth} cm", font=FONTE, fg="#800080")
    labProfV.place(relx=0.245,rely=0.68)
    valProfV.place(relx=0.575,rely=0.68)

    #Funções para atualizar o valor numérico das labels
    def aumentarvalProf():
        valProfV.config(text=f"{depth} cm")
        valProfV.after(1000,aumentarvalProf)
    aumentarvalProf()

    def aumentarvalPres():
        valPres.config(text=f"{pressure} mbar")
        valPres.after(1000,aumentarvalPres)
    aumentarvalPres()

    def aumentarvalTemp():
        valTemp.config(text=f"{temperature} ºC")
        valTemp.after(1000,aumentarvalPres)
    aumentarvalTemp()


    #Funções dos botões SOS e Luz
    def emerg():
        global input                                    #Função igual ao leak, vem até à superfície e desliga tudo
        input ="0 0 0 0 000 1 50 0 0 0"
        client.publish("motores",input)
        messagebox.showwarning("SOS","Detectada Emergência")
        if depth== 0:
            input="0 0 0 0 000 0 00 0 1 0 0"
            client.publish("motores",input)
    
    def ligar_luz():
        global is_on, input
        if is_on == "1":                #Verifica se está ligada, muda o texto do botão e a string do input
            is_on = "0"
            print("Desligado")
            lampadaB.config(text="Ligar Luz")
            input = input[0:17] + is_on + input[18:24]
            client.publish("motores",input)
        else:
            is_on = "1"
            print("Ligado")
            lampadaB.config(text="Desligar Luz")
            input = input[0:17] + is_on + input[18:24]
            client.publish("motores",input)
            print(input)

    #Definir e posicionar os botões SOS e Luz
    sos_button = ttk.Button(sos,text="SOS",command=emerg)
    sos_button.grid(columnspan=1,ipadx=13, ipady=13, padx=20, pady=20, sticky=EW)

    exit_button = ttk.Button(exit,text='Exit',command=lambda: window.destroy())
    exit_button.grid(columnspan=1,ipadx=13, ipady=13, padx=20, pady=20, sticky=EW)
     
    lampadaB = ttk.Button(lampada,text='Ligar Luz',command=ligar_luz)
    lampadaB.grid(columnspan=1,ipadx=13, ipady=13, padx=20, pady=20, sticky=EW)


    #Controlo
    def inserir_Prof():
        global strProf,input,strPerc
        strProf= entradaProf.get()
        if 0 <= int(strProf) < 180:                         #Garante que a profundidade inserida é possível (entre 0 e 180)
            if len(strProf)==3:                             #IFs para adaptar a string a ter sempre 3 dígitos (adiciona zeros antes)
                input = input[0:7] +" " + strProf + " 1 " + strPerc + " 0 0 0 0"
                client.publish("motores",input)
                print (input)
            elif len(strProf)==2:
                input = input[0:7] + " 0" + strProf + " 1 " + strPerc + " 0 0 0 0"
                client.publish("motores",input)
                print (input)
            elif len(strProf)==1:
                input = input[0:7] + " 00" + strProf + " 1 " + strPerc + " 0 0 0 0"
                client.publish("motores",input)
                print (input)
        else:
             messagebox.showerror("ERRO", "Valor Inválido")

    def inserir_Perc():
        global strPerc,input,strProf , perctemp, client
        perctemp= entradaPerc.get()                         #Variável temporária para adaptar a percentagem a 2 digitos
        if 0 < int(perctemp) < 100:
            if len(perctemp)==2:
                strPerc = perctemp
                input = input[0:11] + " 0 " + strPerc + " 0 0 0 0"
                client.publish("motores",input)
                print(input)
            elif len(perctemp) == 1:
                strPerc = "0"+ perctemp                     
                print(strPerc)
                input = input[0:11]+ " 0 " + strPerc + " 0 0 0 0"
                client.publish("motores",input)
                print(input)
        else:
             messagebox.showerror("ERRO", "Valor Inválido")


    submeterProf=ttk.Button(controlo,text="Enviar", command=inserir_Prof)
    submeterProf.place(rely=0.62,relx=0.76)

    submeterVel=ttk.Button(controlo,text="Enviar", command=inserir_Perc)
    submeterVel.place(rely=0.62,relx=0.18)

    entradaProf=Entry(controlo,text="Profundidade", justify=CENTER,bg="white")
    entradaProf.place(rely=0.2,relx=0.67,relheight=0.42,relwidth=0.25)

    entradaPerc=Entry(controlo,text="Velocidade", justify=CENTER, bg="white")
    entradaPerc.place(rely=0.2,relx=0.10,relheight=0.42,relwidth=0.25)

    rangCont = Label(controlo, text="[0-180]", font=FontePeq)
    rangCont.place(relx=0.615,rely=0.44) 

    labCont = Label(controlo, text="Profundidade", font=FontePeq)
    labCont.place(relx=0.6,rely=0.26)

    uniCont = Label(controlo, text="cm", font=FontePeq)
    uniCont.place(relx=0.92,rely=0.32)

    rangVel = Label(controlo, text="[0-99]", font=FontePeq)
    rangVel.place(relx=0.052,rely=0.44)

    labVel = Label(controlo, text="Velocidade", font=FontePeq)
    labVel.place(relx=0.042,rely=0.26)

    uniVel = Label(controlo, text="%", font=FontePeq)
    uniVel.place(relx=0.35,rely=0.32)


    #Camera
    labCam = Label(camera, text="Camera")
    labCam.grid(row=1, sticky=NW)
    #str_pipe = 'udpsrc port=5600 auto-multicast=0 ! application/x-rtp,media=video,encoding-name=H264 ! rtpjitterbuffer latency=0 ! rtph264depay ! avdec_h264 ! videoconvert ! video/x-raw,format=BGR ! appsink drop=1'
    #cap= cv.VideoCapture(str_pipe, cv.CAP_GSTREAMER)

    #if not cap.isOpened():
    #    print("nao consegui abrir")
    cap= cv.VideoCapture(0)
    #cap.set(3,width*3/4)                                #Adapta a imagem da câmera ao quadrado definido na grid
    def show_frames():

        # variáveis globais da camera

        global prev_frame, new_frame, marker_size, camera_width, camera_height, largura_tanque, comprimento_tanque, id_fundo_direita, id_fundo_esquerda, id_inicial_direita, id_inicial_esquerda
        global id_direita, id_esquerda, list_ids, deg_fundo, deg_inicial, deg_direita, deg_esquerda, total_de_frames, N_frames_val, max_ids, linhas, colunas
        global n_ids, len_n_ids, aux_inicial, aux_inicial_2, Pos_rot, Pos_x, Pos_y, ids_paredes, flag_estima_pos
        global Pos_tanque_final

        # Get the latest frame and convert into Image
        ret, frame = cap.read() 
        new_frame = time.time()
        
        #print("cheguei a correr a thread")
        if frame is not None:
            #frame = cv.flip(frame, 1)
            arucoFound = findArucoMarkers(frame)
            #print(frame.shape[0])
            #print(frame.shape[1])
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
                        #for i_x in range(len(Pos_x)):
                        #    Pos_x[i_x] = filtro_amosta(Pos_x[i_x], 10)

                        #for i_y in range(len(Pos_y)):
                        #    Pos_y[i_y] = filtro_amosta(Pos_y[i_y], 10)

                        #for i_Rot in range(len(Pos_rot)):  
                        #    Pos_rot[i_Rot] = filtro_amosta(Pos_rot[i_Rot], 10)

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
            #cv.imshow('Input', frame)

            resized = cv.resize(frame, (1440,720), interpolation = cv.INTER_AREA)

            prev_frame = new_frame

            # codigo morgado

            cvimage = cv.cvtColor(resized,cv.COLOR_BGR2RGB)
            img = Image.fromarray(cvimage)
            # Convert image to PhotoImage
            imgtk = ImageTk.PhotoImage(image = img)
            labCam.imgtk = imgtk
            labCam.configure(image=imgtk)
        # Repeat after an interval to capture continiously
        labCam.after(20, show_frames)

    #Animação da posição Submarino
    class Ball:                                 
        def __init__(self, canvas, x1, y1, x2, y2):
            self.x1 = x1
            self.y1 = y1
            self.x2 = x2
            self.y2 = y2
            self.canvas = canvas
            self.ball = canvas.create_oval(self.x1, self.y1, self.x2, self.y2, fill="#ec651c", outline="white")

        def move_ball(self):
            global strProf, valorx, valory, Pos_tanque_final
            deltax = Pos_tanque_final[0]
            deltay = Pos_tanque_final[1]
            cordx = 450- (450/800)*deltax
            cordy= deltay * (325/400) 
            largura=30
            self.canvas.coords(self.ball, cordx, cordy, cordx+largura,cordy+largura)
            self.canvas.after(50, self.move_ball)

    graph = GraphPage(profundidade, nbpoints=10)
    graph.grid()
    graph.animate()

    canvas = Canvas(lugar)
    canvas.configure(bg="#1ca3ec",height=height*4.6/14,width=width/4.08,bd=1)
    canvas.grid()

    ball1 = Ball(canvas, 60, 30, 30, 60)
    ball1.move_ball()

    #Logger
    def registar():
        logger = logging.getLogger()
        logger.info("%s centimetros",depth)
        logger.info("%s ºC",temperature)
        logger.info("%s bar",pressure)
        labCam.after(10000, registar)               #Cria um novo log a cada 10s
    
    Log_Format = "%(levelname)s %(asctime)s - %(message)s"
    #Guarda os logs num ficheiro chamado logfile, reescreve (w) , e com o tipo INFO
    logging.basicConfig(filename = "logfile.log",filemode = "w",format = Log_Format,level = logging.INFO) 

    
    registar()
    show_frames()
    AvisoLeak(leak)
    window.mainloop()

def thread2():

    global input, client
    # Callback Function on Connection with MQTT Server
    def on_connect( client, userdata, flags, rc):
        print ("Connected with Code :" +str(rc))
        # Subscribe Topic from here
        client.subscribe("sensores")

    # Callback Function on Receiving the Subscribed Topic/Message
    def on_message( client, userdata, msg):
        # print the message received from the subscribed topic
        global pressure, temperature, depth, leak, temperature, valorx, valory
        sensors = str(msg.payload)
        #print(sensors)
        pressure = sensors[2:9]
        temperature = sensors[10:15]
        depth = sensors[16:21]
        leak = sensors[22]
        valorx = int(sensors[24:27])
        valory = int(sensors[28:30])
        #for debug 
        #print (temperature)
        #print (pressure)
        #print (depth)
        #print (leak)

    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    #client.connect("169.254.52.172", 1883, 60)
    client.connect("169.254.76.3", 1883, 60)
    client.username_pw_set("username", "123")

    #client.loop_forever()
    client.loop_start()
    time.sleep(1)
    while True:
        #client.publish("motores",input)
        client.subscribe("sensores")
        #print ("Message Sent")
        time.sleep(0.1)
    


threadlist = []

threadlist.append(Thread(target=thread1))
threadlist.append(Thread(target=thread2)) 

for t in threadlist:
  t.start()

for t in threadlist:
  t.join()