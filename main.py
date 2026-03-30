import sys
import time
from PyQt6.QtWidgets import (QApplication, QWidget, QScrollArea, QVBoxLayout,
                                        QFrame, QHBoxLayout, QGridLayout, QLabel,
                                        QStackedWidget, QSizePolicy)
from PyQt6.QtCore import (Qt, QRectF, QPropertyAnimation, QEasingCurve,
                           QParallelAnimationGroup,
                                    pyqtProperty, pyqtSignal)
from PyQt6.QtGui import (QPainter, QColor, QFont, QPen,
                          QBrush, QLinearGradient)


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


class RectCard(QWidget):
    def __init__(self, index, label, base_width, base_height, parent=None):
        super().__init__(parent)
        self._index = index
        self._label = label
        self._base_width = base_width
        self._base_height = base_height
        self._scale = 1.0
        self._selected = False
        self._glow_opacity = 0.0

        self.setFixedSize(int(base_width * 1.35), int(base_height * 1.35))
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

    def get_scale(self):
        return self._scale

    def set_scale(self, value):
        self._scale = value
        self.update()

    scale = pyqtProperty(float, get_scale, set_scale)

    def get_glow_opacity(self):
        return self._glow_opacity

    def set_glow_opacity(self, value):
        self._glow_opacity = value
        self.update()

    glow_opacity = pyqtProperty(float, get_glow_opacity, set_glow_opacity)

    def set_label(self, label):
        self._label = label
        self.update()

    def set_search_selected(self, selected):
        self._selected = selected
        self._scale = 1.08 if selected else 1.0
        self._glow_opacity = 1.0 if selected else 0.0
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)

        w = self._base_width * self._scale
        h = self._base_height * self._scale

        cx = self.width() / 2.0
        cy = self.height() / 2.0

        rect = QRectF(cx - w / 2, cy - h / 2, w, h)

        # Shadow
        if self._scale > 1.0:
            shadow_offset = 4 * (self._scale - 1.0) / 0.3
            shadow_rect = rect.adjusted(shadow_offset, shadow_offset,
                                         shadow_offset, shadow_offset)
            shadow_color = QColor(0, 0, 0, int(40 * min(self._glow_opacity * 2, 1.0)))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(shadow_color))
            painter.drawRoundedRect(shadow_rect, 10, 10)

        # Card gradient
        gradient = QLinearGradient(rect.topLeft(), rect.bottomRight())
        gradient.setColorAt(0, QColor(58, 63, 78))
        gradient.setColorAt(1, QColor(42, 46, 58))

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(gradient))
        painter.drawRoundedRect(rect, 8, 8)

        # Card title
        font_size = max(12, int(16 * self._scale))
        font = QFont("Helvetica Neue", font_size, QFont.Weight.Medium)
        painter.setFont(font)

        text_color = QColor(255, 255, 255, int(180 + 75 * min(self._glow_opacity, 1.0)))
        painter.setPen(text_color)
        text_rect = rect.adjusted(10, 8, -10, -8)
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap,
                 self._label)

        painter.end()


