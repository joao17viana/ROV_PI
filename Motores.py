from termios import TIOCPKT_FLUSHREAD
import Definir
import time 
import var
import serial


##-----------##
## Variaveis ##
##-----------## 


frente = 1
tras = -1
Potencia_Max = 40
Potencia_Total_Max = 80
tol = 7.5                        ##Em cm
Potencia_Min = 10
R_trans_T100 = 40/14
R_trans_T200 = 50/19
Base = 150
P_estavel_Z = 10 / R_trans_T100 + Base
P_estavel_XY = 10 / R_trans_T200 + Base
Step_Corrente = 0.42
Delay_Corrente = 0.1
Delay_Rotar = 1
pino_luz = 18



##----------------##
## Parte Controlo ##
##----------------##

##Transforma uma potencia em Intensidade da corrente dado o motor
##Argumentos: P, potencia a transformar
##Retorna o valor da corrente que o motor absorve em função da potencia
def Watt_To_Amp(P):
    return int(P * 0.0832)

def Amp_To_Watt(A):
    return(int(A / 0.0832))

##Manda ativar um determinado motor
##Argumentos: Mot, O motor que se pretende ativar
##            Sinal, O Sinal PWM que é suposto enviar ao motor para este reagir da maneira que queremos
##            pos, a posição do motor no vetor, isto serve para facilitar o envio
##Retorna o motor que foi ativo
def Ativar_Motor(Mot, Sinal, pos):
    ajuste = 1
    if(pos == 2 or pos == 3):
        print("T200")
        R_trans = R_trans_T200
    else:
        R_trans = R_trans_T100
    if(abs((Sinal-Base) * R_trans) > Mot.Pot_Limit and (Mot.Pot_Limit != 0)):
        Sinal = (Mot.Pot_Limit / R_trans) + Base
    elif(abs((Sinal-Base) * R_trans) > Mot.Pot_Disponivel):                            ##Limita a potencia fornecida aos motores
        Sinal = (Mot.Pot_disponivel / R_trans) + Base 
    
    if(Sinal < Base and ((Mot.Pot / R_trans) + Base)  >= Base):                        ##Se Pedir uma mudança de sentido
        Mot = Desliga_Motor(Mot, pos)
    elif((Sinal > Base and ((Mot.Pot / R_trans) + Base) <=  Base)):
        Mot = Desliga_Motor(Mot, pos)
    diff = (Watt_To_Amp(abs(Sinal-Base) * R_trans)) - Watt_To_Amp(Mot.Pot)              ##Mede a diferença de correntes, e faz um aumemento step
    if(diff < 0):
        ##Se for diminuição 
        ajuste = -1
        diff = diff * ajuste
    N_Step = int(diff/Step_Corrente)
    if(N_Step > 1):
        for Am in range(0,N_Step):
            Sinal_temp = (((Sinal-Base) * R_trans) + Amp_To_Watt((Am + 1)*Step_Corrente*ajuste))/R_trans
            Send_to_Arduino(str(pos), str(Sinal_temp))
            time.sleep(Delay_Corrente)

    print("Mandei para o arduino" + str(pos) + str(Sinal))

    Send_to_Arduino(str(pos), str(Sinal))                                               ##Manda o sinal PWM do motor e a posição que é preciso ativar
    time.sleep(Delay_Corrente)                                                          ##Dá um pequeno delay
    Mot.Ativo = 1                                                                       ##Ativa o parametro do motor
    Mot.Pot = (Sinal - Base) * R_trans                                                    ##Guarda a informação da potencia que está a emitir
    return Mot




##Envia o comando para desligar um determinado motor
##Argumentos: Mot, O motor que se pretende desativar
##            pos, a posição do motor que é pretendida alterar
##Retorna o motor que foi desativado 
def Desliga_Motor(Mot, pos):
    Mot.Ativo = 0                                                                       ##Atualiza os parametros do motor pretendido
    Mot.Pot = 0
    Mot.Pot_Limit = 0
    time.sleep(Delay_Corrente)
    Send_to_Arduino(str(pos), str(Base))
    time.sleep(0.2)                                                                     ##Delay pequeno para não existirem 
    return Mot


##Calcula a potencia que é necessária atribuir a um motor
##Argumentos: Fator_Dm, é o fator diminuição que vai afetar a potencia fornecida
##Retorna a potencia que será fornecida a um determinado motor
def Calcula_Potencia(Fator_Dm):
    if((Fator_Dm * Potencia_Max) < Potencia_Min):                                       ##Se a potencia for menor que a minima definida, fornece a minima
        return Potencia_Min
    else:
        return Potencia_Max


##Manda Desligar todos os motores
##Argumentos: Motores, O vetor que contem todos os motores
##Retorna o mesmo vetor que recebe depois de desligar os motores
def Limpa_Matriz(Motores):
    for M in range(0, len(Motores)):
        if(Motores[M].Ativo != 0):
            Motores[M] = Desliga_Motor(Motores[M], M)
    return Motores


