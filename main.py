
import sys, os
from PySide6.QtCore import QTime, QUrl, Qt
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtWidgets import QApplication, QHBoxLayout, QLabel, QMainWindow, QPushButton, QSlider, QVBoxLayout, QWidget, QMessageBox
from pymediainfo import MediaInfo

from widgets import WIN95_STYLE, InfoDialog, OpenDialog
from torrent_stream import TorrentStreamer

class VideoPlayer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("VideoLite")
        self.resize(700, 550)
        self.setStyleSheet(WIN95_STYLE)
        self.current_file_path, self.is_fullscreen = None, False

        self.media_player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.media_player.setAudioOutput(self.audio_output)
        self.video_widget = QVideoWidget()
        self.media_player.setVideoOutput(self.video_widget)


        self.menu_bar = self.menuBar()
        file_menu = self.menu_bar.addMenu("Файл")
        file_menu.addAction("Открыть...", self.open_source_dialog, "Ctrl+O")
        self.info_action = file_menu.addAction("Параметры видео", self.show_video_info, "Ctrl+I")
        self.info_action.setEnabled(False)
        file_menu.addSeparator()
        file_menu.addAction("Выйти", self.close, "Alt+F4")
        self.menu_bar.addMenu("Помощь").addAction("О VideoLite...", self.show_about_box)


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

    def open_source_dialog(self):

        dialog = OpenDialog(self)
        if dialog.exec():
            source = dialog.result_path
            if source.startswith("magnet:?"):
                self.setWindowTitle("VideoLite - Буферизация торрента...")
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
        if len(sys.argv) > 1 and os.path.exists(sys.argv):
            self.load_video(sys.argv)

    def load_video(self, path):
        self.current_file_path = path
        self.media_player.setSource(QUrl.fromLocalFile(path))
        self.play_button.setText("Пауза")
        self.media_player.play()
        self.info_button.setEnabled(True)
        self.info_action.setEnabled(True)
        self.setWindowTitle(f"VideoLite - {os.path.basename(path)}")

    def toggle_play(self):
        is_playing = self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState
        self.media_player.pause() if is_playing else self.media_player.play()
        self.play_button.setText("Воспроизвести" if is_playing else "Пауза")

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

    def show_about_box(self):

        about_box = QMessageBox(self)
        about_box.setWindowTitle("О VideoLite")
        about_box.setIcon(QMessageBox.Icon.Information)


        about_box.setTextFormat(Qt.TextFormat.RichText)


        about_box.setTextInteractionFlags(Qt.TextInteractionFlag.LinksAccessibleByMouse)

        info_text = (
            "<b>VideoLite Player Beta v1.0.0</b><br><br>"
            "Поддержите нас: <a href='https://www.donationalerts.com/r/vladisapps'>Donationalerts</a><br><br>"
            "Это Бета Версия и в ней могут присутствовать ошибки.<br>"
            "При нахождении ошибки сообщать сюда:<br>"
            "<b>Россия (VK):</b> <a href='https://vk.ru/club240801897'>vk.com</a><br>"
            "<b>Россия (Telegram):</b> <a href='t.me/f3h7a'>Наш менеджер</a><br>"
            "<b>Европа (Telegram):</b> <a href='https://t.me/f3h7a'>Наш менеджер</a><br>"
            "<b>США (Telegram):</b> <a href='https://t.me/f3h7a'>Наш менеджер</a><br><br>"
            "© 2026 VladisApps"
        )

        about_box.setText(info_text)
        about_box.exec()

    def show_video_info(self):
        if not self.current_file_path: return
        try:
            mi = MediaInfo.parse(self.current_file_path)
            g, v, a = "", "", ""
            for t in mi.tracks:
                if t.track_type == 'General':
                    g += f"Файл: {os.path.basename(self.current_file_path)}\nРазмер: {round((t.file_size or 0) / 1024 / 1024, 2)} MB\nДлительность: {QTime(0, 0, 0).addMSecs(t.duration or 0).toString('hh:mm:ss')}\n"
                elif t.track_type == 'Video':
                    v += f"\n--- ВИДЕО ПОТОК ---\nКодек: {t.codec_id or t.format}\nРазрешение: {t.width}x{t.height}\nFPS: {t.frame_rate}\n"
                elif t.track_type == 'Audio':
                    a += f"\n--- АУДИО ПОТОК ---\nКодек: {t.format}\nКаналы: {t.channel_s} ch\nЧастота: {t.sampling_rate} Hz\n"
            InfoDialog(g + v + a, self).exec()
        except Exception as e:
            InfoDialog(f"Ошибка метаданных:\n{e}", self).exec()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    player = VideoPlayer()
    player.show()
    sys.exit(app.exec())
