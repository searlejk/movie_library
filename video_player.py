import sys
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout,
                              QPushButton, QSlider, QStyle)
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtMultimediaWidgets import QVideoWidget
from PyQt6.QtCore import Qt, QUrl


class VideoPlayer(QWidget):
    def __init__(self, video_path="demo.mp4"):
        super().__init__()
        self.setWindowTitle("Video Player")
        self.setGeometry(100, 100, 900, 600)

        # Media player setup
        self.player = QMediaPlayer()
        self.audio = QAudioOutput()
        self.player.setAudioOutput(self.audio)
        self.video_widget = QVideoWidget()
        self.player.setVideoOutput(self.video_widget)

        # Buttons
        self.btn_back = QPushButton("← Back")
        self.btn_back.setFixedWidth(80)

        self.btn_rw = QPushButton("⏪ -10s")
        self.btn_play = QPushButton("▶ Play")
        self.btn_ff = QPushButton("⏩ +10s")

        # Seek slider
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setRange(0, 0)

        # Top bar layout
        top_layout = QHBoxLayout()
        top_layout.addWidget(self.btn_back)
        top_layout.addStretch()

        # Controls layout
        controls = QHBoxLayout()
        controls.addWidget(self.btn_rw)
        controls.addWidget(self.btn_play)
        controls.addWidget(self.btn_ff)

        # Main layout
        layout = QVBoxLayout()
        layout.addLayout(top_layout)
        layout.addWidget(self.video_widget)
        layout.addWidget(self.slider)
        layout.addLayout(controls)
        self.setLayout(layout)

        # Connections
        self.btn_back.clicked.connect(self.close)
        self.btn_play.clicked.connect(self.toggle_play)
        self.btn_ff.clicked.connect(lambda: self.skip(10000))
        self.btn_rw.clicked.connect(lambda: self.skip(-10000))
        self.player.positionChanged.connect(self.slider.setValue)
        self.player.durationChanged.connect(self.slider.setMaximum)
        self.slider.sliderMoved.connect(self.player.setPosition)
        self.player.playbackStateChanged.connect(self.update_button)

        # Load and play
        self.player.setSource(QUrl.fromLocalFile(video_path))
        self.player.play()

    def toggle_play(self):
        if self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.player.pause()
        else:
            self.player.play()

    def skip(self, ms):
        self.player.setPosition(max(0, self.player.position() + ms))

    def update_button(self):
        if self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.btn_play.setText("⏸ Pause")
        else:
            self.btn_play.setText("▶ Play")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    player = VideoPlayer("demo.mp4")
    player.show()
    sys.exit(app.exec())