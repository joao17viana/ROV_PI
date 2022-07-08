import var
import time
import RPi.GPIO as GPIO 
import numpy as np


##-----------##
## Variaveis ##
##-----------## 


Potencia_Max = 50
Potencia_Total_Max = 120
pino_luz = 18
desliga = 0
sobe = 1
desce = 0
nada = -1
liga = 1
div_vet = 4
tam_vet = 12


class Mot:
    def __init__(self):
        self.ID = 0                           ##ID é o pino do arduino a que o motor está associado
        self.dist = 0                         ##Distancia ao centro de massa
        self.Pot_Disponivel = 0               ##Potencia que dispõe o motor
        self.Pot = 0                          ##Potencia que o motor está a absorver no momento
        self.Pot_Limit = 0                    ##Potencia maxima que se pode fornecer ao motor devido a varios motores a trabalhar em simultaneo
        self.Ativo = 0                        ##Identifica Se o Motor se encontra em funcionamento ou não

##Quando chamada abre o ficheiro .txt cujo nome já é definido pelo utilizador como "mot.txt"
##Não tem argumentos de entrada
##Retorna um vetor com todos os motores presentes no txt e as suas caracteristicas 
def CarregaMotores():
    with open('mot.txt') as f:                                  ##Abre o ficheiro .txt
        contents = f.readlines()
        Motores = []                                            ##Cria um vetor vazio

        for M in range(0, len(contents)):                       ##Para o numero de linhas do ficheiro
            
            Motores.append(Mot())                               ##Acrescente o motor ao vetor de motores com todos as suas caracteristicas
            aux = contents[M].split()
            Motores[M].ID = int(aux[0])
            Motores[M].dist = int(aux[1])
            Motores[M].Pot_Limit =  0  #int(aux[2])
            Motores[M].Pot_Disponivel = 40
            Motores[M].Ativo = 0

    f.close
    return Motores


##Inicializa o pino 12 (GPIO18) para ser um pino de output PWM para o controlo da lapada   
def SetUp_Lampada():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(pino_luz,GPIO.OUT)                               ##Define o pino_luz com opino de saida
    luz=GPIO.PWM(pino_luz, 1)                                   ##Define parametro "luz" como um objeto
    luz.start(desliga)                                          ##Inicializa a luz desligada
    GPIO.setwarnings(False)
    return luz


##Controla a lampada, consoante o comando que recebe, liga ou desliga a lampada
##Argumentos: Comando, que indica o que se pretende fazer com a luz
##            a lampada que é pretendida controlar
def Controla_Lampada(Comando, luz):
    if(Comando == desliga):
        luz.ChangeDutyCycle(0)
    if(Comando == liga):
        luz.ChangeDutyCycle(100)




##Auxiliar para o calculo da potencia maxima 
##
##
def Ver_Pot_Maxima(Mot):
    Mot.Pot_Limit = Mot.Pot_Disponivel



##Retorna a profundidade atual
def Ler_Profundidade():
    return var.profundidade_atual
    


##Cria o vetor e inicializa a 0 que vai conter as ultimas 12 profundidades lidas
def Vetor_prof():
    vetor = []
    for tam in range(12):
        vetor.append(0)
    return vetor


##Atualiza o vetor de profundidades
##Argumentos: nova_prof, é a profundade mais recente lida pelo sensor BAR30
##            vetor, é o vetor que contem todas as profundidades anteriores
#Retorna o vetor atualizado
def Atualiza_Vetor_prof(nova_prof, vetor):
    vetor = np.roll(vetor, 1)                               ##Roda uma posição à direita
    vetor[0] = nova_prof                                    ##Introduz a nova profundidade no primeiro elemento do vetor (o antigo ultimo)
    return vetor


##Determina o a media dos primeiros 4 elementos do vetor, dos 4 elementos centrais, e dos ultimos 4
##Argumentos: vetor, recebe o vetor que contem as ultimas 12 profundidades lidas pelo sensor Bar30
#Retorna um vetor de tamanho 3 com as tres medias calculadas
def Det_Vetor_Medias(vetor):
    Vetor_Media = []                                        ##Cria um novo vetor para encher com as medias
    for i in range(0, round((int(tam_vet)/int(div_vet)))):         ##Para cada uma das divisões
        soma = 0   
        for j in range(0, div_vet-1):                       ##Soma os valores pretendidos
            soma = soma + vetor[j*div_vet + j]
        Vetor_Media.append(soma/div_vet)                    ##Adiciona-os no vetor de medias
    return Vetor_Media

