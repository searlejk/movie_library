import sys
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout,
                              QPushButton, QSlider)
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtMultimediaWidgets import QVideoWidget
from PyQt6.QtCore import Qt, QUrl, pyqtSignal, QTimer


class VideoPlayer(QWidget):
    back_pressed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Video Player")
        self.setStyleSheet("background-color: #1a1b26;")
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        self.player = QMediaPlayer()
        self.audio = QAudioOutput()
        self.player.setAudioOutput(self.audio)
        self.video_widget = QVideoWidget()
        self.player.setVideoOutput(self.video_widget)

        btn_style_normal = (
            "QPushButton { color: #cdd3e5; background: #2e3448; border: 2px solid #4a5168;"
            "border-radius: 8px; padding: 8px; font-size: 13px; }"
            "QPushButton:hover { background: #3f4f72; border-color: #73c0ff; }")
        btn_style_selected = (
            "QPushButton { color: #f0f3ff; background: #3f4f72; border: 2px solid #73c0ff;"
            "border-radius: 8px; padding: 8px; font-size: 13px; font-weight: 600; }")

        self._btn_style_normal = btn_style_normal
        self._btn_style_selected = btn_style_selected

        self.btn_back = QPushButton("← Back")
        self.btn_back.setFixedWidth(80)

        self.btn_rw = QPushButton("⏪ -10s")
        self.btn_rw.setFixedWidth(100)

        self.btn_play = QPushButton("▶ Play")
        self.btn_play.setFixedWidth(100)

        self.btn_ff = QPushButton("⏩ +10s")
        self.btn_ff.setFixedWidth(100)

        self._buttons = [self.btn_back, self.btn_rw, self.btn_play, self.btn_ff]
        self._btn_index = 2  # start on play/pause

        for btn in self._buttons:
            btn.setStyleSheet(btn_style_normal)
            btn.setFixedHeight(36)

        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setRange(0, 0)
        self.slider.setStyleSheet(
            "QSlider::groove:horizontal { background: #2e3448; height: 6px; border-radius: 3px; }"
            "QSlider::handle:horizontal { background: #73c0ff; width: 14px; margin: -4px 0;"
            "border-radius: 7px; }"
            "QSlider::sub-page:horizontal { background: #73c0ff; border-radius: 3px; }")

        # --- Layout is identical to the original ---
        top_layout = QHBoxLayout()
        top_layout.addWidget(self.btn_back)
        top_layout.addStretch()

        controls = QHBoxLayout()
        controls.addStretch()
        controls.addWidget(self.btn_rw)
        controls.addWidget(self.btn_play)
        controls.addWidget(self.btn_ff)
        controls.addStretch()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.addLayout(top_layout)
        layout.addWidget(self.video_widget)
        layout.addWidget(self.slider)
        layout.addLayout(controls)

        self.btn_back.clicked.connect(self._on_back)
        self.btn_play.clicked.connect(self.toggle_play)
        self.btn_ff.clicked.connect(lambda: self.skip(10000))
        self.btn_rw.clicked.connect(lambda: self.skip(-10000))
        self.player.positionChanged.connect(self.slider.setValue)
        self.player.durationChanged.connect(self.slider.setMaximum)
        self.slider.sliderMoved.connect(self.player.setPosition)
        self.player.playbackStateChanged.connect(self._update_play_text)

        # --- Widgets to hide/show ---
        self._hideable = [self.btn_back, self.btn_rw, self.btn_play,
                          self.btn_ff, self.slider]

        # --- Inactivity timer (3 seconds) ---
        self._inactivity_timer = QTimer(self)
        self._inactivity_timer.setSingleShot(True)
        self._inactivity_timer.setInterval(3000)
        self._inactivity_timer.timeout.connect(self._hide_controls)

        self._refresh_btn_styles()
        self._inactivity_timer.start()

    # ---- auto-hide / auto-show ----

    def _hide_controls(self):
        if self.player.playbackState() == QMediaPlayer.PlaybackState.PausedState:
            return
        for w in self._hideable:
            w.setVisible(False)

    def _show_controls(self):
        for w in self._hideable:
            w.setVisible(True)

    def _reset_inactivity(self):
        self._show_controls()
        if self.player.playbackState() == QMediaPlayer.PlaybackState.PausedState:
            self._inactivity_timer.stop()
        else:
            self._inactivity_timer.start()

    # ---- original methods (unchanged) ----

    def load_video(self, path):
        self.player.setSource(QUrl.fromLocalFile(path))
        self.player.play()
        self._btn_index = 2
        self._refresh_btn_styles()
        self._reset_inactivity()

    def stop_video(self):
        self.player.stop()
        self.player.setSource(QUrl())

    def toggle_play(self):
        if self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.player.pause()
        else:
            self.player.play()

    def skip(self, ms):
        self.player.setPosition(max(0, self.player.position() + ms))

    def _update_play_text(self):
        if self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.btn_play.setText("⏸ Pause")
            self._inactivity_timer.start()
        else:
            self.btn_play.setText("▶ Play")
            self._show_controls()
            self._inactivity_timer.stop()

    def _on_back(self):
        self.stop_video()
        self.back_pressed.emit()

    def _refresh_btn_styles(self):
        for i, btn in enumerate(self._buttons):
            if i == self._btn_index:
                btn.setStyleSheet(self._btn_style_selected)
            else:
                btn.setStyleSheet(self._btn_style_normal)

    def _press_current(self):
        btn = self._buttons[self._btn_index]
        btn.click()

    def keyPressEvent(self, event):
        key = event.key()

        # If controls are hidden, first arrow-key press only reveals controls
        # and resets focus to play/pause without moving selection.
        controls_hidden = not self.btn_play.isVisible()
        if key in (Qt.Key.Key_Left, Qt.Key.Key_Right, Qt.Key.Key_Up, Qt.Key.Key_Down) and controls_hidden:
            self._btn_index = 2
            self._refresh_btn_styles()
            self._reset_inactivity()
            return

        self._reset_inactivity()
        if key == Qt.Key.Key_Escape:
            self._on_back()
        elif key == Qt.Key.Key_Left:
            if self._btn_index > 0:
                self._btn_index -= 1
                self._refresh_btn_styles()
        elif key == Qt.Key.Key_Right:
            if self._btn_index < len(self._buttons) - 1:
                self._btn_index += 1
                self._refresh_btn_styles()
        elif key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self._press_current()
        else:
            super().keyPressEvent(event)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    player = VideoPlayer()
    player.load_video("demo.mp4")
    player.resize(900, 600)
    player.show()
    sys.exit(app.exec())