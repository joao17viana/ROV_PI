import Definir
import Motores
import Principal
import time

Matriz = Definir.Cria_Matriz()
while(1):
    Matriz, Principal.Motor = Motores.Matriz_Atc(Matriz,Principal.Motor)
