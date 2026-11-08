
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import io
from PIL import Image
import requests
import serial
import pyaudiowpatch as pyaudio
import numpy as np
import win32gui
import win32process
import psutil
import pygetwindow as gw

from threading import Event, Thread
from serial_config import get_serial, send_packet

n = 10


def send(s, cell_id: int, color=(0, 0, 0), brightnes=50):
    to_com = f'S{str(cell_id)},{color[0]},{color[1]},{color[2]},{int(brightnes)},'
    send_packet(s, to_com.encode())


def change_contrast(img, level):
    factor = (259 * (level + 255)) / (255 * (259 - level))

    def contrast(c):
        return 128 + factor * (c - 128)

    return img.point(contrast)


def normalize(values, actual_bounds, desired_bounds):
    if actual_bounds[0] == actual_bounds[1]:
        return [desired_bounds[0] for _ in values]
    return [desired_bounds[0] + (x - actual_bounds[0]) * (desired_bounds[1] - desired_bounds[0]) / (
            actual_bounds[1] - actual_bounds[0]) for x in values]


def get_win_name():
    hwnd_list = []

    def winEnumHandler(hwnd, ctx):
        if win32gui.IsWindowVisible(hwnd):
            try:
                _, process_id = win32process.GetWindowThreadProcessId(hwnd)
                if psutil.Process(process_id).name().lower() == 'spotify.exe':
                    hwnd_list.append(hwnd)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                return

    win32gui.EnumWindows(winEnumHandler, None)
    if not hwnd_list:
        return None
    try:
        return gw.Win32Window(hwnd_list[0]).title
    except (OSError, RuntimeError):
        return None


class SpotifyThread(Thread):
    def __init__(self):
        super().__init__()
        self.running = True
        self.error = None
        self._image_thread = None

    def stop(self):
        self.running = False
        if self._image_thread is not None:
            self._image_thread.stop()

    def run(self):
        try:
            with get_serial() as s:
                spotify_th = SpotifyImgThread(s)
                self._image_thread = spotify_th
                if not self.running:
                    return
                spotify_th.start()
                try:
                    self._run_audio(s, spotify_th)
                finally:
                    spotify_th.stop()
                    # Retain ownership of the port until the image writer exits.
                    spotify_th.join()
        except Exception as error:
            self.error = str(error)
        finally:
            self.running = False

    def _run_audio(self, s, spotify_th):
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
                else:
                    raise RuntimeError('No WASAPI loopback input matches the output device')

            old_bri = 0

            with p.open(format=pyaudio.paInt16,
                        channels=default_speakers["maxInputChannels"],
                        rate=int(default_speakers["defaultSampleRate"]),
                        frames_per_buffer=CHUNK_SIZE,
                        input=True,
                        input_device_index=default_speakers["index"],
                        ) as stream:
                while self.running:
                    if not spotify_th.is_alive():
                        raise RuntimeError('Spotify artwork worker stopped')
                    data = stream.read(CHUNK_SIZE)
                    data = np.frombuffer(data, dtype=np.int16)
                    xs, data = fft(data)
                    # data = data[1 * (len(data) // 10):]

                    bri = sum(data) // len(data)
                    bri = normalize([bri], (0, 20_000), (10, 50))[0]
                    bri = min(50, max(0, bri))

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
                    old_bri = bri


class SpotifyImgThread(Thread):
    def __init__(self, s):
        super().__init__()
        self.sending_img = False
        self.zero_pix = (0, 0, 0)
        self.running = True
        self.error = None
        self.s = s
        self._stopped = Event()

    def stop(self):
        self.running = False
        self._stopped.set()

    def _make_client(self):
        scope = "user-read-currently-playing"
        sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id="94ca28be207d442ca8978852d28bcb11",
                                                       client_secret="32ae0ee9592f4bbbbe58bfc412ae1c32",
                                                       redirect_uri="https://github.com/MrRodikolion/forArduinoMatrix",
                                                       scope=scope, requests_timeout=5),
                             requests_timeout=5, retries=0, status_retries=0)
        return sp

    def run(self):
        try:
            sp = self._make_client()
            current_track_name = ''
            while self.running:
                try:
                    current_win_name = get_win_name()
                    if (not current_win_name or current_win_name == current_track_name
                            or current_win_name == 'Spotify Free'):
                        self._stopped.wait(0.5)
                        continue
                    if self._stopped.wait(2):
                        break
                    current_track = sp.current_user_playing_track()
                    item = (current_track or {}).get('item') or {}
                    images = (item.get('album') or {}).get('images') or []
                    if not images:
                        self._stopped.wait(1)
                        continue
                    with requests.get(images[0]['url'], timeout=(3, 5)) as response:
                        response.raise_for_status()
                        with Image.open(io.BytesIO(response.content)) as image:
                            img_pil = image.resize((10, 10), Image.Resampling.LANCZOS).convert('RGB')
                    self.zero_pix = img_pil.getpixel((0, 0))
                    self.sending_img = True
                    try:
                        for y in range(10):
                            for x in range(10):
                                if not self.running:
                                    break
                                cell_id = y * 10 + (x if y % 2 == 0 else 9 - x)
                                send(self.s, cell_id, color=img_pil.getpixel((x, y)), brightnes=20)
                            if not self.running:
                                break
                    finally:
                        self.sending_img = False
                    current_track_name = current_win_name
                except (serial.SerialException, TimeoutError):
                    self.error = 'Serial communication with the matrix failed'
                    break
                except Exception as error:
                    self.error = type(error).__name__ + ': artwork update failed'
                    self._stopped.wait(1)
        except Exception as error:
            self.error = type(error).__name__ + ': Spotify initialization failed'
        finally:
            self.sending_img = False
            self.running = False
