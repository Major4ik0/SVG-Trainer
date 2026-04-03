# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QLabel,
                             QLineEdit, QPushButton)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont


class LoginDialog(QDialog):
    login_successful = pyqtSignal()

    def __init__(self, auth_manager, parent=None):
        super().__init__(parent)
        self.auth_manager = auth_manager
        self.setWindowTitle("Вход в СВГ-Тренажер")
        self.setFixedSize(500, 500)
        self.setModal(True)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(20)

        # Заголовок
        title = QLabel("СВГ-Тренажер")
        title_font = QFont()
        title_font.setPointSize(32)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        layout.addSpacing(30)

        # Форма входа
        form_layout = QVBoxLayout()
        form_layout.setSpacing(15)

        # Логин
        self.username_edit = QLineEdit()
        self.username_edit.setPlaceholderText("👤 Логин")
        self.username_edit.setMinimumHeight(40)
        form_layout.addWidget(self.username_edit)

        # Пароль
        self.password_edit = QLineEdit()
        self.password_edit.setPlaceholderText("🔒 Пароль")
        self.password_edit.setEchoMode(QLineEdit.Password)
        self.password_edit.setMinimumHeight(40)
        form_layout.addWidget(self.password_edit)

        layout.addLayout(form_layout)
        layout.addSpacing(20)

        # Кнопка входа
        self.login_button = QPushButton("🚀 Войти в систему")
        self.login_button.setMinimumHeight(50)
        self.login_button.clicked.connect(self.login)
        layout.addWidget(self.login_button)

        # Сообщение об ошибке
        self.error_label = QLabel("")
        self.error_label.setStyleSheet("color: #e74c3c;")
        self.error_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.error_label)

        layout.addStretch()
        self.setLayout(layout)

        # Применяем стили
        self.setStyleSheet("""
            QDialog {
                background-color: #f5f5f5;
            }
            QLineEdit {
                padding: 8px;
                border: 2px solid #bdc3c7;
                border-radius: 8px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border-color: #3498db;
            }
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)

    def login(self):
        username = self.username_edit.text().strip()
        password = self.password_edit.text().strip()

        if not username or not password:
            self.error_label.setText("❌ Введите логин и пароль")
            return

        if self.auth_manager.login(username, password):
            self.login_successful.emit()
            self.accept()
        else:
            self.error_label.setText("❌ Неверный логин или пароль")

from PyQt5.QtCore import Qt


def get_background_style(image_path="background.jpg"):
    """Получение стилей с фоновым изображением"""
    return f"""
    QMainWindow, QDialog {{
        background-image: url({image_path});
        background-position: center;
        background-repeat: no-repeat;
        background-attachment: fixed;
    }}

    QLabel {{
        color: #cdd6f4;
        background-color: rgba(49, 50, 68, 0.7);
        border-radius: 8px;
        padding: 5px;
    }}

    QPushButton {{
        background-color: rgba(137, 180, 250, 0.9);
        color: #1e1e2e;
        border: none;
        border-radius: 8px;
        padding: 8px 16px;
        font-weight: bold;
    }}

    QPushButton:hover {{
        background-color: rgba(180, 190, 254, 0.9);
    }}

    QTabWidget::pane {{
        background-color: rgba(49, 50, 68, 0.85);
        border: 2px solid #45475a;
        border-radius: 10px;
    }}

    QTabBar::tab {{
        background-color: rgba(69, 71, 90, 0.9);
        color: #cdd6f4;
        padding: 10px 20px;
        margin-right: 5px;
        border-top-left-radius: 8px;
        border-top-right-radius: 8px;
    }}

    QTabBar::tab:selected {{
        background-color: rgba(137, 180, 250, 0.9);
        color: #1e1e2e;
    }}

    QScrollArea {{
        background-color: transparent;
        border: none;
    }}

    QFrame {{
        background-color: rgba(49, 50, 68, 0.85);
        border-radius: 10px;
    }}

    QLineEdit, QTextEdit {{
        background-color: rgba(69, 71, 90, 0.9);
        color: #cdd6f4;
        border: 1px solid #6c7086;
        border-radius: 6px;
        padding: 8px;
    }}

    QLineEdit:focus, QTextEdit:focus {{
        border-color: #89b4fa;
    }}

    QTableWidget {{
        background-color: rgba(49, 50, 68, 0.85);
        color: #cdd6f4;
        gridline-color: #45475a;
        selection-background-color: #89b4fa;
    }}

    QHeaderView::section {{
        background-color: rgba(69, 71, 90, 0.9);
        color: #cdd6f4;
        padding: 8px;
        border: 1px solid #6c7086;
    }}

    QCheckBox {{
        color: #cdd6f4;
        spacing: 12px;
        font-size: 14px;
        padding: 8px;
        background-color: rgba(49, 50, 68, 0.7);
        border-radius: 5px;
    }}

    QCheckBox::indicator {{
        width: 20px;
        height: 20px;
        border-radius: 5px;
        border: 2px solid #89b4fa;
        background-color: #313244;
    }}

    QCheckBox::indicator:checked {{
        background-color: #a6e3a1;
        border-color: #a6e3a1;
    }}

    QProgressBar {{
        border: none;
        border-radius: 10px;
        background-color: rgba(49, 50, 68, 0.8);
        text-align: center;
        color: #cdd6f4;
        font-weight: bold;
    }}

    QProgressBar::chunk {{
        background-color: #89b4fa;
        border-radius: 10px;
    }}

    QMessageBox {{
        background-color: #1e1e2e;
    }}
    """