
import sys, os
from PySide6.QtCore import QTime, QUrl, Qt
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtWidgets import QApplication, QHBoxLayout, QLabel, QMainWindow, QPushButton, QSlider, QVBoxLayout, QWidget, QMessageBox
from pymediainfo import MediaInfo
from Crypto.Cipher import AES
from Crypto.Util import Counter

from widgets import WIN95_STYLE, InfoDialog, OpenDialog
from torrent_stream import TorrentStreamer




class VideoPlayer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("VideoLite")
        self.resize(700, 550)
        self.setStyleSheet(WIN95_STYLE)
        self.current_file_path, self.is_fullscreen = None, False
        self.current_lang = "ru"

        self.media_player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.media_player.setAudioOutput(self.audio_output)
        self.video_widget = QVideoWidget()
        self.media_player.setVideoOutput(self.video_widget)

        self.menu_bar = self.menuBar()

        self.file_menu = self.menu_bar.addMenu("Файл")
        self.open_action = self.file_menu.addAction("Открыть...", self.open_source_dialog, "Ctrl+O")
        self.info_action = self.file_menu.addAction("Параметры видео", self.show_video_info, "Ctrl+I")
        self.info_action.setEnabled(False)
        self.file_menu.addSeparator()
        self.file_menu.addAction("Выйти", self.close, "Alt+F4")


        self.help_menu = self.menu_bar.addMenu("Помощь")
        self.help_menu.addAction("О VideoLite...", self.show_about_box)
        lang_menu = self.help_menu.addMenu("Язык (Language)")
        lang_menu.addAction("Русский", lambda: self.change_language("ru"))
        lang_menu.addAction("English", lambda: self.change_language("en"))

        self.play_button = QPushButton("Воспроизвести")
        self.play_button.clicked.connect(self.toggle_play)
        self.open_button = QPushButton("Открыть...")
        self.open_button.clicked.connect(self.open_source_dialog)

        self.time_slider = QSlider(Qt.Orientation.Horizontal)
        self.time_slider.setRange(0, 0)
        self.time_slider.sliderMoved.connect(self.set_position)
        self.time_slider.sliderMoved.connect(self.on_slider_moved_live)

        self.time_label = QLabel("00:00 / 00:00")

        self.info_button = QPushButton("⋮")
        self.info_button.setFixedWidth(30)
        self.info_button.setEnabled(False)
        self.info_button.clicked.connect(self.show_video_info)

        self.fullscreen_button = QPushButton("[]")
        self.fullscreen_button.setFixedWidth(35)
        self.fullscreen_button.clicked.connect(self.toggle_fullscreen)

        for w in (self.time_slider, self.info_button, self.play_button, self.open_button, self.fullscreen_button):
            w.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        self.media_player.positionChanged.connect(self.position_changed)
        self.media_player.durationChanged.connect(self.duration_changed)

        self.control_panel = QWidget()
        control_layout = QHBoxLayout()
        control_layout.setContentsMargins(5, 5, 5, 5)
        for w in (self.play_button, self.open_button, self.time_slider, self.time_label, self.info_button, self.fullscreen_button):
            control_layout.addWidget(w)
        self.control_panel.setLayout(control_layout)

        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(8, 8, 8, 8)
        self.main_layout.addWidget(self.video_widget, stretch=1)
        self.main_layout.addWidget(self.control_panel)

        self.central_widget = QWidget()
        self.central_widget.setLayout(self.main_layout)
        self.setCentralWidget(self.central_widget)
        self.check_arguments()
    def change_language(self, lang_code):

        self.current_lang = lang_code
        is_playing = self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState

        if lang_code == "ru":
            self.file_menu.setTitle("Файл")
            self.help_menu.setTitle("Помощь")
            self.play_button.setText("Пауза" if is_playing else "Воспроизвести")
            self.open_button.setText("Открыть...")
            if not self.current_file_path:
                self.setWindowTitle("VideoLite")

        elif lang_code == "en":
            self.file_menu.setTitle("File")
            self.help_menu.setTitle("Help")
            self.play_button.setText("Pause" if is_playing else "Play")
            self.open_button.setText("Open...")
            if not self.current_file_path:
                self.setWindowTitle("VideoLite")

    def open_source_dialog(self):
        dialog = OpenDialog(self)
        if dialog.exec():
            source = dialog.result_path
            if source.startswith("magnet:?"):
                self.setWindowTitle("VideoLite - Буферизация торрента..." if self.current_lang == "ru" else "VideoLite - Torrent buffering...")
                self.streamer = TorrentStreamer(source)
                self.streamer.start_streaming()
                self.stream_timer = self.startTimer(1000)
            elif os.path.exists(source):
                self.load_video(source)

    def timerEvent(self, event):
        if hasattr(self, 'streamer') and self.streamer.is_ready:
            self.killTimer(self.stream_timer)
            self.load_video(self.streamer.video_file_path)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Right:
            self.media_player.setPosition(min(self.media_player.duration(), self.media_player.position() + 5000))
        elif event.key() == Qt.Key.Key_Left:
            self.media_player.setPosition(max(0, self.media_player.position() - 5000))
        elif event.key() in (Qt.Key.Key_Space, Qt.Key.Key_F, Qt.Key.Key_Escape):
            if event.key() == Qt.Key.Key_Space: self.toggle_play()
            elif event.key() == Qt.Key.Key_F: self.toggle_fullscreen()
            elif event.key() == Qt.Key.Key_Escape and self.is_fullscreen: self.toggle_fullscreen()
        else:
            super().keyPressEvent(event)

    def toggle_fullscreen(self):
        self.is_fullscreen = not self.is_fullscreen
        self.menu_bar.setVisible(not self.is_fullscreen)
        self.control_panel.setVisible(not self.is_fullscreen)
        self.main_layout.setContentsMargins(0 if self.is_fullscreen else 8, 0 if self.is_fullscreen else 8, 0 if self.is_fullscreen else 8, 0 if self.is_fullscreen else 8)
        self.video_widget.setStyleSheet("border: none;" if self.is_fullscreen else "border: 3px inset #808080;")
        self.showFullScreen() if self.is_fullscreen else self.showNormal()

    def check_arguments(self):
        if len(sys.argv) > 1 and os.path.exists(str(sys.argv[1])):
            self.load_video(str(sys.argv[1]))

    def load_video(self, path):
        self.current_file_path = path


        is_vl_file = False


        if path.endswith(".vl"):
            try:
                self.setWindowTitle("VideoLite - Дешифрование..." if self.current_lang == "ru" else "VideoLite - Decrypting...")
                is_vl_file = True

                with open(path, "rb") as f_in:
                    iv = f_in.read(16)
                    if len(iv) < 16:
                        raise ValueError("Файл поврежден")

                    ctr = Counter.new(128, initial_value=int.from_bytes(iv, byteorder='big'))
                    cipher = AES.new(SECRET_KEY, AES.MODE_CTR, counter=ctr)

                    self.temp_playing_file = os.path.join(os.path.dirname(path), ".temp_play.mp4")

                    with open(self.temp_playing_file, "wb") as f_out:
                        while True:
                            chunk = f_in.read(65536)
                            if not chunk:
                                break
                            f_out.write(cipher.decrypt(chunk))

                self.media_player.setSource(QUrl.fromLocalFile(self.temp_playing_file))

            except Exception as e:
                QMessageBox.critical(self, "Ошибка" if self.current_lang == "ru" else "Error", f"Не удалось открыть файл .vl!\n{str(e)}")
                self.setWindowTitle("VideoLite")
                return
        else:

            self.media_player.setSource(QUrl.fromLocalFile(path))
            if hasattr(self, 'temp_playing_file') and os.path.exists(self.temp_playing_file):
                try: os.remove(self.temp_playing_file)
                except: pass

        self.play_button.setText("Пауза" if self.current_lang == "ru" else "Pause")


        if is_vl_file:
            self.media_player.setPlaybackRate(0.5)
        else:
            self.media_player.setPlaybackRate(1.0)
        self.media_player.play()
        self.info_button.setEnabled(True)
        self.info_action.setEnabled(True)
        self.setWindowTitle(f"VideoLite - {os.path.basename(path)}")

    def toggle_play(self):
        is_playing = self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState
        self.media_player.pause() if is_playing else self.media_player.play()

        if self.current_lang == "ru":
            self.play_button.setText("Воспроизвести" if is_playing else "Пауза")
        else:
            self.play_button.setText("Play" if is_playing else "Pause")

    def position_changed(self, position):
        if not self.time_slider.isSliderDown():
            self.time_slider.setValue(position)
            pos_time = QTime(0, 0, 0).addMSecs(position).toString("mm:ss")
            dur_time = QTime(0, 0, 0).addMSecs(self.media_player.duration()).toString("mm:ss")
            self.time_label.setText(f"{pos_time} / {dur_time}")

    def on_slider_moved_live(self, position):
        pos_time = QTime(0, 0, 0).addMSecs(position).toString("mm:ss")
        dur_time = QTime(0, 0, 0).addMSecs(self.media_player.duration()).toString("mm:ss")
        self.time_label.setText(f"{pos_time} / {dur_time}")

    def duration_changed(self, duration): self.time_slider.setRange(0, duration)
    def set_position(self, position): self.media_player.setPosition(position)

    def closeEvent(self, event):

        if hasattr(self, 'temp_playing_file') and os.path.exists(self.temp_playing_file):
            try: os.remove(self.temp_playing_file)
            except: pass
        super().closeEvent(event)

    def show_about_box(self):
        about_box = QMessageBox(self)
        about_box.setIcon(QMessageBox.Icon.Information)
        about_box.setTextFormat(Qt.TextFormat.RichText)
        about_box.setTextInteractionFlags(Qt.TextInteractionFlag.LinksAccessibleByMouse)

        if self.current_lang == "ru":
            about_box.setWindowTitle("О VideoLite")
            info_text = (
                 "<b>VideoLite Player Beta v1.0.3</b><br><br>"
                "Поддержите нас: <a href='https://www.donationalerts.com/r/vladisapps'>Donationalerts</a><br>"
                "Наш <a href='https://github.com/telophon2-cloud/VideoLite-Player'>GitHub</a><br><br>"
                "Это Бета Версия и в ней могут присутствовать ошибки.<br>"
                "При нахождении ошибки сообщать сюда:<br>"
                "<b>Telogram:</b> <a href='t.me/f3h7a'>Наш менеджер</a><br>"
                "© 2026 VladisApps"
            )
        else:
            about_box.setWindowTitle("About VideoLite")
            info_text = (
                "<b>VideoLite Player Beta v1.0.3</b><br><br>"
                "Support us: <a href='https://www.donationalerts.com/r/vladisapps'>Donationalerts</a><br>"
                "Our <a href='https://github.com/telophon2-cloud/VideoLite-Player'>GitHub</a><br><br>"
                "This is a Beta Version and it may contain bugs.<br>"
                "If you find a bug, please report it here:<br>"
                "<b>Telegram:</b> <a href='t.me/f3h7a'>Our manager</a><br>"
                "© 2026 VladisApps"
            )
        about_box.setText(info_text)
        about_box.exec()

    def show_video_info(self):
        if not self.current_file_path:
            return

if __name__ == "__main__":
    app = QApplication(sys.argv)
    player = VideoPlayer()
    player.show()
    sys.exit(app.exec())
