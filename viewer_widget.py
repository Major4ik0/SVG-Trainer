# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QScrollArea, QWidget, QSlider,
                             QFrame, QProgressBar, QToolButton)
from PyQt5.QtCore import Qt, QTimer, QSize
from PyQt5.QtGui import QPixmap, QFont, QKeyEvent, QIcon, QPalette, QLinearGradient, QColor
import fitz  # PyMuPDF
import os


class PDFViewer(QWidget):
    """Встроенный просмотрщик PDF файлов с улучшенным дизайном"""

    def __init__(self, pdf_path, parent=None):
        super().__init__(parent)
        self.pdf_path = pdf_path
        self.doc = None
        self.current_page = 0
        self.total_pages = 0
        self.zoom = 1.0
        self.setup_ui()
        self.load_pdf()

    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Панель управления с градиентом
        control_panel = QFrame()
        control_panel.setStyleSheet("""
            QFrame {
                background-color: #b0c4de;
                padding: 12px;
            }
            QPushButton {
                background-color: rgba(255, 255, 255, 0.2);
                color: #000;
                border: 1px solid rgba(255, 255, 255, 0.3);
                border-radius: 8px;
                padding: 8px 16px;
                font-weight: bold;
                font-size: 13px;
                min-width: 150px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.3);
                border-color: white;
            }
            QPushButton:pressed {
                background-color: rgba(255, 255, 255, 0.1);
            }
            QPushButton:disabled {
                background-color: rgba(255, 255, 255, 0.1);
                color: rgba(255, 255, 255, 0.5);
            }
            QLabel {
                color: white;
                font-weight: bold;
            }
        """)
        control_layout = QHBoxLayout(control_panel)
        control_layout.setSpacing(15)

        # Кнопки навигации (одинаковый стиль с кнопками масштаба)
        self.prev_btn = QPushButton("◀ Предыдущая")
        self.prev_btn.setFixedSize(120, 34)
        self.prev_btn.clicked.connect(self.prev_page)
        self.prev_btn.setEnabled(False)
        self.prev_btn.setStyleSheet(
            "color: #000;"
        )
        control_layout.addWidget(self.prev_btn)

        self.next_btn = QPushButton("Следующая ▶")
        self.next_btn.setFixedSize(120, 34)
        self.next_btn.clicked.connect(self.next_page)
        self.next_btn.setEnabled(False)
        self.next_btn.setStyleSheet(
            "color: #000;"
        )
        control_layout.addWidget(self.next_btn)

        control_layout.addSpacing(20)

        # Информация о странице
        page_frame = QFrame()
        page_frame.setStyleSheet("""
            QFrame {
                background-color: rgba(0, 0, 0, 0.3);
                border-radius: 15px;
                padding: 5px 15px;
            }
        """)
        page_layout = QHBoxLayout(page_frame)
        page_layout.setContentsMargins(10, 5, 10, 5)

        self.page_label = QLabel("Страница: 0 / 0")
        self.page_label.setFont(QFont("Segoe UI", 11, QFont.Bold))
        page_layout.addWidget(self.page_label)
        control_layout.addWidget(page_frame)

        control_layout.addStretch()

        # Масштаб (кнопки с таким же стилем)
        zoom_frame = QFrame()
        zoom_frame.setStyleSheet("""
            QFrame {
                background-color: rgba(0, 0, 0, 0.3);
                border-radius: 20px;
                padding: 3px;
            }
        """)
        zoom_layout = QHBoxLayout(zoom_frame)
        zoom_layout.setSpacing(5)
        zoom_layout.setContentsMargins(8, 3, 8, 3)

        zoom_out_btn = QPushButton("−")
        zoom_out_btn.setFixedSize(34, 34)
        zoom_out_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.2);
                border-radius: 17px;
                font-size: 18px;
                font-weight: bold;
                padding: 0;
            }
        """)
        zoom_out_btn.clicked.connect(self.zoom_out)
        zoom_layout.addWidget(zoom_out_btn)

        self.zoom_label = QLabel("100%")
        self.zoom_label.setMinimumWidth(50)
        self.zoom_label.setAlignment(Qt.AlignCenter)
        self.zoom_label.setFont(QFont("Segoe UI", 11, QFont.Bold))
        zoom_layout.addWidget(self.zoom_label)

        zoom_in_btn = QPushButton("+")
        zoom_in_btn.setFixedSize(34, 34)
        zoom_in_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.2);
                border-radius: 17px;
                font-size: 18px;
                font-weight: bold;
                padding: 0;
            }
        """)
        zoom_in_btn.clicked.connect(self.zoom_in)
        zoom_layout.addWidget(zoom_in_btn)

        control_layout.addWidget(zoom_frame)

        layout.addWidget(control_panel)

        # Область для отображения страницы
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                background-color: #f5f5f5;
                border: none;
            }
            QScrollBar:vertical {
                background: #e0e0e0;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background: #3498db;
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background: #2980b9;
            }
            QScrollBar:horizontal {
                background: #e0e0e0;
                height: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:horizontal {
                background: #3498db;
                border-radius: 6px;
                min-width: 20px;
            }
            QScrollBar::handle:horizontal:hover {
                background: #2980b9;
            }
        """)

        self.page_container = QWidget()
        self.page_container.setStyleSheet("background-color: #f5f5f5;")
        self.page_layout = QVBoxLayout(self.page_container)
        self.page_layout.setAlignment(Qt.AlignCenter)
        self.page_layout.setContentsMargins(20, 20, 20, 20)

        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("""
            QLabel {
                background-color: white;
                border-radius: 12px;
            }
        """)
        self.page_layout.addWidget(self.image_label)

        self.scroll_area.setWidget(self.page_container)
        layout.addWidget(self.scroll_area)

        self.setLayout(layout)

    def load_pdf(self):
        """Загрузка PDF файла"""
        try:
            self.doc = fitz.open(self.pdf_path)
            self.total_pages = len(self.doc)
            self.current_page = 0
            self.update_page()
            self.prev_btn.setEnabled(False)
            self.next_btn.setEnabled(self.total_pages > 1)
        except Exception as e:
            self.image_label.setText(f"❌ Ошибка загрузки PDF:\n{str(e)}")
            self.image_label.setStyleSheet(
                "color: #e74c3c; padding: 40px; background-color: white; border-radius: 12px;")

    def update_page(self):
        """Обновление отображения текущей страницы"""
        if not self.doc:
            return

        try:
            page = self.doc[self.current_page]
            zoom_matrix = fitz.Matrix(self.zoom, self.zoom)
            pix = page.get_pixmap(matrix=zoom_matrix, alpha=False)
            img_data = pix.tobytes("png")
            pixmap = QPixmap()
            pixmap.loadFromData(img_data)

            max_width = self.scroll_area.width() - 40
            if pixmap.width() > max_width:
                pixmap = pixmap.scaledToWidth(max_width, Qt.SmoothTransformation)

            self.image_label.setPixmap(pixmap)
            self.page_label.setText(f"Страница: {self.current_page + 1} / {self.total_pages}")
            self.zoom_label.setText(f"{int(self.zoom * 100)}%")
        except Exception as e:
            self.image_label.setText(f"❌ Ошибка отображения страницы: {str(e)}")

    def prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.update_page()
            self.next_btn.setEnabled(True)
            self.prev_btn.setEnabled(self.current_page > 0)

    def next_page(self):
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
            self.update_page()
            self.prev_btn.setEnabled(True)
            self.next_btn.setEnabled(self.current_page < self.total_pages - 1)

    def zoom_in(self):
        self.zoom = min(self.zoom + 0.25, 3.0)
        self.update_page()

    def zoom_out(self):
        self.zoom = max(self.zoom - 0.25, 0.5)
        self.update_page()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.doc:
            QTimer.singleShot(100, self.update_page)


class ImageViewer(QWidget):
    """Встроенный просмотрщик изображений с улучшенным дизайном"""

    def __init__(self, image_path, parent=None):
        super().__init__(parent)
        self.image_path = image_path
        self.zoom = 1.0
        self.original_pixmap = None
        self.setup_ui()
        self.load_image()

    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Панель управления с градиентом
        control_panel = QFrame()
        control_panel.setStyleSheet("""
            QFrame {
                background-color: #b0c4de;
                padding: 12px;
            }
            QPushButton {
                background-color: rgba(255, 255, 255, 0.2);
                color: #000;
                border: 1px solid rgba(255, 255, 255, 0.3);
                border-radius: 8px;
                padding: 8px 16px;
                font-weight: bold;
                font-size: 13px;
                min-width: 150px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.3);
                border-color: white;
            }
            QPushButton:pressed {
                background-color: rgba(255, 255, 255, 0.1);
            }
            QLabel {
                color: white;
                font-weight: bold;
            }
        """)
        control_layout = QHBoxLayout(control_panel)
        control_layout.setSpacing(15)

        control_layout.addStretch()

        # Масштаб
        zoom_frame = QFrame()
        zoom_frame.setStyleSheet("""
            QFrame {
                background-color: rgba(0, 0, 0, 0.3);
                border-radius: 20px;
                padding: 3px;
            }
        """)
        zoom_layout = QHBoxLayout(zoom_frame)
        zoom_layout.setSpacing(5)
        zoom_layout.setContentsMargins(8, 3, 8, 3)

        zoom_out_btn = QPushButton("−")
        zoom_out_btn.setFixedSize(34, 34)
        zoom_out_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.2);
                border-radius: 17px;
                font-size: 18px;
                font-weight: bold;
                padding: 0;
            }
        """)
        zoom_out_btn.clicked.connect(self.zoom_out)
        zoom_layout.addWidget(zoom_out_btn)

        self.zoom_label = QLabel("100%")
        self.zoom_label.setMinimumWidth(50)
        self.zoom_label.setAlignment(Qt.AlignCenter)
        self.zoom_label.setFont(QFont("Segoe UI", 11, QFont.Bold))
        zoom_layout.addWidget(self.zoom_label)

        zoom_in_btn = QPushButton("+")
        zoom_in_btn.setFixedSize(34, 34)
        zoom_in_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.2);
                border-radius: 17px;
                font-size: 18px;
                font-weight: bold;
                padding: 0;
            }
        """)
        zoom_in_btn.clicked.connect(self.zoom_in)
        zoom_layout.addWidget(zoom_in_btn)

        control_layout.addWidget(zoom_frame)

        # Кнопка сброса
        reset_zoom_btn = QPushButton("⟳ Сброс")
        reset_zoom_btn.setFixedSize(80, 34)
        reset_zoom_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.2);
                border-radius: 8px;
                padding: 8px 16px;
                color: #000;
            }
        """)
        reset_zoom_btn.clicked.connect(self.reset_zoom)
        control_layout.addWidget(reset_zoom_btn)

        control_layout.addStretch()

        layout.addWidget(control_panel)

        # Область для изображения
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                background-color: #f5f5f5;
                border: none;
            }
            QScrollBar:vertical {
                background: #e0e0e0;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background: #27ae60;
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background: #219a52;
            }
            QScrollBar:horizontal {
                background: #e0e0e0;
                height: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:horizontal {
                background: #27ae60;
                border-radius: 6px;
                min-width: 20px;
            }
            QScrollBar::handle:horizontal:hover {
                background: #219a52;
            }
        """)

        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("""
            QLabel {
                background-color: white;
                margin: 20px;
                border-radius: 12px;
            }
        """)
        self.scroll_area.setWidget(self.image_label)
        layout.addWidget(self.scroll_area)

        self.setLayout(layout)

    def load_image(self):
        """Загрузка изображения"""
        try:
            self.original_pixmap = QPixmap(self.image_path)
            if self.original_pixmap.isNull():
                raise Exception("Не удалось загрузить изображение")
            self.update_image()
        except Exception as e:
            self.image_label.setText(f"❌ Ошибка загрузки изображения:\n{str(e)}")
            self.image_label.setStyleSheet(
                "color: #e74c3c; padding: 40px; background-color: white; border-radius: 12px;")

    def update_image(self):
        """Обновление изображения с учетом масштаба"""
        if not self.original_pixmap:
            return

        new_width = int(self.original_pixmap.width() * self.zoom)
        new_height = int(self.original_pixmap.height() * self.zoom)

        scaled_pixmap = self.original_pixmap.scaled(
            new_width, new_height,
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )

        self.image_label.setPixmap(scaled_pixmap)
        self.zoom_label.setText(f"{int(self.zoom * 100)}%")

    def zoom_in(self):
        self.zoom = min(self.zoom + 0.25, 3.0)
        self.update_image()

    def zoom_out(self):
        self.zoom = max(self.zoom - 0.25, 0.25)
        self.update_image()

    def reset_zoom(self):
        self.zoom = 1.0
        self.update_image()


class MaterialViewerDialog(QDialog):
    """Диалог для просмотра материалов с улучшенным дизайном"""

    def __init__(self, material, parent=None):
        super().__init__(parent)
        self.material = material
        self.setWindowTitle(f"📖 {material['filename']}")
        self.setMinimumSize(1100, 850)
        self.resize(1300, 950)
        self.setModal(True)

        # Устанавливаем стиль для диалога
        self.setStyleSheet("""
            QDialog {
                background-color: #f0f2f5;
            }
        """)

        self.setup_ui()
        self.load_content()

    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Верхняя панель с информацией
        info_panel = QFrame()
        info_panel.setStyleSheet("""
            QFrame {
                background-color: #8ca9cf;
                padding: 18px 25px;
            }
            QLabel {
                color: white;
            }
        """)
        info_layout = QHBoxLayout(info_panel)
        info_layout.setSpacing(20)

        # Иконка в зависимости от типа
        file_type = self.material.get('file_type', 'text')
        if file_type == 'pdf':
            icon_color = "#e74c3c"
        elif file_type == 'image':
            icon_color = "#27ae60"
        else:
            icon_color = "#3498db"

        icon_label = QLabel()
        icon_label.setFont(QFont("Segoe UI", 28))
        icon_label.setStyleSheet(f"color: {icon_color}; background-color: transparent;")
        info_layout.addWidget(icon_label)

        # Название и информация
        title_widget = QWidget()
        title_layout = QVBoxLayout(title_widget)
        title_layout.setSpacing(5)
        title_layout.setContentsMargins(0, 0, 0, 0)

        title_label = QLabel(self.material['filename'])
        title_label.setFont(QFont("Segoe UI", 32, QFont.Bold))
        title_label.setStyleSheet("color: white; background-color: transparent;")
        title_layout.addWidget(title_label)

        # Тип и размер
        info_text = f"{'PDF документ' if file_type == 'pdf' else 'Изображение' if file_type == 'image' else 'Текстовый документ'}"
        if file_type in ['pdf', 'image'] and os.path.exists(self.material.get('content', '')):
            size = os.path.getsize(self.material['content'])
            if size < 1024:
                size_str = f"{size} B"
            elif size < 1024 * 1024:
                size_str = f"{size / 1024:.1f} KB"
            else:
                size_str = f"{size / (1024 * 1024):.1f} MB"
            info_text += f" • {size_str}"

        info_label = QLabel(info_text)
        info_label.setStyleSheet("color: #171717; font-size: 16px; background-color: transparent;")
        title_layout.addWidget(info_label)

        info_layout.addWidget(title_widget, stretch=1)

        # Кнопка закрытия
        close_btn = QPushButton("✖ Закрыть")
        close_btn.setFixedSize(100, 38)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border-radius: 8px;
                padding: 8px 16px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
            QPushButton:pressed {
                background-color: #a93226;
            }
        """)
        close_btn.clicked.connect(self.close)
        info_layout.addWidget(close_btn)

        layout.addWidget(info_panel)

        # Область содержимого
        self.content_area = QWidget()
        self.content_area.setStyleSheet("background-color: #f0f2f5;")
        self.content_layout = QVBoxLayout(self.content_area)
        self.content_layout.setContentsMargins(10, 10, 10, 10)

        layout.addWidget(self.content_area)
        self.setLayout(layout)

    def load_content(self):
        """Загрузка содержимого в зависимости от типа"""
        file_type = self.material.get('file_type', 'text')
        content = self.material.get('content', '')

        # Очищаем предыдущее содержимое
        for i in reversed(range(self.content_layout.count())):
            widget = self.content_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()

        if file_type == 'pdf':
            if os.path.exists(content):
                viewer = PDFViewer(content)
                self.content_layout.addWidget(viewer)
            else:
                self.show_error(f"PDF файл не найден: {content}")

        elif file_type == 'image':
            if os.path.exists(content):
                viewer = ImageViewer(content)
                self.content_layout.addWidget(viewer)
            else:
                self.show_error(f"Изображение не найдено: {content}")

        else:  # text
            # Текстовый просмотр с улучшенным дизайном
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setStyleSheet("""
                QScrollArea {
                    background-color: #f0f2f5;
                }
                QScrollBar:vertical {
                    background: #e0e0e0;
                    width: 10px;
                    border-radius: 5px;
                }
                QScrollBar::handle:vertical {
                    background: #3498db;
                    border-radius: 5px;
                    min-height: 20px;
                }
                QScrollBar::handle:vertical:hover {
                    background: #2980b9;
                }
            """)

            text_widget = QWidget()
            text_widget.setStyleSheet("background-color: transparent;")
            text_layout = QVBoxLayout(text_widget)
            text_layout.setContentsMargins(30, 30, 30, 30)

            # Контейнер для текста с тенью
            text_container = QFrame()
            text_container.setStyleSheet("""
                QFrame {
                    background-color: white;
                    border-radius: 15px;
                    box-shadow: 0 4px 15px rgba(0,0,0,0.1);
                }
            """)
            container_layout = QVBoxLayout(text_container)
            container_layout.setContentsMargins(30, 30, 30, 30)

            text_label = QLabel(content)
            text_label.setWordWrap(True)
            text_label.setStyleSheet("""
                QLabel {
                    background-color: transparent;
                    font-size: 14px;
                    line-height: 1.8;
                    color: #2c3e50;
                }
            """)
            text_label.setTextFormat(Qt.RichText)
            container_layout.addWidget(text_label)

            text_layout.addWidget(text_container)
            text_layout.addStretch()

            scroll.setWidget(text_widget)
            self.content_layout.addWidget(scroll)

    def show_error(self, message):
        """Отображение ошибки"""
        error_frame = QFrame()
        error_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 15px;
                margin: 50px;
            }
        """)
        error_layout = QVBoxLayout(error_frame)

        error_label = QLabel(f"❌ {message}")
        error_label.setAlignment(Qt.AlignCenter)
        error_label.setStyleSheet("""
            QLabel {
                color: #e74c3c;
                font-size: 16px;
                padding: 50px;
                background-color: transparent;
            }
        """)
        error_layout.addWidget(error_label)

        self.content_layout.addWidget(error_frame)