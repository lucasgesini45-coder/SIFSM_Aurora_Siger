/*
 * SIFSM Aurora Siger - Sistema de Alerta Energético
 * Arduino Uno + 3 botões + LED + buzzer
 * A = consumo alto (D2)
 * B = módulo crítico (D3)
 * C = falha (D4)
 * LED D8 com resistor 220 ohms
 * Buzzer D9
 * Todos os botões: pino digital ao GND ao pressionar; INPUT_PULLUP.
 *
 * Regra: ALERTA = (A && B) || C
 * Projeto conceitual / Tinkercad; não há comunicação serial Python-Arduino.
 */

const byte PINO_A = 2;
const byte PINO_B = 3;
const byte PINO_C = 4;
const byte PINO_LED = 8;
const byte PINO_BUZZER = 9;

void setup() {
  pinMode(PINO_A, INPUT_PULLUP);
  pinMode(PINO_B, INPUT_PULLUP);
  pinMode(PINO_C, INPUT_PULLUP);
  pinMode(PINO_LED, OUTPUT);
  pinMode(PINO_BUZZER, OUTPUT);
  digitalWrite(PINO_LED, LOW);
  noTone(PINO_BUZZER);
  Serial.begin(9600);
  Serial.println("SIFSM Aurora Siger - Sistema de Alerta Energetico");
  Serial.println("ALERTA = (A && B) || C");
}

void loop() {
  const bool A = digitalRead(PINO_A) == LOW;
  const bool B = digitalRead(PINO_B) == LOW;
  const bool C = digitalRead(PINO_C) == LOW;
  const bool alerta = (A && B) || C;

  digitalWrite(PINO_LED, alerta ? HIGH : LOW);
  if (alerta) {
    tone(PINO_BUZZER, 1000);
  } else {
    noTone(PINO_BUZZER);
  }

  static int estadoAnterior = -1;
  const int estado = (A ? 4 : 0) | (B ? 2 : 0) | (C ? 1 : 0);
  if (estado != estadoAnterior) {
    Serial.print("A="); Serial.print(A);
    Serial.print(" B="); Serial.print(B);
    Serial.print(" C="); Serial.print(C);
    Serial.print(" ALERTA="); Serial.println(alerta);
    estadoAnterior = estado;
  }
  delay(30);  // intervalo de amostragem didático
}
