import pprint
import time

import serial
from time import sleep
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import io
from PIL import Image, ImageEnhance
import requests
import serial
import pyaudiowpatch as pyaudio
import numpy as np
import win32gui
import win32process
import psutil
import pygetwindow as gw

from threading import Thread
from serial_config import get_serial

n = 10


def send(s, cell_id: int, color=(0, 0, 0), brightnes=50):
    to_com = f'S{str(cell_id)},{color[0]},{color[1]},{color[2]},{int(brightnes)},'
    s.write(to_com.encode())
    s.read()


def change_contrast(img, level):
    factor = (259 * (level + 255)) / (255 * (259 - level))

    def contrast(c):
        return 128 + factor * (c - 128)

    return img.point(contrast)


def normalize(values, actual_bounds, desired_bounds):
    return [desired_bounds[0] + (x - actual_bounds[0]) * (desired_bounds[1] - desired_bounds[0]) / (
            actual_bounds[1] - actual_bounds[0]) for x in values]


def get_win_name():
    spoti = r"Spotify.exe"
    hwnd_list = []

    def winEnumHandler(hwnd, ctx):
        if win32gui.IsWindowVisible(hwnd):
            thread_id, process_id = win32process.GetWindowThreadProcessId(hwnd)
            # Get the process name and executable path
            process = psutil.Process(process_id)
            process_name = process.name()
            process_path = process.exe()
            if spoti == process_name:
                hwnd_list.append(hwnd)

    win32gui.EnumWindows(winEnumHandler, None)

    hwnd = hwnd_list[0]

    window = gw.Win32Window(hwnd)

    return window.title


class SpotifyThread(Thread):
    def __init__(self):
        super().__init__()
        self.running = True

    def run(self):
        s = get_serial()

        spotify_th = SpotifyImgThread(s)
        spotify_th.start()

        CHUNK_SIZE = 512
        with pyaudio.PyAudio() as p:
            wasapi_info = p.get_host_api_info_by_type(pyaudio.paWASAPI)

            # Get default WASAPI speakers
            default_speakers = p.get_device_info_by_index(wasapi_info["defaultOutputDevice"])

            def fft(data=None, trimBy=10, logScale=False, divBy=100):
                left, right = np.split(np.abs(np.fft.fft(data)), 2)
                ys = np.add(left, right[::-1])
                if logScale:
                    ys = np.multiply(20, np.log10(ys))
                xs = np.arange(CHUNK_SIZE / 2, dtype=float)
                if trimBy:
                    i = int((CHUNK_SIZE / 2) / trimBy)
                    ys = ys[:i]
                    xs = xs[:i] * int(default_speakers["defaultSampleRate"]) / CHUNK_SIZE
                if divBy:
                    ys = ys / float(divBy)
                return xs, ys

            if not default_speakers["isLoopbackDevice"]:
                for loopback in p.get_loopback_device_info_generator():
                    if default_speakers["name"] in loopback["name"]:
                        default_speakers = loopback
                        break

            old_bri = 0

            with p.open(format=pyaudio.paInt16,
                        channels=default_speakers["maxInputChannels"],
                        rate=int(default_speakers["defaultSampleRate"]),
                        frames_per_buffer=CHUNK_SIZE,
                        input=True,
                        input_device_index=default_speakers["index"],
                        ) as stream:
                while self.running:
                    data = stream.read(CHUNK_SIZE)
                    data = np.frombuffer(data, dtype=np.int16)
                    xs, data = fft(data)
                    # data = data[1 * (len(data) // 10):]

                    bri = sum(data) // len(data)
                    bri = normalize([bri], (0, 20_000), (10, 50))[0]
                    bri = min(50, max(0, bri))

                    ts = time.time()
                    if not spotify_th.sending_img and bri != old_bri and bri != 10 and abs(old_bri - bri) > 2:
                        send(
                            s,
                            0,
                            color=spotify_th.zero_pix,
                            brightnes=bri
                        )
                    else:
                        if bri == 10 and bri != old_bri:
                            send(
                                s,
                                0,
                                color=spotify_th.zero_pix,
                                brightnes=50
                            )
                    if time.time() - ts > 1:
                        break
                    old_bri = bri
        spotify_th.running = False
        spotify_th.join(timeout=5)


class SpotifyImgThread(Thread):
    def __init__(self, s):
        super().__init__()
        self.sending_img = False
        self.zero_pix = (0, 0, 0)
        self.running = True
        self.s = s

    def run(self):
        scope = "user-read-currently-playing"
        sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id="94ca28be207d442ca8978852d28bcb11",
                                                       client_secret="32ae0ee9592f4bbbbe58bfc412ae1c32",
                                                       redirect_uri="https://github.com/MrRodikolion/forArduinoMatrix",
                                                       scope=scope))
        current_track_name = ''
        while self.running:
            current_win_name = get_win_name()
            if current_track_name == current_win_name or current_win_name == 'Spotify Free':
                continue
            current_track_name = get_win_name()
            sleep(2)
            try:
                current_track = sp.current_user_playing_track()
                if current_track is not None:
                    self.sending_img = True

                    album = current_track['item']['album']
                    images = album['images']
                    img = images[0]
                    img_bytes = io.BytesIO(requests.get(img['url']).content)
                    img_pil = Image.open(img_bytes)
                    img_pil = img_pil.resize((10, 10), Image.LANCZOS)
                    img_pil = img_pil.convert('RGB')
                    # img_pil = ImageEnhance.Contrast(img_pil).enhance(100)
                    self.zero_pix = img_pil.getpixel((0, 0))

                    for y in range(10):
                        for x in range(10):
                            pixel = img_pil.getpixel((x, y))

                            cell_id = y * 10
                            if y % 2 == 0:
                                cell_id += x
                            else:
                                cell_id += 9 - x

                            ts = time.time()
                            send(
                                self.s,
                                cell_id,
                                color=pixel,
                                brightnes=20
                            )
                            if time.time() - ts > 1:
                                self.running = False
                                break
                        if not self.running:
                            break
                    self.sending_img = False
            except BaseException as e:
                print(e)