##Compara os valores das 3 medias do vetor e determina se a posição (em media) está a aumentar, diminuir ou é inconclusivo
##Argumentos: media, um vetor de tamanho 3 com a media de cada divisão do vetor de profundidades
def Det_tendencia(media):  
    if(media[0] > media[1]):
        if(media[1] > media[2]):                        ##Se media[0] > media[1] > media [2]                
            return desce                                ##Que dizer que está a subir, logo tem de descer
    else:
        if(media[1] < media[2]):                        ##Se media[0] < media[1] < media [2]                    
            return sobe                                 ##Quer dizer que está a descer, logo tem de subir
    return nada                                         ##O Resultado foi inconclusivo, logo não tem nada para controlar



def Limitar_portencia(Motores):
    global Potencia_Total_Max
    total = 0
    Restante = Potencia_Total_Max
    ct = 0
    for M in range(0, len(Motores)):
        if(Motores[M].Pot > 0 ):
            total = total + Motores[M].Pot
        elif(Motores[M].Pot_Limit > 0):
            total = total + Motores[M].Pot_Limit
    if(total > Potencia_Total_Max):
        #É preciso fazer ajustes
        Motores[0].Pot_Limit = Motores[0].Pot_Disponivel
        Motores[1].Pot_Limit = Motores[1].Pot_Disponivel
        Restante = Potencia_Total_Max - Motores[0].Pot_Disponivel - Motores[1].Pot_Disponivel
        if(Restante > 0):
            ##Aqui vai contar quantos motores estão a trabalhar
            for i in range(2, len(Motores)):
                if(Motores[i].Pot_Limit > 0):
                    ct += 1
            for i in range(2, len(Motores)):
                if(Motores[i].Pot_Limit > 0):
                    Motores[i].Pot_Limit = Restante/ct
    return Motores
        
##Le Os inputs da matriz
##Retorna a matriz atualizada
def Ler_inputs_matriz():    
    Nova_Matriz = Cria_Matriz()                             ##Cria uma matriz nova
    Nova_Matriz = Definir_Matriz(Nova_Matriz)               ##Preenche consoante os inputs a matriz recem criada
    return Nova_Matriz


##Cria uma nova matriz 3x3 inicializada a 0
##Retorna a matriz criada
def Cria_Matriz():
    filas = 3
    columnas = 3
    matriz_mov = []
    for i in range(filas):
        matriz_mov.append([])                       ##Cria um vetor com 3 vetores vazios []
        for j in range(columnas):
            matriz_mov[i].append(0)                 ##Preenche a matriz com 0
    return matriz_mov


##Preenche a matriz consoante os inputs vindos da interface 
##Argumentos: matriz_mov, recebe a matriz que pretende alterar 
#Retorna a matriz que recebeu mas com as alterações feitas consoante os inputs
def Definir_Matriz(matriz_mov):    
    w = 0                                           ##Inicializa todas as variaveis a 0 por segurança
    a = 0
    s = 0
    d = 0
    wx = var.w                                      ##Declara as variaveis wx ax sx dx iguais aos respetivos inputs
    ax = var.a                                      ##Esta declaração é para proteger de uma alteração de uma variavel a meio do processo
    sx = var.s
    dx = var.d
    n_input = (wx + ax + sx + dx)                   ##Calcula o numero de inputs que está a receber em simultaneo
    if( n_input ) >= 3:
        if(n_input == 4):                           ##Se tiver 4 inputs (w a s d) não faz nada
            wx = 0
            dx = 0
            sx = 0
            ax = 0
        elif(dx == 0):                              ##Se tiver 3 inputs, (asw, asd, wds, awd) os opostos se anulam
            wx = 0
            sx = 0
        elif(sx == 0):
            ax = 0 
            dx = 0
        elif(ax == 0):
            wx = 0
            sx = 0
        elif(wx == 0):
            ax = 0 
            dx = 0

    n_input = (wx + ax + sx + dx)                 ##Recalcula o valor de n_input
    if(wx): w = 1
    if(ax): a = 3
    if(dx): d = 5
    if(sx): s = 7

    input = w + d + s + a                           
    if(n_input == 1):                            ##Se tiver apenas um input, é só "ligar" essa direção e sentido
        matriz_mov[int(input/3)][input%3] = 1

    if(n_input >= 2):                            ##Se tiver mais do que dois inputs, o movimento vai ser diagonal
        input = int(input/2)
        if(w and d):
            input = input - 1
        elif(w and a):
            input = input - 2
        elif(s and d):
            input = input + 2
        elif(s and a):
            input = input + 1
        matriz_mov[int(input/3)][input%3] = 1
    return matriz_mov
