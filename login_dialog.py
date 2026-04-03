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
        title.setStyleSheet("color: #2c3e50; background-color: transparent;")
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
        self.error_label.setStyleSheet("color: #e74c3c; background-color: transparent;")
        self.error_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.error_label)

        layout.addStretch()
        self.setLayout(layout)

        # Применяем стили
        self.setStyleSheet("""
            QDialog {
                background-color: rgba(255, 255, 255, 0.95);
            }
            QLabel {
                color: #2c3e50;
                background-color: transparent;
            }
            QLineEdit {
                padding: 8px;
                border: 2px solid #bdc3c7;
                border-radius: 8px;
                font-size: 14px;
                background-color: white;
                color: #2c3e50;
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
                padding: 10px;
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

