import pprint

import serial
from time import sleep
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import io
from PIL import Image, ImageEnhance
import requests

n = 10

s = serial.Serial('COM3', 9600)


def send(cell_id: int, color=(0, 0, 0)):
    s.write(f'${str(cell_id)}_{color[0]}_{color[1]}_{color[2]};'.encode())
    s.read()


def clear():
    for y in range(10):
        for x in range(10):
            cell_id = y * 10
            if y % 2 == 0:
                cell_id += x
            else:
                cell_id += 9 - x
            send(cell_id)
            sleep(0.15)


def change_contrast(img, level):
    factor = (259 * (level + 255)) / (255 * (259 - level))

    def contrast(c):
        return 128 + factor * (c - 128)

    return img.point(contrast)


def main():
    scope = "user-read-currently-playing"
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id="94ca28be207d442ca8978852d28bcb11",
                                                   client_secret="32ae0ee9592f4bbbbe58bfc412ae1c32",
                                                   redirect_uri="https://github.com/MrRodikolion/forArduinoMatrix",
                                                   scope=scope))
    current_track_name = ''

    while True:
        current_track = sp.current_user_playing_track()
        if current_track is not None:
            if current_track_name == current_track['item']['name']:
                continue
            current_track_name = current_track['item']['name']

            album = current_track['item']['album']
            images = album['images']
            img = images[0]
            img_bytes = io.BytesIO(requests.get(img['url']).content)
            img_pil = Image.open(img_bytes)
            # img_pil = ImageEnhance.Brightness(img_pil).enhance(50)
            img_pil = img_pil.resize((10, 10))
            img_pil = img_pil.convert('RGB')
            img_pil = ImageEnhance.Contrast(img_pil).enhance(100)

            for y in range(10):
                for x in range(10):
                    pixel = img_pil.getpixel((x, y))

                    cell_id = y * 10
                    if y % 2 == 0:
                        cell_id += x
                    else:
                        cell_id += 9 - x
                    send(cell_id, pixel)

        else:
            print("No song is currently playing.")


if __name__ == '__main__':
    main()
