from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
import serial
from spotify import SpotifyThread
from Equalizer import EqualizerThread


def quit_app():
    global spotify_th, equalizer_th
    if equalizer_th.is_alive():
        equalizer_th.running = False
        equalizer_th.join()
    if spotify_th.is_alive():
        spotify_th.running = False
        spotify_th.join()

    app.quit()


def set_spotify_mode():
    global spotify_th, equalizer_th
    if equalizer_th.is_alive():
        equalizer_th.running = False
        equalizer_th.join()
    spotify_th = SpotifyThread()
    spotify_th.start()


def set_equalizer_mode():
    global equalizer_th, spotify_th
    if spotify_th.is_alive():
        spotify_th.running = False
        spotify_th.join()
    equalizer_th = EqualizerThread()
    equalizer_th.start()


spotify_th = SpotifyThread()
equalizer_th = EqualizerThread()

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
