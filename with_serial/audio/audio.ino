#define LED_PIN 5
#define LED_NUM 100
#include "FastLED.h"

CRGB leds[LED_NUM];

// ВНИМАНИЕ! Если отправляет print (отправка символа) - ASCII_CONVERT должен быть '0'
// (переводит символы даты в цифры)
// Если отправляет write (отправка чистого байта) - ASCII_CONVERT должен быть просто 0
#define ASCII_CONVERT '0'


byte buffer[10][10];
int buffer_len = 0;
byte counters[10];

float col_val;



void setup() {
  Serial.begin(9600);
  FastLED.addLeds<WS2812, LED_PIN, GRB>(leds, LED_NUM);
  FastLED.setBrightness(50);
}

void loop() {
  buffer_len = parsing();
  if (buffer_len) {
    FastLED.clear();

    for (int col = 0; col < 10; ++col) {
      col_val = 0;
      for (int i = 0; i < counters[col]; ++i) {
        col_val += buffer[col][counters[col] - i - 1] * pow(10, i);
      }
      // Serial.print(col_val);Serial.print(' ');
      int cell_id = 0;
      for (int cell_y = 0; cell_y < col_val; ++cell_y){
        cell_id = (9 - cell_y) * 10;
        if (cell_y % 2 != 0) {
          cell_id += col;
        } else {
          cell_id += 9 - col;
        }
        leds[cell_id] = CRGB(random(255), random(255), random(255));
        // Serial.print(cell_id);Serial.print(' ');Serial.print(cell_y);Serial.print(' ');Serial.print(col);Serial.print(' ');Serial.println(col_val);
        
      }
    }
    // Serial.println();

    FastLED.show();
    Serial.print('d');
  }
}

// парсер. Возвращает количество принятых байтов даты
int parsing() {
  static bool parseStart = false;
  static byte counter = 0;
  static size_t bi = 0;

  if (Serial.available()) {
    char in = Serial.read();
    if (in == '\n' || in == '\r')
      return 0;       // игнорируем перевод строки
    if (in == ';') {  // завершение пакета
      counters[bi] = counter;
      parseStart = false;
      return counter;
    }
    if (in == '$') {  // начало пакета
      parseStart = true;
      counter = 0;
      bi = 0;
      return 0;
    }
    if (in == ',') {
      counters[bi] = counter;

      counter = 0;
      bi++;
      return 0;
    }
    if (parseStart) {  // чтение пакета
      // - '0' это перевод в число (если отправитель print)
      buffer[bi][counter] = in - ASCII_CONVERT;
      counter++;
    }
  }
  return 0;
}