##Compara duas matrizes, a matriz que está a comandar e a matriz que recebe os novos inputs, se for diferente atualiza a matriz pela nova
##Argumentos: matriz_mov, é a matriz atual que está a comandar a ação dos motores
##            Motores, é o vetor com todos os motores carregados
##Retorna a matriz inicial se não houver alteração ou a nova caso exista alteração e o vetor dos motores atualizado
def Matriz_Atc(matriz_mov, Motores):
    ##print("Atualizando Matriz")
    matriz_mov_nova = Definir.Ler_inputs_matriz()                                       ##Le a nova matriz
    if(matriz_mov_nova != matriz_mov):                                                  ##Compara as matrizes
        Motores = Limpa_Matriz(Motores)
        Motores = Traduzir_Matriz(matriz_mov_nova, Motores)                             ##Caso sejam diferentes altera a matriz e ativa os respetivos motores
        return matriz_mov_nova, Motores
    else:
        return matriz_mov, Motores
    


def Send_to_Arduino(pos, sinal):
    var.mutex = 1
    dados = pos + "/" + sinal + "x"   
    #var.ser = serial.Serial('/dev/ttyUSB0', 9600, timeout=1)
    var.ser.reset_input_buffer()
    #print(dados.encode('utf-8'))
    var.ser.write(dados.encode('utf-8'))
    var.mutex = 0


##---------------------##
## Parte Movimentos XY ##
##---------------------##

##Traduz a matriz dos movimentos, isto é, recebe uma matriz e ativa os motores correspondentes a o movimento pretendido
##Argumentos: Matriz, A matriz que é suposto traduzir
##            Motores, o vetor que contem todos os motores
##Retorna o vetor que contem todos os motores 
def Traduzir_Matriz(Matriz, Motores):

    #Definir.Ver_Pot_Maxima(Motores[2])
    #Definir.Ver_Pot_Maxima(Motores[3])
    #Definir.Ver_Pot_Maxima(Motores[4])
    #Definir.Ver_Pot_Maxima(Motores[5])
    #Definir.Limitar_portencia(Motores)
    for linha in range(0, len(Matriz)):
        for col in range(0, len(Matriz)):                                           ##Ativa os motores correspondentes
            if(Matriz[linha][col] == 1):
                if(linha == 0):
                    Sinal = Traduzir_Valores(frente, 2)
                    Motores[2] = Ativar_Motor(Motores[2], int(Sinal), 2)
                    Motores[3] = Ativar_Motor(Motores[3], int(Sinal), 3)                    
                    
                if(linha == 2):
                    Sinal = Traduzir_Valores(tras, 2)
                    Motores[2] = Ativar_Motor(Motores[2], int(Sinal), 2)
                    Motores[3] = Ativar_Motor(Motores[3], int(Sinal), 3)
                    
                if(col == 0):
                    Sinal = Traduzir_Valores(frente, 4)
                    Motores[4] = Ativar_Motor(Motores[4], int(Sinal), 4)
                    Motores[5] = Ativar_Motor(Motores[5], int(Sinal), 5)
                    
                if(col == 2):
                    Sinal = Traduzir_Valores(tras, 4)
                    Motores[4] = Ativar_Motor(Motores[4], int(Sinal), 4)
                    Motores[5] = Ativar_Motor(Motores[5], int(Sinal), 5)
                    
    return Motores

##Calcula o valor do sinal PWM consoanete a variavel global velocidade e o sentido que recebe
##Aviso: A razão de transormaçao nesta parte do codigo depende do motor que se está a controlar,
##       só está R_TransT200 porque ficamos sem os T100 para os eixos XY
##Argumentos sent, o sentido do movimento, se é pretendido o movimento para frente ou para tras
##Retorna O valor do sinal que será enviado para o arduino
def Traduzir_Valores(sent, R_trans):
    #Vai até 40 a variação
    if(R_trans == 2 or R_trans == 3):
        R_trans = R_trans_T200
    else:
        R_trans = R_trans_T100
    if(sent == frente):                                                         
        inc = var.velocidade /100 * Potencia_Max / R_trans
        print(inc)
        if (inc < 3):                                                           ##Define o minimo 
            inc = 3
        return int(Base + inc)
    elif(sent == tras):
        inc = (var.velocidade /100) * (Potencia_Max / R_trans)
        if (inc < 3):                                                           ##Define o minimo
            print(inc)
            inc = 3
        return int(Base - inc)
    return int(Base)
     

