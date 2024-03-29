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


byte buffer[4][5];
int buffer_len = 0;
byte cell_len = 0, r_len = 0, g_len = 0, b_len = 0;

float cell_id = 0;
float R = 0;
float G = 0;
float B = 0;

void setup() {
  Serial.begin(9600);
  FastLED.addLeds<WS2812, LED_PIN, GRB>(leds, LED_NUM);
  FastLED.setBrightness(50);
}

void loop() {
  b_len = parsing();
  if (b_len) {
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

    Serial.print(cell_id);Serial.print(' ');Serial.print(R);Serial.print(' ');Serial.print(G);Serial.print(' ');Serial.println(B);

    leds[(int)cell_id] = CRGB(min((int)R, 255), min((int)G, 255), min((int)B, 255));
    FastLED.show();
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
      parseStart = false;
      return counter;
    }
    if (in == '$') {  // начало пакета
      parseStart = true;
      counter = 0;
      bi = 0;
      return 0;
    }
    if (in == '_') {
      switch (bi)
      {
      case 0:
        cell_len = counter;
        break;
      
      case 1:
        r_len = counter;
        break;

      case 2:
        g_len = counter;
        break;

      case 3:
        b_len = counter;
        break;

      default:
        break;
      }
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