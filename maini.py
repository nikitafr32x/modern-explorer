import sys
import os
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QPushButton, QScrollArea, QGridLayout, QMenu, QInputDialog, QMessageBox, QLineEdit, QTabBar
)
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor, QCursor, QDragEnterEvent, QDropEvent, QDrag
from PyQt6.QtCore import Qt, QSize, QMimeData, QPoint, QUrl, QEvent, QPropertyAnimation, QEasingCurve
from pathlib import Path
import shutil
from mimetypes import guess_type
import winshell
import string
import ctypes

USER_DIRS = {
    "Home": str(Path.home()),
    "Desktop": str(Path.home() / "Desktop"),
    "Documents": str(Path.home() / "Documents"),
    "Downloads": str(Path.home() / "Downloads"),
    "Music": str(Path.home() / "Music"),
    "Pictures": str(Path.home() / "Pictures"),
    "Videos": str(Path.home() / "Videos"),
    "Templates": str(Path.home() / "Templates"),
    "Public": str(Path.home() / "Public"),
}

# Получить иконку файла по расширению (Windows)
def get_file_icon(path):
    # Для файлов и папок — системная иконка Windows
    return get_win_icon(path)

def get_file_icon_or_preview(path):
    if os.path.isdir(path):
        return get_win_icon(path), False
    mime, _ = guess_type(path)
    if mime and mime.startswith('image'):
        try:
            pixmap = QPixmap(path)
            if not pixmap.isNull():
                return pixmap, True
        except Exception:
            pass
    # Для остальных файлов — unknow.png
    if os.path.exists("unknow.png"):
        return QIcon("unknow.png"), False
    if os.path.exists("unknown.png"):
        return QIcon("unknown.png"), False
    return QIcon(), False

try:
    import win32com.client
    import pythoncom
    def get_win_icon(path):
        try:
            pythoncom.CoInitialize()
            shl = win32com.client.Dispatch('Shell.Application')
            folder, name = os.path.split(path)
            folder_item = shl.NameSpace(folder).ParseName(name)
            return QIcon(folder_item.GetIconLocation()[0])
        except Exception:
            return QIcon("folder.png")
except ImportError:
    def get_win_icon(path):
        return QIcon("folder.png")

