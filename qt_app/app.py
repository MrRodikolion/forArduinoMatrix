import sys
from pathlib import Path

from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QAction, QApplication, QMenu, QMessageBox, QSystemTrayIcon

from spotify import SpotifyThread
from Equalizer import EqualizerThread

spotify_th = None
equalizer_th = None
app = None


def _stop_thread(worker):
    if worker is not None and worker.is_alive():
        worker.stop()
        worker.join(timeout=5)
        if worker.is_alive():
            QMessageBox.warning(None, 'Matrix',
                                'The current mode is still stopping. Please retry shortly.')
            return False
    return True


def pause():
    equalizer_stopped = _stop_thread(equalizer_th)
    spotify_stopped = _stop_thread(spotify_th)
    return equalizer_stopped and spotify_stopped


def quit_app():
    if pause() and app is not None:
        app.quit()


def set_spotify_mode():
    global spotify_th
    if spotify_th is not None and spotify_th.is_alive() and spotify_th.running:
        return
    if pause():
        spotify_th = SpotifyThread()
        spotify_th.start()


def set_equalizer_mode():
    global equalizer_th
    if equalizer_th is not None and equalizer_th.is_alive() and equalizer_th.running:
        return
    if pause():
        equalizer_th = EqualizerThread()
        equalizer_th.start()


def main():
    global app
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    app.aboutToQuit.connect(pause)

    icon = QIcon(str(Path(__file__).resolve().parent / 'icon.png'))
    tray = QSystemTrayIcon(icon)
    tray.setToolTip('Arduino Matrix')

    menu = QMenu()
    for label, callback in (('Spotify Mode', set_spotify_mode),
                            ('Equalizer Mode', set_equalizer_mode),
                            ('Pause', pause), ('Quit', quit_app)):
        action = QAction(label, menu)
        action.triggered.connect(callback)
        menu.addAction(action)

    tray.setContextMenu(menu)
    tray.show()
    set_equalizer_mode()
    return app.exec_()


if __name__ == '__main__':
    sys.exit(main())
