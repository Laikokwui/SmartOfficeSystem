// include library
#include <SPI.h>
#include <MFRC522.h>

// Digiatal I/O
int sm = 2;
int ledR = 3;
int ledG = 4; 
int ledB = 5;
int led = 6;
int buzzer = 7;
int pir = 8; 
int rfid_rst = 9;
int rfid_sda = 10;
int rfid_mosi = 11;
int rfid_miso = 12;
int rfid_sck = 13;

// Analog I/O
int ldr = A1;

// lamp colours
int ledR_value = 255;
int ledG_value = 255;
int ledB_value = 255;

// State
int led_state = 0;
int ledR_state = 0;
int ledG_state = 0;
int ledB_state = 0;
int Lamp_status = 0;
int Light_status = 0;
String card_id = "NO CARD";
int LDR = 0;
int PIR = 0;
int SM = 0;

MFRC522 mfrc522(rfid_sda, rfid_rst); 
 
void setup() {
  SPI.begin(); 
  mfrc522.PCD_Init();
  
  pinMode(led, OUTPUT);
  pinMode(ledR, OUTPUT);
  pinMode(ledG, OUTPUT);
  pinMode(ledB, OUTPUT);
  pinMode(buzzer, OUTPUT);
  pinMode(pir, INPUT);
  pinMode(sm, INPUT);
  pinMode(ldr, INPUT);
  
  Serial.begin(9600);
}
 
void loop(){
  SM = digitalRead(sm);
  LDR = analogRead(ldr);
  PIR = digitalRead(pir);
  RFID();
  SendData();
  // receive serial message to perform action
  if (Serial.available() > 0){
    String Input = Serial.readStringUntil('\n');
    if(Input == "light on"){ // turn on led lights
      led_state = 1;
      Light_status = 1;
    }
    if(Input == "light off"){ // turn off led lights
      led_state = 0;
      Light_status = 0;
    }
    if(Input == "lamp on"){ // turn on table lamp
      ledR_state = ledR_value;
      ledG_state = ledG_value;
      ledB_state = ledB_value;
      Lamp_status = 1;
    }
    if(Input == "lamp off"){ // turn off table lamp
      ledR_state = 0;
      ledG_state = 0;
      ledB_state = 0;
      Lamp_status = 0;
    }
    if(Input == "buzzer success"){ // buzzer once
      tone(buzzer, 1000, 200); // buzzer alert
    }
    if(Input == "buzzer fail"){ // buzzer triple
      // Buzzer alert
      tone(buzzer, 1000, 50);
      delay(250);
      tone(buzzer, 1000, 50);
      delay(250);
      tone(buzzer, 1000, 50);
    }
    if(Input == "white"){ // lamp colour white
      ledR_value = 255;
      ledG_value = 255;
      ledB_value = 255;
    }
    if(Input == "red"){ // lamp colour red
      ledR_value = 255;
      ledG_value = 0;
      ledB_value = 0;
    }
    if(Input == "green"){ // lamp colour green
      ledR_value = 0;
      ledG_value = 255;
      ledB_value = 0;
    }
    if(Input == "blue"){ // lamp colour blue
      ledR_value = 0;
      ledG_value = 0;
      ledB_value = 255;
    }
    if(Input == "cyan"){ // lamp colour cyan
      ledR_value = 0;
      ledG_value = 255; 
      ledB_value = 255;
    }
    if(Input == "yellow"){ // lamp colour yellow
      ledR_value = 255;
      ledG_value = 230;
      ledB_value = 0;
    }
  }
  TableLampLight(ledR_state,ledG_state,ledB_state);
  digitalWrite(led, led_state);
  delay(1000);
}

void TableLampLight(int ledr, int ledg, int ledb){
  digitalWrite(ledR, ledr);
  digitalWrite(ledG, ledg);
  digitalWrite(ledB, ledb);
}

void SendData() {
  Serial.print(card_id);
  Serial.print(",");
  Serial.print(LDR);
  Serial.print(",");
  Serial.print(PIR);
  Serial.print(",");
  Serial.print(SM);
  Serial.print(",");
  Serial.print(Lamp_status);
  Serial.print(",");
  Serial.print(Light_status);
  Serial.println(",");
}

void RFID() {
  if ( ! mfrc522.PICC_IsNewCardPresent()){
    card_id = "NO CARD";
    return; 
  }
  if ( ! mfrc522.PICC_ReadCardSerial()){ 
    card_id = "NO CARD";
    return; 
  }

  String content = "";
  for (byte i = 0; i < mfrc522.uid.size; i++){
     content.concat(String(mfrc522.uid.uidByte[i] < 0x10 ? " 0" : " "));
     content.concat(String(mfrc522.uid.uidByte[i], HEX));
  }
  content.toUpperCase();
  card_id = content.substring(1);
  delay(3000);
}
