
import Definir
import time
liga = 1
desliga = 0

luz = Definir.SetUp_Lampada()
while(1):
    Definir.Controla_Lampada(liga, luz)
    time.sleep(5)
    Definir.Controla_Lampada(desliga, luz)
    time.sleep(5)
