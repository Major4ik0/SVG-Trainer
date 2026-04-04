# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QScrollArea, QWidget, QSlider,
                             QFrame, QProgressBar)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPixmap, QFont, QKeyEvent
import fitz  # PyMuPDF
import os


class PDFViewer(QWidget):
    """Встроенный просмотрщик PDF файлов"""

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
        layout.setSpacing(5)

        # Панель управления
        control_panel = QFrame()
        control_panel.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border-bottom: 1px solid #dee2e6;
                padding: 10px;
            }
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 6px 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QLabel {
                color: #2c3e50;
            }
        """)
        control_layout = QHBoxLayout(control_panel)

        # Кнопки навигации
        self.prev_btn = QPushButton("◀ Предыдущая")
        self.prev_btn.clicked.connect(self.prev_page)
        self.prev_btn.setEnabled(False)
        control_layout.addWidget(self.prev_btn)

        self.next_btn = QPushButton("Следующая ▶")
        self.next_btn.clicked.connect(self.next_page)
        self.next_btn.setEnabled(False)
        control_layout.addWidget(self.next_btn)

        control_layout.addSpacing(20)

        # Информация о странице
        self.page_label = QLabel("Страница: 0 / 0")
        self.page_label.setFont(QFont("Arial", 10, QFont.Bold))
        control_layout.addWidget(self.page_label)

        control_layout.addStretch()

        # Масштаб
        zoom_out_btn = QPushButton("🔍-")
        zoom_out_btn.clicked.connect(self.zoom_out)
        control_layout.addWidget(zoom_out_btn)

        self.zoom_label = QLabel("100%")
        self.zoom_label.setMinimumWidth(50)
        self.zoom_label.setAlignment(Qt.AlignCenter)
        control_layout.addWidget(self.zoom_label)

        zoom_in_btn = QPushButton("🔍+")
        zoom_in_btn.clicked.connect(self.zoom_in)
        control_layout.addWidget(zoom_in_btn)

        layout.addWidget(control_panel)

        # Область для отображения страницы
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                background-color: #e9ecef;
                border: none;
            }
        """)

        self.page_container = QWidget()
        self.page_layout = QVBoxLayout(self.page_container)
        self.page_layout.setAlignment(Qt.AlignCenter)

        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("background-color: white; border-radius: 5px;")
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
            self.image_label.setStyleSheet("color: #e74c3c; padding: 40px;")

    def update_page(self):
        """Обновление отображения текущей страницы"""
        if not self.doc:
            return

        try:
            page = self.doc[self.current_page]

            # Рассчитываем размер с учетом масштаба
            zoom_matrix = fitz.Matrix(self.zoom, self.zoom)
            pix = page.get_pixmap(matrix=zoom_matrix, alpha=False)

            # Конвертируем в QPixmap
            img_data = pix.tobytes("png")
            pixmap = QPixmap()
            pixmap.loadFromData(img_data)

            # Масштабируем под размер окна, если нужно
            max_width = self.scroll_area.width() - 20
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
        """При изменении размера окна перерисовываем страницу"""
        super().resizeEvent(event)
        if self.doc:
            QTimer.singleShot(100, self.update_page)


class ImageViewer(QWidget):
    """Встроенный просмотрщик изображений"""

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
        layout.setSpacing(5)

        # Панель управления
        control_panel = QFrame()
        control_panel.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border-bottom: 1px solid #dee2e6;
                padding: 10px;
            }
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 6px 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QLabel {
                color: #2c3e50;
            }
        """)
        control_layout = QHBoxLayout(control_panel)

        control_layout.addStretch()

        # Масштаб
        zoom_out_btn = QPushButton("🔍-")
        zoom_out_btn.clicked.connect(self.zoom_out)
        control_layout.addWidget(zoom_out_btn)

        self.zoom_label = QLabel("100%")
        self.zoom_label.setMinimumWidth(50)
        self.zoom_label.setAlignment(Qt.AlignCenter)
        control_layout.addWidget(self.zoom_label)

        zoom_in_btn = QPushButton("🔍+")
        zoom_in_btn.clicked.connect(self.zoom_in)
        control_layout.addWidget(zoom_in_btn)

        reset_zoom_btn = QPushButton("⟳ Сброс")
        reset_zoom_btn.clicked.connect(self.reset_zoom)
        control_layout.addWidget(reset_zoom_btn)

        control_layout.addStretch()

        layout.addWidget(control_panel)

        # Область для изображения
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                background-color: #e9ecef;
                border: none;
            }
        """)

        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("background-color: white;")
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
            self.image_label.setStyleSheet("color: #e74c3c; padding: 40px;")

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
    """Диалог для просмотра материалов (PDF, изображения, текст)"""

    def __init__(self, material, parent=None):
        super().__init__(parent)
        self.material = material
        self.setWindowTitle(f"📖 Просмотр: {material['filename']}")
        self.setMinimumSize(1000, 800)
        self.resize(1200, 900)
        self.setModal(True)

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
                background-color: #2c3e50;
                color: white;
                padding: 15px;
            }
            QLabel {
                color: white;
            }
        """)
        info_layout = QHBoxLayout(info_panel)

        # Название
        title_label = QLabel(f"📄 {self.material['filename']}")
        title_label.setFont(QFont("Arial", 14, QFont.Bold))
        info_layout.addWidget(title_label)

        info_layout.addStretch()

        # Кнопка закрытия
        close_btn = QPushButton("✖ Закрыть")
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        close_btn.clicked.connect(self.close)
        info_layout.addWidget(close_btn)

        layout.addWidget(info_panel)

        # Область содержимого
        self.content_area = QWidget()
        self.content_layout = QVBoxLayout(self.content_area)
        self.content_layout.setContentsMargins(0, 0, 0, 0)

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
            # Встраиваем PDF просмотрщик
            if os.path.exists(content):
                viewer = PDFViewer(content)
                self.content_layout.addWidget(viewer)
            else:
                self.show_error(f"PDF файл не найден: {content}")

        elif file_type == 'image':
            # Встраиваем просмотрщик изображений
            if os.path.exists(content):
                viewer = ImageViewer(content)
                self.content_layout.addWidget(viewer)
            else:
                self.show_error(f"Изображение не найдено: {content}")

        else:  # text
            # Текстовый просмотр с прокруткой
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setStyleSheet("""
                QScrollArea {
                    background-color: #f8f9fa;
                    border: none;
                }
            """)

            text_widget = QWidget()
            text_layout = QVBoxLayout(text_widget)

            text_label = QLabel(content)
            text_label.setWordWrap(True)
            text_label.setStyleSheet("""
                QLabel {
                    background-color: white;
                    padding: 30px;
                    font-size: 14px;
                    line-height: 1.6;
                    color: #2c3e50;
                }
            """)
            text_label.setTextFormat(Qt.RichText)

            text_layout.addWidget(text_label)
            text_layout.addStretch()

            scroll.setWidget(text_widget)
            self.content_layout.addWidget(scroll)

    def show_error(self, message):
        """Отображение ошибки"""
        error_label = QLabel(f"❌ {message}")
        error_label.setAlignment(Qt.AlignCenter)
        error_label.setStyleSheet("""
            QLabel {
                color: #e74c3c;
                font-size: 16px;
                padding: 50px;
                background-color: #f8f9fa;
            }
        """)
        self.content_layout.addWidget(error_label)