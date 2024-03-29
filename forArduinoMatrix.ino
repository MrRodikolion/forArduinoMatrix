#define LED_PIN 5
#define LED_NUM 100

#include "FastLED.h"
#include "res.h"

CRGB leds[LED_NUM];

void setup() {
  FastLED.addLeds<WS2812, LED_PIN, GRB>(leds, LED_NUM);
  FastLED.setBrightness(50);

  for (size_t i = 0; i < LED_NUM; ++i) {
    leds[i] = CRGB(cells[i][0], cells[i][1], cells[i][2]);
  }
  FastLED.show();
}

void loop() {}