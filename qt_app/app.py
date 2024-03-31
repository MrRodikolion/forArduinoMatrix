from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
import serial
from spotify import SpotifyThread
from Equalizer import EqualizerThread

def quit_app():
    spotify_th.running = False
    spotify_th.global_running = False
    equalizer_th.running = False
    equalizer_th.global_running = False
    if spotify_th.is_alive():
        spotify_th.join(timeout=5)
    if equalizer_th.is_alive():
        equalizer_th.join(timeout=5)

    app.quit()


def set_spotify_mode():
    try:
        equalizer_th.running = False
        while not equalizer_th.sleeping:
            pass
        spotify_th.running = True
        spotify_th.sleeping = False
    except BaseException as e:
        print(e)

def set_equalizer_mode():
    try:
        spotify_th.running = False
        while not spotify_th.sleeping:
            pass
        equalizer_th.running = True
        equalizer_th.sleeping = False
    except BaseException as e:
        print(e)



spotify_th = SpotifyThread()
equalizer_th = EqualizerThread()
spotify_th.start()
equalizer_th.start()

app = QApplication([])
app.setQuitOnLastWindowClosed(False)

icon = QIcon("icon.png")

tray = QSystemTrayIcon()
tray.setIcon(icon)
tray.setVisible(True)

menu = QMenu()
spotify_option = QAction("Spotify Mode")
spotify_option.triggered.connect(set_spotify_mode)
menu.addAction(spotify_option)
equalizer_option = QAction("Equalizer Mode")
equalizer_option.triggered.connect(set_equalizer_mode)
menu.addAction(equalizer_option)

quito = QAction("Quit")
quito.triggered.connect(quit_app)
menu.addAction(quito)

tray.setContextMenu(menu)

app.exec_()
spotify_th.join()
