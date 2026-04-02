import sys
import time
import json
import math
from pathlib import Path
from datetime import datetime
from PyQt6.QtWidgets import (QApplication, QWidget, QScrollArea, QVBoxLayout,
                              QFrame, QHBoxLayout, QGridLayout, QLabel, QStackedWidget,
                              QGraphicsOpacityEffect)
from PyQt6.QtCore import (Qt, QRectF, QPoint, QTimer, QPropertyAnimation, QEasingCurve,
                           QParallelAnimationGroup, pyqtProperty)
from PyQt6.QtGui import QPainter, QColor, QFont, QPen, QLinearGradient
from video_player import VideoPlayer

ANIMAL_NAMES = [
    "Aardvark", "Albatross", "Alligator", "Alpaca", "Anaconda", "Antelope",
    "Baboon", "Badger", "Barracuda", "Bat", "Bear", "Beaver",
    "Bison", "Boar", "Buffalo", "Camel", "Capybara", "Caribou",
    "Cheetah", "Cobra", "Cougar", "Coyote", "Crocodile", "Crow",
    "Deer", "Dingo", "Dolphin", "Donkey", "Eagle", "Elephant",
    "Falcon", "Ferret", "Fox", "Frog", "Gazelle", "Giraffe",
    "Goat", "Gorilla", "Hamster", "Hawk", "Hippo", "Horse",
    "Hyena", "Iguana", "Jackal", "Jaguar", "Kangaroo", "Koala",
    "Lemur", "Leopard", "Liger", "Lion", "Lizard", "Llama",
    "Lynx", "Moose", "Narwhal", "Ocelot", "Otter", "Panda",
]

KEY_MAP = {
    Qt.Key.Key_Left: "left", Qt.Key.Key_Right: "right",
    Qt.Key.Key_Up: "up", Qt.Key.Key_Down: "down",
}

TOKEN_LABELS = {"SPACE": "Space", "DEL": "Delete", "CLEAR": "Clear", "EXIT": "Exit"}
MOVS_DIR = Path(__file__).resolve().parent / "movs"
WATCH_STATE_PATH = Path(__file__).resolve().parent / "watch_state.json"


def make_anim(target, prop, start, end, duration, parent=None):
    anim = QPropertyAnimation(target, prop, parent)
    anim.setDuration(duration)
    anim.setStartValue(start)
    anim.setEndValue(end)
    anim.setEasingCurve(QEasingCurve.Type.OutCubic)
    return anim


class RectCard(QWidget):
    EXTRA_TEXT_H = 60  # Increased to accommodate two lines of text

    def __init__(self, index, label, base_width, base_height, parent=None):
        super().__init__(parent)
        self._index, self._label = index, label
        self._subtitle = ""
        self._resume_progress = None
        self._base_width, self._base_height = base_width, base_height
        self._scale, self._selected, self._glow_opacity = 1.0, False, 0.0
        self._base_cell_w = int(base_width * 1.35)
        self._base_cell_h = int(base_height * 1.35)
        self.setFixedSize(self._base_cell_w, self._base_cell_h + self.EXTRA_TEXT_H)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

    def _get_scale(self): return self._scale
    def _set_scale(self, v): self._scale = v; self.update()
    scale = pyqtProperty(float, _get_scale, _set_scale)

    def _get_glow(self): return self._glow_opacity
    def _set_glow(self, v): self._glow_opacity = v; self.update()
    glow_opacity = pyqtProperty(float, _get_glow, _set_glow)

    def set_label(self, label): self._label = label; self.update()

    def set_subtitle(self, subtitle): self._subtitle = subtitle; self.update()

    def set_resume_progress(self, progress):
        if progress is None:
            self._resume_progress = None
        else:
            self._resume_progress = max(0.0, min(1.0, float(progress)))
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.TextAntialiasing)

        text_top = self._base_cell_h
        w, h = self._base_width * self._scale, self._base_height * self._scale
        cx, cy = self.width() / 2.0, text_top / 2.0
        rect = QRectF(cx - w / 2, cy - h / 2, w, h)

        # Shadow effect
        if self._scale > 1.0:
            off = 4 * (self._scale - 1.0) / 0.3
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(0, 0, 0, int(40 * min(self._glow_opacity * 2, 1.0))))
            p.drawRoundedRect(rect.adjusted(off, off, off, off), 10, 10)

        # Card background
        grad = QLinearGradient(rect.topLeft(), rect.bottomRight())
        grad.setColorAt(0, QColor(58, 63, 78))
        grad.setColorAt(1, QColor(42, 46, 58))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(grad)
        p.drawRoundedRect(rect, 8, 8)

        if self._resume_progress is not None:
            # Red badge indicates that a resume timestamp exists.
            badge_r = 5
            badge_x = rect.right() - 12
            badge_y = rect.top() + 12
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(240, 68, 68))
            p.drawEllipse(QPoint(int(badge_x), int(badge_y)), badge_r, badge_r)

            # Progress bar at the bottom of the card with dot at saved timestamp.
            bar_margin = 16
            bar_h = 4
            bar_w = max(24.0, rect.width() - bar_margin * 2)
            bar_x = rect.left() + bar_margin
            bar_y = rect.bottom() - 10
            bar_rect = QRectF(bar_x, bar_y, bar_w, bar_h)

            p.setBrush(QColor(95, 103, 126, 180))
            p.drawRoundedRect(bar_rect, 2, 2)

            fill_w = bar_w * self._resume_progress
            fill_rect = QRectF(bar_x, bar_y, fill_w, bar_h)
            p.setBrush(QColor(240, 68, 68, 220))
            p.drawRoundedRect(fill_rect, 2, 2)

            dot_x = bar_x + fill_w
            dot_y = bar_y + bar_h / 2.0
            p.setBrush(QColor(252, 128, 128))
            p.drawEllipse(QPoint(int(dot_x), int(dot_y)), 4, 4)

        # Title (fixed size, doesn't scale)
        title_font = QFont("Helvetica Neue", 14, QFont.Weight.Medium)
        p.setFont(title_font)
        p.setPen(QColor(232, 236, 245, int(190 + 65 * min(self._glow_opacity, 1.0))))
        title_h = p.fontMetrics().height()
        title_rect = QRectF(6, rect.bottom() + 2, self.width() - 12, title_h)
        title = p.fontMetrics().elidedText(self._label, Qt.TextElideMode.ElideRight, int(title_rect.width()))
        p.drawText(title_rect, Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter, title)

        # Subtitle (fixed size, doesn't scale)
        if self._subtitle:
            sub_font = QFont("Helvetica Neue", 11, QFont.Weight.Normal)
            p.setFont(sub_font)
            p.setPen(QColor(170, 178, 194))
            sub_h = p.fontMetrics().height()
            sub_rect = QRectF(6, title_rect.bottom() + 2, self.width() - 12, sub_h)
            subtitle = p.fontMetrics().elidedText(self._subtitle, Qt.TextElideMode.ElideRight, int(sub_rect.width()))
            p.drawText(sub_rect, Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter, subtitle)
        p.end()


