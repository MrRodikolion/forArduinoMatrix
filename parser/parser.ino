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

// парсер. Возвращает количество принятых байтов даты
bool parse()
{
    bool isParsing = true;

    while (Serial.available())
    {
        char in = Serial.read();

        if (type == '-')
        {
            type = in;
            continue;
        }
        if (type == 'S')
        {
            sdata.cell_id = 0;
            while (in != ',')
            {
                if (Serial.available())
                {
                    sdata.cell_id = sdata.cell_id * 10 + (in - '0');

                    in = Serial.read();
                }
            }

            while (in == ',')
            {
                if (Serial.available())
                {
                    in = Serial.read();
                }
            }
            sdata.r = 0;
            while (in != ',')
            {
                if (Serial.available())
                {
                    sdata.r = sdata.r * 10 + (in - '0');

                    in = Serial.read();
                }
            }

            while (in == ',')
            {
                if (Serial.available())
                {
                    in = Serial.read();
                }
            }
            sdata.g = 0;
            while (in != ',')
            {
                if (Serial.available())
                {
                    sdata.g = sdata.g * 10 + (in - '0');

                    in = Serial.read();
                }
            }

            while (in == ',')
            {
                if (Serial.available())
                {
                    in = Serial.read();
                }
            }
            sdata.b = 0;
            while (in != ',')
            {
                if (Serial.available())
                {
                    sdata.b = sdata.b * 10 + (in - '0');

                    in = Serial.read();
                }
            }

            while (in == ',')
            {
                if (Serial.available())
                {
                    in = Serial.read();
                }
            }
            sdata.brightness = 0;
            while (in != ',')
            {
                if (Serial.available())
                {
                    sdata.brightness = sdata.brightness * 10 + (in - '0');

                    in = Serial.read();
                }
            }

            return 1;
        }
        else if (type == 'E')
        {
            for (size_t i = 0; i < 10; ++i)
            {
                while (in == ',')
                {
                    if (Serial.available())
                    {
                        in = Serial.read();
                    }
                }
                edata.cols_val[i] = 0;
                while (in != ',')
                {
                    if (Serial.available())
                    {
                        edata.cols_val[i] = edata.cols_val[i] * 10 + (in - '0');

                        in = Serial.read();
                    }
                }
            }
            return 1;
        }
    }
    return 0;
}