class GridWidget(QWidget):
    def __init__(self, cols, labels, card_w, card_h, spacing, margin, parent=None):
        super().__init__(parent)
        # ===================== CARD GROW ANIMATION SPEED =====================
        # Tweak this number to control how quickly selection grows/shrinks.
        # Lower = faster, Higher = slower (milliseconds)
        self.CARD_GROW_ANIMATION_MS = 500
        # =====================================================================
        self._cols = cols
        self._labels = labels
        self._total = len(labels)
        self._card_w = card_w
        self._card_h = card_h
        self._spacing = spacing
        self._row_spacing = spacing // 2
        self._margin = margin
        self._current = 0
        self._selection_visible = True

        self._rows = (self._total + cols - 1) // cols
        self._cards = []
        self._animations = QParallelAnimationGroup(self)

        cell_w = int(card_w * 1.35)
        cell_h = int(card_h * 1.35)
        self._row_step = cell_h + self._row_spacing

        total_width = margin * 2 + cols * cell_w + (cols - 1) * spacing
        total_height = margin * 2 + self._rows * cell_h + (self._rows - 1) * self._row_spacing

        self.setFixedSize(total_width, total_height)

        for i, label in enumerate(labels):
            card = RectCard(i, label, card_w, card_h, self)
            row = i // cols
            col = i % cols
            x = margin + col * (cell_w + spacing)
            y = margin + row * self._row_step
            card.move(x, y)
            self._cards.append(card)

        self._select(0, animate=False)

    def _select(self, index, animate=True):
        if index < 0 or index >= self._total:
            return

        self._animations.stop()
        self._animations = QParallelAnimationGroup(self)

        old = self._current
        self._current = index

        duration = self.CARD_GROW_ANIMATION_MS if animate else 0

        if old != index and old < len(self._cards):
            old_card = self._cards[old]
            old_card._selected = False

            anim_s = QPropertyAnimation(old_card, b"scale")
            anim_s.setDuration(duration)
            anim_s.setStartValue(old_card._scale)
            anim_s.setEndValue(1.0)
            anim_s.setEasingCurve(QEasingCurve.Type.OutCubic)
            self._animations.addAnimation(anim_s)


        new_card = self._cards[index]
        new_card._selected = True

        target_scale = 1.3 if self._selection_visible else 1.0

        anim_s = QPropertyAnimation(new_card, b"scale")
        anim_s.setDuration(duration)
        anim_s.setStartValue(new_card._scale)
        anim_s.setEndValue(target_scale)
        anim_s.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._animations.addAnimation(anim_s)


        if animate:
            self._animations.start()
        else:
            new_card._scale = target_scale
            new_card.update()

    def set_selection_visible(self, visible, animate=True):
        if self._selection_visible == visible:
            return

        self._selection_visible = visible

        if self._current < 0 or self._current >= len(self._cards):
            return

        card = self._cards[self._current]
        target_scale = 1.3 if visible else 1.0
        duration = self.CARD_GROW_ANIMATION_MS if animate else 0

        self._animations.stop()
        self._animations = QParallelAnimationGroup(self)

        anim_s = QPropertyAnimation(card, b"scale")
        anim_s.setDuration(duration)
        anim_s.setStartValue(card._scale)
        anim_s.setEndValue(target_scale)
        anim_s.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._animations.addAnimation(anim_s)

        if animate:
            self._animations.start()
        else:
            card._scale = target_scale
            card.update()

    def move_selection(self, direction):
        row = self._current // self._cols
        col = self._current % self._cols

        if direction == "left":
            col = max(0, col - 1)
        elif direction == "right":
            col = min(self._cols - 1, col + 1)
        elif direction == "up":
            row = max(0, row - 1)
        elif direction == "down":
            row = min(self._rows - 1, row + 1)

        new_index = row * self._cols + col
        if new_index < self._total and new_index != self._current:
            self._select(new_index)

        return self._cards[self._current]