##Função que trata da rotação, rota durante um pequeno periodo de tempo e para os motores. Visto que não temos controlo da rotação
##Argumentos: Motores, o vetor que contem todos os motores
##            sentido, O Sentido será 1 ou -1 dependendo se a rotacao for clockwise ou anti clock wise 
##Retorna o vetor dos motores com os motores atualizados
def Rotar_XY(Motores, sentido): 
    Definir.Ver_Pot_Maxima(Motores[2])
    Definir.Ver_Pot_Maxima(Motores[3])
    Definir.Limitar_portencia(Motores)
    #A partida sentido = 1 é clockwise  
    Sin = Base - sentido * ((P_estavel_XY - Base) * 2)                            ##Define o sinal que é fornecido a um motor
    Sin_C = Base + sentido * ((P_estavel_XY - Base) * 2)                          ##O outro motor vai ter o sinal contrário
    Motores[2] = Ativar_Motor(Motores[2], Sin, 2)
    Motores[3] = Ativar_Motor(Motores[3], Sin_C, 3)
    time.sleep(Delay_Rotar)
    Motores[2] = Desliga_Motor(Motores[2], 2)
    Motores[3] = Desliga_Motor(Motores[3], 3)
    return Motores


##-------------------##
## Movimentos eixo Z ##
##-------------------##


##Função destinada à manunteção da profundidade 
##Argumentos: Motores, o vetor que contem todos os motores
##Retorna o vetor dos motores com os motores atualizados
def Manter_Profundidade(Motores, sentido):
    ##Ler profundidade
    Sin = Base + sentido * ((P_estavel_Z - Base) )
    Motores[0] = Ativar_Motor(Motores[0], Sin, 0)
    Motores[1] = Ativar_Motor(Motores[1], Sin, 1)
    return Motores


##Define um degrau para baixar a velocidade caso o veiculo se esteja a aproximar à profundidade de destino
##Argumentos: prof_sen, profundidade mais recente lida pelo sensor de profundidade BAR30
##Retorna: O fator de diminuição da velocidade
def Degrau(prof_sen, prof):
    #Aqui vou definir os valores limitantes quando se aproxima
    Total = 1
    Prox = 0.75
    Mt_prox = 0.4
    Deg = prof - prof_sen   
    if(Deg < 0):
        Deg = -1 * Deg
    if(Deg >= 50):                                          ##Se estiver longe, não diminui
        return Total
    elif(Deg >= 25):                                        ##Se a aproximar-se, diminuis com um fator de 0.75
        return Prox
    else:
        return Mt_prox                                      ##Se estiver muito proximo diminui a velocidade com um fator de 0.25
    



##Altera a profundidade, ativa os motores para o ROV atingir uma posição especifica no eixo dos ZZ
##Argumentos: Motores, o vetor que contem todos os motores
##            prof, a profundidade que é pretendida atingir
##Retorna o vetor de motores com eles atualizados
def Altera_Profundidade(Motores, prof):
    prof_sen = Definir.Ler_Profundidade()
    var.altera = 0
    if(prof_sen + tol <= prof):
        while(prof_sen + tol <= prof):                                              ##Se a profundidade atual for menor que a pretendida
            Fator_dm = Degrau(prof_sen, prof)   
            if(var.altera == 1):break
            Pot = Motores[0].Pot_Disponivel * Fator_dm * var.velocidade / 100       ##Calcula a potencia que é pretendida fornecer ao motor
            if(Motores[0].Ativo == 0 or round(Motores[0].Pot) != round(Pot)):                     ##Ativa os motores
                Signal = (Pot / R_trans_T100) + Base
                Motores[0] = Ativar_Motor(Motores[0], Signal, 0)
            if(Motores[1].Ativo == 0  or round(Motores[1].Pot) != round(Pot)):
                Signal = (Pot / R_trans_T100) + Base
                Motores[1] = Ativar_Motor(Motores[1], Signal, 1)
            prof_sen = Definir.Ler_Profundidade()
    elif(prof_sen + tol >= prof):
        while(prof_sen + tol >= prof):                                               ##Se a profundidade atual for maior que a pretendida
            Fator_dm = Degrau(prof_sen, prof)  
            if(var.altera == 1):break
            Pot = Motores[0].Pot_Disponivel * Fator_dm * var.velocidade / 100        ##Calcula a potencia que é pretendida enviar
            if(Motores[0].Ativo == 0 or round(abs(Motores[0].Pot)) != round(Pot)):                      ##Ativa os motores
                Signal =  Base - (Pot / R_trans_T100)
                Motores[0] = Ativar_Motor(Motores[0], Signal, 0)
            if(Motores[1].Ativo == 0 or round(abs(Motores[1].Pot)) != round(Pot)):
                Signal = Base - (Pot / R_trans_T100)
                Motores[1] = Ativar_Motor(Motores[1], Signal, 1)
            prof_sen = Definir.Ler_Profundidade()
    print("saí da altera profundidade")
    Desliga_Motor(Motores[0], 0)
    Desliga_Motor(Motores[1], 1)
    return Motores

