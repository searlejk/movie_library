import sys
from PyQt6.QtWidgets import (QApplication, QWidget, QScrollArea, QVBoxLayout,
                              QFrame)
from PyQt6.QtCore import (Qt, QRectF, QPropertyAnimation, QEasingCurve,
                           QParallelAnimationGroup, pyqtProperty, QPointF)
from PyQt6.QtGui import (QPainter, QColor, QFont, QFontMetrics, QPen,
                          QBrush, QLinearGradient)


class RectCard(QWidget):
    def __init__(self, index, base_width, base_height, parent=None):
        super().__init__(parent)
        self._index = index
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

        # Number text
        font_size = max(12, int(16 * self._scale))
        font = QFont("Segoe UI", font_size, QFont.Weight.Medium)
        painter.setFont(font)

        text_color = QColor(255, 255, 255, int(180 + 75 * min(self._glow_opacity, 1.0)))
        painter.setPen(text_color)
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, str(self._index + 1))

        painter.end()


class GridWidget(QWidget):
    def __init__(self, cols, total_items, card_w, card_h, spacing, margin, parent=None):
        super().__init__(parent)
        # ===================== CARD GROW ANIMATION SPEED =====================
        # Tweak this number to control how quickly selection grows/shrinks.
        # Lower = faster, Higher = slower (milliseconds)
        self.CARD_GROW_ANIMATION_MS = 500
        # =====================================================================
        self._cols = cols
        self._total = total_items
        self._card_w = card_w
        self._card_h = card_h
        self._spacing = spacing
        self._margin = margin
        self._current = 0

        self._rows = (total_items + cols - 1) // cols
        self._cards = []
        self._animations = QParallelAnimationGroup(self)

        cell_w = int(card_w * 1.35)
        cell_h = int(card_h * 1.35)

        total_width = margin * 2 + cols * cell_w + (cols - 1) * spacing
        total_height = margin * 2 + self._rows * cell_h + (self._rows - 1) * spacing

        self.setFixedSize(total_width, total_height)

        for i in range(total_items):
            card = RectCard(i, card_w, card_h, self)
            row = i // cols
            col = i % cols
            x = margin + col * (cell_w + spacing)
            y = margin + row * (cell_h + spacing)
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

        anim_s = QPropertyAnimation(new_card, b"scale")
        anim_s.setDuration(duration)
        anim_s.setStartValue(new_card._scale)
        anim_s.setEndValue(1.3)
        anim_s.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._animations.addAnimation(anim_s)


        if animate:
            self._animations.start()
        else:
            new_card._scale = 1.3
            new_card.update()

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


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Grid Navigator")
        self.setStyleSheet("background-color: #1a1b26;")

        # ==================== SCROLL ANIMATION SPEED ====================
        # Tweak this number to control keyboard navigation scroll speed.
        # Lower = faster, Higher = slower (milliseconds)
        self.SCROLL_ANIMATION_MS = 1200
        # ================================================================

        screen = QApplication.primaryScreen().availableGeometry()
        screen_w = screen.width()
        screen_h = screen.height()

        cols = 6
        total_items = 60
        spacing = 12
        margin = 24

        # Calculate card size so grid fits within screen width
        # total_width = margin*2 + cols*cell_w + (cols-1)*spacing
        # cell_w = card_w * 1.35
        # So: card_w * 1.35 = (screen_w - margin*2 - (cols-1)*spacing) / cols
        max_cell_w = (screen_w - margin * 2 - (cols - 1) * spacing) / cols
        card_w = int(max_cell_w / 1.35)
        card_h = int(card_w * 3 / 2)  # 2:3 aspect ratio

        self._grid = GridWidget(cols, total_items, card_w, card_h, spacing, margin)

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

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._scroll)

        win_w = min(self._grid.width() + 20, screen_w)
        win_h = min(screen_h - 80, self._grid.height() + 20)
        self.resize(win_w, win_h)

        # Center window
        self.move((screen_w - win_w) // 2, (screen_h - win_h) // 2)

        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        self._scroll_anim = QPropertyAnimation(self._scroll.verticalScrollBar(), b"value", self)
        self._scroll_anim.setDuration(self.SCROLL_ANIMATION_MS)
        self._scroll_anim.setEasingCurve(QEasingCurve.Type.OutCubic)

    def _animate_scroll_to_card(self, card):
        bar = self._scroll.verticalScrollBar()
        viewport_h = self._scroll.viewport().height()
        target = card.y() + card.height() // 2 - viewport_h // 2
        target = max(bar.minimum(), min(bar.maximum(), target))

        self._scroll_anim.stop()
        self._scroll_anim.setStartValue(bar.value())
        self._scroll_anim.setEndValue(target)
        self._scroll_anim.start()

    def keyPressEvent(self, event):
        key = event.key()
        direction = None

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
            card = self._grid.move_selection(direction)
            self._animate_scroll_to_card(card)
        else:
            super().keyPressEvent(event)


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    font = QFont("Segoe UI", 10)
    app.setFont(font)

    window = MainWindow()
    window.show()
    window.setFocus()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()