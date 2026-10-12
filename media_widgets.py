import numpy as np
import math
from PySide6.QtWidgets import QStackedWidget, QWidget
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtMultimedia import QAudioBufferOutput, QAudioBuffer, QAudioFormat
from PySide6.QtGui import QPainter, QPen, QColor, QBrush, QRadialGradient
from PySide6.QtCore import Qt

class AudioVisualizer(QWidget):
    """Визуализация-туннель с радужным фоном, белым осциллографом и мерцающей обводкой"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent)
        self.samples = []
        self.mode = "scope"  # Режимы: "scope" или "xp"
        self.setMinimumHeight(150)

        # Переменные для анимации
        self.rotation_angle = 0.0
        self.hue_phase = 0.0

    def update_samples(self, samples):
        self.samples = samples
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        height, width = self.height(), self.width()
        mid_y = height // 2
        mid_x = width // 2

        # Вычисляем пиковую громкость для динамического мерцания и пульсации
        max_amplitude = 0.05
        if self.samples:
            max_amplitude = max([abs(s) for s in self.samples]) / 32768.0
            max_amplitude = max(0.05, min(1.0, max_amplitude))

        self.rotation_angle += 0.04 + max_amplitude * 0.06
        self.hue_phase = (self.hue_phase + 0.3) % 360

        if self.mode == "scope":
            # Режим 1: Обычный зеленый осциллограф
            painter.fillRect(event.rect(), QColor(0, 0, 0))
            painter.setPen(QPen(QColor(0, 255, 0), 2, Qt.PenStyle.SolidLine))

            if not self.samples:
                painter.drawLine(0, mid_y, width, mid_y)
                return

            num_samples = len(self.samples)

            # Строим ломаную линию точно от левого до правого края окна плеера
            for x in range(width - 1):
                idx1 = int(x * (num_samples / width))
                idx2 = int((x + 1) * (num_samples / width))

                if idx1 < num_samples and idx2 < num_samples:
                    s1 = self.samples[idx1] / 32768.0
                    s2 = self.samples[idx2] / 32768.0

                    y1 = int(mid_y + (s1 * mid_y * 0.8))
                    y2 = int(mid_y + (s2 * mid_y * 0.8))

                    y1 = max(0, min(height - 1, y1))
                    y2 = max(0, min(height - 1, y2))

                    painter.drawLine(x, y1, x + 1, y2)
        elif self.mode == "xp":
            # Режим 2: Динамический переливающийся туннель в стиле WMP 9
            center_color = QColor.fromHsv(int(self.hue_phase), 230, 255)
            mid_color = QColor.fromHsv(int((self.hue_phase + 40) % 360), 200, 180)
            outer_color = QColor.fromHsv(int((self.hue_phase + 80) % 360), 255, 40)

            gradient = QRadialGradient(mid_x, mid_y, max(width, height) // 2)
            gradient.setColorAt(0.0, QColor(255, 255, 255))
            gradient.setColorAt(0.2, center_color)
            gradient.setColorAt(0.6, mid_color)
            gradient.setColorAt(1.0, outer_color)
            painter.fillRect(event.rect(), QBrush(gradient))

            max_radius = min(mid_x, mid_y) * 0.9

            # --- ЭФФЕКТ МЕРЦАНИЯ И СВЕЧЕНИЯ ДЛЯ ОБВОДКИ ШАРИКА ---
            # Прозрачность и толщина внешнего свечения зависят от мощности басов
            glow_opacity = int(80 + max_amplitude * 155)
            glow_thickness = int(4 + max_amplitude * 12)

            # Рисуем внешнее размытое неоновое кольцо свечения (Glow)
            painter.setPen(QPen(QColor(255, 255, 255, glow_opacity // 2), glow_thickness))
            painter.drawEllipse(mid_x - int(max_radius * 0.4), mid_y - int(max_radius * 0.4),
                                int(max_radius * 0.8), int(max_radius * 0.8))

            if not self.samples:
                # Статичное белое кольцо в состоянии покоя
                painter.setPen(QPen(QColor(255, 255, 255, 180), 3))
                painter.drawEllipse(mid_x - int(max_radius * 0.4), mid_y - int(max_radius * 0.4),
                                    int(max_radius * 0.8), int(max_radius * 0.8))
                return

            # Отрисовка белых энергетических петель осциллографа
            num_points = min(180, len(self.samples))
            step = len(self.samples) // num_points
            points = []

            for i in range(num_points):
                s = self.samples[(i * step) % len(self.samples)] / 32768.0
                angle = (i / num_points) * 2 * math.pi + self.rotation_angle
                r = max_radius * (0.4 + s * 0.25)
                points.append((int(mid_x + r * math.cos(angle)), int(mid_y + r * math.sin(angle))))

            # Основная белая обводка (исправлен баг падения типов координат)
            painter.setPen(QPen(QColor(255, 255, 255, 220), 3))
            for i in range(len(points) - 1):
                painter.drawLine(points[i][0], points[i][1], points[i+1][0], points[i+1][1])
            if points:
                painter.drawLine(points[-1][0], points[-1][1], points[0][0], points[0][1])

            # Тонкие лучи взрыва из центра
            painter.setPen(QPen(QColor(255, 255, 255, 90), 1))
            for i in range(0, num_points, 15):
                s = self.samples[(i * step) % len(self.samples)] / 32768.0
                ang = (i / num_points) * 2 * math.pi - self.rotation_angle * 0.5
                r_out = max_radius * (0.7 + abs(s) * 0.3)
                painter.drawLine(mid_x, mid_y, int(mid_x + r_out * math.cos(ang)), int(mid_y + r_out * math.sin(ang)))


class PlayerDisplayManager(QStackedWidget):
    def __init__(self, media_player, parent=None):
        super().__init__(parent)
        self.video_widget = QVideoWidget()
        self.visualizer = AudioVisualizer()

        self.addWidget(self.video_widget)
        self.addWidget(self.visualizer)

        self.buffer_output = QAudioBufferOutput()
        self.buffer_output.audioBufferReceived.connect(self.process_audio_buffer)
        media_player.setAudioBufferOutput(self.buffer_output)

        self.setCurrentIndex(0)

    def update_display_mode(self, file_path: str) -> bool:
        audio_extensions = ('.mp3', '.wav', '.ogg', '.flac', '.m4a')
        if file_path.lower().endswith(audio_extensions):
            self.setCurrentIndex(1)
            return True
        else:
            self.setCurrentIndex(0)
            return False

    def process_audio_buffer(self, audio_buffer: QAudioBuffer):
        if self.currentIndex() != 1:
            return

        audio_format = audio_buffer.format()
        sample_count = audio_buffer.sampleCount()
        if sample_count == 0:
            return

        data_ptr = audio_buffer.constData()

        if audio_format.sampleFormat() == QAudioFormat.SampleFormat.Int16:
            samples = np.frombuffer(data_ptr, dtype=np.int16, count=sample_count)
        elif audio_format.sampleFormat() == QAudioFormat.SampleFormat.Float:
            floats = np.frombuffer(data_ptr, dtype=np.float32, count=sample_count)
            samples = (floats * 32767).astype(np.int16)
        else:
            return

        if audio_format.channelCount() > 1:
            samples = samples[::audio_format.channelCount()]

        self.visualizer.update_samples(samples.tolist())
