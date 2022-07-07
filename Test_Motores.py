import Definir
import Motores
import time
import var

Motor = 0

Motor = Definir.CarregaMotores()
Definir.SetUp_Motores(Motor)


for i in range(0, 1):
    print("ok vamos tentar pôr 10 perc da velocidade a cada um durante 10 segundos aos pares")
    var.velocidade = 10
    Motores.Ativar_Motor(Motor[i*2], Motores.Traduzir_Valores(Motores.frente))
    Motores.Ativar_Motor(Motor[i*2 + 1], Motores.Traduzir_Valores(Motores.frente))
    time.sleep(10)
    Motores.Desliga_Motor(Motor[i*2])
    Motores.Desliga_Motor(Motor[i*2 + 1])

for i in range(0, 1):
    print("ok vamos tentar pôr 25 perc da velocidade a cada um durante 10 segundos aos pares")
    var.velocidade = 25
    Motores.Ativar_Motor(Motor[i*2], Motores.Traduzir_Valores(Motores.frente))
    Motores.Ativar_Motor(Motor[i*2 + 1], Motores.Traduzir_Valores(Motores.frente))
    time.sleep(10)
    Motores.Desliga_Motor(Motor[i*2])
    Motores.Desliga_Motor(Motor[i*2 + 1])