class SearchBarWidget(QWidget):
    clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._text = ""
        self._selected = False
        self._expanded = False
        self.setFixedHeight(52)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def set_text(self, text):
        self._text = text
        self.update()

    def set_selected(self, selected):
        self._selected = selected
        self.update()

    def set_expanded(self, expanded):
        self._expanded = expanded
        self.update()

    def mousePressEvent(self, event):
        self.clicked.emit()
        super().mousePressEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)

        rect = self.rect().adjusted(1, 1, -1, -1)

        gradient = QLinearGradient(float(rect.left()), float(rect.top()),
                       float(rect.left()), float(rect.bottom()))
        if self._expanded:
            gradient.setColorAt(0, QColor(46, 52, 70))
            gradient.setColorAt(1, QColor(37, 41, 56))
        else:
            gradient.setColorAt(0, QColor(41, 45, 60))
            gradient.setColorAt(1, QColor(34, 37, 49))

        border_color = QColor(122, 188, 255) if self._selected else QColor(72, 78, 98)

        painter.setPen(QPen(border_color, 2))
        painter.setBrush(QBrush(gradient))
        painter.drawRoundedRect(rect, 12, 12)

        icon_x = rect.left() + 18
        icon_y = rect.center().y()
        painter.setPen(QPen(QColor(205, 210, 226), 2))
        painter.drawEllipse(icon_x - 6, icon_y - 6, 12, 12)
        painter.drawLine(icon_x + 5, icon_y + 5, icon_x + 10, icon_y + 10)

        text = self._text if self._text else "Search"
        text_color = QColor(236, 239, 248) if self._text else QColor(165, 171, 192)
        painter.setPen(text_color)
        painter.setFont(QFont("Helvetica Neue", 13, QFont.Weight.Medium))
        painter.drawText(rect.adjusted(40, 0, -12, 0), Qt.AlignmentFlag.AlignVCenter, text)

        painter.end()


class SelectableTile(QFrame):
    def __init__(self, text="", min_height=58, card_like=False, parent=None):
        super().__init__(parent)
        self._selected = False
        self._card_like = card_like

        self.setMinimumHeight(min_height)
        if self._card_like:
            self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setFrameShape(QFrame.Shape.NoFrame)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(0)

        self._label = QLabel(text, self)
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._label.setWordWrap(True)
        self._label.setStyleSheet("color: #e9edf7; font-size: 14px; font-family: 'Helvetica Neue';")
        layout.addWidget(self._label)

        self._apply_style()

    def set_text(self, text):
        self._label.setText(text)

    def set_selected(self, selected):
        self._selected = selected
        self._apply_style()

    def _apply_style(self):
        border = "2px solid #73c0ff" if self._selected else "1px solid #4a5168"
        if self._card_like:
            background = "#3a4968" if self._selected else "#31394f"
            radius = "8px"
        else:
            background = "#3f4f72" if self._selected else "#2e3448"
            radius = "10px"
        self.setStyleSheet(
            f"QFrame {{"
            f"background: {background};"
            f"border: {border};"
            f"border-radius: {radius};"
            f"}}"
        )


