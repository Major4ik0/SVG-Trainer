from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QPushButton, QTabWidget, QFrame,
                             QScrollArea, QMessageBox, QDialog, QLineEdit,
                             QTextEdit, QCheckBox,
                             QFileDialog, QTableWidget,
                             QTableWidgetItem, QComboBox, QSizePolicy, QApplication)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QPixmap, QColor
from PyQt5.uic import loadUi
import os
import sys
import subprocess
import shutil
from datetime import datetime

from database import Database, QUESTIONS_IMAGES_DIR
from auth_manager import AuthManager
from test_window import TestWindow
from login_dialog import LoginDialog
from statistics_widget import StatisticsChart


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.db = Database()
        self.auth_manager = AuthManager(self.db)

        # Загрузка UI
        ui_path = os.path.join(os.path.dirname(__file__), 'design.ui')
        if os.path.exists(ui_path):
            loadUi(ui_path, self)

        # Подключаем сигналы для кнопок из UI
        self.connect_signals()


        # Инициализация переменных для админских вкладок
        self.admin_users_tab = None
        self.admin_questions_tab = None
        self.admin_materials_tab = None
        self.admin_stats_tab = None

        # Переменная для хранения пути к изображению вопроса
        self.current_question_image_path = None

        # Показываем окно входа
        self.show_login_dialog()

    def connect_signals(self):
        """Подключение сигналов кнопок"""
        if hasattr(self, 'startTestButton'):
            self.startTestButton.clicked.connect(self.start_test)

        if hasattr(self, 'startPracticeButton'):
            self.startPracticeButton.clicked.connect(self.start_practice)

        if hasattr(self, 'refreshStudyButton'):
            self.refreshStudyButton.clicked.connect(self.load_study_materials)

        if hasattr(self, 'refreshStatsButton'):
            self.refreshStatsButton.clicked.connect(self.load_stats)

        if hasattr(self, 'refreshMistakesButton'):
            self.refreshMistakesButton.clicked.connect(self.load_mistakes)

        if hasattr(self, 'changeUserButton'):
            self.changeUserButton.clicked.connect(self.change_user)

        if hasattr(self, 'logoutButton'):
            self.logoutButton.clicked.connect(self.logout)

    def setup_study_tab(self):
        """Настройка вкладки обучения с поддержкой PDF и изображений"""
        layout = QVBoxLayout(self.studyTab)

        # Кнопка добавления материала для админа
        self.addMaterialButton = QPushButton("➕ Добавить учебный материал")
        self.addMaterialButton.clicked.connect(self.add_learning_material)
        layout.addWidget(self.addMaterialButton)

        # Область для материалов
        self.studyScrollArea = QScrollArea()
        self.studyScrollArea.setWidgetResizable(True)
        self.studyContent = QWidget()
        self.studyMaterialsLayout = QVBoxLayout(self.studyContent)
        self.studyScrollArea.setWidget(self.studyContent)
        layout.addWidget(self.studyScrollArea)

        if not self.auth_manager.is_admin():
            self.addMaterialButton.hide()

    def view_user_full_stats(self, user_id):
        """Просмотр полной статистики пользователя (для админа)"""
        user = self.db.get_user_by_id(user_id)
        if not user:
            return

        stats = self.db.get_user_detailed_stats(user_id)
        results = self.db.get_user_test_results(user_id)

        dialog = QDialog(self)
        dialog.setWindowTitle(f"📊 Полная статистика: {user['full_name']}")
        dialog.setMinimumSize(1000, 800)
        dialog.setStyleSheet("""
            QDialog {
                background-color: #1e1e2e;
            }
            QLabel {
                color: #cdd6f4;
            }
            QPushButton {
                background-color: #89b4fa;
                color: #1e1e2e;
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #b4befe;
            }
            QTabWidget::pane {
                background-color: #313244;
                border-radius: 10px;
            }
            QTabBar::tab {
                background-color: #f5f5f5;
                color: #cdd6f4;
                padding: 8px 16px;
                border-radius: 5px;
            }
            QTabBar::tab:selected {
                background-color: #89b4fa;
                color: #1e1e2e;
            }
        """)

        layout = QVBoxLayout(dialog)

        # Информация о пользователе
        info_text = f"""
        <div style='background-color: #ffffff; border-radius: 15px; padding: 20px; text-align: center; border: 1px solid #dee2e6;'>
            <h2 style='color: #2c3e50;'>👤 {user['full_name']}</h2>
            <p style='color: #495057;'><b>Логин:</b> {user['username']}</p>
            <hr style='border-color: #dee2e6;'>
            <table style='width: 100%; margin-top: 10px;'>
                <tr>
                    <td style='padding: 8px; color: #495057;'><b>📝 Всего тестов:</b></td>
                    <td style='padding: 8px; color: #2c3e50;'>{stats['total_tests']}</td>
                    <td style='padding: 8px; color: #495057;'><b>✅ Сдано:</b></td>
                    <td style='padding: 8px; color: #27ae60;'>{stats['passed_tests']}</td>
                </tr>
                <tr>
                    <td style='padding: 8px; color: #495057;'><b>❌ Не сдано:</b></td>
                    <td style='padding: 8px; color: #e74c3c;'>{stats['failed_tests']}</td>
                    <td style='padding: 8px; color: #495057;'><b>📈 Средний балл:</b></td>
                    <td style='padding: 8px; color: #2c3e50;'>{stats['avg_percent']:.1f}%</td>
                </tr>
                <tr>
                    <td style='padding: 8px; color: #495057;'><b>✅ Верных ответов:</b></td>
                    <td style='padding: 8px; color: #2c3e50;'>{stats['total_correct']}</td>
                    <td style='padding: 8px; color: #495057;'><b>📝 Всего вопросов:</b></td>
                    <td style='padding: 8px; color: #2c3e50;'>{stats['total_questions']}</td>
                </tr>
                <tr>
                    <td style='padding: 8px; color: #495057;'><b>🏆 Лучший результат:</b></td>
                    <td style='padding: 8px; color: #27ae60;'>{stats['best_result']:.1f}%</td>
                    <td style='padding: 8px; color: #495057;'><b>📉 Худший результат:</b></td>
                    <td style='padding: 8px; color: #e74c3c;'>{stats['worst_result']:.1f}%</td>
                </tr>
            </table>
        </div>
        """
        info_label = QLabel(info_text)
        info_label.setWordWrap(True)
        layout.addWidget(info_label)

        # Вкладки с графиками и деталями
        tabs = QTabWidget()

        # Вкладка с графиками
        charts_tab = QWidget()
        charts_layout = QVBoxLayout(charts_tab)

        # График динамики
        chart_widget = StatisticsChart()
        chart_widget.update_chart(results, passing_threshold=80)
        charts_layout.addWidget(chart_widget)

        # Круговая диаграмма
        if stats['total_tests'] > 0:
            pie_widget = StatisticsChart()
            pie_widget.create_pie_chart(
                [stats['passed_tests'], stats['failed_tests']],
                ['Успешно', 'Не сдано'],
                'Соотношение результатов'
            )
            charts_layout.addWidget(pie_widget)

        tabs.addTab(charts_tab, "📊 Графики")

        # Вкладка с детальными результатами
        details_tab = QWidget()
        details_layout = QVBoxLayout(details_tab)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)

        for i, result in enumerate(results, 1):
            card = QFrame()
            card.setStyleSheet("background-color: #f5f5f5; border-radius: 10px; margin: 5px; padding: 10px;")

            percent = result['score'] / result['total'] * 100
            status = "✅ Сдано" if result['passed'] else "❌ Не сдано"
            status_color = "#a6e3a1" if result['passed'] else "#f38ba8"

            date_obj = datetime.fromisoformat(result['date'].replace(' ', 'T'))
            date_str = date_obj.strftime('%d.%m.%Y %H:%M:%S')

            card_layout = QVBoxLayout(card)

            title_label = QLabel(f"<b>Попытка #{i}</b> | 📅 {date_str}")
            title_label.setStyleSheet("color: #89b4fa; font-size: 14px;")
            card_layout.addWidget(title_label)

            result_label = QLabel(f"📊 Результат: {result['score']}/{result['total']} ({percent:.1f}%) - {status}")
            result_label.setStyleSheet(f"color: {status_color};")
            card_layout.addWidget(result_label)

            view_btn = QPushButton("📖 Посмотреть детали")
            view_btn.clicked.connect(lambda checked, rid=result['id']: self.view_test_details(rid))
            card_layout.addWidget(view_btn)

            scroll_layout.addWidget(card)

        scroll.setWidget(scroll_widget)
        details_layout.addWidget(scroll)
        tabs.addTab(details_tab, "📋 Детальные результаты")

        layout.addWidget(tabs)

        close_btn = QPushButton("✖ Закрыть")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)

        dialog.exec_()

    def setup_mistakes_tab(self):
        """Настройка вкладки ошибок"""
        layout = QVBoxLayout(self.mistakesTab)

        self.mistakesLabel = QLabel("❗ Вопросы, в которых были допущены ошибки:")
        self.mistakesLabel.setFont(QFont("", 14, QFont.Bold))
        layout.addWidget(self.mistakesLabel)

        self.mistakesList = QScrollArea()
        self.mistakesList.setWidgetResizable(True)
        self.mistakesContent = QWidget()
        self.mistakesLayout = QVBoxLayout(self.mistakesContent)
        self.mistakesList.setWidget(self.mistakesContent)
        layout.addWidget(self.mistakesList)

    def show_login_dialog(self):
        self.hide()
        login_dialog = LoginDialog(self.auth_manager, self)
        login_dialog.login_successful.connect(self.on_login_success)

        # Если диалог был закрыт (через крестик или Esc), выходим из приложения
        if login_dialog.exec_() != QDialog.Accepted:
            QApplication.quit()
            sys.exit(0)

    def update_user_info(self):
        user = self.auth_manager.get_current_user()
        if user and hasattr(self, 'userLabel'):
            self.userLabel.setText(f"👤 {user['full_name']} ({user['username']})")

    def setup_admin_tabs(self):
        if self.auth_manager.is_admin():
            self.admin_users_tab = QWidget()
            self.admin_questions_tab = QWidget()
            self.admin_materials_tab = QWidget()
            self.admin_stats_tab = QWidget()

            self.tabWidget.addTab(self.admin_users_tab, "👥 Пользователи")
            self.tabWidget.addTab(self.admin_questions_tab, "❓ Вопросы")
            self.tabWidget.addTab(self.admin_materials_tab, "📁 Материалы")
            self.tabWidget.addTab(self.admin_stats_tab, "📈 Статистика")

            self.setup_admin_users_tab()
            self.setup_admin_questions_tab()
            self.setup_admin_materials_tab()
            self.setup_admin_stats_tab()

    def setup_admin_users_tab(self):
        """Улучшенный дизайн таблицы пользователей"""
        layout = QVBoxLayout(self.admin_users_tab)

        add_button = QPushButton("➕ Добавить пользователя")
        add_button.clicked.connect(self.add_user_dialog)
        layout.addWidget(add_button)

        # Используем QTableWidget для красивого отображения
        self.users_table = QTableWidget()
        self.users_table.setColumnCount(4)
        self.users_table.setHorizontalHeaderLabels(["ID", "ФИО", "Логин", "Действия"])
        self.users_table.horizontalHeader().setStretchLastSection(True)
        self.users_table.setAlternatingRowColors(True)

        # Настройка ширины колонок
        self.users_table.setColumnWidth(0, 50)  # ID
        self.users_table.setColumnWidth(1, 250)  # ФИО
        self.users_table.setColumnWidth(2, 150)  # Логин
        # Колонка "Действия" растягивается автоматически

        layout.addWidget(self.users_table)

        self.load_users_list()

    def setup_admin_questions_tab(self):
        """Улучшенный дизайн таблицы вопросов"""
        layout = QVBoxLayout(self.admin_questions_tab)

        add_button = QPushButton("➕ Добавить вопрос")
        add_button.clicked.connect(self.add_question_dialog)
        layout.addWidget(add_button)

        # Таблица вопросов
        self.questions_table = QTableWidget()
        self.questions_table.setColumnCount(3)
        self.questions_table.setHorizontalHeaderLabels(["ID", "Вопрос", "Действия"])
        self.questions_table.horizontalHeader().setStretchLastSection(True)
        self.questions_table.setAlternatingRowColors(True)
        layout.addWidget(self.questions_table)

        self.load_questions_list()

    def setup_admin_materials_tab(self):
        layout = QVBoxLayout(self.admin_materials_tab)

        add_button = QPushButton("➕ Добавить учебный материал")
        add_button.clicked.connect(self.add_learning_material)
        layout.addWidget(add_button)

        self.admin_materials_table = QTableWidget()
        self.admin_materials_table.setColumnCount(3)
        self.admin_materials_table.setHorizontalHeaderLabels(["Название", "Тип", "Действия"])
        self.admin_materials_table.horizontalHeader().setStretchLastSection(True)
        self.admin_materials_table.setAlternatingRowColors(True)
        layout.addWidget(self.admin_materials_table)

        self.load_admin_materials()

    def load_users_list(self):
        """Загрузка пользователей в таблицу"""
        self.users_table.setRowCount(0)
        users = self.db.get_all_users()

        for user in users:
            if user['role'] == 'admin':
                continue

            row = self.users_table.rowCount()
            self.users_table.insertRow(row)

            self.users_table.setItem(row, 0, QTableWidgetItem(str(user['id'])))
            self.users_table.setItem(row, 1, QTableWidgetItem(user['full_name']))
            self.users_table.setItem(row, 2, QTableWidgetItem(user['username']))

            # Создаем виджет с кнопками
            buttons_widget = QWidget()
            buttons_layout = QHBoxLayout(buttons_widget)
            buttons_layout.setContentsMargins(0, 0, 0, 0)
            buttons_layout.setSpacing(5)

            # Кнопка редактирования
            edit_btn = QPushButton("✏ Редактировать")
            edit_btn.clicked.connect(lambda checked, uid=user['id']: self.edit_user(uid))
            edit_btn.setStyleSheet("""
                QPushButton {
                    background-color: #f9e2af;
                    color: #1e1e2e;
                    padding: 5px 10px;
                    font-size: 11px;
                }
                QPushButton:hover {
                    background-color: #f9e2af;
                    opacity: 0.8;
                }
            """)

            # Кнопка удаления
            delete_btn = QPushButton("🗑 Удалить")
            delete_btn.clicked.connect(lambda checked, uid=user['id']: self.delete_user(uid))
            delete_btn.setStyleSheet("""
                QPushButton {
                    background-color: #f38ba8;
                    color: #1e1e2e;
                    padding: 5px 10px;
                    font-size: 11px;
                }
                QPushButton:hover {
                    background-color: #f38ba8;
                    opacity: 0.8;
                }
            """)

            buttons_layout.addWidget(edit_btn)
            buttons_layout.addWidget(delete_btn)
            self.users_table.setCellWidget(row, 3, buttons_widget)

    def load_questions_list(self):
        """Загрузка вопросов в таблицу"""
        self.questions_table.setRowCount(0)
        questions = self.db.get_all_questions()

        for q in questions:
            row = self.questions_table.rowCount()
            self.questions_table.insertRow(row)

            self.questions_table.setItem(row, 0, QTableWidgetItem(str(q['id'])))
            self.questions_table.setItem(row, 1, QTableWidgetItem(q['text'][:100] + "..."))

            # Кнопки действий
            buttons_widget = QWidget()
            buttons_layout = QHBoxLayout(buttons_widget)
            buttons_layout.setContentsMargins(0, 0, 0, 0)

            edit_btn = QPushButton("✏ Редактировать")
            edit_btn.clicked.connect(lambda checked, qid=q['id']: self.edit_question(qid))
            delete_btn = QPushButton("🗑 Удалить")
            delete_btn.clicked.connect(lambda checked, qid=q['id']: self.delete_question(qid))

            buttons_layout.addWidget(edit_btn)
            buttons_layout.addWidget(delete_btn)
            self.questions_table.setCellWidget(row, 2, buttons_widget)

    def load_admin_materials(self):
        """Загрузка материалов в таблицу для админа"""
        self.admin_materials_table.setRowCount(0)
        materials = self.db.get_all_learning_materials()

        for material in materials:
            row = self.admin_materials_table.rowCount()
            self.admin_materials_table.insertRow(row)

            self.admin_materials_table.setItem(row, 0, QTableWidgetItem(material['filename']))

            file_type = material['file_type']
            type_icon = "📄" if file_type == 'text' else "🖼" if file_type == 'image' else "📑"
            self.admin_materials_table.setItem(row, 1, QTableWidgetItem(f"{type_icon} {file_type.upper()}"))

            # Кнопка удаления
            delete_btn = QPushButton("🗑 Удалить")
            delete_btn.clicked.connect(lambda checked, mid=material['id']: self.delete_material(mid))
            self.admin_materials_table.setCellWidget(row, 2, delete_btn)

    def load_study_materials(self):
        """Загрузка учебных материалов для обычного пользователя"""
        if hasattr(self, 'studyMaterialsLayout'):
            for i in reversed(range(self.studyMaterialsLayout.count())):
                widget = self.studyMaterialsLayout.itemAt(i).widget()
                if widget:
                    widget.deleteLater()

        materials = self.db.get_all_learning_materials()

        if not materials:
            no_data = QLabel("📭 Нет учебных материалов")
            no_data.setAlignment(Qt.AlignCenter)
            no_data.setStyleSheet("color: #6c7086; padding: 40px; font-size: 16px;")
            self.studyMaterialsLayout.addWidget(no_data)
            return

        for material in materials:
            card = QFrame()
            card.setStyleSheet("""
                QFrame {
                    background-color: #f5f5f5;
                    border-radius: 12px;
                    margin: 8px;
                    padding: 15px;
                }
                QFrame:hover {
                    background-color: #585b70;
                }
            """)

            card_layout = QVBoxLayout(card)

            title = QLabel(f"📄 {material['filename']}")
            title.setFont(QFont("", 14, QFont.Bold))
            title.setStyleSheet("color: #89b4fa;")
            card_layout.addWidget(title)

            if material.get('description'):
                desc = QLabel(material['description'])
                desc.setWordWrap(True)
                desc.setStyleSheet("color: #a6adc8;")
                card_layout.addWidget(desc)

            # Отображение содержимого в зависимости от типа
            if material.get('content'):
                if material['file_type'] == 'image':
                    # Для изображений показываем миниатюру
                    if os.path.exists(material['content']):
                        pixmap = QPixmap(material['content'])
                        if not pixmap.isNull():
                            pixmap = pixmap.scaled(200, 150, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                            img_label = QLabel()
                            img_label.setPixmap(pixmap)
                            img_label.setAlignment(Qt.AlignCenter)
                            card_layout.addWidget(img_label)
                else:
                    content = QLabel(material['content'][:300] + ("..." if len(material['content']) > 300 else ""))
                    content.setWordWrap(True)
                    content.setStyleSheet("color: #cdd6f4;")
                    card_layout.addWidget(content)

            self.studyMaterialsLayout.addWidget(card)

    def load_mistakes(self):
        """Загрузка ошибок пользователя"""
        user = self.auth_manager.get_current_user()
        if not user or not hasattr(self, 'mistakesLayout'):
            return

        for i in reversed(range(self.mistakesLayout.count())):
            widget = self.mistakesLayout.itemAt(i).widget()
            if widget:
                widget.deleteLater()

        mistakes = self.db.get_user_mistakes(user['id'])

        if not mistakes:
            no_mistakes = QLabel("✨ Отлично! Нет повторяющихся ошибок.")
            no_mistakes.setAlignment(Qt.AlignCenter)
            no_mistakes.setStyleSheet("color: #a6e3a1; padding: 40px; font-size: 16px;")
            self.mistakesLayout.addWidget(no_mistakes)
            return

        for mistake in mistakes:
            card = QFrame()
            card.setStyleSheet("background-color: #f5f5f5; border-radius: 12px; margin: 8px; padding: 15px;")

            card_layout = QVBoxLayout(card)

            question = QLabel(f"❓ {mistake['text']}")
            question.setWordWrap(True)
            question.setFont(QFont("", 11, QFont.Bold))
            question.setStyleSheet("color: #f38ba8;")
            card_layout.addWidget(question)

            correct_options = []
            for i in range(4):
                if (mistake['correct_mask'] >> i) & 1:
                    correct_options.append(mistake[f'option{i + 1}'])

            correct_text = f"✅ <b>Правильный ответ:</b> {', '.join(correct_options)}"
            correct_label = QLabel(correct_text)
            correct_label.setWordWrap(True)
            correct_label.setStyleSheet("color: #a6e3a1;")
            card_layout.addWidget(correct_label)

            if mistake.get('explanation'):
                explanation = QLabel(f"💡 <b>Пояснение:</b> {mistake['explanation']}")
                explanation.setWordWrap(True)
                explanation.setStyleSheet("color: #89b4fa;")
                card_layout.addWidget(explanation)

            self.mistakesLayout.addWidget(card)

    def view_user_stats(self, user_id):
        """Просмотр детальной статистики пользователя"""
        user = self.db.get_user_by_id(user_id)
        if not user:
            return

        results = self.db.get_user_test_results(user_id)

        dialog = QDialog(self)
        dialog.setWindowTitle(f"Статистика пользователя {user['full_name']}")
        dialog.setMinimumSize(800, 600)

        layout = QVBoxLayout(dialog)

        # График для пользователя
        chart = StatisticsChart()
        chart.update_chart(results, passing_threshold=80)
        layout.addWidget(chart)

        # Список результатов
        results_list = QScrollArea()
        results_content = QWidget()
        results_layout = QVBoxLayout(results_content)

        for result in results[:20]:
            frame = QFrame()
            frame.setStyleSheet("background-color: #f5f5f5; border-radius: 8px; margin: 5px; padding: 10px;")

            percent = result['score'] / result['total'] * 100
            status = "✅ Сдано" if result['passed'] else "❌ Не сдано"

            date_obj = datetime.fromisoformat(result['date'].replace(' ', 'T'))
            date_str = date_obj.strftime('%d.%m.%Y %H:%M:%S')

            text = QLabel(f"📅 {date_str}\n📊 {result['score']}/{result['total']} ({percent:.1f}%) - {status}")
            text.setWordWrap(True)

            frame_layout = QHBoxLayout(frame)
            frame_layout.addWidget(text)
            results_layout.addWidget(frame)

        results_list.setWidget(results_content)
        results_list.setWidgetResizable(True)
        layout.addWidget(results_list)

        close_btn = QPushButton("Закрыть")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)

        dialog.exec_()

    def add_learning_material(self):
        """Диалог добавления учебного материала с поддержкой PDF и изображений"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Добавление учебного материала")
        dialog.setMinimumSize(500, 500)

        layout = QVBoxLayout(dialog)

        # Название
        filename_edit = QLineEdit()
        filename_edit.setPlaceholderText("Название материала")
        layout.addWidget(filename_edit)

        # Описание
        desc_edit = QTextEdit()
        desc_edit.setPlaceholderText("Описание (необязательно)")
        desc_edit.setMaximumHeight(80)
        layout.addWidget(desc_edit)

        # Тип материала
        type_label = QLabel("Тип материала:")
        layout.addWidget(type_label)

        type_combo = QComboBox()
        type_combo.addItems(["Текст", "Изображение", "PDF"])
        layout.addWidget(type_combo)

        # Содержание (для текста)
        content_edit = QTextEdit()
        content_edit.setPlaceholderText("Содержание материала...")
        content_edit.hide()
        layout.addWidget(content_edit)

        # Кнопка выбора файла (для изображений и PDF)
        file_button = QPushButton("📁 Выбрать файл")
        file_button.hide()
        layout.addWidget(file_button)

        file_path_label = QLabel()
        file_path_label.hide()
        layout.addWidget(file_path_label)

        selected_file_path = None

        def on_type_changed():
            material_type = type_combo.currentText()
            if material_type == "Текст":
                content_edit.show()
                file_button.hide()
                file_path_label.hide()
            else:
                content_edit.hide()
                file_button.show()
                file_path_label.show()

        type_combo.currentTextChanged.connect(on_type_changed)

        def select_file():
            nonlocal selected_file_path
            material_type = type_combo.currentText()
            if material_type == "Изображение":
                file_path, _ = QFileDialog.getOpenFileName(dialog, "Выберите изображение", "",
                                                           "Images (*.png *.jpg *.jpeg *.bmp *.gif)")
                if file_path:
                    selected_file_path = file_path
                    file_path_label.setText(f"Выбран файл: {os.path.basename(file_path)}")
            elif material_type == "PDF":
                file_path, _ = QFileDialog.getOpenFileName(dialog, "Выберите PDF файл", "", "PDF Files (*.pdf)")
                if file_path:
                    selected_file_path = file_path
                    file_path_label.setText(f"Выбран файл: {os.path.basename(file_path)}")

        file_button.clicked.connect(select_file)

        save_button = QPushButton("💾 Сохранить")
        layout.addWidget(save_button)

        def save_material():
            filename = filename_edit.text().strip()
            if not filename:
                QMessageBox.warning(dialog, "Ошибка", "Введите название материала")
                return

            material_type = type_combo.currentText()
            user = self.auth_manager.get_current_user()

            if material_type == "Текст":
                content = content_edit.toPlainText().strip()
                if not content:
                    QMessageBox.warning(dialog, "Ошибка", "Введите содержание материала")
                    return

                self.db.add_learning_material(
                    filename=filename,
                    content=content,
                    file_path="",
                    file_type="text",
                    uploaded_by=user['id'],
                    description=desc_edit.toPlainText().strip()
                )
            else:
                if not selected_file_path:
                    QMessageBox.warning(dialog, "Ошибка", "Выберите файл")
                    return

                # Копируем файл в папку materials
                ext = os.path.splitext(selected_file_path)[1]
                new_filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}{ext}"
                new_path = os.path.join("materials", new_filename)
                shutil.copy2(selected_file_path, new_path)

                file_type = "image" if material_type == "Изображение" else "pdf"
                self.db.add_learning_material(
                    filename=filename,
                    content=new_path,
                    file_path=new_path,
                    file_type=file_type,
                    uploaded_by=user['id'],
                    description=desc_edit.toPlainText().strip()
                )

            dialog.accept()
            self.load_study_materials()
            self.load_admin_materials()
            QMessageBox.information(self, "Успех", "Материал добавлен")

        save_button.clicked.connect(save_material)
        dialog.exec_()

    def add_question_dialog(self):
        """Диалог добавления вопроса с поддержкой изображений"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Добавление вопроса")
        dialog.setMinimumSize(800, 800)

        layout = QVBoxLayout(dialog)

        # Текст вопроса
        question_text = QTextEdit()
        question_text.setPlaceholderText("Текст вопроса...")
        question_text.setMinimumHeight(100)
        layout.addWidget(question_text)

        # Изображение
        image_label = QLabel("Изображение для вопроса (необязательно):")
        layout.addWidget(image_label)

        image_buttons_layout = QHBoxLayout()
        select_image_btn = QPushButton("📁 Выбрать изображение")
        clear_image_btn = QPushButton("🗑 Очистить")
        image_buttons_layout.addWidget(select_image_btn)
        image_buttons_layout.addWidget(clear_image_btn)
        layout.addLayout(image_buttons_layout)

        image_preview = QLabel()
        image_preview.setAlignment(Qt.AlignCenter)
        image_preview.setMinimumHeight(150)
        image_preview.setStyleSheet("background-color: #f5f5f5; border-radius: 8px;")
        layout.addWidget(image_preview)

        self.current_question_image_path = None

        def select_image():
            file_path, _ = QFileDialog.getOpenFileName(dialog, "Выберите изображение", QUESTIONS_IMAGES_DIR,
                                                       "Images (*.png *.jpg *.jpeg *.bmp *.gif)")
            if file_path:
                # Копируем изображение в папку questions_images
                ext = os.path.splitext(file_path)[1]
                new_filename = f"q_{datetime.now().strftime('%Y%m%d_%H%M%S')}{ext}"
                new_path = os.path.join(QUESTIONS_IMAGES_DIR, new_filename)
                shutil.copy2(file_path, new_path)
                self.current_question_image_path = new_path

                pixmap = QPixmap(new_path)
                pixmap = pixmap.scaled(300, 150, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                image_preview.setPixmap(pixmap)

        def clear_image():
            self.current_question_image_path = None
            image_preview.clear()
            image_preview.setText("Изображение не выбрано")

        select_image_btn.clicked.connect(select_image)
        clear_image_btn.clicked.connect(clear_image)
        clear_image()  # Инициализация

        # Варианты ответов
        options_label = QLabel("Варианты ответов:")
        options_label.setFont(QFont("", 12, QFont.Bold))
        layout.addWidget(options_label)

        options = []
        for i in range(4):
            opt_edit = QLineEdit()
            opt_edit.setPlaceholderText(f"Вариант {i + 1}")
            layout.addWidget(opt_edit)
            options.append(opt_edit)

        # Правильные ответы
        correct_label = QLabel("Правильные ответы (можно выбрать несколько):")
        correct_label.setFont(QFont("", 12, QFont.Bold))
        layout.addWidget(correct_label)

        correct_checkboxes = []
        for i in range(4):
            cb = QCheckBox(f"Вариант {i + 1}")
            layout.addWidget(cb)
            correct_checkboxes.append(cb)

        # Пояснение
        explanation_label = QLabel("Пояснение:")
        explanation_label.setFont(QFont("", 12, QFont.Bold))
        layout.addWidget(explanation_label)

        explanation = QTextEdit()
        explanation.setPlaceholderText("Пояснение к правильному ответу...")
        explanation.setMinimumHeight(80)
        layout.addWidget(explanation)

        # Категория
        category_edit = QLineEdit()
        category_edit.setPlaceholderText("Категория (необязательно)")
        layout.addWidget(category_edit)

        save_button = QPushButton("💾 Сохранить вопрос")
        layout.addWidget(save_button)

        def save_question():
            text = question_text.toPlainText().strip()
            if not text:
                QMessageBox.warning(dialog, "Ошибка", "Введите текст вопроса")
                return

            opts = [opt.text().strip() for opt in options]
            if any(not o for o in opts):
                QMessageBox.warning(dialog, "Ошибка", "Заполните все варианты ответов")
                return

            mask = 0
            for i, cb in enumerate(correct_checkboxes):
                if cb.isChecked():
                    mask |= (1 << i)

            if mask == 0:
                QMessageBox.warning(dialog, "Ошибка", "Выберите хотя бы один правильный ответ")
                return

            expl = explanation.toPlainText().strip()
            category = category_edit.text().strip()

            self.db.add_question(text, self.current_question_image_path, opts, mask, expl, category)
            dialog.accept()
            self.load_questions_list()
            QMessageBox.information(self, "Успех", "Вопрос добавлен")

        save_button.clicked.connect(save_question)
        dialog.exec_()

    def edit_question(self, question_id):
        """Редактирование вопроса"""
        q = self.db.get_question_by_id(question_id)
        if not q:
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("Редактирование вопроса")
        dialog.setMinimumSize(800, 800)

        layout = QVBoxLayout(dialog)

        # Текст вопроса
        question_text = QTextEdit()
        question_text.setPlainText(q['text'])
        question_text.setMinimumHeight(100)
        layout.addWidget(question_text)

        # Изображение
        image_label = QLabel("Изображение для вопроса:")
        layout.addWidget(image_label)

        image_buttons_layout = QHBoxLayout()
        select_image_btn = QPushButton("📁 Выбрать изображение")
        clear_image_btn = QPushButton("🗑 Очистить")
        image_buttons_layout.addWidget(select_image_btn)
        image_buttons_layout.addWidget(clear_image_btn)
        layout.addLayout(image_buttons_layout)

        image_preview = QLabel()
        image_preview.setAlignment(Qt.AlignCenter)
        image_preview.setMinimumHeight(150)
        image_preview.setStyleSheet("background-color: #45475a; border-radius: 8px;")
        layout.addWidget(image_preview)

        current_image = q.get('image_path')
        if current_image and os.path.exists(current_image):
            pixmap = QPixmap(current_image)
            pixmap = pixmap.scaled(300, 150, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            image_preview.setPixmap(pixmap)
        else:
            image_preview.setText("Изображение не выбрано")

        def select_image():
            file_path, _ = QFileDialog.getOpenFileName(dialog, "Выберите изображение", QUESTIONS_IMAGES_DIR,
                                                       "Images (*.png *.jpg *.jpeg *.bmp *.gif)")
            if file_path:
                ext = os.path.splitext(file_path)[1]
                new_filename = f"q_{datetime.now().strftime('%Y%m%d_%H%M%S')}{ext}"
                new_path = os.path.join(QUESTIONS_IMAGES_DIR, new_filename)
                shutil.copy2(file_path, new_path)
                current_image = new_path

                pixmap = QPixmap(new_path)
                pixmap = pixmap.scaled(300, 150, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                image_preview.setPixmap(pixmap)

        def clear_image():
            nonlocal current_image
            current_image = None
            image_preview.clear()
            image_preview.setText("Изображение не выбрано")

        select_image_btn.clicked.connect(select_image)
        clear_image_btn.clicked.connect(clear_image)

        # Варианты ответов
        options_label = QLabel("Варианты ответов:")
        options_label.setFont(QFont("", 12, QFont.Bold))
        layout.addWidget(options_label)

        options = []
        for i in range(4):
            opt_edit = QLineEdit()
            opt_edit.setText(q[f'option{i + 1}'])
            opt_edit.setPlaceholderText(f"Вариант {i + 1}")
            layout.addWidget(opt_edit)
            options.append(opt_edit)

        # Правильные ответы
        correct_label = QLabel("Правильные ответы (можно выбрать несколько):")
        correct_label.setFont(QFont("", 12, QFont.Bold))
        layout.addWidget(correct_label)

        correct_checkboxes = []
        for i in range(4):
            cb = QCheckBox(f"Вариант {i + 1}")
            cb.setChecked((q['correct_mask'] >> i) & 1)
            layout.addWidget(cb)
            correct_checkboxes.append(cb)

        # Пояснение
        explanation_label = QLabel("Пояснение:")
        explanation_label.setFont(QFont("", 12, QFont.Bold))
        layout.addWidget(explanation_label)

        explanation = QTextEdit()
        explanation.setPlainText(q.get('explanation', ''))
        explanation.setMinimumHeight(80)
        layout.addWidget(explanation)

        # Категория
        category_edit = QLineEdit()
        category_edit.setText(q.get('category', ''))
        category_edit.setPlaceholderText("Категория (необязательно)")
        layout.addWidget(category_edit)

        save_button = QPushButton("💾 Сохранить изменения")
        layout.addWidget(save_button)

        def save_question():
            text = question_text.toPlainText().strip()
            if not text:
                QMessageBox.warning(dialog, "Ошибка", "Введите текст вопроса")
                return

            opts = [opt.text().strip() for opt in options]
            if any(not o for o in opts):
                QMessageBox.warning(dialog, "Ошибка", "Заполните все варианты ответов")
                return

            mask = 0
            for i, cb in enumerate(correct_checkboxes):
                if cb.isChecked():
                    mask |= (1 << i)

            if mask == 0:
                QMessageBox.warning(dialog, "Ошибка", "Выберите хотя бы один правильный ответ")
                return

            expl = explanation.toPlainText().strip()
            category = category_edit.text().strip()

            self.db.update_question(question_id, text, current_image, opts, mask, expl, category)
            dialog.accept()
            self.load_questions_list()
            QMessageBox.information(self, "Успех", "Вопрос обновлен")

        save_button.clicked.connect(save_question)
        dialog.exec_()

    def delete_material(self, material_id):
        reply = QMessageBox.question(self, "Удаление", "Удалить материал?",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.db.delete_learning_material(material_id)
            self.load_study_materials()
            self.load_admin_materials()

    def delete_user(self, user_id):
        reply = QMessageBox.question(self, "Удаление", "Удалить пользователя?",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.db.delete_user(user_id)
            self.load_users_list()

    def delete_question(self, question_id):
        reply = QMessageBox.question(self, "Удаление", "Удалить вопрос?",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.db.delete_question(question_id)
            self.load_questions_list()

    def add_user_dialog(self):
        """Диалог добавления/редактирования пользователя"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Добавление пользователя")
        dialog.setMinimumSize(400, 400)
        dialog.setStyleSheet("""
            QDialog {
                background-color: #1e1e2e;
            }
            QLabel {
                color: #cdd6f4;
            }
            QLineEdit, QComboBox {
                background-color: #45475a;
                color: #cdd6f4;
                border: 1px solid #6c7086;
                border-radius: 6px;
                padding: 18px;
                font-size: 12px;
            }
            QPushButton {
                background-color: #89b4fa;
                color: #1e1e2e;
                border: none;
                border-radius: 8px;
                padding: 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #b4befe;
            }
        """)

        layout = QVBoxLayout(dialog)
        layout.setSpacing(15)

        # ФИО
        full_name_label = QLabel("ФИО пользователя:")
        layout.addWidget(full_name_label)
        full_name_edit = QLineEdit()
        full_name_edit.setPlaceholderText("Иванов Иван Иванович")
        layout.addWidget(full_name_edit)

        # Логин
        username_label = QLabel("Логин:")
        layout.addWidget(username_label)
        username_edit = QLineEdit()
        username_edit.setPlaceholderText("username")
        layout.addWidget(username_edit)

        # Пароль
        password_label = QLabel("Пароль:")
        layout.addWidget(password_label)
        password_edit = QLineEdit()
        password_edit.setPlaceholderText("пароль")
        password_edit.setEchoMode(QLineEdit.Password)
        layout.addWidget(password_edit)

        # Подтверждение пароля
        confirm_label = QLabel("Подтверждение пароля:")
        layout.addWidget(confirm_label)
        confirm_edit = QLineEdit()
        confirm_edit.setPlaceholderText("повторите пароль")
        confirm_edit.setEchoMode(QLineEdit.Password)
        layout.addWidget(confirm_edit)

        # Роль
        role_label = QLabel("Роль:")
        layout.addWidget(role_label)
        role_combo = QComboBox()
        role_combo.addItems(["user", "admin"])
        layout.addWidget(role_combo)

        layout.addStretch()

        # Кнопки
        buttons_layout = QHBoxLayout()
        save_btn = QPushButton("💾 Сохранить")
        cancel_btn = QPushButton("❌ Отмена")
        buttons_layout.addWidget(save_btn)
        buttons_layout.addWidget(cancel_btn)
        layout.addLayout(buttons_layout)

        def save_user():
            full_name = full_name_edit.text().strip()
            username = username_edit.text().strip()
            password = password_edit.text().strip()
            confirm = confirm_edit.text().strip()
            role = role_combo.currentText()

            if not full_name or not username or not password:
                QMessageBox.warning(dialog, "Ошибка", "Заполните все поля")
                return

            if password != confirm:
                QMessageBox.warning(dialog, "Ошибка", "Пароли не совпадают")
                return

            if self.db.add_user(username, password, role, full_name):
                QMessageBox.information(dialog, "Успех", "Пользователь добавлен")
                dialog.accept()
                self.load_users_list()
            else:
                QMessageBox.warning(dialog, "Ошибка", "Пользователь с таким логином уже существует")

        save_btn.clicked.connect(save_user)
        cancel_btn.clicked.connect(dialog.reject)
        dialog.exec_()

    def edit_user(self, user_id):
        """Редактирование пользователя"""
        user = self.db.get_user_by_id(user_id)
        if not user:
            return

        dialog = QDialog(self)
        dialog.setWindowTitle(f"Редактирование пользователя: {user['username']}")
        dialog.setMinimumSize(400, 450)
        dialog.setStyleSheet("""
            QDialog {
                background-color: #1e1e2e;
            }
            QLabel {
                color: #cdd6f4;
            }
            QLineEdit, QComboBox {
                background-color: #45475a;
                color: #cdd6f4;
                border: 1px solid #6c7086;
                border-radius: 6px;
                padding: 20px;
                font-size: 12px;
            }
            QCheckBox {
                color: #cdd6f4;
            }
            QPushButton {
                background-color: #89b4fa;
                color: #1e1e2e;
                border: none;
                border-radius: 8px;
                padding: 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #b4befe;
            }
        """)

        layout = QVBoxLayout(dialog)
        layout.setSpacing(15)

        # ФИО
        full_name_label = QLabel("ФИО пользователя:")
        layout.addWidget(full_name_label)
        full_name_edit = QLineEdit()
        full_name_edit.setText(user['full_name'])
        layout.addWidget(full_name_edit)

        # Логин
        username_label = QLabel("Логин:")
        layout.addWidget(username_label)
        username_edit = QLineEdit()
        username_edit.setText(user['username'])
        layout.addWidget(username_edit)

        # Чекбокс смены пароля
        change_password_cb = QCheckBox("Изменить пароль")
        layout.addWidget(change_password_cb)

        # Пароль (скрыт по умолчанию)
        password_label = QLabel("Новый пароль:")
        password_label.hide()
        layout.addWidget(password_label)
        password_edit = QLineEdit()
        password_edit.setPlaceholderText("новый пароль")
        password_edit.setEchoMode(QLineEdit.Password)
        password_edit.hide()
        layout.addWidget(password_edit)

        # Подтверждение пароля
        confirm_label = QLabel("Подтверждение пароля:")
        confirm_label.hide()
        layout.addWidget(confirm_label)
        confirm_edit = QLineEdit()
        confirm_edit.setPlaceholderText("повторите пароль")
        confirm_edit.setEchoMode(QLineEdit.Password)
        confirm_edit.hide()
        layout.addWidget(confirm_edit)

        # Роль
        role_label = QLabel("Роль:")
        layout.addWidget(role_label)
        role_combo = QComboBox()
        role_combo.addItems(["user", "admin"])
        role_combo.setCurrentText(user['role'])
        layout.addWidget(role_combo)

        def toggle_password_fields(state):
            is_checked = state == Qt.Checked
            password_label.setVisible(is_checked)
            password_edit.setVisible(is_checked)
            confirm_label.setVisible(is_checked)
            confirm_edit.setVisible(is_checked)

        change_password_cb.stateChanged.connect(toggle_password_fields)

        layout.addStretch()

        # Кнопки
        buttons_layout = QHBoxLayout()
        save_btn = QPushButton("💾 Сохранить изменения")
        cancel_btn = QPushButton("❌ Отмена")
        buttons_layout.addWidget(save_btn)
        buttons_layout.addWidget(cancel_btn)
        layout.addLayout(buttons_layout)

        def save_user():
            full_name = full_name_edit.text().strip()
            username = username_edit.text().strip()
            role = role_combo.currentText()

            if not full_name or not username:
                QMessageBox.warning(dialog, "Ошибка", "Заполните ФИО и логин")
                return

            # Проверка на дубликат логина (если логин изменился)
            if username != user['username']:
                existing = self.db.get_user_by_username(username)
                if existing and existing['id'] != user_id:
                    QMessageBox.warning(dialog, "Ошибка", "Пользователь с таким логином уже существует")
                    return

            # Если нужно изменить пароль
            if change_password_cb.isChecked():
                password = password_edit.text().strip()
                confirm = confirm_edit.text().strip()

                if not password:
                    QMessageBox.warning(dialog, "Ошибка", "Введите новый пароль")
                    return

                if password != confirm:
                    QMessageBox.warning(dialog, "Ошибка", "Пароли не совпадают")
                    return

                if self.db.update_user(user_id, username, full_name, role, password):
                    QMessageBox.information(dialog, "Успех", "Пользователь обновлен")
                    dialog.accept()
                    self.load_users_list()
                else:
                    QMessageBox.warning(dialog, "Ошибка", "Не удалось обновить пользователя")
            else:
                # Обновляем без смены пароля
                if self.db.update_user(user_id, username, full_name, role):
                    QMessageBox.information(dialog, "Успех", "Пользователь обновлен")
                    dialog.accept()
                    self.load_users_list()
                else:
                    QMessageBox.warning(dialog, "Ошибка", "Не удалось обновить пользователя")

        save_btn.clicked.connect(save_user)
        cancel_btn.clicked.connect(dialog.reject)
        dialog.exec_()

    def start_test(self):
        user = self.auth_manager.get_current_user()
        if user:
            test_window = TestWindow(self, self.db, user['id'], training_mode=False)
            test_window.test_finished.connect(self.on_test_finished)
            test_window.exec_()

    def start_practice(self):
        user = self.auth_manager.get_current_user()
        if user:
            test_window = TestWindow(self, self.db, user['id'], training_mode=True)
            test_window.test_finished.connect(self.on_test_finished)
            test_window.exec_()

    def on_test_finished(self):
        self.load_stats()
        self.load_mistakes()

    def change_user(self):
        """Смена пользователя без перезапуска приложения"""
        reply = QMessageBox.question(self, "Смена пользователя",
                                     "Вы действительно хотите сменить пользователя?\nТекущая сессия будет завершена.",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            # Очищаем текущего пользователя
            self.auth_manager.logout()

            # Скрываем главное окно
            self.hide()

            # Создаем и показываем диалог входа
            login_dialog = LoginDialog(self.auth_manager, self)
            login_dialog.login_successful.connect(self.on_login_success)

            # Если диалог был закрыт без входа (крестик), выходим из приложения
            if login_dialog.exec_() != QDialog.Accepted:
                QApplication.quit()
                sys.exit(0)

    def logout(self):
        self.auth_manager.logout()
        self.show_login_dialog()

    def restart_application(self):
        python = sys.executable
        subprocess.Popen([python] + sys.argv)
        sys.exit(0)

    # Добавим новый метод для просмотра детальной статистики пользователя
    def view_user_details(self, user_id, username):
        """Просмотр детальной статистики конкретного пользователя (для админа)"""
        user = self.db.get_user_by_id(user_id)
        if not user:
            return

        results = self.db.get_user_test_results(user_id)

        dialog = QDialog(self)
        dialog.setWindowTitle(f"📊 Детальная статистика: {user['full_name']}")
        dialog.setMinimumSize(900, 700)
        dialog.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #1a1a2e, stop:1 #16213e);
            }
            QLabel {
                color: #e2e2e2;
            }
            QPushButton {
                background: #e94560;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #ff6b6b;
            }
            QTableWidget {
                background-color: #2c2c3e;
                color: #e2e2e2;
                gridline-color: #4a4a5a;
                border-radius: 10px;
            }
            QHeaderView::section {
                background-color: #0f3460;
                color: #e2e2e2;
                padding: 8px;
            }
        """)

        layout = QVBoxLayout(dialog)

        # Информация о пользователе
        if results:
            total_score = sum(r['score'] for r in results)
            total_questions = sum(r['total'] for r in results)
            avg_percent = (total_score / total_questions * 100) if total_questions > 0 else 0
            passed_count = sum(1 for r in results if r['passed'])

            info_text = f"""
            <div style='background-color: #ffffff; border-radius: 15px; padding: 20px; border: 1px solid #dee2e6;'>
                <h2 style='color: #2c3e50;'>👤 {user['full_name']}</h2>
                <p style='color: #495057;'>📝 <b>Логин:</b> {user['username']}</p>
                <p style='color: #495057;'>📊 <b>Всего тестов:</b> {len(results)}</p>
                <p style='color: #495057;'>✅ <b>Правильных ответов:</b> {total_score} из {total_questions}</p>
                <p style='color: #495057;'>📈 <b>Средний результат:</b> {avg_percent:.1f}%</p>
                <p style='color: #495057;'>🏆 <b>Успешно сдано (≥80%):</b> {passed_count}</p>
            </div>
            """
        else:
            info_text = f"""
            <div style='background-color: #ffffff; border-radius: 15px; padding: 20px; border: 1px solid #dee2e6;'>
                <h2 style='color: #2c3e50;'>👤 {user['full_name']}</h2>
                <p style='color: #495057;'>📝 <b>Логин:</b> {user['username']}</p>
                <p style='color: #f39c12;'>⚠️ Пользователь еще не проходил тесты</p>
            </div>
            """

        info_label = QLabel(info_text)
        info_label.setWordWrap(True)
        layout.addWidget(info_label)

        # График
        chart = StatisticsChart()
        chart.update_chart(results, passing_threshold=80)
        layout.addWidget(chart)

        # Таблица с результатами
        if results:
            table_label = QLabel("📋 Детальные результаты тестов:")
            table_label.setFont(QFont("Segoe UI", 14, QFont.Bold))
            layout.addWidget(table_label)

            table = QTableWidget()
            table.setColumnCount(5)
            table.setHorizontalHeaderLabels(["Дата", "Результат", "Процент", "Статус", "Детали"])
            table.horizontalHeader().setStretchLastSection(True)

            for row, result in enumerate(results[:20]):
                table.insertRow(row)

                date_obj = datetime.fromisoformat(result['date'].replace(' ', 'T'))
                date_str = date_obj.strftime('%d.%m.%Y %H:%M:%S')
                percent = result['score'] / result['total'] * 100
                status = "✅ Сдано" if result['passed'] else "❌ Не сдано"

                table.setItem(row, 0, QTableWidgetItem(date_str))
                table.setItem(row, 1, QTableWidgetItem(f"{result['score']}/{result['total']}"))
                table.setItem(row, 2, QTableWidgetItem(f"{percent:.1f}%"))

                status_item = QTableWidgetItem(status)
                status_item.setForeground(QColor("#4caf50" if result['passed'] else "#f44336"))
                table.setItem(row, 3, status_item)

                # Кнопка просмотра деталей
                view_btn = QPushButton("📖 Подробнее")
                view_btn.clicked.connect(lambda checked, rid=result['id']: self.view_test_details(rid))
                table.setCellWidget(row, 4, view_btn)

            table.setAlternatingRowColors(True)
            layout.addWidget(table)

        close_btn = QPushButton("✖ Закрыть")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)

        dialog.exec_()

    def view_test_details(self, result_id):
        """Просмотр деталей конкретного теста"""
        result = self.db.get_test_result_by_id(result_id)
        if not result:
            return

        import json
        details = json.loads(result['details'])

        dialog = QDialog(self)
        dialog.setWindowTitle(f"Детали теста от {result['date']}")
        dialog.setMinimumSize(800, 600)
        dialog.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #1a1a2e, stop:1 #16213e);
            }
            QLabel {
                color: #e2e2e2;
            }
            QPushButton {
                background: #e94560;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
            }
        """)

        layout = QVBoxLayout(dialog)

        # Общая информация
        percent = result['score'] / result['total'] * 100
        info_label = QLabel(f"""
        <div style='text-align: center; padding: 20px;'>
            <h2 style='color: #e94560;'>Результат теста</h2>
            <p><b>Дата:</b> {result['date']}</p>
            <p><b>Результат:</b> {result['score']}/{result['total']} ({percent:.1f}%)</p>
            <p><b>Статус:</b> <span style='color: {"#4caf50" if result['passed'] else "#f44336"};'>
                {"✅ Сдано" if result['passed'] else "❌ Не сдано"}
            </span></p>
        </div>
        """)
        info_label.setWordWrap(True)
        layout.addWidget(info_label)

        # Список вопросов
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)

        for i, detail in enumerate(details, 1):
            if detail is None:
                continue

            card = QFrame()
            card.setStyleSheet(f"""
                QFrame {{
                    background-color: #2c2c3e;
                    border-radius: 10px;
                    margin: 5px;
                    padding: 10px;
                    border-left: 5px solid {"#4caf50" if detail['correct'] else "#f44336"};
                }}
            """)

            card_layout = QVBoxLayout(card)

            # Вопрос
            q_text = QLabel(f"<b>Вопрос {i}:</b> {detail['question_text'][:200]}...")
            q_text.setWordWrap(True)
            card_layout.addWidget(q_text)

            # Ответ
            status_text = "✅ Верно" if detail['correct'] else "❌ Неверно"
            status_color = "#4caf50" if detail['correct'] else "#f44336"

            # Показываем выбранные ответы
            selected_options = []
            for j, opt in enumerate(detail['options']):
                if (detail['selected_mask'] >> j) & 1:
                    selected_options.append(opt)

            correct_options = []
            for j, opt in enumerate(detail['options']):
                if (detail['correct_mask'] >> j) & 1:
                    correct_options.append(opt)

            answer_text = f"""
            <p><span style='color: {status_color};'><b>{status_text}</b></span></p>
            <p><b>📌 Ваш ответ:</b> {', '.join(selected_options) if selected_options else 'Не выбран'}</p>
            <p><b>✅ Правильный ответ:</b> {', '.join(correct_options)}</p>
            """

            if detail.get('explanation'):
                answer_text += f"<p><b>💡 Пояснение:</b> {detail['explanation']}</p>"

            answer_label = QLabel(answer_text)
            answer_label.setWordWrap(True)
            card_layout.addWidget(answer_label)

            scroll_layout.addWidget(card)

        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)

        close_btn = QPushButton("✖ Закрыть")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)

        dialog.exec_()

    def on_login_success(self):
        """После успешного входа"""
        self.show()
        self.update_user_info()

        start_test_btn = self.findChild(QPushButton, "startTestButton")
        start_practice_btn = self.findChild(QPushButton, "startPracticeButton")

        if start_test_btn:
            start_test_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #3498db;
                        color: white;
                        border: none;
                        border-radius: 12px;
                        padding: 12px 24px;
                        font-weight: bold;
                        font-size: 18px;
                    }
                    QPushButton:hover {
                        background-color: #2980b9;
                    }
                    QPushButton:pressed {
                        background-color: #1c6ea4;
                    }
                """)

        if start_practice_btn:
            start_practice_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #27ae60;
                        color: white;
                        border: none;
                        border-radius: 12px;
                        padding: 12px 24px;
                        font-weight: bold;
                        font-size: 18px;
                    }
                    QPushButton:hover {
                        background-color: #219a52;
                    }
                    QPushButton:pressed {
                        background-color: #1e8449;
                    }
                """)

        # Принудительно обновляем кнопки
        if start_test_btn:
            start_test_btn.update()
            start_test_btn.repaint()
        if start_practice_btn:
            start_practice_btn.update()
            start_practice_btn.repaint()

        if hasattr(self, 'statsTab'):
            # Удаляем все виджеты на вкладке
            layout = self.statsTab.layout()
            if layout is None:
                layout = QVBoxLayout(self.statsTab)

            # Очищаем layout
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget:
                    widget.deleteLater()

            # Создаем новое содержимое
            self.setup_stats_tab_content()
        self.setup_admin_tabs()

        # Принудительно загружаем данные
        self.load_study_materials()
        self.load_stats()  # Загружаем статистику пользователя
        self.load_mistakes()

        if self.auth_manager.is_admin():
            self.load_admin_stats()

        # Подключаем сигнал смены вкладки для обновления статистики
        self.tabWidget.currentChanged.connect(self.on_tab_changed)

    def on_tab_changed(self, index):
        """При смене вкладки обновляем данные"""
        tab_text = self.tabWidget.tabText(index)

        if "Статистика" in tab_text:
            self.load_stats()
        elif "Ошибки" in tab_text:
            self.load_mistakes()
        elif "Материалы" in tab_text and hasattr(self, 'admin_materials_table'):
            self.load_admin_materials()
        elif "Пользователи" in tab_text:
            self.load_users_list()
        elif "Вопросы" in tab_text:
            self.load_questions_list()

    def setup_stats_tab(self):
        """Настройка вкладки статистики с расширенной информацией"""
        # Очищаем существующие виджеты
        if self.statsTab.layout():
            self.clear_layout(self.statsTab.layout())

        layout = QVBoxLayout(self.statsTab)
        layout.setContentsMargins(10, 10, 10, 10)

        # Создаем вкладки внутри статистики
        self.stats_tabs = QTabWidget()
        self.stats_tabs.setStyleSheet("""
            QTabWidget::pane {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 10px;
            }
            QTabBar::tab {
                background-color: #e9ecef;
                color: #495057;
                padding: 10px 20px;
                margin-right: 5px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
            }
            QTabBar::tab:selected {
                background-color: #3498db;
                color: white;
            }
            QTabBar::tab:hover:!selected {
                background-color: #dee2e6;
            }
        """)
        layout.addWidget(self.stats_tabs)

        # Вкладка общей статистики
        self.general_stats_tab = QWidget()
        self.general_stats_tab.setStyleSheet("background-color: #f8f9fa;")
        self.stats_tabs.addTab(self.general_stats_tab, "📊 Общая статистика")

        # Вкладка детальной статистики
        self.detailed_stats_tab = QWidget()
        self.detailed_stats_tab.setStyleSheet("background-color: #f8f9fa;")
        self.stats_tabs.addTab(self.detailed_stats_tab, "📈 Детальная статистика")

        # Настройка общей статистики
        general_layout = QVBoxLayout(self.general_stats_tab)
        general_layout.setContentsMargins(10, 10, 10, 10)

        # Информационная карточка
        self.statsInfoLabel = QLabel()
        self.statsInfoLabel.setWordWrap(True)
        self.statsInfoLabel.setStyleSheet("""
            background-color: white;
            padding: 15px;
            border-radius: 10px;
            border: 1px solid #dee2e6;
        """)
        self.statsInfoLabel.setMinimumHeight(200)
        general_layout.addWidget(self.statsInfoLabel)

        # График динамики
        chart_label = QLabel("📈 Динамика результатов:")
        chart_label.setFont(QFont("Segoe UI", 12, QFont.Bold))
        chart_label.setStyleSheet("color: #2c3e50;")
        general_layout.addWidget(chart_label)

        self.chart_widget = StatisticsChart()
        self.chart_widget.setMinimumHeight(350)
        general_layout.addWidget(self.chart_widget)

        # Круговая диаграмма
        pie_chart_label = QLabel("📊 Соотношение успешных и неуспешных тестов:")
        pie_chart_label.setFont(QFont("Segoe UI", 12, QFont.Bold))
        pie_chart_label.setStyleSheet("color: #2c3e50;")
        general_layout.addWidget(pie_chart_label)

        self.pie_chart_widget = StatisticsChart()
        self.pie_chart_widget.setMinimumHeight(250)
        general_layout.addWidget(self.pie_chart_widget)

        # Настройка детальной статистики
        detailed_layout = QVBoxLayout(self.detailed_stats_tab)
        detailed_layout.setContentsMargins(10, 10, 10, 10)

        # Список результатов
        results_label = QLabel("📝 История всех тестирований:")
        results_label.setFont(QFont("Segoe UI", 12, QFont.Bold))
        results_label.setStyleSheet("color: #2c3e50;")
        detailed_layout.addWidget(results_label)

        self.statsList = QScrollArea()
        self.statsList.setWidgetResizable(True)
        self.statsList.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")

        self.statsContent = QWidget()
        self.statsContent.setStyleSheet("background-color: transparent;")
        self.statsResultsLayout = QVBoxLayout(self.statsContent)
        self.statsResultsLayout.setSpacing(10)
        self.statsList.setWidget(self.statsContent)
        detailed_layout.addWidget(self.statsList)

    def clear_layout(self, layout):
        """Очистка layout от всех виджетов"""
        if layout is not None:
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()
                else:
                    self.clear_layout(item.layout())

    def load_stats(self):
        """Загрузка расширенной статистики для пользователя"""
        user = self.auth_manager.get_current_user()
        if not user:
            return
        # Получаем детальную статистику
        stats = self.db.get_user_detailed_stats(user['id'])
        results = self.db.get_user_test_results(user['id'])

        # Общая статистика
        if stats['total_tests'] > 0:
            info_text = f"""
            <div style='text-align: center; background-color: #ffffff; border-radius: 15px; padding: 20px;'>
                <h2 style='color: #2c3e50;'>📊 Статистика пользователя</h2>
                <p style='font-size: 16px; color: #2c3e50;'><b>{user['full_name']}</b> ({user['username']})</p>
                <hr style='border-color: #dee2e6;'>
                <table style='width: 100%; margin-top: 10px;'>
                    <tr>
                        <td style='padding: 8px; color: #495057;'><b>📝 Всего тестов:</b></td>
                        <td style='padding: 8px; color: #2c3e50;'>{stats['total_tests']}</td>
                        <td style='padding: 8px; color: #495057;'><b>✅ Успешно сдано:</b></td>
                        <td style='padding: 8px; color: #27ae60;'>{stats['passed_tests']}</td>
                    </tr>
                    <tr>
                        <td style='padding: 8px; color: #495057;'><b>❌ Не сдано:</b></td>
                        <td style='padding: 8px; color: #e74c3c;'>{stats['failed_tests']}</td>
                        <td style='padding: 8px; color: #495057;'><b>📈 Средний балл:</b></td>
                        <td style='padding: 8px; color: #2c3e50;'>{stats['avg_percent']:.1f}%</td>
                    </tr>
                    <tr>
                        <td style='padding: 8px; color: #495057;'><b>✅ Всего верных ответов:</b></td>
                        <td style='padding: 8px; color: #2c3e50;'>{stats['total_correct']}</td>
                        <td style='padding: 8px; color: #495057;'><b>📝 Всего вопросов:</b></td>
                        <td style='padding: 8px; color: #2c3e50;'>{stats['total_questions']}</td>
                    </tr>
                    <tr>
                        <td style='padding: 8px; color: #495057;'><b>🏆 Лучший результат:</b></td>
                        <td style='padding: 8px; color: #27ae60;'>{stats['best_result']:.1f}%</td>
                        <td style='padding: 8px; color: #495057;'><b>📉 Худший результат:</b></td>
                        <td style='padding: 8px; color: #e74c3c;'>{stats['worst_result']:.1f}%</td>
                    </tr>
                </table>
            </div>
            """
        else:
            info_text = f"""
            <div style='text-align: center; background-color: #ffffff; border-radius: 15px; padding: 20px;'>
                <h2 style='color: #2c3e50;'>📊 Статистика пользователя</h2>
                <p style='font-size: 16px; color: #2c3e50;'><b>{user['full_name']}</b> ({user['username']})</p>
                <hr style='border-color: #dee2e6;'>
                <p style='color: #f39c12; padding: 20px;'>⚠️ У вас пока нет пройденных тестов</p>
                <p style='color: #6c757d;'>Пройдите тест в разделе "Тестирование", чтобы увидеть статистику</p>
            </div>
            """

        self.statsInfoLabel.setText(info_text)

        # График динамики
        if results:
            self.chart_widget.update_chart(results, passing_threshold=80)

            # Круговая диаграмма
            if stats['total_tests'] > 0:
                self.pie_chart_widget.create_pie_chart(
                    [stats['passed_tests'], stats['failed_tests']],
                    ['Успешно сдано', 'Не сдано'],
                    'Соотношение результатов тестов',
                    ['#a6e3a1', '#f38ba8']
                )
        else:
            self.chart_widget.update_chart([])
            self.pie_chart_widget.create_pie_chart([1], ['Нет данных'], 'Нет пройденных тестов', ['#6c7086'])

        # Очищаем список результатов
        if hasattr(self, 'statsResultsLayout'):
            for i in reversed(range(self.statsResultsLayout.count())):
                widget = self.statsResultsLayout.itemAt(i).widget()
                if widget:
                    widget.deleteLater()

        # Детальный список всех тестов
        if results:
            for i, result in enumerate(results, 1):
                card = QFrame()
                card.setStyleSheet("background-color: #45475a; border-radius: 10px; margin: 5px; padding: 10px;")

                percent = result['score'] / result['total'] * 100
                status = "✅ Сдано" if result['passed'] else "❌ Не сдано"
                status_color = "#a6e3a1" if result['passed'] else "#f38ba8"

                date_obj = datetime.fromisoformat(result['date'].replace(' ', 'T'))
                date_str = date_obj.strftime('%d.%m.%Y %H:%M:%S')

                # Кнопка просмотра деталей
                main_layout = QVBoxLayout(card)

                info_layout = QHBoxLayout()
                info_text_label = QLabel(f"<b>Попытка #{i}</b> | 📅 {date_str}")
                info_text_label.setStyleSheet("color: #89b4fa;")
                info_layout.addWidget(info_text_label)
                info_layout.addStretch()

                result_text = QLabel(f"📊 Результат: {result['score']}/{result['total']} ({percent:.1f}%)")
                result_text.setStyleSheet("color: #cdd6f4;")
                info_layout.addWidget(result_text)

                status_label = QLabel(status)
                status_label.setStyleSheet(f"color: {status_color}; font-weight: bold;")
                info_layout.addWidget(status_label)

                main_layout.addLayout(info_layout)

                details_btn = QPushButton("📖 Подробнее")
                details_btn.clicked.connect(lambda checked, rid=result['id']: self.view_test_details(rid))
                main_layout.addWidget(details_btn)

                self.statsResultsLayout.addWidget(card)
        else:
            no_data_label = QLabel("📭 Нет пройденных тестов")
            no_data_label.setAlignment(Qt.AlignCenter)
            no_data_label.setStyleSheet("color: #6c7086; padding: 40px; font-size: 14px;")
            self.statsResultsLayout.addWidget(no_data_label)

    def setup_admin_stats_tab(self):
        """Настройка админской вкладки статистики"""
        layout = QVBoxLayout(self.admin_stats_tab)
        layout.setContentsMargins(10, 10, 10, 10)

        # Создаем вкладки внутри админской статистики
        self.admin_stats_tabs = QTabWidget()
        self.admin_stats_tabs.setStyleSheet("""
            QTabWidget::pane {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 10px;
            }
            QTabBar::tab {
                background-color: #e9ecef;
                color: #495057;
                padding: 10px 20px;
                margin-right: 5px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
            }
            QTabBar::tab:selected {
                background-color: #3498db;
                color: white;
            }
            QTabBar::tab:hover:!selected {
                background-color: #dee2e6;
            }
        """)
        layout.addWidget(self.admin_stats_tabs)

        # Вкладка общей статистики
        self.admin_general_tab = QWidget()
        self.admin_general_tab.setStyleSheet("background-color: #f8f9fa;")
        self.admin_stats_tabs.addTab(self.admin_general_tab, "📊 Общая статистика")

        # Вкладка пользователей
        self.admin_users_stats_tab = QWidget()
        self.admin_users_stats_tab.setStyleSheet("background-color: #f8f9fa;")
        self.admin_stats_tabs.addTab(self.admin_users_stats_tab, "👥 Статистика пользователей")

        # Настройка общей статистики
        general_layout = QVBoxLayout(self.admin_general_tab)
        general_layout.setContentsMargins(10, 10, 10, 10)

        self.admin_stats_label = QLabel()
        self.admin_stats_label.setWordWrap(True)
        self.admin_stats_label.setStyleSheet("""
            background-color: white;
            padding: 15px;
            border-radius: 10px;
            border: 1px solid #dee2e6;
        """)
        general_layout.addWidget(self.admin_stats_label)

        # График успеваемости пользователей
        chart_label = QLabel("📊 Средняя успеваемость пользователей:")
        chart_label.setFont(QFont("Segoe UI", 12, QFont.Bold))
        chart_label.setStyleSheet("color: #2c3e50;")
        general_layout.addWidget(chart_label)

        self.admin_chart_widget = StatisticsChart()
        self.admin_chart_widget.setMinimumHeight(350)
        general_layout.addWidget(self.admin_chart_widget)

        # Настройка статистики пользователей
        users_layout = QVBoxLayout(self.admin_users_stats_tab)
        users_layout.setContentsMargins(10, 10, 10, 10)

        # Фильтр поиска
        filter_layout = QHBoxLayout()
        filter_label = QLabel("🔍 Поиск пользователя:")
        filter_label.setStyleSheet("color: #2c3e50; background-color: transparent;")
        filter_layout.addWidget(filter_label)

        self.user_search_edit = QLineEdit()
        self.user_search_edit.setPlaceholderText("Введите имя или логин...")
        self.user_search_edit.setStyleSheet("""
            QLineEdit {
                background-color: white;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                padding: 8px;
                color: #2c3e50;
            }
            QLineEdit:focus {
                border-color: #3498db;
            }
        """)
        self.user_search_edit.textChanged.connect(self.filter_users_stats)
        filter_layout.addWidget(self.user_search_edit)

        users_layout.addLayout(filter_layout)

        # Таблица пользователей
        self.admin_stats_table = QTableWidget()
        self.admin_stats_table.setColumnCount(7)
        self.admin_stats_table.setHorizontalHeaderLabels([
            "Пользователь", "Тестов", "Верных ответов", "Средний балл",
            "Сдано/Не сдано", "Последний тест", "Действия"
        ])
        self.admin_stats_table.horizontalHeader().setStretchLastSection(True)
        self.admin_stats_table.setAlternatingRowColors(True)
        self.admin_stats_table.setStyleSheet("""
            QTableWidget {
                background-color: white;
                color: #2c3e50;
                gridline-color: #dee2e6;
                selection-background-color: #3498db;
                selection-color: white;
            }
            QHeaderView::section {
                background-color: #e9ecef;
                color: #2c3e50;
                padding: 8px;
                border: 1px solid #dee2e6;
            }
        """)
        self.admin_stats_table.setSortingEnabled(True)
        users_layout.addWidget(self.admin_stats_table)

        # Загружаем данные
        self.load_admin_stats()

    def load_admin_stats(self):
        """Загрузка расширенной статистики для админа"""
        stats = self.db.get_overall_stats()
        all_users_stats = self.db.get_all_users_stats()
        # Общая статистика
        total_tests = sum(u['total_tests'] for u in all_users_stats)
        total_correct = sum(u['total_correct'] for u in all_users_stats)
        total_questions = sum(u['total_questions'] for u in all_users_stats)
        avg_system_percent = (total_correct / total_questions * 100) if total_questions > 0 else 0

        info_text = f"""
        <div style='text-align: center; background-color: #ffffff; border-radius: 15px; padding: 20px;'>
            <h2 style='color: #2c3e50;'>📊 Общая статистика системы</h2>
            <hr style='border-color: #dee2e6;'>
            <table style='width: 100%; margin-top: 10px;'>
                <tr>
                    <td style='padding: 8px; color: #495057;'><b>👥 Всего пользователей:</b></td>
                    <td style='padding: 8px; color: #2c3e50;'>{stats['total_users']}</td>
                    <td style='padding: 8px; color: #495057;'><b>❓ Всего вопросов:</b></td>
                    <td style='padding: 8px; color: #2c3e50;'>{stats['total_questions']}</td>
                </tr>
                <tr>
                    <td style='padding: 8px; color: #495057;'><b>📝 Всего тестов:</b></td>
                    <td style='padding: 8px; color: #2c3e50;'>{total_tests}</td>
                    <td style='padding: 8px; color: #495057;'><b>✅ Всего верных ответов:</b></td>
                    <td style='padding: 8px; color: #2c3e50;'>{total_correct}/{total_questions}</td>
                </tr>
                <tr>
                    <td style='padding: 8px; color: #495057;'><b>📈 Средний балл системы:</b></td>
                    <td style='padding: 8px; color: #2c3e50;'>{avg_system_percent:.1f}%</td>
                    <td style='padding: 8px; color: #495057;'><b>🎯 Успешных тестов:</b></td>
                    <td style='padding: 8px; color: #2c3e50;'>{stats['passed_percent']:.1f}%</td>
                </tr>
            </table>
        </div>
        """
        self.admin_stats_label.setText(info_text)

        # График успеваемости пользователей
        if all_users_stats:
            user_names = []
            avg_scores = []

            for u in all_users_stats:
                name = u['full_name'][:15] if u['full_name'] else u['username'][:15]
                user_names.append(name)
                avg_scores.append(u['avg_percent'])

            self.admin_chart_widget.create_bar_chart(
                avg_scores, user_names,
                'Средняя успеваемость пользователей',
                'Средний балл, %', threshold=80
            )
        else:
            self.admin_chart_widget.create_bar_chart([0], ['Нет данных'], 'Нет данных', 'Средний балл, %')

        # Сохраняем данные для фильтрации
        self.all_users_stats = all_users_stats
        self.load_users_stats_table(all_users_stats)

    def load_users_stats_table(self, users_stats):
        """Загрузка таблицы со статистикой пользователей"""
        self.admin_stats_table.setRowCount(0)

        if not users_stats:
            # Показываем сообщение о отсутствии данных
            row = self.admin_stats_table.rowCount()
            self.admin_stats_table.insertRow(row)
            no_data_item = QTableWidgetItem("Нет данных о тестах")
            no_data_item.setTextAlignment(Qt.AlignCenter)
            self.admin_stats_table.setSpan(row, 0, 1, 7)
            self.admin_stats_table.setItem(row, 0, no_data_item)
            return

        for user_stat in users_stats:
            row = self.admin_stats_table.rowCount()
            self.admin_stats_table.insertRow(row)

            # ФИО и логин
            name_text = f"{user_stat['full_name']}\n({user_stat['username']})" if user_stat['full_name'] else user_stat[
                'username']
            name_item = QTableWidgetItem(name_text)
            self.admin_stats_table.setItem(row, 0, name_item)

            # Количество тестов
            tests_count_item = QTableWidgetItem(str(user_stat['total_tests']))
            self.admin_stats_table.setItem(row, 1, tests_count_item)

            # Верных ответов
            if user_stat['total_questions'] > 0:
                correct_item = QTableWidgetItem(f"{user_stat['total_correct']}/{user_stat['total_questions']}")
            else:
                correct_item = QTableWidgetItem("0/0")
            self.admin_stats_table.setItem(row, 2, correct_item)

            # Средний балл с цветом
            avg_score = user_stat['avg_percent']
            avg_item = QTableWidgetItem(f"{avg_score:.1f}%")
            if avg_score >= 80:
                avg_item.setForeground(QColor("#a6e3a1"))
            elif avg_score >= 60:
                avg_item.setForeground(QColor("#f9e2af"))
            else:
                avg_item.setForeground(QColor("#f38ba8"))
            self.admin_stats_table.setItem(row, 3, avg_item)

            # Сдано/Не сдано
            ratio_item = QTableWidgetItem(f"✅ {user_stat['passed_tests']} / ❌ {user_stat['failed_tests']}")
            self.admin_stats_table.setItem(row, 4, ratio_item)

            # Последний тест
            if user_stat['last_test_date']:
                date_obj = datetime.fromisoformat(user_stat['last_test_date'].replace(' ', 'T'))
                date_str = date_obj.strftime('%d.%m.%Y %H:%M')
            else:
                date_str = "Нет тестов"
            self.admin_stats_table.setItem(row, 5, QTableWidgetItem(date_str))

            # Кнопка детальной статистики
            details_btn = QPushButton("📊 Подробно")
            details_btn.clicked.connect(lambda checked, uid=user_stat['user_id']:
                                        self.view_user_full_stats(uid))
            self.admin_stats_table.setCellWidget(row, 6, details_btn)

        # Настройка ширины колонок
        self.admin_stats_table.setColumnWidth(0, 180)
        self.admin_stats_table.setColumnWidth(1, 70)
        self.admin_stats_table.setColumnWidth(2, 100)
        self.admin_stats_table.setColumnWidth(3, 100)
        self.admin_stats_table.setColumnWidth(4, 120)
        self.admin_stats_table.setColumnWidth(5, 130)
        self.admin_stats_table.setColumnWidth(6, 100)

    def filter_users_stats(self):
        """Фильтрация пользователей по поиску"""
        if not hasattr(self, 'all_users_stats'):
            return

        search_text = self.user_search_edit.text().lower()

        if not search_text:
            filtered_users = self.all_users_stats
        else:
            filtered_users = []
            for user in self.all_users_stats:
                name = user['full_name'].lower() if user['full_name'] else ''
                username = user['username'].lower()
                if search_text in name or search_text in username:
                    filtered_users.append(user)

        self.load_users_stats_table(filtered_users)

    def setup_stats_tab_content(self):
        """Создание содержимого вкладки статистики с прокруткой"""
        # Получаем layout вкладки statsTab
        layout = self.statsTab.layout()
        if layout is None:
            layout = QVBoxLayout(self.statsTab)

        # Создаем scroll area для всего содержимого
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")

        # Создаем контейнер для содержимого
        content_widget = QWidget()
        content_widget.setStyleSheet("background-color: transparent;")
        content_layout = QVBoxLayout(content_widget)

        # Создаем вкладки внутри статистики
        self.stats_tabs = QTabWidget()
        self.stats_tabs.setStyleSheet("""
            QTabWidget::pane {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 10px;
            }
            QTabBar::tab {
                background-color: #e9ecef;
                color: #495057;
                padding: 10px 20px;
                margin-right: 5px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
            }
            QTabBar::tab:selected {
                background-color: #3498db;
                color: white;
            }
            QTabBar::tab:hover:!selected {
                background-color: #dee2e6;
            }
        """)
        content_layout.addWidget(self.stats_tabs)

        # Вкладка общей статистики
        self.general_stats_tab = QWidget()
        self.general_stats_tab.setStyleSheet("background-color: #f8f9fa;")
        self.stats_tabs.addTab(self.general_stats_tab, "📊 Общая статистика")

        # Вкладка детальной статистики
        self.detailed_stats_tab = QWidget()
        self.detailed_stats_tab.setStyleSheet("background-color: #f8f9fa;")
        self.stats_tabs.addTab(self.detailed_stats_tab, "📈 Детальная статистика")

        # Настройка общей статистики - с прокруткой внутри
        general_scroll = QScrollArea()
        general_scroll.setWidgetResizable(True)
        general_scroll.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")

        general_content = QWidget()
        general_content.setStyleSheet("background-color: transparent;")
        general_layout = QVBoxLayout(general_content)
        general_layout.setSpacing(15)

        # Информационная карточка
        self.statsInfoLabel = QLabel()
        self.statsInfoLabel.setWordWrap(True)
        self.statsInfoLabel.setStyleSheet("""
            background-color: white;
            padding: 15px;
            border-radius: 10px;
            border: 1px solid #dee2e6;
        """)
        self.statsInfoLabel.setMinimumHeight(200)
        general_layout.addWidget(self.statsInfoLabel)

        # График динамики
        chart_label = QLabel("📈 Динамика результатов:")
        chart_label.setFont(QFont("Segoe UI", 12, QFont.Bold))
        chart_label.setStyleSheet("color: #2c3e50; background-color: transparent;")
        general_layout.addWidget(chart_label)

        self.chart_widget = StatisticsChart()
        self.chart_widget.setMinimumHeight(400)
        self.chart_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        general_layout.addWidget(self.chart_widget)

        # Круговая диаграмма
        pie_chart_label = QLabel("📊 Соотношение успешных и неуспешных тестов:")
        pie_chart_label.setFont(QFont("Segoe UI", 12, QFont.Bold))
        pie_chart_label.setStyleSheet("color: #2c3e50; background-color: transparent;")
        general_layout.addWidget(pie_chart_label)

        self.pie_chart_widget = StatisticsChart()
        self.pie_chart_widget.setMinimumHeight(300)
        general_layout.addWidget(self.pie_chart_widget)

        general_layout.addStretch()
        general_scroll.setWidget(general_content)

        # Добавляем scroll в общую статистику
        general_tab_layout = QVBoxLayout(self.general_stats_tab)
        general_tab_layout.addWidget(general_scroll)

        # Настройка детальной статистики
        detailed_layout = QVBoxLayout(self.detailed_stats_tab)
        detailed_layout.setContentsMargins(10, 10, 10, 10)

        results_label = QLabel("📝 История всех тестирований:")
        results_label.setFont(QFont("Segoe UI", 12, QFont.Bold))
        results_label.setStyleSheet("color: #2c3e50; background-color: transparent;")
        detailed_layout.addWidget(results_label)

        self.statsList = QScrollArea()
        self.statsList.setWidgetResizable(True)
        self.statsList.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")

        self.statsContent = QWidget()
        self.statsContent.setStyleSheet("background-color: transparent;")
        self.statsResultsLayout = QVBoxLayout(self.statsContent)
        self.statsResultsLayout.setSpacing(10)
        self.statsList.setWidget(self.statsContent)
        detailed_layout.addWidget(self.statsList)

        scroll_area.setWidget(content_widget)
        layout.addWidget(scroll_area)
