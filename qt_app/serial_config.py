import os
from threading import Lock

import serial

_packet_lock = Lock()

def get_serial():
    return serial.Serial(os.environ.get('MATRIX_PORT', 'COM8'), 9600,
                         timeout=1, write_timeout=1)


def send_packet(connection, packet):
    # Artwork and audio share a port: keep each command and its ACK together.
    with _packet_lock:
        if connection.write(packet) != len(packet):
            raise serial.SerialTimeoutException('Incomplete matrix command write')
        if connection.read(1) != b'd':
            raise TimeoutError('Matrix did not acknowledge the command')