class GridWidget(QWidget):
    CARD_ANIM_MS = 500

    def __init__(self, cols, labels, card_w, card_h, spacing, margin,
                 subtitle_provider=None, resume_provider=None, parent=None):
        super().__init__(parent)
        self._cols, self._total = cols, len(labels)
        self._card_w, self._card_h = card_w, card_h
        self._subtitle_provider = subtitle_provider or (lambda _: "")
        self._resume_provider = resume_provider or (lambda _: None)
        self._margin, self._current = margin, 0
        self._selection_visible = True
        self._rows = (self._total + cols - 1) // cols
        self._cards = []
        self._animations = QParallelAnimationGroup(self)

        cell_w = int(card_w * 1.35)
        cell_h = int(card_h * 1.35) + RectCard.EXTRA_TEXT_H
        row_spacing = spacing // 2
        self._row_step = cell_h + row_spacing

        self.setFixedSize(margin * 2 + cols * cell_w + (cols - 1) * spacing,
                          margin * 2 + self._rows * cell_h + (self._rows - 1) * row_spacing)

        for i, label in enumerate(labels):
            card = RectCard(i, label, card_w, card_h, self)
            card.set_subtitle(self._subtitle_provider(label))
            card.set_resume_progress(self._resume_provider(label))
            card.move(margin + (i % cols) * (cell_w + spacing),
                      margin + (i // cols) * self._row_step)
            self._cards.append(card)

        self._select(0, animate=False)

    def current_label(self):
        return self._cards[self._current]._label if 0 <= self._current < len(self._cards) else ""

    def refresh_subtitles(self):
        for card in self._cards:
            card.set_subtitle(self._subtitle_provider(card._label))
            card.set_resume_progress(self._resume_provider(card._label))

    def _select(self, index, animate=True):
        if not (0 <= index < self._total):
            return

        self._animations.stop()
        self._animations = QParallelAnimationGroup(self)
        dur = self.CARD_ANIM_MS if animate else 0
        old, self._current = self._current, index

        if old != index and old < len(self._cards):
            self._cards[old]._selected = False
            self._animations.addAnimation(
                make_anim(self._cards[old], b"scale", self._cards[old]._scale, 1.0, dur))

        card = self._cards[index]
        card._selected = True
        target = 1.3 if self._selection_visible else 1.0

        if animate:
            self._animations.addAnimation(make_anim(card, b"scale", card._scale, target, dur))
            self._animations.start()
        else:
            card._scale = target
            card.update()

    def set_selection_visible(self, visible, animate=True):
        if self._selection_visible == visible:
            return
        self._selection_visible = visible
        if not (0 <= self._current < len(self._cards)):
            return

        card = self._cards[self._current]
        target = 1.3 if visible else 1.0
        self._animations.stop()
        self._animations = QParallelAnimationGroup(self)

        if animate:
            self._animations.addAnimation(
                make_anim(card, b"scale", card._scale, target, self.CARD_ANIM_MS))
            self._animations.start()
        else:
            card._scale = target
            card.update()

    def move_selection(self, direction):
        row, col = self._current // self._cols, self._current % self._cols

        if direction == "left":    col = max(0, col - 1)
        elif direction == "right": col = min(self._cols - 1, col + 1)
        elif direction == "up":    row = max(0, row - 1)
        elif direction == "down":  row = min(self._rows - 1, row + 1)

        new_index = row * self._cols + col
        if new_index < self._total and new_index != self._current:
            self._select(new_index)
        return self._cards[self._current]


class SearchBarWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._text, self._selected, self._expanded = "", False, False
        self.setFixedHeight(52)

    def set_text(self, t):     self._text = t; self.update()
    def set_selected(self, s): self._selected = s; self.update()
    def set_expanded(self, e): self._expanded = e; self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.TextAntialiasing)

        rect = self.rect().adjusted(1, 1, -1, -1)
        grad = QLinearGradient(float(rect.left()), float(rect.top()),
                               float(rect.left()), float(rect.bottom()))
        if self._expanded:
            grad.setColorAt(0, QColor(46, 52, 70))
            grad.setColorAt(1, QColor(37, 41, 56))
        else:
            grad.setColorAt(0, QColor(41, 45, 60))
            grad.setColorAt(1, QColor(34, 37, 49))

        p.setPen(QPen(QColor(122, 188, 255) if self._selected else QColor(72, 78, 98), 2))
        p.setBrush(grad)
        p.drawRoundedRect(rect, 12, 12)

        # Search icon
        ix, iy = rect.left() + 18, rect.center().y()
        p.setPen(QPen(QColor(205, 210, 226), 2))
        p.drawEllipse(ix - 6, iy - 6, 12, 12)
        p.drawLine(ix + 5, iy + 5, ix + 10, iy + 10)

        # Search text
        text = self._text or "Search"
        p.setPen(QColor(236, 239, 248) if self._text else QColor(165, 171, 192))
        p.setFont(QFont("Helvetica Neue", 13, QFont.Weight.Medium))
        p.drawText(rect.adjusted(40, 0, -12, 0), Qt.AlignmentFlag.AlignVCenter, text)
        p.end()


class KeyboardKey(QFrame):
    def __init__(self, text="", parent=None):
        super().__init__(parent)
        self._selected = False
        self.setMinimumSize(72, 48)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setStyleSheet("background: transparent;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(0)
        self._label = QLabel(text, self)
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._label)
        self._apply_style()

    def set_selected(self, selected):
        self._selected = selected
        self._apply_style()

    def _apply_style(self):
        if self._selected:
            self.setStyleSheet("QFrame { background: #3f4f72; border: 2px solid #73c0ff; border-radius: 10px; }")
            self._label.setStyleSheet("color: #f0f3ff; font-size: 19px; font-weight: 600; font-family: 'Helvetica Neue';")
        else:
            self.setStyleSheet("QFrame { background: #2e3448; border: 1px solid #4a5168; border-radius: 10px; }")
            self._label.setStyleSheet("color: #cdd3e5; font-size: 14px; font-weight: 500; font-family: 'Helvetica Neue';")


class SearchPanel(QWidget):
    ROWS = [
        ["A", "B", "C", "D", "E", "F"],
        ["G", "H", "I", "J", "K", "L"],
        ["M", "N", "O", "P", "Q", "R"],
        ["S", "T", "U", "V", "W", "X"],
        ["Y", "Z", "SPACE", "DEL", "CLEAR", "EXIT"],
    ]

    def __init__(self, card_w, card_h, anim_ms=500,
                 subtitle_provider=None, resume_provider=None, parent=None):
        super().__init__(parent)
        self._kb_tiles, self._res_tiles = [], []
        self._results = []
        self._subtitle_provider = subtitle_provider or (lambda _: "")
        self._resume_provider = resume_provider or (lambda _: None)
        self._focus_zone = "keyboard"
        self._key_row = self._key_col = self._res_idx = 0
        self._active_res_idx = None
        self._anim_ms = anim_ms
        self._res_anims = QParallelAnimationGroup(self)

        root = QHBoxLayout(self)
        root.setContentsMargins(24, 14, 24, 20)
        root.setSpacing(20)

        # Keyboard section
        left = QWidget(self)
        left_lay = QVBoxLayout(left)
        left_lay.setContentsMargins(0, 0, 0, 0)
        left_lay.setSpacing(10)
        kb_grid = QGridLayout()
        kb_grid.setSpacing(10)
        for r, row in enumerate(self.ROWS):
            tile_row = []
            for c, token in enumerate(row):
                tile = KeyboardKey(TOKEN_LABELS.get(token, token), parent=left)
                kb_grid.addWidget(tile, r, c)
                tile_row.append(tile)
            self._kb_tiles.append(tile_row)
        left_lay.addLayout(kb_grid)
        left_lay.addStretch(1)

        # Results section
        right = QWidget(self)
        right_lay = QVBoxLayout(right)
        right_lay.setContentsMargins(0, 0, 0, 0)
        right_lay.setSpacing(10)
        res_grid = QGridLayout()
        res_grid.setSpacing(12)
        for c in range(3):
            res_grid.setColumnStretch(c, 1)
        for i in range(6):
            tile = RectCard(i, "", card_w, card_h, right)
            tile.hide()
            self._res_tiles.append(tile)
            res_grid.addWidget(tile, i // 3, i % 3)
        right_lay.addLayout(res_grid)
        right_lay.addStretch(1)

        root.addWidget(left, 1)
        root.addWidget(right, 1)
        self._refresh_selection()

    def reset_navigation(self):
        self._focus_zone = "keyboard"
        self._key_row = self._key_col = self._res_idx = 0
        self._refresh_selection()

    def focus_zone(self): return self._focus_zone

    def set_results(self, results):
        self._results = results[:6]
        for i, tile in enumerate(self._res_tiles):
            if i < len(self._results):
                label = self._results[i]
                tile.set_label(label)
                tile.set_subtitle(self._subtitle_provider(label))
                tile.set_resume_progress(self._resume_provider(label))
                tile.show()
                # FIX: Reset all tiles to default state initially
                if i != self._active_res_idx:
                    tile._scale = 1.0
                    tile._glow_opacity = 0.0
            else:
                tile.hide()
                tile._scale = 1.0
                tile._glow_opacity = 0.0
        if not self._results and self._focus_zone == "results":
            self._focus_zone = "keyboard"
        self._res_idx = min(self._res_idx, max(0, len(self._results) - 1))
        self._refresh_selection()

    def refresh_subtitles(self):
        for i, tile in enumerate(self._res_tiles):
            if i < len(self._results):
                label = self._results[i]
                tile.set_subtitle(self._subtitle_provider(label))
                tile.set_resume_progress(self._resume_provider(label))

    def move(self, direction):
        if self._focus_zone == "keyboard":
            self._move_kb(direction)
        else:
            self._move_res(direction)
        self._refresh_selection()

    def _move_kb(self, d):
        if d == "left":
            self._key_col = max(0, self._key_col - 1)
        elif d == "right":
            if self._key_col < len(self.ROWS[self._key_row]) - 1:
                self._key_col += 1
            elif self._results:
                self._focus_zone = "results"
                self._res_idx = 0
        elif d == "up":
            self._key_row = max(0, self._key_row - 1)
            self._key_col = min(self._key_col, len(self.ROWS[self._key_row]) - 1)
        elif d == "down":
            self._key_row = min(len(self.ROWS) - 1, self._key_row + 1)
            self._key_col = min(self._key_col, len(self.ROWS[self._key_row]) - 1)

    def _move_res(self, d):
        if not self._results:
            self._focus_zone = "keyboard"
            return
        row, col = self._res_idx // 3, self._res_idx % 3
        if d == "left":
            if col > 0:
                self._res_idx -= 1
            else:
                self._focus_zone = "keyboard"
                self._key_row = min(row, len(self.ROWS) - 1)
                self._key_col = len(self.ROWS[self._key_row]) - 1
        elif d == "right":
            cand = self._res_idx + 1
            if col < 2 and cand < len(self._results):
                self._res_idx = cand
        elif d == "up":
            cand = self._res_idx - 3
            if cand >= 0:
                self._res_idx = cand
        elif d == "down":
            cand = self._res_idx + 3
            if cand < len(self._results):
                self._res_idx = cand

    def press_enter(self):
        if self._focus_zone == "keyboard":
            return "key", self.ROWS[self._key_row][self._key_col]
        if self._focus_zone == "results" and self._results:
            return "result", self._results[self._res_idx]
        return None, None

    def _refresh_selection(self):
        for r, row in enumerate(self._kb_tiles):
            for c, tile in enumerate(row):
                tile.set_selected(self._focus_zone == "keyboard"
                                  and r == self._key_row and c == self._key_col)

        next_idx = (self._res_idx
                    if self._focus_zone == "results" and self._res_idx < len(self._results)
                    else None)
        if self._active_res_idx != next_idx:
            self._animate_res_focus(self._active_res_idx, next_idx)
            self._active_res_idx = next_idx

    def _animate_res_focus(self, old, new):
        self._res_anims.stop()
        self._res_anims = QParallelAnimationGroup(self)
        d = self._anim_ms

        # FIX: Reset ALL visible tiles first, then animate the focused one
        for i, tile in enumerate(self._res_tiles):
            if i < len(self._results) and i != new and i != old:
                tile._scale = 1.0
                tile._glow_opacity = 0.0
                tile.update()

        if old is not None and 0 <= old < len(self._res_tiles):
            c = self._res_tiles[old]
            self._res_anims.addAnimation(make_anim(c, b"scale", c._scale, 1.0, d, self))
            self._res_anims.addAnimation(make_anim(c, b"glow_opacity", c._glow_opacity, 0.0, d, self))

        if new is not None and 0 <= new < len(self._res_tiles):
            c = self._res_tiles[new]
            self._res_anims.addAnimation(make_anim(c, b"scale", c._scale, 1.3, d, self))
            self._res_anims.addAnimation(make_anim(c, b"glow_opacity", c._glow_opacity, 1.0, d, self))

        # Hidden tiles should also be reset
        for i, tile in enumerate(self._res_tiles):
            if i >= len(self._results):
                tile._scale = 1.0
                tile._glow_opacity = 0.0
                tile.update()

        if self._res_anims.animationCount() > 0:
            self._res_anims.start()


class MainWindow(QWidget):
    SCROLL_ANIM_MS = 1550
    VERT_COOLDOWN_MS = 150
    SEARCH_ANIM_MS = 500
    SEARCH_VERT_COOLDOWN_MS = 150
    SEARCH_BAR_ANIM_MS = 600
    VIDEO_RETURN_TRANSITION_MS = 400
    RESUME_LIMIT = 3
    WATCH_THRESHOLD_RATIO = 0.25
    RESUME_CLEAR_RATIO = 0.99

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Grid Navigator")
        self.setStyleSheet("background-color: #1a1b26;")

        self._last_vert_ms = self._last_search_vert_ms = 0
        self._mode, self._focus_area, self._search_query = "grid", "grid", ""
        self._return_to = "grid"
        self._is_video_transitioning = False
        self._current_video_animal = None
        self._current_video_session_qualified = False
        self._last_watched_by_animal = {}
        self._watch_qualified_by_animal = {}
        self._resume_positions_ms = {}
        self._resume_order = []
        self._duration_seconds_by_animal = {name: 15 for name in ANIMAL_NAMES}
        self._load_watch_state()

        screen = QApplication.primaryScreen().availableGeometry()
        sw, sh = screen.width(), screen.height()

        cols, spacing, margin = 6, 12, 24
        card_w = int(((sw - margin * 2 - (cols - 1) * spacing) / cols) / 1.35)
        card_h = int(card_w * 3 / 2)

        self._grid = GridWidget(cols, ANIMAL_NAMES, card_w, card_h, spacing, margin,
                                subtitle_provider=self._subtitle_for_animal,
                                resume_provider=self._resume_progress_for_animal)

        self._scroll = QScrollArea(self)
        self._scroll.setWidgetResizable(False)
        self._scroll.setWidget(self._grid)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self._scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._scroll.setStyleSheet("""
            QScrollArea { background: transparent; border: none; }
            QScrollBar:vertical { background: #1a1b26; width: 8px; margin: 0; }
            QScrollBar::handle:vertical { background: #3b3f54; border-radius: 4px; min-height: 30px; }
            QScrollBar::handle:vertical:hover { background: #5a5f7a; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
        """)

        self._search_bar = SearchBarWidget(self)
        self._search_panel = SearchPanel(card_w, card_h, self.SEARCH_ANIM_MS,
                                         subtitle_provider=self._subtitle_for_animal,
                                         resume_provider=self._resume_progress_for_animal,
                                         parent=self)

        self._video_player = VideoPlayer(self)
        self._video_player.back_transition_started.connect(self._on_video_back_transition_started)
        self._video_player.back_pressed.connect(self._on_video_back_transition_finished)
        self._video_player.player.positionChanged.connect(self._on_video_position_changed)
        self._video_player.player.durationChanged.connect(self._on_video_duration_changed)

        # Browse page setup
        self._browse_page = QWidget(self)
        browse_lay = QVBoxLayout(self._browse_page)
        browse_lay.setContentsMargins(0, 0, 0, 0)
        browse_lay.setSpacing(0)

        search_row = QWidget(self._browse_page)
        sr_lay = QHBoxLayout(search_row)
        sr_lay.setContentsMargins(8, 10, 8, 8)
        sr_lay.setSpacing(0)
        sr_lay.addWidget(self._search_bar, 0, Qt.AlignmentFlag.AlignHCenter)

        self._content = QStackedWidget(self._browse_page)
        self._content.addWidget(self._scroll)
        self._content.addWidget(self._search_panel)

        browse_lay.addWidget(search_row)
        browse_lay.addWidget(self._content)

        # Top-level stack
        self._top_stack = QStackedWidget(self)
        self._top_stack.addWidget(self._browse_page)
        self._top_stack.addWidget(self._video_player)
        self._browse_fx = QGraphicsOpacityEffect(self._browse_page)
        self._browse_fx.setOpacity(1.0)
        self._browse_page.setGraphicsEffect(self._browse_fx)

        self._transition_overlay = QWidget(self)
        self._transition_overlay.setStyleSheet("background-color: #000000;")
        self._transition_overlay.hide()
        self._transition_fx = QGraphicsOpacityEffect(self._transition_overlay)
        self._transition_fx.setOpacity(0.0)
        self._transition_overlay.setGraphicsEffect(self._transition_fx)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        lay.addWidget(self._top_stack)

        win_w = min(self._grid.width() + 20, sw)
        win_h = min(sh - 80, self._grid.height() + 86)
        self.resize(win_w, win_h)
        self.move((sw - win_w) // 2, (sh - win_h) // 2)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        # Animations
        self._scroll_anim = QPropertyAnimation(self._scroll.verticalScrollBar(), b"value", self)
        self._scroll_anim.setDuration(self.SCROLL_ANIM_MS)
        self._scroll_anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        self._sb_anim = QParallelAnimationGroup(self)
        self._video_return_slide = QPropertyAnimation(self._browse_page, b"pos", self)
        self._video_return_fade = QPropertyAnimation(self._browse_fx, b"opacity", self)
        self._transition_fade = QPropertyAnimation(self._transition_fx, b"opacity", self)
        self._video_return_group = QParallelAnimationGroup(self)
        self._video_return_group.addAnimation(self._video_return_slide)
        self._video_return_group.addAnimation(self._video_return_fade)
        self._video_return_group.addAnimation(self._transition_fade)
        self._video_enter_slide = QPropertyAnimation(self._browse_page, b"pos", self)
        self._video_enter_fade = QPropertyAnimation(self._browse_fx, b"opacity", self)
        self._video_enter_overlay_fade = QPropertyAnimation(self._transition_fx, b"opacity", self)
        self._video_enter_group = QParallelAnimationGroup(self)
        self._video_enter_group.addAnimation(self._video_enter_slide)
        self._video_enter_group.addAnimation(self._video_enter_fade)
        self._video_enter_group.addAnimation(self._video_enter_overlay_fade)

        self._set_sb_width(self._collapsed_w())
        self._search_bar.set_selected(False)

    def _collapsed_w(self): return max(300, min(460, self.width() - 50))
    def _expanded_w(self):  return max(320, self.width() - 16)

    def _set_sb_width(self, w):
        w = max(100, int(w))
        self._search_bar.setMinimumWidth(w)
        self._search_bar.setMaximumWidth(w)

    def _animate_sb_width(self, target):
        target = max(100, int(target))
        current = self._search_bar.width() or target
        self._sb_anim.stop()
        self._sb_anim = QParallelAnimationGroup(self)
        for prop in (b"minimumWidth", b"maximumWidth"):
            self._sb_anim.addAnimation(
                make_anim(self._search_bar, prop, current, target, self.SEARCH_BAR_ANIM_MS, self))
        self._sb_anim.start()

    def _focus_search_bar(self):
        self._focus_area = "searchbar"
        self._grid.set_selection_visible(False)
        self._search_bar.set_selected(True)

    def _focus_grid(self):
        self._focus_area = "grid"
        self._grid.set_selection_visible(True)
        self._search_bar.set_selected(False)

    def _enter_search(self):
        self._mode = "search"
        self._grid.set_selection_visible(False)
        self._search_bar.set_selected(True)
        self._search_bar.set_expanded(True)
        self._content.setCurrentWidget(self._search_panel)
        self._search_panel.reset_navigation()
        self._animate_sb_width(self._expanded_w())
        self._refresh_results()

    def _exit_search(self):
        self._mode, self._search_query = "grid", ""
        self._search_bar.set_text("")
        self._search_panel.set_results([])
        self._search_panel.reset_navigation()
        self._search_bar.set_expanded(False)
        self._content.setCurrentWidget(self._scroll)
        self._animate_sb_width(self._collapsed_w())
        self._focus_grid()

    def _refresh_results(self):
        q = self._search_query.strip().lower()
        self._search_panel.set_results(
            [x for x in ANIMAL_NAMES if q in x.lower()][:6] if q else [])

    def _apply_token(self, token):
        if token == "EXIT":
            self._exit_search()
            return
        if token == "SPACE":     self._search_query += " "
        elif token == "DEL":     self._search_query = self._search_query[:-1]
        elif token == "CLEAR":   self._search_query = ""
        else:                    self._search_query += token
        self._search_bar.set_text(self._search_query)
        self._refresh_results()

    def _scroll_to_card(self, card):
        bar = self._scroll.verticalScrollBar()
        top_row = ((card._index // self._grid._cols) // 2) * 2
        target = max(bar.minimum(), min(bar.maximum(), top_row * self._grid._row_step))
        if target == bar.value():
            return
        self._scroll_anim.stop()
        self._scroll_anim.setStartValue(bar.value())
        self._scroll_anim.setEndValue(target)
        self._scroll_anim.start()

    def _play_video(self, from_where, animal_name):
        self._return_to = from_where
        self._is_video_transitioning = True
        self._current_video_animal = animal_name
        self._current_video_session_qualified = False
        video_path = MOVS_DIR / f"{animal_name}.mp4"
        if not video_path.exists():
            self._is_video_transitioning = False
            self._current_video_animal = None
            print(f"Missing video for '{animal_name}': {video_path}")
            return

        start_ms = self._register_resume_slot(animal_name)

        if self._watch_qualified_by_animal.get(animal_name, False):
            self._last_watched_by_animal[animal_name] = datetime.now()

        self._save_watch_state()
        self._refresh_card_metadata()

        self._video_player.load_video(str(video_path), start_position_ms=start_ms)
        self._start_video_enter_transition()

    def _start_video_enter_transition(self):
        self._video_enter_group.stop()
        self._top_stack.setCurrentWidget(self._browse_page)
        self._transition_overlay.setGeometry(self.rect())
        self._transition_overlay.show()
        self._transition_overlay.raise_()

        w = self._top_stack.width()
        self._browse_page.move(0, 0)
        self._browse_fx.setOpacity(1.0)
        self._transition_fx.setOpacity(0.0)

        self._video_enter_slide.setDuration(self.VIDEO_RETURN_TRANSITION_MS)
        self._video_enter_slide.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._video_enter_slide.setStartValue(self._browse_page.pos())
        self._video_enter_slide.setEndValue(QPoint(-w, 0))

        self._video_enter_fade.setDuration(self.VIDEO_RETURN_TRANSITION_MS)
        self._video_enter_fade.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._video_enter_fade.setStartValue(1.0)
        self._video_enter_fade.setEndValue(0.0)

        self._video_enter_overlay_fade.setDuration(self.VIDEO_RETURN_TRANSITION_MS)
        self._video_enter_overlay_fade.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._video_enter_overlay_fade.setStartValue(0.0)
        self._video_enter_overlay_fade.setEndValue(1.0)

        self._video_enter_group.start()
        QTimer.singleShot(self.VIDEO_RETURN_TRANSITION_MS, self._finish_video_enter_transition)

    def _finish_video_enter_transition(self):
        self._top_stack.setCurrentWidget(self._video_player)
        self._browse_page.move(0, 0)
        self._browse_fx.setOpacity(1.0)
        self._transition_overlay.hide()
        self._transition_fx.setOpacity(0.0)
        self._is_video_transitioning = False
        self._video_player.setFocus()

    def _prepare_browse_return_state(self):
        if self._return_to == "search":
            self._enter_search()
            self._search_bar.set_text(self._search_query)
            self._refresh_results()
        else:
            self._focus_grid()

    def _on_video_back_transition_started(self):
        self._is_video_transitioning = True

        if self._current_video_animal:
            self._save_resume_for_current_video()
            if self._watch_qualified_by_animal.get(self._current_video_animal, False):
                self._last_watched_by_animal[self._current_video_animal] = datetime.now()
            self._save_watch_state()

        self._top_stack.setCurrentWidget(self._browse_page)
        self._prepare_browse_return_state()
        self._video_return_group.stop()
        w = self._top_stack.width()
        self._browse_page.move(-w, 0)
        self._browse_fx.setOpacity(0.0)
        self._transition_overlay.setGeometry(self.rect())
        self._transition_overlay.show()
        self._transition_overlay.raise_()

        self._video_return_slide.setDuration(self.VIDEO_RETURN_TRANSITION_MS)
        self._video_return_slide.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._video_return_slide.setStartValue(self._browse_page.pos())
        self._video_return_slide.setEndValue(self._top_stack.rect().topLeft())

        self._video_return_fade.setDuration(self.VIDEO_RETURN_TRANSITION_MS)
        self._video_return_fade.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._video_return_fade.setStartValue(0.0)
        self._video_return_fade.setEndValue(1.0)

        self._transition_fade.setDuration(self.VIDEO_RETURN_TRANSITION_MS)
        self._transition_fade.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._transition_fade.setStartValue(1.0)
        self._transition_fade.setEndValue(0.0)

        self._video_return_group.start()

    def _on_video_back_transition_finished(self):
        self._top_stack.setCurrentWidget(self._browse_page)
        self._browse_page.move(0, 0)
        self._browse_fx.setOpacity(1.0)
        self._transition_overlay.hide()
        self._transition_fx.setOpacity(0.0)
        self._is_video_transitioning = False

        if self._current_video_animal:
            self._refresh_card_metadata()
            self._current_video_animal = None
            self._current_video_session_qualified = False

        self.setFocus()

    def _load_watch_state(self):
        if not WATCH_STATE_PATH.exists():
            return

        try:
            data = json.loads(WATCH_STATE_PATH.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError, ValueError):
            return

        last_watched_raw = data.get("last_watched_iso", {})
        for animal, ts in last_watched_raw.items():
            if animal in ANIMAL_NAMES and isinstance(ts, str):
                try:
                    self._last_watched_by_animal[animal] = datetime.fromisoformat(ts)
                except ValueError:
                    continue

        qualified_raw = data.get("watch_qualified", {})
        for animal, qualified in qualified_raw.items():
            if animal in ANIMAL_NAMES:
                self._watch_qualified_by_animal[animal] = bool(qualified)

        resume_raw = data.get("resume_positions_ms", {})
        for animal, position in resume_raw.items():
            if animal in ANIMAL_NAMES:
                try:
                    self._resume_positions_ms[animal] = max(0, int(position))
                except (TypeError, ValueError):
                    continue

        order_raw = data.get("resume_order", [])
        if isinstance(order_raw, list):
            self._resume_order = [
                animal for animal in order_raw
                if animal in self._resume_positions_ms
            ][-self.RESUME_LIMIT:]

    def _save_watch_state(self):
        payload = {
            "last_watched_iso": {
                animal: when.isoformat()
                for animal, when in self._last_watched_by_animal.items()
            },
            "watch_qualified": self._watch_qualified_by_animal,
            "resume_positions_ms": self._resume_positions_ms,
            "resume_order": self._resume_order,
        }
        try:
            WATCH_STATE_PATH.write_text(
                json.dumps(payload, indent=2, sort_keys=True),
                encoding="utf-8",
            )
        except OSError:
            pass

    def _register_resume_slot(self, animal_name):
        if animal_name in self._resume_order:
            self._resume_order.remove(animal_name)
        self._resume_order.append(animal_name)

        while len(self._resume_order) > self.RESUME_LIMIT:
            dropped = self._resume_order.pop(0)
            self._resume_positions_ms.pop(dropped, None)

        return self._resume_positions_ms.get(animal_name, 0)

    def _clear_resume_for(self, animal_name):
        self._resume_positions_ms.pop(animal_name, None)
        if animal_name in self._resume_order:
            self._resume_order.remove(animal_name)

    def _is_near_end(self, position_ms, duration_ms):
        if duration_ms <= 0:
            return False
        return position_ms >= int(duration_ms * self.RESUME_CLEAR_RATIO)

    def _save_resume_for_current_video(self):
        if not self._current_video_animal:
            return

        position_ms = max(0, int(self._video_player.player.position()))
        duration_ms = max(0, int(self._video_player.player.duration()))

        if self._is_near_end(position_ms, duration_ms):
            self._clear_resume_for(self._current_video_animal)
            return

        self._resume_positions_ms[self._current_video_animal] = position_ms

    def _on_video_duration_changed(self, duration_ms):
        if self._current_video_animal and duration_ms > 0:
            self._duration_seconds_by_animal[self._current_video_animal] = int(duration_ms / 1000)
            self._refresh_card_metadata()

    def _on_video_position_changed(self, position_ms):
        if not self._current_video_animal:
            return

        duration_ms = self._video_player.player.duration()
        if duration_ms <= 0:
            return

        if self._is_near_end(position_ms, duration_ms):
            had_resume = (
                self._current_video_animal in self._resume_positions_ms
                or self._current_video_animal in self._resume_order
            )
            self._clear_resume_for(self._current_video_animal)
            if had_resume:
                self._save_watch_state()

        if (not self._current_video_session_qualified
                and position_ms >= int(duration_ms * self.WATCH_THRESHOLD_RATIO)):
            self._current_video_session_qualified = True
            self._watch_qualified_by_animal[self._current_video_animal] = True
            self._last_watched_by_animal[self._current_video_animal] = datetime.now()
            self._save_watch_state()
            self._refresh_card_metadata()

    def _resume_progress_for_animal(self, animal_name):
        position_ms = self._resume_positions_ms.get(animal_name)
        if position_ms is None:
            return None

        duration_ms = max(1, int(self._duration_seconds_by_animal.get(animal_name, 15) * 1000))
        progress = position_ms / duration_ms
        if progress >= self.RESUME_CLEAR_RATIO:
            return None
        return max(0.0, min(progress, 1.0))

    def _refresh_card_metadata(self):
        self._grid.refresh_subtitles()
        self._search_panel.refresh_subtitles()

    def _format_duration(self, total_seconds):
        total_seconds = max(0, float(total_seconds))
        total_minutes = max(1, int(math.ceil(total_seconds / 60.0)))
        hours = total_minutes // 60
        minutes = total_minutes % 60

        if hours > 0 and minutes > 0:
            return f"{hours}h {minutes}min"
        if hours > 0:
            return f"{hours}h"
        return f"{total_minutes}min"

    def _format_last_watched(self, when):
        if when is None:
            return "Last watched never"

        delta = datetime.now() - when
        days = delta.days
        if days >= 1:
            unit = "day" if days == 1 else "days"
            return f"Last watched {days} {unit} ago"

        hours = delta.seconds // 3600
        if hours >= 1:
            unit = "hour" if hours == 1 else "hours"
            return f"Last watched {hours} {unit} ago"

        minutes = max(1, delta.seconds // 60)
        unit = "minute" if minutes == 1 else "minutes"
        return f"Last watched {minutes} {unit} ago"

    def _subtitle_for_animal(self, animal_name):
        duration_seconds = self._duration_seconds_by_animal.get(animal_name, 15)
        resume_ms = self._resume_positions_ms.get(animal_name)

        if resume_ms is not None:
            remaining_seconds = max(0.0, float(duration_seconds) - (float(resume_ms) / 1000.0))
            return f"{self._format_duration(remaining_seconds)} left"

        watched = self._format_last_watched(self._last_watched_by_animal.get(animal_name))
        return f"{self._format_duration(duration_seconds)} • {watched}"

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._set_sb_width(self._expanded_w() if self._mode == "search" else self._collapsed_w())
        self._transition_overlay.setGeometry(self.rect())

    def keyPressEvent(self, event):
        if self._is_video_transitioning:
            event.accept()
            return

        key = event.key()
        d = KEY_MAP.get(key)

        if self._top_stack.currentWidget() == self._video_player:
            self._video_player.keyPressEvent(event)
            return

        if self._mode == "search":
            if key == Qt.Key.Key_Escape:
                self._exit_search()
                return
            if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                action, val = self._search_panel.press_enter()
                if action == "key":
                    self._apply_token(val)
                elif action == "result" and val:
                    self._play_video("search", val)
                return
            if d:
                if d in ("up", "down") and self._search_panel.focus_zone() == "results":
                    now = int(time.monotonic() * 1000)
                    if now - self._last_search_vert_ms < self.SEARCH_VERT_COOLDOWN_MS:
                        return
                    self._last_search_vert_ms = now
                self._search_panel.move(d)
            return

        if self._focus_area == "searchbar":
            if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                self._enter_search()
            elif key == Qt.Key.Key_Down:
                self._focus_grid()
            elif key == Qt.Key.Key_Escape:
                self.close()
            return

        if key == Qt.Key.Key_Escape:
            self.close()
            return

        if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self._play_video("grid", self._grid.current_label())
            return

        if d:
            if d == "up" and self._grid._current < self._grid._cols:
                self._focus_search_bar()
                return
            if d in ("up", "down"):
                now = int(time.monotonic() * 1000)
                if now - self._last_vert_ms < self.VERT_COOLDOWN_MS:
                    return
                self._last_vert_ms = now
            self._scroll_to_card(self._grid.move_selection(d))


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setFont(QFont("Helvetica Neue", 10))
    window = MainWindow()
    window.show()
    window.setFocus()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()