class FileWidget(QFrame):
    def __init__(self, name, path, is_dir, on_click, parent=None, main_window=None, scale_factor=1.0, is_disk=False):
        super().__init__(parent)
        #print(f"FileWidget: name={name}, path={path}, is_dir={is_dir}")  # Debug print
        self.path = path
        self.is_dir = is_dir
        self.is_disk = is_disk
        self.main_window = main_window
        self.on_click = on_click
        self.scale_factor = scale_factor
        self.setAcceptDrops(True)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        
        # Use disk.png for disks, otherwise get normal icon
        if is_disk and os.path.exists("disk.png"):
            icon_or_pixmap = QIcon("disk.png")
            is_pixmap = False
        else:
            icon_or_pixmap, is_pixmap = get_file_icon_or_preview(path)
        # Scale icon size based on scale_factor
        icon_size = max(int(80 * scale_factor), 16)  # Minimum 16px
        if is_pixmap:
            pixmap = icon_or_pixmap.scaled(icon_size, icon_size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        else:
            pixmap = icon_or_pixmap.pixmap(icon_size, icon_size)
        icon_label = QLabel()
        icon_label.setPixmap(pixmap)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        text_label = QLabel(name)
        text_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        # Scale font size based on scale_factor
        font_size = max(int(15 * scale_factor), 8)  # Minimum 8px
        text_label.setStyleSheet(f"font-size: {font_size}px; color: #333;")
        layout.addWidget(icon_label)
        layout.addWidget(text_label)
        # Scale widget width based on scale_factor
        widget_width = max(int(110 * scale_factor), 50)  # Minimum 50px
        self.setFixedWidth(widget_width)
        self.setStyleSheet("QFrame:hover {background: #f0f4ff; border-radius: 10px;}")
        self._drag_start_pos = None
        # Animation for click effect
        self.animation = None

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_start_pos = event.position().toPoint()
            # Add click animation
            self.animate_click()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and self._drag_start_pos is not None:
            if (event.position().toPoint() - self._drag_start_pos).manhattanLength() > 10:
                drag = QDrag(self)
                mime = QMimeData()
                mime.setUrls([QUrl.fromLocalFile(self.path)])
                drag.setMimeData(mime)
                drag.exec()
                self._drag_start_pos = None
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self._drag_start_pos is not None:
            if (event.position().toPoint() - self._drag_start_pos).manhattanLength() <= 10:
                self.on_click(self.path, self.is_dir)
            self._drag_start_pos = None
        super().mouseReleaseEvent(event)

    def animate_click(self):
        """Animate the file widget on click"""
        if self.animation and self.animation.state() == QPropertyAnimation.State.Running:
            self.animation.stop()
        
        # Create animation for scaling effect
        self.animation = QPropertyAnimation(self, b"geometry")
        self.animation.setDuration(200)  # 200ms duration
        
        # Get current geometry
        current_geometry = self.geometry()
        
        # Calculate scaled geometry (95% of original size)
        scaled_width = int(current_geometry.width() * 0.95)
        scaled_height = int(current_geometry.height() * 0.95)
        dx = (current_geometry.width() - scaled_width) // 2
        dy = (current_geometry.height() - scaled_height) // 2
        scaled_geometry = current_geometry.adjusted(dx, dy, -dx, -dy)
        
        # Set up animation
        self.animation.setStartValue(current_geometry)
        self.animation.setEndValue(scaled_geometry)
        self.animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        # Add another animation to return to original size
        self.animation2 = QPropertyAnimation(self, b"geometry")
        self.animation2.setDuration(200)
        self.animation2.setStartValue(scaled_geometry)
        self.animation2.setEndValue(current_geometry)
        self.animation2.setEasingCurve(QEasingCurve.Type.InCubic)
        
        # Chain animations
        self.animation.finished.connect(self.animation2.start)
        self.animation.start()
    
    def update_scale(self, scale_factor):
        """Update the widget's appearance based on scale factor"""
        # Update icon size
        icon_label = self.layout().itemAt(0).widget() if self.layout().count() > 0 else None
        text_label = self.layout().itemAt(1).widget() if self.layout().count() > 1 else None
        
        if icon_label:
            # Get the original pixmap or icon
            path = self.path
            icon_or_pixmap, is_pixmap = get_file_icon_or_preview(path)
            icon_size = max(int(80 * scale_factor), 16)
            if is_pixmap:
                pixmap = icon_or_pixmap.scaled(icon_size, icon_size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            else:
                pixmap = icon_or_pixmap.pixmap(icon_size, icon_size)
            icon_label.setPixmap(pixmap)
        
        # Update text label font size
        if text_label:
            font_size = max(int(15 * scale_factor), 8)
            text_label.setStyleSheet(f"font-size: {font_size}px; color: #333;")
        
        # Update widget width
        widget_width = max(int(110 * scale_factor), 50)
        self.setFixedWidth(widget_width)

    def contextMenuEvent(self, event):
        menu = QMenu(self.main_window if self.main_window else self)
        menu.setStyleSheet("""
            QMenu {
                background: #fff;
                border: 1px solid #d0d0d0;
                border-radius: 10px;
                padding: 6px;
                color: #222;
                font-size: 15px;
            }
            QMenu::item {
                padding: 8px 24px 8px 24px;
                border-radius: 6px;
            }
            QMenu::item:selected {
                background: #e6f0ff;
                color: #1a73e8;
            }
            QMenu::separator {
                height: 1px;
                background: #e0e0e0;
                margin: 4px 0 4px 0;
            }
        """)
        menu.addAction("Открыть", lambda: self.main_window.file_clicked(self.path, self.is_dir))
        menu.addSeparator()
        menu.addAction("Копировать", lambda: self.main_window.set_clipboard(self.path, cut=False))
        menu.addAction("Вырезать", lambda: self.main_window.set_clipboard(self.path, cut=True))
        menu.addAction("Вставить", lambda: self.main_window.paste_to(self.path if self.is_dir else os.path.dirname(self.path)))
        menu.addSeparator()
        menu.addAction("Переименовать", lambda: self.main_window.rename_item(self.path))
        menu.addAction("Удалить", lambda: self.main_window.delete_item(self.path))
        menu.addSeparator()
        menu.addAction("Свойства", lambda: self.main_window.show_properties(self.path))
        menu.exec(event.globalPos())

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        for url in event.mimeData().urls():
            src = url.toLocalFile()
            if os.path.exists(src):
                dst = os.path.join(self.path, os.path.basename(src)) if self.is_dir else os.path.dirname(self.path)
                if os.path.isdir(src):
                    shutil.copytree(src, dst, dirs_exist_ok=True)
                else:
                    shutil.copy2(src, dst)
        event.acceptProposedAction()

class CustomWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Window)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setMinimumSize(900, 600)
        self.setAcceptDrops(True)
        self.history = []
        self.current_path = USER_DIRS["Home"]
        self.drag_pos = None
        self.resizing = False
        self.clipboard_path = None
        self.clipboard_cut = False
        self._window_drag_active = False
        self._window_drag_pos = None
        self._resize_direction = None
        self._resize_start_pos = None
        self._resize_start_geometry = None
        self.all_entries = []  # Store all entries for search filtering
        self.scale_factor = 1.0  # For file icon scaling
        self.show_hidden = False  # For showing hidden files
        self.view_mode = "grid"  # View mode: "grid" or "list"
        # For progressive file loading
        self.chunk_size = 50  # Number of files to load per chunk
        self.loaded_entries = []  # Files already loaded and displayed
        self.remaining_entries = []  # Files not yet loaded
        self.loading_in_progress = False  # Flag to prevent multiple simultaneous loads
        # For window maximize/restore state
        self.is_maximized = False
        self.normal_geometry = None  # Store geometry when windowed
        
        # Loading indicator
        self.loading_label = QLabel("Загрузка файлов...")
        self.loading_label.setStyleSheet("font-size: 16px; color: #666; padding: 10px;")
        self.loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.loading_label.setVisible(False)
        
        self.init_ui()

    def init_ui(self):
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setSpacing(0)

        # Сайдбар
        self.sidebar = QFrame()
        self.sidebar.setFixedWidth(200)
        self.sidebar.setStyleSheet("""
            QFrame {
                background: #f5f6fa;
                border-top-left-radius: 18px;
                border-bottom-left-radius: 18px;
            }
        """)
        self.sidebar_layout = QVBoxLayout(self.sidebar)
        self.sidebar_layout.setContentsMargins(0, 16, 0, 16)
        self.sidebar_layout.setSpacing(0)
        
        # Search input in sidebar
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Поиск файлов...")
        self.search_input.setStyleSheet("""
            QLineEdit {
                padding: 8px 12px;
                font-size: 14px;
                border: 1px solid #e0e4ea;
                border-radius: 8px;
                background: #fff;
                color: #000;
                margin: 0 12px 12px 12px;
            }
        """)
        self.search_input.textChanged.connect(self.on_search_text_changed)
        self.sidebar_layout.addWidget(self.search_input)

        # Список пунктов и иконок
        self.sidebar_items = [
            ("Home", "sample.png"),
            ("Disks", "disk.png"),
            ("Trash", "sample.png"),
            ("sep", None),
            ("Documents", "sample.png"),
            ("Music", "sample.png"),
            ("Pictures", "sample.png"),
            ("Videos", "sample.png"),
            ("Downloads", "sample.png"),
        ]
        self.sidebar_btns = {}
        for name, icon in self.sidebar_items:
            if name == "sep":
                line = QFrame()
                line.setFrameShape(QFrame.Shape.HLine)
                line.setStyleSheet("color: #e0e4ea; background: #e0e4ea; margin: 8px 0 8px 0; height: 1px;")
                self.sidebar_layout.addWidget(line)
                continue
            btn = QPushButton(f"  {name}")
            btn.setIcon(QIcon(icon) if icon else QIcon())
            btn.setIconSize(QSize(22, 22))
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet("""
                QPushButton {
                    font-size: 16px;
                    color: #444;
                    padding: 10px 0 10px 24px;
                    border: none;
                    text-align: left;
                    border-radius: 8px;
                    background: transparent;
                }
                QPushButton:hover {
                    background: #e6f0ff;
                }
            """)
            btn.clicked.connect(lambda checked, n=name: self.sidebar_navigate(n))
            btn.installEventFilter(self)
            self.sidebar_layout.addWidget(btn)
            self.sidebar_btns[name] = btn
        self.sidebar_layout.addStretch()
        self.active_sidebar = None

        # Основная область
        self.content = QFrame()
        self.content.setStyleSheet("background: #fff; border-radius: 16px;")
        self.content_layout = QVBoxLayout(self.content)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(0)

        # Верхняя панель
        self.topbar_frame = QFrame()
        self.topbar_frame.setStyleSheet("""
            QFrame {
                background: #f8fafc;
                border-top-left-radius: 16px;
                border-top-right-radius: 16px;
                border-bottom: 1px solid #e0e4ea;
            }
        """)
        self.topbar_frame.setFixedHeight(60)
        self.topbar_layout = QHBoxLayout(self.topbar_frame)
        self.topbar_layout.setContentsMargins(24, 10, 24, 10)
        self.topbar_layout.setSpacing(10)
        self.back_btn = QPushButton("←")
        self.back_btn.setFixedSize(32, 32)
        self.back_btn.setStyleSheet("""
            QPushButton {
                font-size: 18px; border: none; background: transparent; color: #7a8ca3;
            }
            QPushButton:hover {
                background: #e6f0ff; color: #1a73e8;
            }
        """)
        self.back_btn.clicked.connect(self.go_back)
        self.topbar_layout.addWidget(self.back_btn)

        # Breadcrumb + edit
        self.breadcrumb_widget = QWidget()
        self.breadcrumb_layout = QHBoxLayout(self.breadcrumb_widget)
        self.breadcrumb_layout.setContentsMargins(0, 0, 0, 0)
        self.breadcrumb_layout.setSpacing(0)
        self.topbar_layout.addWidget(self.breadcrumb_widget, 1)
        self.breadcrumb_edit = QLineEdit()
        self.breadcrumb_edit.setVisible(False)
        self.breadcrumb_edit.setStyleSheet("font-size: 18px; border: 1px solid #e0e4ea; border-radius: 8px; padding: 4px 10px; background: #fff; color: #000;")
        self.breadcrumb_edit.returnPressed.connect(self.breadcrumb_edit_apply)
        self.topbar_layout.addWidget(self.breadcrumb_edit, 1)
        self.edit_path_btn = QPushButton("✎")
        self.edit_path_btn.setFixedSize(28, 28)
        self.edit_path_btn.setStyleSheet("QPushButton { border: none; background: transparent; color: #7a8ca3; } QPushButton:hover { background: #e6f0ff; color: #1a73e8; }")
        self.edit_path_btn.clicked.connect(self.breadcrumb_edit_mode)
        self.topbar_layout.addWidget(self.edit_path_btn)
        
        # Add button for toggling hidden files
        self.toggle_hidden_btn = QPushButton("👁")
        self.toggle_hidden_btn.setFixedSize(28, 28)
        self.toggle_hidden_btn.setStyleSheet("QPushButton { border: none; background: transparent; color: #7a8ca3; } QPushButton:hover { background: #e6f0ff; color: #1a73e8; }")
        self.toggle_hidden_btn.clicked.connect(self.toggle_hidden_files)
        self.topbar_layout.addWidget(self.toggle_hidden_btn)

        # Add button for toggling view mode (grid/list)
        self.toggle_view_btn = QPushButton("☰")
        self.toggle_view_btn.setFixedSize(28, 28)
        self.toggle_view_btn.setStyleSheet("QPushButton { border: none; background: transparent; color: #7a8ca3; } QPushButton:hover { background: #e6f0ff; color: #1a73e8; }")
        self.toggle_view_btn.clicked.connect(self.toggle_view_mode)
        self.topbar_layout.addWidget(self.toggle_view_btn)

        # Кнопки управления окном
        self.min_btn = QPushButton("–")
        self.min_btn.setFixedSize(32, 32)
        self.min_btn.setStyleSheet("""
            QPushButton {
                font-size: 18px; border: none; background: transparent; color: #7a8ca3;
            }
            QPushButton:hover {
                background: #e6f0ff; color: #1a73e8;
            }
        """)
        self.min_btn.clicked.connect(self.showMinimized)
        
        # Maximize/Restore button
        self.max_btn = QPushButton("□")
        self.max_btn.setFixedSize(32, 32)
        self.max_btn.setStyleSheet("""
            QPushButton {
                font-size: 16px; border: none; background: transparent; color: #7a8ca3;
            }
            QPushButton:hover {
                background: #e6f0ff; color: #1a73e8;
            }
        """)
        self.max_btn.clicked.connect(self.toggle_maximize)
        
        self.close_btn = QPushButton("×")
        self.close_btn.setFixedSize(32, 32)
        self.close_btn.setStyleSheet("""
            QPushButton {
                font-size: 18px; border: none; background: transparent; color: #e57373;
            }
            QPushButton:hover {
                background: #ffeaea; color: #d32f2f;
            }
        """)
        self.close_btn.clicked.connect(self.close)
        self.topbar_layout.addWidget(self.min_btn)
        self.topbar_layout.addWidget(self.max_btn)
        self.topbar_layout.addWidget(self.close_btn)
        self.content_layout.addWidget(self.topbar_frame)
        self.content_layout.setSpacing(0)
        self.content_layout.setContentsMargins(0, 0, 0, 0)

        # Прокручиваемая область с файлами и папками
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("border: none;")
        self.folders_widget = QWidget()
        self.folders_widget.setAcceptDrops(True)
        self.folders_widget.dragEnterEvent = self.folders_drag_enter_event
        self.folders_widget.dragLeaveEvent = self.folders_drag_leave_event
        self.folders_widget.dropEvent = self.folders_drop_event
        self.folders_widget._drag_over = False
        self.folders_layout = QGridLayout(self.folders_widget)
        self.folders_layout.setSpacing(20)
        self.folders_layout.setContentsMargins(20, 20, 20, 20)
        self.scroll.setWidget(self.folders_widget)
        
        # Add loading label to the layout
        self.folders_layout.addWidget(self.loading_label, 0, 0, 1, 5)
        
        self.content_layout.addWidget(self.scroll)
        
        # Initialize grid centering
        self.center_grid_items()

        # Вкладки дисков
        self.disk_tabbar = QTabBar()
        self.disk_tabbar.setExpanding(False)
        self.disk_tabbar.setDrawBase(False)
        self.disk_tabbar.setStyleSheet("""
            QTabBar::tab {
                background: #f5f6fa;
                border: 1px solid #e0e4ea;
                border-radius: 8px;
                min-width: 60px;
                min-height: 28px;
                margin-right: 8px;
                font-size: 15px;
                color: #444;
                padding: 4px 16px;
            }
            QTabBar::tab:selected {
                background: #e6f0ff;
                color: #1a73e8;
            }
        """)
        self.disk_tabbar.setMovable(False)
        self.disk_tabbar.tabBarClicked.connect(self.on_disk_tab_clicked)
        self.content_layout.addWidget(self.disk_tabbar)
        self.update_disk_tabs()

        self.main_layout.addWidget(self.sidebar)
        self.main_layout.addSpacing(20)
        self.main_layout.addWidget(self.content)

        # Вызов навигации по сайдбару только после создания всех элементов верхней панели
        self.sidebar_navigate("Home")

    def update_breadcrumb(self, path):
        # Очищаем старые элементы
        for i in reversed(range(self.breadcrumb_layout.count())):
            w = self.breadcrumb_layout.itemAt(i).widget()
            if w:
                w.setParent(None)
        parts = Path(path).parts
        acc = ""
        for i, part in enumerate(parts):
            if i == 0 and os.name == "nt":
                acc = part
            else:
                acc = os.path.join(acc, part) if acc else part
            btn = QPushButton(part)
            btn.setStyleSheet("QPushButton { background: transparent; border: none; color: #222; font-size: 18px; padding: 2px 8px; border-radius: 6px; } QPushButton:hover { background: #e6f0ff; color: #1a73e8; }")
            btn.clicked.connect(lambda checked, p=acc: self.open_dir(p, add_history=True))
            self.breadcrumb_layout.addWidget(btn)
            if i < len(parts) - 1:
                sep = QLabel("/")
                sep.setStyleSheet("color: #b0b8c9; font-size: 18px; padding: 0 2px;")
                self.breadcrumb_layout.addWidget(sep)

    def breadcrumb_edit_mode(self):
        self.breadcrumb_widget.setVisible(False)
        self.breadcrumb_edit.setText(self.current_path)
        self.breadcrumb_edit.setVisible(True)
        self.breadcrumb_edit.setFocus()
        self.breadcrumb_edit.selectAll()
    
    def toggle_hidden_files(self):
        """Toggle visibility of hidden files"""
        self.show_hidden = not self.show_hidden
        # Update button appearance
        if self.show_hidden:
            self.toggle_hidden_btn.setStyleSheet("QPushButton { border: none; background: #e6f0ff; color: #1a73e8; } QPushButton:hover { background: #d9e6ff; }")
        else:
            self.toggle_hidden_btn.setStyleSheet("QPushButton { border: none; background: transparent; color: #7a8ca3; } QPushButton:hover { background: #e6f0ff; color: #1a73e8; }")
        # Re-open current directory to apply changes
        self.open_dir(self.current_path, add_history=False)

    def toggle_view_mode(self):
        """Toggle between grid and list view modes"""
        if self.view_mode == "grid":
            self.view_mode = "list"
            # Update button appearance for list view
            self.toggle_view_btn.setStyleSheet("QPushButton { border: none; background: #e6f0ff; color: #1a73e8; } QPushButton:hover { background: #d9e6ff; }")
        else:
            self.view_mode = "grid"
            # Update button appearance for grid view
            self.toggle_view_btn.setStyleSheet("QPushButton { border: none; background: transparent; color: #7a8ca3; } QPushButton:hover { background: #e6f0ff; color: #1a73e8; }")
        # Re-open current directory to apply changes
        self.open_dir(self.current_path, add_history=False)

    def breadcrumb_edit_apply(self):
        path = self.breadcrumb_edit.text()
        if os.path.isdir(path):
            self.open_dir(path, add_history=True)
        self.breadcrumb_edit.setVisible(False)
        self.breadcrumb_widget.setVisible(True)

    def open_dir(self, path, add_history=True):
        #print(f"open_dir: path={path}, isdir={os.path.isdir(path)}")  # Debug print
        if not os.path.isdir(path):
            return
        if add_history:
            self.history.append(self.current_path)
        self.current_path = path
        self.update_breadcrumb(path)
        self.update_disk_tabs()
        # Очистить старые виджеты
        while self.folders_layout.count():
            item = self.folders_layout.takeAt(0)
            if item and item.widget():
                widget = item.widget()
                widget.setParent(None)
                widget.deleteLater()
        # Reset progressive loading state
        self.loaded_entries = []
        self.loading_in_progress = False
        # Добавить папки и файлы
        try:
            entries = os.listdir(path)
        except Exception as e:
            # Show folder as "inaccessible" instead of going back
            entries = []
            # Display a message in the folder area
            empty_widget = QWidget()
            vbox = QVBoxLayout(empty_widget)
            vbox.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
            icon = QIcon("folder.png") if os.path.exists("folder.png") else QIcon()
            icon_label = QLabel()
            if not icon.isNull():
                icon_label.setPixmap(icon.pixmap(120, 120))
            vbox.addWidget(icon_label, alignment=Qt.AlignmentFlag.AlignHCenter)
            text_label = QLabel("Нет доступа к папке")
            text_label.setStyleSheet("font-size: 22px; color: #b0b8c9; margin-top: 16px;")
            text_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
            vbox.addWidget(text_label, alignment=Qt.AlignmentFlag.AlignHCenter)
            detail_label = QLabel(f"Путь: {path}")
            detail_label.setStyleSheet("font-size: 16px; color: #888; margin-top: 8px;")
            detail_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
            vbox.addWidget(detail_label, alignment=Qt.AlignmentFlag.AlignHCenter)
            error_label = QLabel(f"Ошибка: {str(e)}")
            error_label.setStyleSheet("font-size: 14px; color: #888; margin-top: 8px;")
            error_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
            vbox.addWidget(error_label, alignment=Qt.AlignmentFlag.AlignHCenter)
            self.folders_layout.addWidget(empty_widget, 0, 0, 1, 5)
            self.folders_widget.adjustSize()
            self.scroll.verticalScrollBar().setValue(0)
            self.back_btn.setEnabled(len(self.history) > 0)
            # Don't return here, continue with empty entries list
        # Filter out hidden files if show_hidden is False
        if not self.show_hidden:
            self.all_entries = [e for e in entries if not e.startswith('.')]
        else:
            self.all_entries = entries[:]
        self.all_entries.sort()
        entries = self.all_entries[:]  # Work with a copy
        
        # Filter entries based on search text if provided
        search_text = self.search_input.text().strip().lower()
        if search_text:
            entries = [e for e in entries if search_text in e.lower()]
        entries.sort()
        
        # Set up progressive loading
        self.remaining_entries = entries[:]
        
        if not entries:
            empty_widget = QWidget()
            vbox = QVBoxLayout(empty_widget)
            vbox.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
            icon = QIcon("folder.png") if os.path.exists("folder.png") else QIcon()
            icon_label = QLabel()
            if not icon.isNull():
                icon_label.setPixmap(icon.pixmap(120, 120))
            vbox.addWidget(icon_label, alignment=Qt.AlignmentFlag.AlignHCenter)
            text_label = QLabel("эта папка пустая")
            text_label.setStyleSheet("font-size: 22px; color: #b0b8c9; margin-top: 16px;")
            text_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
            vbox.addWidget(text_label, alignment=Qt.AlignmentFlag.AlignHCenter)
            self.folders_layout.addWidget(empty_widget, 0, 0, 1, 5)
        else:
            # Load first chunk of files
            self.load_next_chunk()
            
        self.folders_widget.adjustSize()
        self.scroll.verticalScrollBar().setValue(0)
        self.back_btn.setEnabled(len(self.history) > 0)
        
        # Add animation for directory switching
        self.animate_folder_transition()
        
        # Center grid items if in grid view
        if self.view_mode == "grid":
            self.center_grid_items()
    
    def load_next_chunk(self):
        """Load and display the next chunk of files"""
        if self.loading_in_progress or not self.remaining_entries:
            return
            
        self.loading_in_progress = True
        # Take a chunk of entries to load
        chunk = self.remaining_entries[:self.chunk_size]
        self.remaining_entries = self.remaining_entries[self.chunk_size:]
        self.loaded_entries.extend(chunk)
        
        # Get current index for layout positioning
        current_idx = len(self.loaded_entries) - len(chunk)
        
        # Create and add widgets for this chunk
        for i, entry in enumerate(chunk):
            abs_path = os.path.join(self.current_path, entry)
            is_dir = os.path.isdir(abs_path)
            
            if self.view_mode == "grid":
                # Grid view (existing implementation)
                fw = FileWidget(entry, abs_path, is_dir, self.file_clicked, main_window=self, scale_factor=self.scale_factor)
                row, col = divmod(current_idx + i, 5)
                self.folders_layout.addWidget(fw, row, col)
            else:
                # List view
                list_widget = QWidget()
                list_layout = QHBoxLayout(list_widget)
                list_layout.setContentsMargins(10, 5, 10, 5)
                list_layout.setSpacing(10)
                
                # Get icon for the file/folder
                icon_or_pixmap, is_pixmap = get_file_icon_or_preview(abs_path)
                icon_size = max(int(32 * self.scale_factor), 16)  # Minimum 16px
                
                icon_label = QLabel()
                if is_pixmap:
                    pixmap = icon_or_pixmap.scaled(icon_size, icon_size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                    icon_label.setPixmap(pixmap)
                else:
                    pixmap = icon_or_pixmap.pixmap(icon_size, icon_size)
                    icon_label.setPixmap(pixmap)
                
                # Name label
                name_label = QLabel(entry)
                name_label.setStyleSheet("font-size: 16px; color: #333;")
                
                # Size label
                try:
                    size = os.path.getsize(abs_path) if not is_dir else 0
                    if is_dir:
                        size_text = "<ПАПКА>"
                    else:
                        if size < 1024:
                            size_text = f"{size} Б"
                        elif size < 1024 * 1024:
                            size_text = f"{size // 1024} КБ"
                        elif size < 1024 * 1024 * 1024:
                            size_text = f"{size // (1024 * 1024)} МБ"
                        else:
                            size_text = f"{size // (1024 * 1024 * 1024)} ГБ"
                except:
                    size_text = "Н/Д"
                
                size_label = QLabel(size_text)
                size_label.setStyleSheet("font-size: 14px; color: #666;")
                size_label.setAlignment(Qt.AlignmentFlag.AlignRight)
                
                # Add widgets to layout
                list_layout.addWidget(icon_label)
                list_layout.addWidget(name_label, 1)  # Stretch factor 1 to take available space
                list_layout.addWidget(size_label)
                
                # Set widget properties
                list_widget.setStyleSheet("""
                    QWidget {
                        border-bottom: 1px solid #e0e4ea;
                        background: transparent;
                    }
                    QWidget:hover {
                        background: #f0f4ff;
                    }
                """)
                list_widget.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
                
                # Connect click event
                def make_click_handler(path, is_dir):
                    return lambda event: self.file_clicked(path, is_dir)
                
                list_widget.mousePressEvent = make_click_handler(abs_path, is_dir)
                
                # Add to layout
                self.folders_layout.addWidget(list_widget, current_idx + i, 0, 1, 5)
        
        # If there are more entries to load, set up automatic loading
        if self.remaining_entries:
            # Connect to scroll event to load more when user scrolls near the bottom
            # Using try-except to handle cases where connection already exists
            try:
                self.scroll.verticalScrollBar().valueChanged.disconnect(self.check_scroll_for_loading)
            except (TypeError, AttributeError):
                # No existing connection to disconnect, which is fine
                pass
            try:
                self.scroll.verticalScrollBar().valueChanged.connect(self.check_scroll_for_loading)
            except (TypeError, AttributeError):
                # Connection failed for some reason, which we'll ignore
                pass
        
        
        # Center the grid items if we're in grid view mode
        if self.view_mode == "grid":
            self.center_grid_items()
         
        self.loading_in_progress = False
        self.folders_widget.adjustSize()
    
    def center_grid_items(self):
        """Center grid items when there are fewer items than columns in the last row"""
        # Only apply centering in grid view mode
        if self.view_mode != "grid":
            return
            
        # Get the number of items in the grid
        item_count = self.folders_layout.count()
        
        # If we have items, check if the last row is incomplete
        if item_count > 0:
            # Calculate how many items are in the last row
            items_in_last_row = item_count % 5
            if items_in_last_row == 0 and item_count > 0:
                items_in_last_row = 5
                
            # If the last row is incomplete, center those items
            if items_in_last_row > 0 and items_in_last_row < 5:
                # Calculate how many empty positions we have in the last row
                empty_positions = 5 - items_in_last_row
                
                # Distribute empty positions evenly on both sides
                left_padding = empty_positions // 2
                right_padding = empty_positions - left_padding
                
                # Set column stretch factors to center the items
                # Left padding columns
                for i in range(left_padding):
                    self.folders_layout.setColumnStretch(i, 1)
                    
                # Item columns (no stretch, they'll take their natural size)
                for i in range(left_padding, left_padding + items_in_last_row):
                    self.folders_layout.setColumnStretch(i, 0)
                    
                # Right padding columns
                for i in range(left_padding + items_in_last_row, 5):
                    self.folders_layout.setColumnStretch(i, 1)
            else:
                # If the last row is complete or empty, reset all column stretch factors
                for i in range(5):
                    self.folders_layout.setColumnStretch(i, 0)
    def check_scroll_for_loading(self, value):
        """Check if we need to load more files based on scroll position"""
        if not self.remaining_entries or self.loading_in_progress:
            return
            
        # Get scroll bar and widget heights
        scroll_bar = self.scroll.verticalScrollBar()
        scroll_max = scroll_bar.maximum()
        
        # If we're near the bottom (within 20% of the end), load more files
        if value >= scroll_max * 0.8:
            self.load_next_chunk()
    def update_scale(self):
        """Update file widgets with current scale factor"""
        # Iterate through all widgets in folders_layout and update their scale
        for i in range(self.folders_layout.count()):
            item = self.folders_layout.itemAt(i)
            if item and item.widget():
                widget = item.widget()
                if isinstance(widget, FileWidget):
                    widget.update_scale(self.scale_factor)
    
    def animate_folder_transition(self):
        """Add a subtle animation when switching directories"""
        # Create a property animation for the folders_widget
        animation = QPropertyAnimation(self.folders_widget, b"geometry")
        animation.setDuration(300)  # 300ms duration
        
        # Get current geometry
        current_geometry = self.folders_widget.geometry()
        
        # Calculate slightly scaled geometry for the animation effect
        scale_factor = 0.95
        scaled_width = int(current_geometry.width() * scale_factor)
        scaled_height = int(current_geometry.height() * scale_factor)
        dx = (current_geometry.width() - scaled_width) // 2
        dy = (current_geometry.height() - scaled_height) // 2
        scaled_geometry = current_geometry.adjusted(dx, dy, -dx, -dy)
        
        # Set up animation
        animation.setStartValue(scaled_geometry)
        animation.setEndValue(current_geometry)
        animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        # Start animation
        animation.start(QPropertyAnimation.DeletionPolicy.DeleteWhenStopped)

    def eventFilter(self, obj, event):
        # Handle sidebar button animations
        if obj in self.sidebar_btns.values():
            if event.type() == QEvent.Type.MouseButtonPress and event.button() == Qt.MouseButton.LeftButton:
                self.animate_button_press(obj, True)
            elif event.type() == QEvent.Type.MouseButtonRelease and event.button() == Qt.MouseButton.LeftButton:
                self.animate_button_press(obj, False)
        # Handle paint event for folders_widget drag-over indication
        elif hasattr(self, 'folders_widget') and obj is self.folders_widget and event.type() == QEvent.Type.Paint:
            if getattr(self.folders_widget, '_drag_over', False):
                painter = QPainter(self.folders_widget)
                painter.setRenderHint(QPainter.RenderHint.Antialiasing)
                rect = self.folders_widget.rect()
                painter.setBrush(QColor(230, 240, 255, 120))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawRoundedRect(rect, 24, 24)
        return super().eventFilter(obj, event)

    def file_clicked(self, path, is_dir):
        if is_dir:
            self.open_dir(path, add_history=True)
        else:
            try:
                os.startfile(path)
            except Exception as e:
                dialog = WarningDialog("Ошибка", f"Не удалось открыть файл:\n{path}\n\nОшибка: {str(e)}", self)
                dialog.exec()

    def on_search_text_changed(self, text):
        # Re-open current directory with filtered entries
        self.open_dir(self.current_path, add_history=False)

    def go_back(self):
        if self.history:
            prev = self.history.pop()
            self.open_dir(prev, add_history=False)

    # Drag and drop для окна
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        for url in event.mimeData().urls():
            src = url.toLocalFile()
            if os.path.exists(src):
                dst = os.path.join(self.current_path, os.path.basename(src))
                if os.path.isdir(src):
                    shutil.copytree(src, dst, dirs_exist_ok=True)
                else:
                    shutil.copy2(src, dst)
        self.open_dir(self.current_path, add_history=False)
        event.acceptProposedAction()

    # Кастомный resize и перемещение окна
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            # Проверяем, если клик на краю окна для изменения размера
            self.check_resize_edges(event.pos())
            if self.resizing:
                # Начинаем изменение размера
                self._resize_start_pos = event.globalPosition().toPoint()
                self._resize_start_geometry = self.geometry()
                return
            
            # Проверяем, что клик внутри topbar_frame для перемещения
            topbar_rect = self.topbar_frame.geometry()
            # Преобразуем координаты события в координаты окна
            local_pos = self.mapFromGlobal(event.globalPosition().toPoint())
            if topbar_rect.contains(local_pos):
                widget = self.childAt(local_pos)
                forbidden = [self.min_btn, self.close_btn, self.back_btn, self.edit_path_btn, self.breadcrumb_edit, self.breadcrumb_widget]
                if not any(w is widget or (hasattr(w, 'isAncestorOf') and w.isAncestorOf(widget)) for w in forbidden):
                    self._window_drag_active = True
                    self._window_drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._window_drag_active and event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._window_drag_pos)
        elif self.resizing and event.buttons() == Qt.MouseButton.LeftButton:
            self.perform_resize(event.globalPosition().toPoint())
        else:
            # Обновляем курсор при наведении на край окна только если кнопка мыши не нажата
            if event.buttons() == Qt.MouseButton.NoButton:
                self.check_resize_edges(event.pos())
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._window_drag_active = False
        self._window_drag_pos = None
        self.resizing = False
        self._resize_direction = None
        self._resize_start_pos = None
        self._resize_start_geometry = None
        self.unsetCursor()
        super().mouseReleaseEvent(event)
    
    def wheelEvent(self, event):
        """Handle Ctrl+Wheel for zooming"""
        if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            # Get vertical scroll delta (usually +/- 120 for one wheel click)
            delta = event.angleDelta().y()
            if delta > 0:
                # Zoom in
                self.scale_factor = min(self.scale_factor * 1.1, 3.0)  # Max 3x zoom
            elif delta < 0:
                # Zoom out
                self.scale_factor = max(self.scale_factor / 1.1, 0.3)  # Min 0.3x zoom
            self.update_scale()
            event.accept()
        else:
            # Pass event to parent for normal scrolling
            super().wheelEvent(event)
    
    def keyPressEvent(self, event):
        """Handle Ctrl++ and Ctrl+- for zooming"""
        if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            if event.key() == Qt.Key.Key_Plus or event.key() == Qt.Key.Key_Equal:
                # Zoom in (Ctrl++)
                self.scale_factor = min(self.scale_factor * 1.1, 3.0)
                self.update_scale()
                event.accept()
                return
            elif event.key() == Qt.Key.Key_Minus:
                # Zoom out (Ctrl+-)
                self.scale_factor = max(self.scale_factor / 1.1, 0.3)
                self.update_scale()
                event.accept()
                return
        super().keyPressEvent(event)

    def toggle_maximize(self):
        """Toggle between maximized and normal window states"""
        if not self.is_maximized:
            # Store current geometry before maximizing
            self.normal_geometry = self.geometry()
            # Get the available screen geometry (excluding taskbar)
            screen_geometry = self.screen().availableGeometry()
            # Set window to fill the screen
            self.setGeometry(screen_geometry)
            self.is_maximized = True
            # Update button text to restore symbol
            self.max_btn.setText("❐")
        else:
            # Restore to previous geometry
            if self.normal_geometry:
                self.setGeometry(self.normal_geometry)
            self.is_maximized = False
            # Update button text to maximize symbol
            self.max_btn.setText("□")

    def check_resize_edges(self, pos):
        """Check if mouse position is near window edges for resizing"""
        margin = 8  # pixels from edge to trigger resize cursor
        rect = self.rect()
        
        # Check corners first (diagonal resize)
        if pos.x() <= margin and pos.y() <= margin:
            # Top-left corner
            self.setCursor(Qt.CursorShape.SizeFDiagCursor)
            self._resize_direction = "top-left"
            self.resizing = True
        elif pos.x() >= rect.width() - margin and pos.y() <= margin:
            # Top-right corner
            self.setCursor(Qt.CursorShape.SizeBDiagCursor)
            self._resize_direction = "top-right"
            self.resizing = True
        elif pos.x() <= margin and pos.y() >= rect.height() - margin:
            # Bottom-left corner
            self.setCursor(Qt.CursorShape.SizeBDiagCursor)
            self._resize_direction = "bottom-left"
            self.resizing = True
        elif pos.x() >= rect.width() - margin and pos.y() >= rect.height() - margin:
            # Bottom-right corner
            self.setCursor(Qt.CursorShape.SizeFDiagCursor)
            self._resize_direction = "bottom-right"
            self.resizing = True
        # Check edges (non-diagonal resize)
        elif pos.x() <= margin:
            # Left edge
            self.setCursor(Qt.CursorShape.SizeHorCursor)
            self._resize_direction = "left"
            self.resizing = True
        elif pos.x() >= rect.width() - margin:
            # Right edge
            self.setCursor(Qt.CursorShape.SizeHorCursor)
            self._resize_direction = "right"
            self.resizing = True
        elif pos.y() <= margin:
            # Top edge
            self.setCursor(Qt.CursorShape.SizeVerCursor)
            self._resize_direction = "top"
            self.resizing = True
        elif pos.y() >= rect.height() - margin:
            # Bottom edge
            self.setCursor(Qt.CursorShape.SizeVerCursor)
            self._resize_direction = "bottom"
            self.resizing = True
        else:
            # Not near any edge
            self.unsetCursor()
            self.resizing = False
            self._resize_direction = None

    def perform_resize(self, global_pos):
        """Perform window resizing based on direction and mouse position"""
        if not self._resize_direction or not self._resize_start_geometry:
            return
            
        delta = global_pos - self._resize_start_pos
        geo = self._resize_start_geometry
        new_geo = geo
        
        # Calculate new geometry based on resize direction
        if self._resize_direction == "top-left":
            new_geo = geo.adjusted(delta.x(), delta.y(), 0, 0)
        elif self._resize_direction == "top-right":
            new_geo = geo.adjusted(0, delta.y(), delta.x(), 0)
        elif self._resize_direction == "bottom-left":
            new_geo = geo.adjusted(delta.x(), 0, 0, delta.y())
        elif self._resize_direction == "bottom-right":
            new_geo = geo.adjusted(0, 0, delta.x(), delta.y())
        elif self._resize_direction == "left":
            new_geo = geo.adjusted(delta.x(), 0, 0, 0)
        elif self._resize_direction == "right":
            new_geo = geo.adjusted(0, 0, delta.x(), 0)
        elif self._resize_direction == "top":
            new_geo = geo.adjusted(0, delta.y(), 0, 0)
        elif self._resize_direction == "bottom":
            new_geo = geo.adjusted(0, 0, 0, delta.y())
            
        # Ensure minimum size
        min_width = 300
        min_height = 200
        if new_geo.width() < min_width:
            if "left" in self._resize_direction:
                new_geo.setLeft(new_geo.right() - min_width)
            else:
                new_geo.setRight(new_geo.left() + min_width)
        if new_geo.height() < min_height:
            if "top" in self._resize_direction:
                new_geo.setTop(new_geo.bottom() - min_height)
            else:
                new_geo.setBottom(new_geo.top() + min_height)
                
        self.setGeometry(new_geo)

    # Drag and drop for folders area

    def folders_drag_enter_event(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.folders_widget._drag_over = True
            self.folders_widget.update()

    def folders_drag_leave_event(self, event):
        self.folders_widget._drag_over = False
        self.folders_widget.update()

    def folders_drop_event(self, event):
        for url in event.mimeData().urls():
            src = url.toLocalFile()
            if os.path.exists(src):
                dst = os.path.join(self.current_path, os.path.basename(src))
                # Пропускать, если src и dst — один и тот же файл
                try:
                    if os.path.abspath(src) == os.path.abspath(dst):
                        continue
                    if os.path.isdir(src):
                        shutil.copytree(src, dst, dirs_exist_ok=True)
                    else:
                        shutil.copy2(src, dst)
                except shutil.SameFileError:
                    continue
        self.open_dir(self.current_path, add_history=False)
        self.folders_widget._drag_over = False
        self.folders_widget.update()
        event.acceptProposedAction()


    def showEvent(self, event):
        super().showEvent(event)
        self.folders_widget.installEventFilter(self)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect()
        painter.setBrush(QColor(240, 242, 245, 255))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(rect, 24, 24)
        # Рисуем угол для resize
        painter.setPen(QColor(180, 180, 200))
        for i in range(3):
            painter.drawLine(self.width()-10, self.height()-10+i*3, self.width()-10+i*3, self.height()-10)

    def set_clipboard(self, path, cut=False):
        self.clipboard_path = path
        self.clipboard_cut = cut

    def paste_to(self, dst_dir):
        if not self.clipboard_path:
            return
        name = os.path.basename(self.clipboard_path)
        dst = os.path.join(dst_dir, name)
        if os.path.isdir(self.clipboard_path):
            if self.clipboard_cut:
                shutil.move(self.clipboard_path, dst)
            else:
                shutil.copytree(self.clipboard_path, dst, dirs_exist_ok=True)
        else:
            if self.clipboard_cut:
                shutil.move(self.clipboard_path, dst)
            else:
                shutil.copy2(self.clipboard_path, dst)
        if self.clipboard_cut:
            self.clipboard_path = None
            self.clipboard_cut = False
        self.open_dir(self.current_path, add_history=False)

    def rename_item(self, path):
        name, ok = QInputDialog.getText(self, "Переименовать", "Новое имя:", text=os.path.basename(path))
        if ok and name:
            new_path = os.path.join(os.path.dirname(path), name)
            os.rename(path, new_path)
            self.open_dir(self.current_path, add_history=False)

    def delete_item(self, path):
        dialog = QuestionDialog("Удалить", f"Удалить '{os.path.basename(path)}'?", self)
        dialog.exec()
        # Check if the dialog was accepted (user clicked "Yes")
        if hasattr(dialog, 'result') and dialog.result:
            try:
                if os.path.isdir(path):
                    shutil.rmtree(path)
                else:
                    os.remove(path)
                self.open_dir(self.current_path, add_history=False)
            except Exception as e:
                dialog = WarningDialog("Ошибка", str(e), self)
                dialog.exec()

    def show_properties(self, path):
        info = os.stat(path)
        size = info.st_size
        mtime = info.st_mtime
        is_dir = os.path.isdir(path)
        msg = f"Путь: {path}\nТип: {'Папка' if is_dir else 'Файл'}\nРазмер: {size} байт\nИзменён: {mtime}"
        dialog = InformationDialog("Свойства", msg, self)
        dialog.exec()

    def contextMenuEvent(self, event):
        # Контекстное меню для пустой области (например, вставить)
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background: #fff;
                border: 1px solid #d0d0d0;
                border-radius: 10px;
                padding: 6px;
                color: #222;
                font-size: 15px;
            }
            QMenu::item {
                padding: 8px 24px 8px 24px;
                border-radius: 6px;
            }
            QMenu::item:selected {
                background: #e6f0ff;
                color: #1a73e8;
            }
            QMenu::separator {
                height: 1px;
                background: #e0e0e0;
                margin: 4px 0 4px 0;
            }
        """)
        create_menu = QMenu("Создать", self)
        create_menu.setStyleSheet(menu.styleSheet())
        folder_icon = QIcon("folder.png") if os.path.exists("folder.png") else QIcon()
        file_icon = QIcon("unknow.png") if os.path.exists("unknow.png") else QIcon()
        create_menu.addAction(folder_icon, "Папка", self.create_folder_dialog)
        create_menu.addAction(file_icon, "Текстовой файл", self.create_file_dialog)
        menu.addMenu(create_menu)
        menu.addAction("Вставить", lambda: self.paste_to(self.current_path))
        menu.exec(event.globalPos())

    def create_file_dialog(self):
        name, ok = QInputDialog.getText(self, "Создать файл", "Имя файла:")
        if ok and name:
            file_path = os.path.join(self.current_path, name)
            if not os.path.exists(file_path):
                try:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        pass
                    self.open_dir(self.current_path, add_history=False)
                except Exception as e:
                    dialog = WarningDialog("Ошибка", f"Не удалось создать файл:\n{e}", self)
                    dialog.exec()
            else:
                dialog = WarningDialog("Ошибка", "Файл с таким именем уже существует.", self)
                dialog.exec()

    def create_folder_dialog(self):
        name, ok = QInputDialog.getText(self, "Создать папку", "Имя папки:")
        if ok and name:
            folder_path = os.path.join(self.current_path, name)
            if not os.path.exists(folder_path):
                try:
                    os.makedirs(folder_path)
                    self.open_dir(self.current_path, add_history=False)
                except Exception as e:
                    dialog = WarningDialog("Ошибка", f"Не удалось создать папку:\n{e}", self)
                    dialog.exec()
            else:
                dialog = WarningDialog("Ошибка", "Папка с таким именем уже существует.", self)
                dialog.exec()

    def sidebar_navigate(self, name):
        # Снять выделение со всех
        for btn in self.sidebar_btns.values():
            btn.setStyleSheet(btn.styleSheet().replace("background: #dbeafe;", "background: transparent;"))
        # Выделить активный
        btn = self.sidebar_btns.get(name)
        if btn:
            btn.setStyleSheet(btn.styleSheet().replace("background: transparent;", "background: #dbeafe;"))
        self.active_sidebar = name
        # Открыть соответствующую папку
        if name == "Trash":
            self.open_recycle_bin_dir()
            return
        if name == "Disks":
            self.open_disks_dir()
            return
        if name in USER_DIRS:
            self.open_dir(USER_DIRS[name], add_history=True)

    def open_recycle_bin_dir(self):
        # Очистить старые виджеты
        for i in reversed(range(self.folders_layout.count())):
            widget = self.folders_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)
        try:
            items = list(winshell.recycle_bin())
        except Exception as e:
            items = []
        if not items:
            empty_widget = QWidget()
            vbox = QVBoxLayout(empty_widget)
            vbox.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
            icon = QIcon("folder.png") if os.path.exists("folder.png") else QIcon()
            icon_label = QLabel()
            if not icon.isNull():
                icon_label.setPixmap(icon.pixmap(120, 120))
            vbox.addWidget(icon_label, alignment=Qt.AlignmentFlag.AlignHCenter)
            text_label = QLabel("Корзина пуста")
            text_label.setStyleSheet("font-size: 22px; color: #b0b8c9; margin-top: 16px;")
            text_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
            vbox.addWidget(text_label, alignment=Qt.AlignmentFlag.AlignHCenter)
            self.folders_layout.addWidget(empty_widget, 0, 0, 1, 5)
        else:
            for idx, item in enumerate(items):
                w = QWidget()
                vbox = QVBoxLayout(w)
                vbox.setContentsMargins(10, 10, 10, 10)
                vbox.setSpacing(5)
                icon_label = QLabel()
                icon_label.setPixmap(QIcon("unknow.png").pixmap(64, 64) if os.path.exists("unknow.png") else QIcon().pixmap(64, 64))
                icon_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
                vbox.addWidget(icon_label)
                name_label = QLabel(os.path.basename(item.original_filename()))
                name_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
                name_label.setStyleSheet("font-size: 15px; color: #333;")
                vbox.addWidget(name_label)
                path_label = QLabel(item.original_filename())
                path_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
                path_label.setStyleSheet("font-size: 11px; color: #888;")
                vbox.addWidget(path_label)
                date_label = QLabel(str(item.recycle_date()))
                date_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
                date_label.setStyleSheet("font-size: 11px; color: #888;")
                vbox.addWidget(date_label)
                self.folders_layout.addWidget(w, idx // 5, idx % 5)
            
            # Center items if fewer than 5
            self.center_grid_items()

    def open_disks_dir(self):
        # Clear existing widgets
        for i in reversed(range(self.folders_layout.count())):
            widget = self.folders_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)
        
        # Update breadcrumb to show "Disks"
        self.update_breadcrumb("Disks")
        
        # Get all drives
        drives = self.get_windows_drives()
        
        if not drives:
            # Show empty state if no drives found
            empty_widget = QWidget()
            vbox = QVBoxLayout(empty_widget)
            vbox.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
            icon = QIcon("disk.png") if os.path.exists("disk.png") else QIcon()
            icon_label = QLabel()
            if not icon.isNull():
                icon_label.setPixmap(icon.pixmap(120, 120))
            vbox.addWidget(icon_label, alignment=Qt.AlignmentFlag.AlignHCenter)
            text_label = QLabel("Нет доступных дисков")
            text_label.setStyleSheet("font-size: 22px; color: #b0b8c9; margin-top: 16px;")
            text_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
            vbox.addWidget(text_label, alignment=Qt.AlignmentFlag.AlignHCenter)
            self.folders_layout.addWidget(empty_widget, 0, 0, 1, 5)
        else:
            # Display each drive as a FileWidget
            for idx, drive in enumerate(drives):
                # Create a FileWidget for each drive with is_disk=True
                fw = FileWidget(drive, drive, True, self.file_clicked, main_window=self, scale_factor=self.scale_factor, is_disk=True)
                self.folders_layout.addWidget(fw, idx // 5, idx % 5)
            
            # Center items if fewer than 5
            self.center_grid_items()
        
        self.folders_widget.adjustSize()
        self.scroll.verticalScrollBar().setValue(0)
        self.back_btn.setEnabled(len(self.history) > 0)

    def update_disk_tabs(self):
        while self.disk_tabbar.count() > 0:
            self.disk_tabbar.removeTab(self.disk_tabbar.count() - 1)
        drives = self.get_windows_drives()
        for i, drive in enumerate(drives):
            self.disk_tabbar.addTab(drive)
            if self.current_path.lower().startswith(drive.lower()):
                self.disk_tabbar.setCurrentIndex(i)

    def get_windows_drives(self):
        drives = []
        if sys.platform.startswith("win"):
            bitmask = ctypes.windll.kernel32.GetLogicalDrives()
            for letter in string.ascii_uppercase:
                if bitmask & 1:
                    drives.append(f"{letter}:/")
                bitmask >>= 1
        return drives

    def on_disk_tab_clicked(self, index):
        drive = self.disk_tabbar.tabText(index)
        self.open_dir(drive, add_history=True)

    def animate_button_press(self, button, pressed):
        """Animate button press effect"""
        if pressed:
            # Button press animation - slightly darker background
            button.setStyleSheet("""
                QPushButton {
                    font-size: 16px;
                    color: #444;
                    padding: 10px 0 10px 24px;
                    border: none;
                    text-align: left;
                    border-radius: 8px;
                    background: #d9e6ff;
                }
                QPushButton:hover {
                    background: #e6f0ff;
                }
            """)
        else:
            # Button release animation - return to normal
            button.setStyleSheet("""
                QPushButton {
                    font-size: 16px;
                    color: #444;
                    padding: 10px 0 10px 24px;
                    border: none;
                    text-align: left;
                    border-radius: 8px;
                    background: transparent;
                }
                QPushButton:hover {
                    background: #e6f0ff;
                }
            """)

class CustomDialog(QFrame):
    def __init__(self, title, message, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setStyleSheet("background: transparent;")
        self.setFixedSize(400, 200)
        
        # Main container
        self.container = QFrame()
        self.container.setStyleSheet("""
            QFrame {
                background: #fff;
                border-radius: 16px;
                border: 1px solid #e0e4ea;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        layout.addWidget(self.container)
        
        # Container layout
        container_layout = QVBoxLayout(self.container)
        container_layout.setContentsMargins(20, 20, 20, 20)
        container_layout.setSpacing(15)
        
        # Title
        self.title_label = QLabel(title)
        self.title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #222;")
        container_layout.addWidget(self.title_label)
        
        # Message
        self.message_label = QLabel(message)
        self.message_label.setStyleSheet("font-size: 15px; color: #444;")
        self.message_label.setWordWrap(True)
        container_layout.addWidget(self.message_label)
        
        # Buttons layout
        self.buttons_layout = QHBoxLayout()
        self.buttons_layout.setSpacing(10)
        container_layout.addLayout(self.buttons_layout)
        
        # Make draggable
        self.drag_position = None
        self.drag_start_position = None
    
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            # Check if we're clicking on a button or other interactive element
            widget = self.childAt(event.pos())
            if widget and (isinstance(widget, QPushButton) or widget.parent() and isinstance(widget.parent(), QPushButton)):
                # Clicked on a button, don't start dragging
                event.ignore()
                return
            # Clicked on the container, start dragging
            self.drag_start_position = event.position().toPoint()
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
    
    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and self.drag_position is not None:
            # Check if we've moved enough to consider it a drag operation
            if self.drag_start_position is not None:
                distance = (event.position().toPoint() - self.drag_start_position).manhattanLength()
                if distance < 10:  # Less than 10 pixels movement, still consider it a click
                    return
            self.move(event.globalPosition().toPoint() - self.drag_position)
    
    
    def mouseReleaseEvent(self, event):
        self.drag_position = None
        self.drag_start_position = None
    
    def add_button(self, text, role=None):
        button = QPushButton(text)
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.setFixedSize(80, 32)
        
        if role == "accept":
            button.setStyleSheet("""
                QPushButton {
                    background: #1a73e8;
                    color: white;
                    border: none;
                    border-radius: 8px;
                    font-size: 14px;
                }
                QPushButton:hover {
                    background: #0d62c9;
                }
            """)
        elif role == "reject":
            button.setStyleSheet("""
                QPushButton {
                    background: #f5f6fa;
                    color: #444;
                    border: 1px solid #e0e4ea;
                    border-radius: 8px;
                    font-size: 14px;
                }
                QPushButton:hover {
                    background: #e6f0ff;
                }
            """)
        else:
            button.setStyleSheet("""
                QPushButton {
                    background: #f5f6fa;
                    color: #444;
                    border: 1px solid #e0e4ea;
                    border-radius: 8px;
                    font-size: 14px;
                }
                QPushButton:hover {
                    background: #e6f0ff;
                }
            """)
        
        self.buttons_layout.addWidget(button)
        return button
    
    def exec(self):
        # Show the dialog as a modal window
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.show()
        
        # Use the application's event loop
        from PyQt6.QtCore import QEventLoop, QTimer
        loop = QEventLoop()
        
        # Create a timer to periodically check if the dialog is hidden
        timer = QTimer()
        timer.setInterval(50)  # Check every 50ms
        
        # Flag to track when the dialog is hidden
        dialog_hidden = [False]
        
        # Timer callback to check if dialog is hidden
        def check_hidden():
            if not self.isVisible():
                dialog_hidden[0] = True
                loop.quit()
                
        timer.timeout.connect(check_hidden)
        timer.start()
        
        # Run the event loop until the dialog is hidden
        loop.exec()
        
        # Clean up
        timer.stop()
        timer.deleteLater()
        
        # Return the result (if the dialog has a result attribute)
        if hasattr(self, 'result'):
            return self.result
        return False
class WarningDialog(CustomDialog):
    def __init__(self, title, message, parent=None):
        super().__init__(title, message, parent)
        self.setFixedSize(400, 200)
        
        # Add warning icon
        icon_label = QLabel("⚠")
        icon_label.setStyleSheet("font-size: 24px; color: #ff9800;")
        self.layout().itemAt(0).widget().layout().insertWidget(0, icon_label)
        
        # OK button
        ok_button = self.add_button("OK", "accept")
        ok_button.clicked.connect(self.accept)
        self.buttons_layout.insertStretch(0)
    
    def accept(self):
        self.close()

class ErrorDialog(CustomDialog):
    def __init__(self, title, message, parent=None):
        super().__init__(title, message, parent)
        self.setFixedSize(400, 200)
        
        # Add error icon
        icon_label = QLabel("❌")
        icon_label.setStyleSheet("font-size: 24px; color: #f44336;")
        self.layout().itemAt(0).widget().layout().insertWidget(0, icon_label)
        
        # OK button
        ok_button = self.add_button("OK", "accept")
        ok_button.clicked.connect(self.accept)
        self.buttons_layout.insertStretch(0)
    
    def accept(self):
        self.close()

class QuestionDialog(CustomDialog):
    def __init__(self, title, message, parent=None):
        super().__init__(title, message, parent)
        self.setFixedSize(400, 200)
        self.result = False
        
        # Add question icon
        icon_label = QLabel("❓")
        icon_label.setStyleSheet("font-size: 24px; color: #1a73e8;")
        self.layout().itemAt(0).widget().layout().insertWidget(0, icon_label)
        
        # Yes/No buttons
        yes_button = self.add_button("Да", "accept")
        no_button = self.add_button("Нет", "reject")
        
        yes_button.clicked.connect(self.accept)
        no_button.clicked.connect(self.reject)
        
        self.buttons_layout.insertStretch(0)
    
    
    def accept(self):
        self.result = True
        self.hide()
    
    def reject(self):
        self.result = False
        self.hide()
class InformationDialog(CustomDialog):
    def __init__(self, title, message, parent=None):
        super().__init__(title, message, parent)
        self.setFixedSize(400, 250)
        
        # Add info icon
        icon_label = QLabel("ℹ")
        icon_label.setStyleSheet("font-size: 24px; color: #1a73e8;")
        self.layout().itemAt(0).widget().layout().insertWidget(0, icon_label)
        
        # OK button
        ok_button = self.add_button("OK", "accept")
        ok_button.clicked.connect(self.accept)
        self.buttons_layout.insertStretch(0)
    
    def accept(self):
        self.close()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CustomWindow()
    window.setWindowTitle("Maini file manager")
    window.show()
    sys.exit(app.exec())
