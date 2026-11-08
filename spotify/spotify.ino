// Делаем свой протокол для общения с устройствами по UART
// Протокол: $ дата_1 дата_2 дата_3 ;
// Пробелов между байтами нет! Просто передаём потоком
// Стартовый байт $ (значение 36)
// Конечный байт ; (значение 59)
// Первый байт даты - номер команды
// Остальные байты - данные
// Принимаем "вручную"

#define LED_PIN 5
#define LED_NUM 100
#include "FastLED.h"

CRGB leds[LED_NUM];

// ВНИМАНИЕ! Если отправляет print (отправка символа) - ASCII_CONVERT должен быть '0'
// (переводит символы даты в цифры)
// Если отправляет write (отправка чистого байта) - ASCII_CONVERT должен быть просто 0
#define ASCII_CONVERT '0'


byte buffer[5][5];
int buffer_len = 0;
byte cell_len = 0, r_len = 0, g_len = 0, b_len = 0, bri_len = 0;

float cell_id = 0;
float R = 0;
float G = 0;
float B = 0;
float bri = 0;

void setup() {
  Serial.begin(9600);
  FastLED.addLeds<WS2812, LED_PIN, GRB>(leds, LED_NUM);
  FastLED.setBrightness(20);
}

void loop() {
  bri_len = parsing();
  if (bri_len) {
    cell_id = 0;
    for (int i = 0; i < cell_len; ++i) {
      cell_id += buffer[0][cell_len - i - 1] * pow(10, i);
    }
    R = 0;
    for (int i = 0; i < r_len; ++i) {
      R += buffer[1][r_len - i - 1] * pow(10, i);
    }
    G = 0;
    for (int i = 0; i < g_len; ++i) {
      G += buffer[2][g_len - i - 1] * pow(10, i);
    }
    B = 0;
    for (int i = 0; i < b_len; ++i) {
      B += buffer[3][b_len - i - 1] * pow(10, i);
    }
    bri = 0;
    for (int i = 0; i < bri_len; ++i) {
      bri += buffer[4][bri_len - i - 1] * pow(10, i);
    }

    // Serial.print(cell_id);Serial.print(' ');Serial.print(R);Serial.print(' ');Serial.print(G);Serial.print(' ');Serial.print(B);Serial.print(' ');Serial.println(bri);
    
    FastLED.setBrightness((int)min(bri, 255.0f));
    if (cell_id < 0 || cell_id >= LED_NUM) {
      return;
    }
    leds[(int)cell_id] = CRGB((int)min(R, 255.0f), (int)min(G, 255.0f), (int)min(B, 255.0f));
    FastLED.show();
    Serial.print('d');
  }
}

// Validate field count and digit capacity before touching the receive buffer.
int parsing() {
  static bool parseStart = false;
  static byte counter = 0;
  static size_t bi = 0;

  if (Serial.available()) {
    char in = Serial.read();
    if (in == '$') {
      parseStart = true;
      counter = 0;
      bi = 0;
      return 0;
    }
    if (!parseStart || in == '\n' || in == '\r') {
      return 0;
    }
    if (in == ';') {
      parseStart = false;
      if (bi != 4 || counter == 0) {
        return 0;
      }
      return counter;
    }
    if (in == '_') {
      if (bi >= 4 || counter == 0) {
        parseStart = false;
        return 0;
      }
      switch (bi) {
        case 0: cell_len = counter; break;
        case 1: r_len = counter; break;
        case 2: g_len = counter; break;
        case 3: b_len = counter; break;
      }
      counter = 0;
      ++bi;
      return 0;
    }
    if (in < '0' || in > '9' || bi >= sizeof(buffer) / sizeof(buffer[0])
        || counter >= sizeof(buffer[0])) {
      parseStart = false;
      return 0;
    }
    buffer[bi][counter++] = in - ASCII_CONVERT;
  }
  return 0;
}
