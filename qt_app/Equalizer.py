import serial
from serial.tools import list_ports
import pyaudiowpatch as pyaudio
import time
import numpy as np
import matplotlib.pyplot as plt
from random import randint
from threading import Thread
from serial_config import get_serial



def send(s: serial.Serial, cols):
    to_com = f'E{",".join(str(int(col)) for col in cols)},'

    s.write(to_com.encode())
    s.read()



def normalize(values, actual_bounds, desired_bounds):
    return [desired_bounds[0] + (x - actual_bounds[0]) * (desired_bounds[1] - desired_bounds[0]) / (
            actual_bounds[1] - actual_bounds[0]) for x in values]


CHUNK_SIZE = 512


class EqualizerThread(Thread):
    def __init__(self):
        super().__init__()
        self.running = True


    def run(self):
        s = get_serial()
        h = 0
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

                    new_h = (max(data) + min(data)) / 2
                    if new_h > h:
                        h = new_h

                    um = []
                    for i in range(10):
                        patch = np.max(data[i * (len(data) // 10): (i + 1) * (len(data) // 10)])
                        patch = max(0, min(h, patch))
                        um.append(patch)
                    um = normalize(um, (0, h), (0, 10))[::-1]

                    ts = time.time()
                    send(s, um)
                    if time.time() - ts > 1:
                        break