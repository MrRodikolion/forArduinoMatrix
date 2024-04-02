import serial

def get_serial():
    return serial.Serial('COM8', 9600, timeout=1)