import Definir
import Motores
import time
import var

Motor = 0

Motor = Definir.CarregaMotores()
var.velocidade = 35

Motores.Ativar_Motor(Motor[0], Motores.Traduzir_Valores(Motores.frente), 0)
time.sleep(5)

print("Troca")
Motores.Ativar_Motor(Motor[0], Motores.Traduzir_Valores(Motores.tras), 0)
time.sleep(5)
Motores.Desliga_Motor(Motor[0],0)
