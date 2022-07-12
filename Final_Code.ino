#include <Wire.h>
#include "MS5837.h"
#include <stdio.h>
#include <string.h>
#include <Servo.h>
#include <stdlib.h> 
#include <Arduino_FreeRTOS.h>


MS5837 sensor;
#define I2C_SLAVE_ADDRESS 11 // 12 pour l'esclave 2 et ainsi de suite
//int n;
int ledPin = 13;  // LED
int leakPin = 2;    // Leak Signal Pin
int leak = 0;      // 0 = Dry , 1 = Leak
int Base = 1500;
int position = 0, signal = 0;
const int interval = 1000;
int aux_time = 0;
float v[4] = {0};
Servo Vetor[6];
Servo Motor1, Motor2, Motor3, Motor4, Motor5, Motor6;
String pres, temp, dep, data = "\0", envia;
unsigned long myTime = 0;
//char *data;


void bar30();
void requestEvents(int temp);
int sosleak();
void SetUp_Motores();
void Ativa_Mot();
void Desliga_mot(int pos);
void Teste();
void Raspberry();

void setup() {

  Serial.begin(9600);
  Wire.begin();
  Wire.begin(I2C_SLAVE_ADDRESS);
  Wire.onRequest(requestEvents);
  pinMode(ledPin, OUTPUT);
  pinMode(12, OUTPUT);
  pinMode(8, OUTPUT);
  pinMode(leakPin, INPUT);
  Serial.begin(9600);
  while (!sensor.init()) {
    Serial.println("Bar30 Failed");
    delay(5000);
  }
  sensor.setModel(MS5837::MS5837_30BA);
  sensor.setFluidDensity(997); // kg/m^3 (freshwater, 1029 for seawater)
  SetUp_Motores();
}

void loop() {
  // put your main code here, to run repeatedly:
  int x = 0; 
  Raspberry();
  bar30();
  x = sosleak();
  Serial.print(pres + "/" + temp + "/" + dep + "/" + x + "/");
  Serial.print("\n");
  delay(10);
}

void SetUp_Motores(){
  Motor1.attach(3);
  Motor1.writeMicroseconds(1500); // send "stop" signal to ESC.
  
  Motor2.attach(5);
  Motor2.writeMicroseconds(1500); // send "stop" signal to ESC.
  
  Motor3.attach(6);
  Motor3.writeMicroseconds(1500); // send "stop" signal to ESC.
  
  Motor4.attach(9);
  Motor4.writeMicroseconds(1500); // send "stop" signal to ESC.
  
  Motor5.attach(10);
  Motor5.writeMicroseconds(1500); // send "stop" signal to ESC.
  
  Motor6.attach(11);
  Motor6.writeMicroseconds(1500); // send "stop" signal to ESC.
  Vetor[0] = Motor1;
  Vetor[1] = Motor2;
  Vetor[2] = Motor3;
  Vetor[3] = Motor4;
  Vetor[4] = Motor5;
  Vetor[5] = Motor6;
}
void bar30(){

  // Update pressure and temperature readings
  sensor.read();

  //Serial.print("Pressure: ");   
  v[0] = sensor.pressure();  
  pres = String(v[0]).c_str();
  if(v[0] < 1000)  {
    
    pres = "0" + pres;
  }
  
  //Serial.print("Temperature: "); 
  v[1] = sensor.temperature();
  temp = String(v[1]).c_str();
  if(v[1] < 10)
  {    
    temp = "0" + temp;
  }
  requestEvents(sensor.temperature());
  v[2] = sensor.depth();  
  dep = String(v[2]).c_str();
  if(v[2] < 0)
  {
    dep = "00.00";
  }
  else if(v[2] < 10)
  {
    dep = "0" + dep;
  }
  //Serial.println("Saí bar30");

}
void requestEvents(int temp)
{
  Wire.write(temp);
}

int sosleak(){
  leak = digitalRead(leakPin);   // Read the Leak Sensor Pin
  digitalWrite(ledPin, leak);  // Sets the LED to the Leak Sensor's Value

  if (leak == 1) {
    //Leak Detected!
    return 1;
  }
  else{    
    //Leak Undetected!
    return 0;
  }
}

void Ativa_Mot(){
  
  switch(position){
    case(0):
      Motor1.writeMicroseconds(signal*10);
      break;
    case(1):
      Motor2.writeMicroseconds(signal*10);
      break;
    case(2):
      Motor3.writeMicroseconds(signal*10);
      break;
    case(3):
      Motor4.writeMicroseconds(signal*10);
      break;
    case(4):
      Motor5.writeMicroseconds(signal*10);
      break;
    case(5):
      Motor6.writeMicroseconds(signal*10); 
      break;
  }
}

void Desliga_Mot(int pos){
  Vetor[pos].writeMicroseconds(Base);
}


void Raspberry()
{  
  if (Serial.available() > 0) {
    int x = 0, y = 0, z = 0, m = 0;
    char aux[2], aux2[2], aux3[2], aux4[2];
    data = Serial.readStringUntil('x');
    aux[0] = data[0];
    aux[1] = "\0";
    aux2[0] = data[2];
    aux2[1] = "\0";
    aux3[0] = data[3];
    aux3[1] = "\0";
    aux4[0] = data[4];
    aux4[1] = "\0";    
    position = atoi(aux);
    y = atoi(aux2) * 100;
    z = atoi(aux3) * 10;    
    m = atoi(aux4);
    signal = y + z + m;
    Ativa_Mot();
  }

}
