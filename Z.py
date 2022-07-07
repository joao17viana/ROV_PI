import Definir
import Motores
import Principal
import communication

while(1):
    while(communication.altera == 0):
        Principal.Motor = Motores.Manter_Profundidade(Principal.Motor)
    Motor = Motores.Altera_Profundidade(Motor, communication.nova_profundidade)