class SearchPanel(QWidget):
    def __init__(self, card_w, card_h, selection_animation_ms=500, parent=None):
        super().__init__(parent)

        self._keyboard_rows = [
            ["A", "B", "C", "D", "E", "F"],
            ["G", "H", "I", "J", "K", "L"],
            ["M", "N", "O", "P", "Q", "R"],
            ["S", "T", "U", "V", "W", "X"],
            ["Y", "Z", "SPACE", "DEL", "CLEAR", "EXIT"],
        ]

        self._keyboard_tiles = []
        self._result_tiles = []
        self._results = []
        self._focus_zone = "keyboard"
        self._key_row = 0
        self._key_col = 0
        self._result_index = 0
        self._active_result_index = None
        self._selection_animation_ms = selection_animation_ms
        self._result_animations = QParallelAnimationGroup(self)

        root = QHBoxLayout(self)
        root.setContentsMargins(24, 14, 24, 20)
        root.setSpacing(20)

        left = QWidget(self)
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(10)

        keyboard_title = QLabel("Keyboard", left)
        keyboard_title.setStyleSheet(
            "color: #cdd3e5; font-size: 14px; font-family: 'Helvetica Neue'; letter-spacing: 0.5px;"
        )
        left_layout.addWidget(keyboard_title)

        keyboard_grid = QGridLayout()
        keyboard_grid.setSpacing(10)
        for r, row in enumerate(self._keyboard_rows):
            tile_row = []
            for c, token in enumerate(row):
                tile = SelectableTile(self._token_label(token), min_height=56, parent=left)
                keyboard_grid.addWidget(tile, r, c)
                tile_row.append(tile)
            self._keyboard_tiles.append(tile_row)

        left_layout.addLayout(keyboard_grid)
        left_layout.addStretch(1)

        right = QWidget(self)
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(10)

        self._results_title = QLabel("Results", right)
        self._results_title.setStyleSheet(
            "color: #cdd3e5; font-size: 14px; font-family: 'Helvetica Neue'; letter-spacing: 0.5px;"
        )
        right_layout.addWidget(self._results_title)

        results_grid = QGridLayout()
        results_grid.setSpacing(12)
        for col in range(3):
            results_grid.setColumnStretch(col, 1)
        for i in range(6):
            tile = RectCard(i, "", card_w, card_h, right)
            tile.hide()
            self._result_tiles.append(tile)
            results_grid.addWidget(tile, i // 3, i % 3)

        right_layout.addLayout(results_grid)
        right_layout.addStretch(1)

        root.addWidget(left, 1)
        root.addWidget(right, 1)

        self._refresh_selection()
        self._refresh_results_visibility()

    def _token_label(self, token):
        if token == "SPACE":
            return "Space"
        if token == "DEL":
            return "Delete"
        if token == "CLEAR":
            return "Clear"
        if token == "EXIT":
            return "Exit"
        return token

    def reset_navigation(self):
        self._focus_zone = "keyboard"
        self._key_row = 0
        self._key_col = 0
        self._result_index = 0
        self._refresh_selection()

    def focus_zone(self):
        return self._focus_zone

    def set_results(self, results):
        self._results = results[:6]

        for i, tile in enumerate(self._result_tiles):
            if i < len(self._results):
                tile.set_label(self._results[i])
                tile.show()
            else:
                tile.hide()

        if not self._results and self._focus_zone == "results":
            self._focus_zone = "keyboard"
        if self._result_index >= len(self._results):
            self._result_index = max(0, len(self._results) - 1)

        self._refresh_results_visibility()
        self._refresh_selection()

    def _refresh_results_visibility(self):
        self._results_title.setVisible(bool(self._results))

    def move(self, direction):
        if self._focus_zone == "keyboard":
            self._move_keyboard(direction)
        else:
            self._move_results(direction)
        self._refresh_selection()

    def _move_keyboard(self, direction):
        if direction == "left":
            self._key_col = max(0, self._key_col - 1)
            return

        if direction == "right":
            row_len = len(self._keyboard_rows[self._key_row])
            if self._key_col < row_len - 1:
                self._key_col += 1
            elif self._results:
                self._focus_zone = "results"
                self._result_index = 0
            return

        if direction == "up":
            self._key_row = max(0, self._key_row - 1)
        elif direction == "down":
            self._key_row = min(len(self._keyboard_rows) - 1, self._key_row + 1)

        self._key_col = min(self._key_col, len(self._keyboard_rows[self._key_row]) - 1)

    def _move_results(self, direction):
        if not self._results:
            self._focus_zone = "keyboard"
            return

        row = self._result_index // 3
        col = self._result_index % 3

        if direction == "left":
            if col > 0:
                self._result_index -= 1
            else:
                self._focus_zone = "keyboard"
                self._key_row = min(row, len(self._keyboard_rows) - 1)
                self._key_col = len(self._keyboard_rows[self._key_row]) - 1
            return

        if direction == "right":
            candidate = self._result_index + 1
            if col < 2 and candidate < len(self._results):
                self._result_index = candidate
            return

        if direction == "up":
            candidate = self._result_index - 3
            if candidate >= 0:
                self._result_index = candidate
            return

        if direction == "down":
            candidate = self._result_index + 3
            if candidate < len(self._results):
                self._result_index = candidate

    def press_enter(self):
        if self._focus_zone == "keyboard":
            token = self._keyboard_rows[self._key_row][self._key_col]
            return "key", token

        if self._focus_zone == "results" and self._results:
            return "result", self._results[self._result_index]

        return None, None

    def _refresh_selection(self):
        for r, row in enumerate(self._keyboard_tiles):
            for c, tile in enumerate(row):
                tile.set_selected(self._focus_zone == "keyboard" and r == self._key_row and c == self._key_col)

        next_index = None
        if self._focus_zone == "results" and self._result_index < len(self._results):
            next_index = self._result_index

        if self._active_result_index != next_index:
            self._animate_result_focus_change(self._active_result_index, next_index)
            self._active_result_index = next_index

    def _animate_result_focus_change(self, old_index, new_index):
        self._result_animations.stop()
        self._result_animations = QParallelAnimationGroup(self)

        duration = self._selection_animation_ms

        if old_index is not None and 0 <= old_index < len(self._result_tiles):
            self._add_result_animation(self._result_tiles[old_index], 1.0, 0.0, duration)

        if new_index is not None and 0 <= new_index < len(self._result_tiles):
            self._add_result_animation(self._result_tiles[new_index], 1.3, 1.0, duration)

        if self._result_animations.animationCount() > 0:
            self._result_animations.start()

    def _add_result_animation(self, card, target_scale, target_glow, duration):
        anim_s = QPropertyAnimation(card, b"scale", self)
        anim_s.setDuration(duration)
        anim_s.setStartValue(card._scale)
        anim_s.setEndValue(target_scale)
        anim_s.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._result_animations.addAnimation(anim_s)

        anim_g = QPropertyAnimation(card, b"glow_opacity", self)
        anim_g.setDuration(duration)
        anim_g.setStartValue(card._glow_opacity)
        anim_g.setEndValue(target_glow)
        anim_g.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._result_animations.addAnimation(anim_g)

        for i, tile in enumerate(self._result_tiles):
            if i >= len(self._results):
                tile._scale = 1.0
                tile._glow_opacity = 0.0
                tile.update()


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Grid Navigator")
        self.setStyleSheet("background-color: #1a1b26;")

        # ==================== SCROLL ANIMATION SPEED ====================
        # Tweak this number to control keyboard navigation scroll speed.
        # Lower = faster, Higher = slower (milliseconds)
        self.SCROLL_ANIMATION_MS = 1550
        # ================================================================

        # =================== VERTICAL INPUT COOLDOWN ====================
        # Tweak this number to limit how quickly UP/DOWN can repeat.
        # Lower = more responsive, Higher = more delay (milliseconds)
        self.VERTICAL_INPUT_COOLDOWN_MS = 150
        # ================================================================
        # =============== SEARCH RESULTS ANIMATION/CADENCE ===============
        self.SEARCH_RESULTS_ANIMATION_MS = 500
        self.SEARCH_RESULTS_VERTICAL_INPUT_COOLDOWN_MS = 150
        # ================================================================
        self._last_vertical_input_ms = 0
        self._last_search_results_vertical_input_ms = 0
        self._mode = "grid"
        self._focus_area = "grid"
        self._search_query = ""

        screen = QApplication.primaryScreen().availableGeometry()
        screen_w = screen.width()
        screen_h = screen.height()

        cols = 6
        self._animal_names = ANIMAL_NAMES
        total_items = len(self._animal_names)
        spacing = 12
        margin = 24

        # Calculate card size so grid fits within screen width
        # total_width = margin*2 + cols*cell_w + (cols-1)*spacing
        # cell_w = card_w * 1.35
        # So: card_w * 1.35 = (screen_w - margin*2 - (cols-1)*spacing) / cols
        max_cell_w = (screen_w - margin * 2 - (cols - 1) * spacing) / cols
        card_w = int(max_cell_w / 1.35)
        card_h = int(card_w * 3 / 2)  # 2:3 aspect ratio

        self._grid = GridWidget(cols, self._animal_names, card_w, card_h, spacing, margin)

        self._scroll = QScrollArea(self)
        self._scroll.setWidgetResizable(False)
        self._scroll.setWidget(self._grid)
        self._scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scroll.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self._scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._scroll.setStyleSheet("""
            QScrollArea { background: transparent; border: none; }
            QScrollBar:vertical {
                background: #1a1b26;
                width: 8px;
                margin: 0;
            }
            QScrollBar::handle:vertical {
                background: #3b3f54;
                border-radius: 4px;
                min-height: 30px;
            }
            QScrollBar::handle:vertical:hover {
                background: #5a5f7a;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0;
            }
        """)

        self._search_bar = SearchBarWidget(self)
        self._search_bar.clicked.connect(self._handle_search_bar_click)

        self._search_panel = SearchPanel(
            card_w,
            card_h,
            selection_animation_ms=self.SEARCH_RESULTS_ANIMATION_MS,
            parent=self,
        )
        self._search_items = self._animal_names

        self._content = QStackedWidget(self)
        self._content.addWidget(self._scroll)
        self._content.addWidget(self._search_panel)

        search_row = QWidget(self)
        search_row_layout = QHBoxLayout(search_row)
        search_row_layout.setContentsMargins(8, 10, 8, 8)
        search_row_layout.setSpacing(0)
        search_row_layout.addWidget(self._search_bar, 0, Qt.AlignmentFlag.AlignHCenter)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(search_row)
        layout.addWidget(self._content)

        win_w = min(self._grid.width() + 20, screen_w)
        win_h = min(screen_h - 80, self._grid.height() + 86)
        self.resize(win_w, win_h)

        # Center window
        self.move((screen_w - win_w) // 2, (screen_h - win_h) // 2)

        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        self._scroll_anim = QPropertyAnimation(self._scroll.verticalScrollBar(), b"value", self)
        self._scroll_anim.setDuration(self.SCROLL_ANIMATION_MS)
        self._scroll_anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        self._search_bar_anim = QParallelAnimationGroup(self)
        self._apply_search_bar_width(self._collapsed_search_width())
        self._search_bar.set_selected(False)

    def _collapsed_search_width(self):
        return max(300, min(460, self.width() - 50))

    def _expanded_search_width(self):
        return max(320, self.width() - 16)

    def _apply_search_bar_width(self, width):
        width = max(100, int(width))
        self._search_bar.setMinimumWidth(width)
        self._search_bar.setMaximumWidth(width)

    def _animate_search_bar_width(self, target):
        target = max(100, int(target))
        current = self._search_bar.width() if self._search_bar.width() > 0 else target

        self._search_bar_anim.stop()
        self._search_bar_anim = QParallelAnimationGroup(self)

        for prop in (b"minimumWidth", b"maximumWidth"):
            anim = QPropertyAnimation(self._search_bar, prop, self)
            anim.setDuration(220)
            anim.setStartValue(current)
            anim.setEndValue(target)
            anim.setEasingCurve(QEasingCurve.Type.OutCubic)
            self._search_bar_anim.addAnimation(anim)

        self._search_bar_anim.start()

    def _focus_search_bar(self):
        self._focus_area = "searchbar"
        self._grid.set_selection_visible(False)
        self._search_bar.set_selected(True)

    def _focus_grid(self):
        self._focus_area = "grid"
        self._grid.set_selection_visible(True)
        self._search_bar.set_selected(False)

    def _handle_search_bar_click(self):
        if self._mode != "search":
            self._enter_search_mode()

    def _enter_search_mode(self):
        self._mode = "search"
        self._grid.set_selection_visible(False)
        self._search_bar.set_selected(True)
        self._search_bar.set_expanded(True)
        self._content.setCurrentWidget(self._search_panel)
        self._search_panel.reset_navigation()
        self._animate_search_bar_width(self._expanded_search_width())
        self._refresh_search_results()

    def _exit_search_mode(self):
        self._mode = "grid"
        self._search_query = ""
        self._search_bar.set_text("")
        self._search_panel.set_results([])
        self._search_panel.reset_navigation()
        self._search_bar.set_expanded(False)
        self._content.setCurrentWidget(self._scroll)
        self._animate_search_bar_width(self._collapsed_search_width())
        self._focus_grid()

    def _refresh_search_results(self):
        query = self._search_query.strip()
        if not query:
            self._search_panel.set_results([])
            return

        lowered = query.lower()
        matches = [item for item in self._search_items if lowered in item.lower()]
        self._search_panel.set_results(matches[:6])

    def _apply_key_token(self, token):
        if token == "EXIT":
            self._exit_search_mode()
            return

        if token == "SPACE":
            self._search_query += " "
        elif token == "DEL":
            self._search_query = self._search_query[:-1]
        elif token == "CLEAR":
            self._search_query = ""
        else:
            self._search_query += token

        self._search_bar.set_text(self._search_query)
        self._refresh_search_results()

    def _animate_scroll_to_card(self, card):
        bar = self._scroll.verticalScrollBar()
        row = card._index // self._grid._cols
        top_row = (row // 2) * 2
        target = top_row * self._grid._row_step
        target = max(bar.minimum(), min(bar.maximum(), target))

        if target == bar.value():
            return

        self._scroll_anim.stop()
        self._scroll_anim.setStartValue(bar.value())
        self._scroll_anim.setEndValue(target)
        self._scroll_anim.start()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self._mode == "search":
            self._apply_search_bar_width(self._expanded_search_width())
        else:
            self._apply_search_bar_width(self._collapsed_search_width())

    def keyPressEvent(self, event):
        key = event.key()
        direction = None

        if self._mode == "search":
            if key == Qt.Key.Key_Escape:
                self._exit_search_mode()
                return

            if key == Qt.Key.Key_Left:
                direction = "left"
            elif key == Qt.Key.Key_Right:
                direction = "right"
            elif key == Qt.Key.Key_Up:
                direction = "up"
            elif key == Qt.Key.Key_Down:
                direction = "down"
            elif key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                action, value = self._search_panel.press_enter()
                if action == "key":
                    self._apply_key_token(value)
                elif action == "result" and value:
                    self._search_query = value
                    self._search_bar.set_text(value)
                    self._refresh_search_results()
                return

            if direction:
                if direction in ("up", "down") and self._search_panel.focus_zone() == "results":
                    now_ms = int(time.monotonic() * 1000)
                    if (now_ms - self._last_search_results_vertical_input_ms
                            < self.SEARCH_RESULTS_VERTICAL_INPUT_COOLDOWN_MS):
                        return
                    self._last_search_results_vertical_input_ms = now_ms
                self._search_panel.move(direction)
                return

            super().keyPressEvent(event)
            return

        if self._focus_area == "searchbar":
            if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                self._enter_search_mode()
                return
            if key == Qt.Key.Key_Down:
                self._focus_grid()
                return
            if key == Qt.Key.Key_Escape:
                self.close()
                return
            super().keyPressEvent(event)
            return

        if key == Qt.Key.Key_Left:
            direction = "left"
        elif key == Qt.Key.Key_Right:
            direction = "right"
        elif key == Qt.Key.Key_Up:
            direction = "up"
        elif key == Qt.Key.Key_Down:
            direction = "down"
        elif key == Qt.Key.Key_Escape:
            self.close()
            return

        if direction:
            if direction == "up" and self._grid._current < self._grid._cols:
                self._focus_search_bar()
                return

            if direction in ("up", "down"):
                now_ms = int(time.monotonic() * 1000)
                if now_ms - self._last_vertical_input_ms < self.VERTICAL_INPUT_COOLDOWN_MS:
                    return
                self._last_vertical_input_ms = now_ms
            card = self._grid.move_selection(direction)
            self._animate_scroll_to_card(card)
        else:
            super().keyPressEvent(event)


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    font = QFont("Helvetica Neue", 10)
    app.setFont(font)

    window = MainWindow()
    window.show()
    window.setFocus()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()