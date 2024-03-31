import serial

s = serial.Serial('COM3', 9600)

s.write('S0,2,5,168,20,'.encode())

print(s.read())