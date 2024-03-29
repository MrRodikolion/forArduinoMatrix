import serial

s = serial.Serial('COM3', 9600)

s.write('$9,2,2,2,2,2,2,2,2,2;'.encode())

print(s.read())