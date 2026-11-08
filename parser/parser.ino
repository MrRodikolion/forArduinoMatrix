#define LED_PIN 5
#define LED_NUM 100
#include "FastLED.h"

CRGB leds[LED_NUM];

// ВНИМАНИЕ! Если отправляет print (отправка символа) - ASCII_CONVERT должен быть '0'
// (переводит символы даты в цифры)
// Если отправляет write (отправка чистого байта) - ASCII_CONVERT должен быть просто 0
#define ASCII_CONVERT '0'

char type = '-';

struct SpotifyData
{
    int cell_id;
    int r, g, b;
    int brightness;
};
SpotifyData sdata;

struct EqualizerData
{
    int cols_val[10];
};
EqualizerData edata;

void setup()
{
    Serial.begin(9600);
    FastLED.addLeds<WS2812, LED_PIN, GRB>(leds, LED_NUM);
    FastLED.setBrightness(20);
}

void loop()
{
    if (parse())
    {
        if (type == 'S')
        {
            FastLED.setBrightness(sdata.brightness);
            leds[sdata.cell_id] = CRGB(min(sdata.r, 255), min(sdata.g, 255), min(sdata.b, 255));
            FastLED.show();
        }
        else if (type == 'E')
        {
            FastLED.clear();

            for (int col = 0; col < 10; ++col)
            {   
                int cell_id = 0;
                for (int cell_y = 0; cell_y < edata.cols_val[col]; ++cell_y)
                {
                    cell_id = (9 - cell_y) * 10;
                    if (cell_y % 2 != 0)
                    {
                        cell_id += col;
                    }
                    else
                    {
                        cell_id += 9 - col;
                    }
                    leds[cell_id] = CRGB(random(255), random(255), random(255));
                }
            }

            FastLED.show();
        }
        Serial.print('d');
        type = '-';
    }
}

// Consume only available bytes; partial frames never block loop().
bool parse()
{
    static char activeType = '-';
    static uint8_t field = 0;
    static uint16_t value = 0;
    static bool hasDigit = false;
    static int values[10];
    static unsigned long lastByte = 0;

    if (activeType != '-' && (unsigned long)(millis() - lastByte) > 1000)
    {
        activeType = '-';
    }

    while (Serial.available())
    {
        char in = Serial.read();
        if (in == 'S' || in == 'E')
        {
            activeType = in;
            field = 0;
            value = 0;
            hasDigit = false;
            lastByte = millis();
            continue;
        }
        if (activeType == '-')
        {
            continue;
        }
        lastByte = millis();
        if (in == '\r' || in == '\n')
        {
            continue;
        }
        if (in >= '0' && in <= '9')
        {
            uint16_t limit = activeType == 'E' ? 10 : (field == 0 ? LED_NUM - 1 : 255);
            uint8_t digit = in - '0';
            if (value > limit / 10 || (value == limit / 10 && digit > limit % 10))
            {
                activeType = '-';
                continue;
            }
            value = value * 10 + digit;
            hasDigit = true;
        }
        else if (in == ',' && hasDigit)
        {
            values[field++] = value;
            value = 0;
            hasDigit = false;
            uint8_t expected = activeType == 'S' ? 5 : 10;
            if (field == expected)
            {
                type = activeType;
                activeType = '-';
                if (type == 'S')
                {
                    sdata.cell_id = values[0];
                    sdata.r = values[1];
                    sdata.g = values[2];
                    sdata.b = values[3];
                    sdata.brightness = values[4];
                }
                else
                {
                    for (uint8_t i = 0; i < 10; ++i)
                    {
                        edata.cols_val[i] = values[i];
                    }
                }
                return true;
            }
        }
        else
        {
            activeType = '-';
        }
    }
    return false;
}
