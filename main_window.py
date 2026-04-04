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
from viewer_widget import MaterialViewerDialog


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

        if hasattr(self, 'logoutButton'):
            self.logoutButton.clicked.connect(self.logout)

    def setup_study_tab(self):
        """Настройка вкладки обучения - видна всем пользователям с поиском"""
        # Получаем или создаем layout
        layout = self.studyTab.layout()
        if layout is None:
            layout = QVBoxLayout(self.studyTab)
            layout.setContentsMargins(10, 10, 10, 10)
        else:
            # Очищаем layout
            self.clear_layout(layout)

        # Панель поиска
        search_frame = QFrame()
        search_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 10px;
                border: 1px solid #dee2e6;
                padding: 10px;
            }
        """)
        search_layout = QHBoxLayout(search_frame)

        search_icon = QLabel("🔍")
        search_icon.setStyleSheet("font-size: 10px;")
        search_layout.addWidget(search_icon)

        self.study_search_edit = QLineEdit()
        self.study_search_edit.setPlaceholderText("Поиск по названию материала...")
        self.study_search_edit.setStyleSheet("""
            QLineEdit {
                border: none;
                padding: 1px;
                font-size: 13px;
                background-color: transparent;
            }
            QLineEdit:focus {
                border: none;
            }
        """)
        self.study_search_edit.textChanged.connect(self.filter_study_materials)
        search_layout.addWidget(self.study_search_edit)

        clear_search_btn = QPushButton("✖")
        clear_search_btn.setFixedSize(30, 30)
        clear_search_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #6c757d;
                border: none;
                font-size: 14px;
            }
            QPushButton:hover {
                color: #e74c3c;
            }
        """)
        clear_search_btn.clicked.connect(lambda: self.study_search_edit.clear())
        search_layout.addWidget(clear_search_btn)

        layout.addWidget(search_frame)

        # Область для материалов (видна всем)
        studyScrollArea = QScrollArea()
        studyScrollArea.setWidgetResizable(True)
        studyScrollArea.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                background: #e9ecef;
                width: 10px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical {
                background: #3498db;
                border-radius: 5px;
            }
        """)

        studyContent = QWidget()
        studyContent.setStyleSheet("background-color: transparent;")
        studyMaterialsLayout = QVBoxLayout(studyContent)
        studyMaterialsLayout.setSpacing(10)
        studyMaterialsLayout.setContentsMargins(5, 5, 5, 5)
        studyScrollArea.setWidget(studyContent)
        layout.addWidget(studyScrollArea)

        # Сохраняем ссылки
        self.studyScrollArea = studyScrollArea
        self.studyContent = studyContent
        self.studyMaterialsLayout = studyMaterialsLayout
        self.all_study_materials = []  # Для хранения всех материалов

    def filter_study_materials(self):
        """Фильтрация учебных материалов по поиску"""
        search_text = self.study_search_edit.text().strip().lower()

        if not hasattr(self, 'all_study_materials'):
            return

        if not search_text:
            filtered_materials = self.all_study_materials
        else:
            filtered_materials = [m for m in self.all_study_materials
                                  if search_text in m['filename'].lower()]

        self.display_study_materials(filtered_materials)

    def display_study_materials(self, materials):
        """Отображение учебных материалов в таблице"""
        if not hasattr(self, 'studyMaterialsLayout'):
            return

        # Очищаем layout
        for i in reversed(range(self.studyMaterialsLayout.count())):
            widget = self.studyMaterialsLayout.itemAt(i).widget()
            if widget:
                widget.deleteLater()

        if not materials:
            no_data = QLabel("📭 Нет учебных материалов")
            no_data.setAlignment(Qt.AlignCenter)
            no_data.setStyleSheet("color: #6c7086; padding: 40px; font-size: 16px;")
            self.studyMaterialsLayout.addWidget(no_data)
            return

        # Создаем контейнер для таблицы с границей
        table_container = QFrame()
        table_container.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #dee2e6;
                border-radius: 10px;
                padding: 0px;
            }
        """)
        container_layout = QVBoxLayout(table_container)
        container_layout.setContentsMargins(0, 0, 0, 0)

        # Создаем таблицу для материалов
        table = QTableWidget()
        table.setColumnCount(3)
        table.setHorizontalHeaderLabels(["Тип", "Название", ""])

        # Центрирование заголовков
        header = table.horizontalHeader()
        header.setDefaultAlignment(Qt.AlignCenter)
        header.setStretchLastSection(True)

        # Настройка внешнего вида
        table.setAlternatingRowColors(True)
        table.setShowGrid(False)
        table.verticalHeader().setVisible(False)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.setSelectionBehavior(QTableWidget.SelectRows)
        table.setSelectionMode(QTableWidget.SingleSelection)

        # Устанавливаем высоту строк
        table.verticalHeader().setDefaultSectionSize(50)

        table.setStyleSheet("""
            QTableWidget {
                background-color: transparent;
                border: none;
                outline: none;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #dee2e6;
            }
            QTableWidget::item:selected {
                background-color: #e3f2fd;
                color: #2c3e50;
            }
            QHeaderView::section {
                background-color: #f8f9fa;
                color: #2c3e50;
                padding: 10px;
                border: none;
                border-bottom: 2px solid #dee2e6;
                font-weight: bold;
                font-size: 13px;
            }
        """)

        table.setRowCount(len(materials))

        for row, material in enumerate(materials):
            # Тип с иконкой - центрирование
            file_type = material.get('file_type', 'text')
            if file_type == 'pdf':
                type_icon = "📑 PDF"
                type_color = "#e74c3c"
            elif file_type == 'image':
                type_icon = "🖼️ Изображение"
                type_color = "#27ae60"
            else:
                type_icon = "📄 Текст"
                type_color = "#3498db"

            type_item = QTableWidgetItem(type_icon)
            type_item.setForeground(QColor(type_color))
            type_item.setTextAlignment(Qt.AlignCenter)
            table.setItem(row, 0, type_item)

            # Название - центрирование полностью
            name_item = QTableWidgetItem(material['filename'])
            name_item.setToolTip(material.get('description', ''))
            name_item.setTextAlignment(Qt.AlignCenter)
            table.setItem(row, 1, name_item)

            # Кнопка открытия
            open_btn = QPushButton("📖 Открыть")
            open_btn.setFixedSize(90, 34)
            open_btn.setStyleSheet("""
                QPushButton {
                    background-color: #3498db;
                    color: white;
                    border: none;
                    border-radius: 5px;
                    font-size: 11px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #2980b9;
                }
                QPushButton:pressed {
                    background-color: #1c6ea4;
                }
            """)
            open_btn.clicked.connect(lambda checked, m=material: self.open_material(m))

            # Устанавливаем кнопку
            table.setCellWidget(row, 2, open_btn)

        # Настройка ширины колонок
        table.setColumnWidth(0, 130)  # Тип
        table.setColumnWidth(1, 450)  # Название

        # Центрирование кнопок
        for row in range(len(materials)):
            btn = table.cellWidget(row, 2)
            if btn:
                cell_widget = QWidget()
                cell_layout = QHBoxLayout(cell_widget)
                cell_layout.setContentsMargins(0, 0, 0, 0)
                cell_layout.setAlignment(Qt.AlignCenter)
                cell_layout.addWidget(btn)
                table.setCellWidget(row, 2, cell_widget)

        # Подключаем двойной клик для открытия
        table.cellDoubleClicked.connect(lambda row, col: self.open_material(materials[row]))

        container_layout.addWidget(table)
        self.studyMaterialsLayout.addWidget(table_container)

    def view_user_full_stats(self, user_id):
        """Просмотр полной статистики пользователя (для админа)"""
        user = self.db.get_user_by_id(user_id)
        if not user:
            return

        stats = self.db.get_user_detailed_stats(user_id)
        results = self.db.get_user_test_results(user_id)

        dialog = QDialog(self)
        dialog.setWindowTitle(f"Полная статистика: {user['full_name']}")
        dialog.setMinimumSize(1000, 800)
        dialog.resize(1100, 850)
        dialog.setModal(True)
        dialog.setStyleSheet("""
            QDialog {
                background-color: #f0f2f5;
            }
            QLabel {
                color: #2c3e50;
            }
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QTabWidget::pane {
                background-color: white;
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
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                background: #e9ecef;
                width: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: #3498db;
                border-radius: 4px;
            }
        """)

        # Основной layout
        main_layout = QVBoxLayout(dialog)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Scroll area для всего содержимого
        main_scroll = QScrollArea()
        main_scroll.setWidgetResizable(True)
        main_scroll.setStyleSheet("border: none; background-color: transparent;")

        # Контейнер для содержимого
        content_widget = QWidget()
        content_widget.setStyleSheet("background-color: #f0f2f5;")
        layout = QVBoxLayout(content_widget)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # Информация о пользователе
        info_frame = QFrame()
        info_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 15px;
                border: 1px solid #dee2e6;
            }
        """)
        info_layout = QVBoxLayout(info_frame)
        info_layout.setContentsMargins(20, 20, 20, 20)

        info_text = f"""
        <div style='text-align: center;'>
            <h2 style='color: #2c3e50; margin: 0 0 10px 0;'>👤 {user['full_name']}</h2>
            <p style='color: #6c757d; margin: 5px 0;'><b>Логин:</b> {user['username']}</p>
            <hr style='border-color: #dee2e6; margin: 15px 0;'>
            <table style='width: 100%;'>
                <tr>
                    <td style='padding: 8px;'><b>📝 Всего тестов:</b></td>
                    <td style='padding: 8px; color: #2c3e50;'>{stats['total_tests']}</td>
                    <td style='padding: 8px;'><b>✅ Сдано:</b></td>
                    <td style='padding: 8px; color: #27ae60;'>{stats['passed_tests']}</td>
                </tr>
                <tr>
                    <td style='padding: 8px;'><b>❌ Не сдано:</b></td>
                    <td style='padding: 8px; color: #e74c3c;'>{stats['failed_tests']}</td>
                    <td style='padding: 8px;'><b>📈 Средний балл:</b></td>
                    <td style='padding: 8px; color: #2c3e50;'>{stats['avg_percent']:.1f}%</td>
                </tr>
                <tr>
                    <td style='padding: 8px;'><b>✅ Верных ответов:</b></td>
                    <td style='padding: 8px; color: #2c3e50;'>{stats['total_correct']}</td>
                    <td style='padding: 8px;'><b>📝 Всего вопросов:</b></td>
                    <td style='padding: 8px; color: #2c3e50;'>{stats['total_questions']}</td>
                </tr>
                <tr>
                    <td style='padding: 8px;'><b>🏆 Лучший результат:</b></td>
                    <td style='padding: 8px; color: #27ae60;'>{stats['best_result']:.1f}%</td>
                    <td style='padding: 8px;'><b>📉 Худший результат:</b></td>
                    <td style='padding: 8px; color: #e74c3c;'>{stats['worst_result']:.1f}%</td>
                </tr>
            </table>
        </div>
        """
        info_label = QLabel(info_text)
        info_label.setWordWrap(True)
        info_label.setStyleSheet("background-color: transparent;")
        info_layout.addWidget(info_label)
        layout.addWidget(info_frame)

        # Вкладки с графиками и деталями
        tabs = QTabWidget()
        tabs.setStyleSheet("""
            QTabWidget::pane {
                background-color: white;
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
        """)

        # Вкладка с графиками
        charts_tab = QWidget()
        charts_layout = QVBoxLayout(charts_tab)
        charts_layout.setContentsMargins(15, 15, 15, 15)

        # График динамики
        chart_label = QLabel("📈 Динамика результатов тестирования")
        chart_label.setFont(QFont("Segoe UI", 12, QFont.Bold))
        chart_label.setStyleSheet("color: #2c3e50; margin-bottom: 10px;")
        charts_layout.addWidget(chart_label)

        chart_widget = StatisticsChart()
        chart_widget.update_chart(results, passing_threshold=80)
        charts_layout.addWidget(chart_widget)

        # Круговая диаграмма
        if stats['total_tests'] > 0:
            pie_label = QLabel("📊 Соотношение результатов")
            pie_label.setFont(QFont("Segoe UI", 12, QFont.Bold))
            pie_label.setStyleSheet("color: #2c3e50; margin: 20px 0 10px 0;")
            charts_layout.addWidget(pie_label)

            pie_widget = StatisticsChart()
            pie_widget.create_pie_chart(
                [stats['passed_tests'], stats['failed_tests']],
                ['Успешно', 'Не сдано'],
                'Соотношение результатов'
            )
            charts_layout.addWidget(pie_widget)

        charts_layout.addStretch()
        tabs.addTab(charts_tab, "📊 Графики")

        # Вкладка с детальными результатами
        details_tab = QWidget()
        details_layout = QVBoxLayout(details_tab)
        details_layout.setContentsMargins(15, 15, 15, 15)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                background: #e9ecef;
                width: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: #3498db;
                border-radius: 4px;
            }
        """)

        scroll_widget = QWidget()
        scroll_widget.setStyleSheet("background-color: transparent;")
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_layout.setSpacing(10)

        if results:
            for i, result in enumerate(results, 1):
                card = QFrame()
                card.setStyleSheet("""
                    QFrame {
                        background-color: #f8f9fa;
                        border-radius: 12px;
                        border: 1px solid #dee2e6;
                        margin: 5px;
                    }
                    QFrame:hover {
                        background-color: #f0f2f5;
                    }
                """)

                percent = result['score'] / result['total'] * 100
                status = "✅ Сдано" if result['passed'] else "❌ Не сдано"
                status_color = "#27ae60" if result['passed'] else "#e74c3c"
                status_bg = "#d4edda" if result['passed'] else "#f8d7da"

                date_obj = datetime.fromisoformat(result['date'].replace(' ', 'T'))
                date_str = date_obj.strftime('%d.%m.%Y %H:%M:%S')

                card_layout = QVBoxLayout(card)
                card_layout.setSpacing(10)
                card_layout.setContentsMargins(15, 12, 15, 12)

                # Заголовок
                header_layout = QHBoxLayout()

                title_label = QLabel(f"<b>Попытка #{i}</b>")
                title_label.setStyleSheet("color: #3498db; font-size: 14px;")
                header_layout.addWidget(title_label)

                header_layout.addStretch()

                date_label = QLabel(f"📅 {date_str}")
                date_label.setStyleSheet("color: #6c757d; font-size: 11px;")
                header_layout.addWidget(date_label)

                card_layout.addLayout(header_layout)

                # Результат
                result_layout = QHBoxLayout()

                result_label = QLabel(f"📊 Результат: <b>{result['score']}/{result['total']}</b> ({percent:.1f}%)")
                result_label.setStyleSheet("color: #2c3e50;")
                result_layout.addWidget(result_label)

                result_layout.addStretch()

                status_label = QLabel(status)
                status_label.setStyleSheet(f"""
                    QLabel {{
                        color: {status_color};
                        background-color: {status_bg};
                        padding: 4px 12px;
                        border-radius: 12px;
                        font-size: 11px;
                        font-weight: bold;
                    }}
                """)
                result_layout.addWidget(status_label)

                card_layout.addLayout(result_layout)

                # Кнопка просмотра деталей
                view_btn = QPushButton("📖 Посмотреть детали")
                view_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #3498db;
                        color: white;
                        border: none;
                        border-radius: 6px;
                        padding: 6px 12px;
                        font-size: 12px;
                    }
                    QPushButton:hover {
                        background-color: #2980b9;
                    }
                """)
                view_btn.clicked.connect(lambda checked, rid=result['id']: self.view_test_details(rid))
                card_layout.addWidget(view_btn)

                scroll_layout.addWidget(card)
        else:
            no_data_label = QLabel("📭 Нет пройденных тестов")
            no_data_label.setAlignment(Qt.AlignCenter)
            no_data_label.setStyleSheet("color: #6c757d; padding: 40px; font-size: 14px;")
            scroll_layout.addWidget(no_data_label)

        scroll_layout.addStretch()
        scroll.setWidget(scroll_widget)
        details_layout.addWidget(scroll)
        tabs.addTab(details_tab, "📋 Детальные результаты")

        layout.addWidget(tabs)

        # Кнопка закрытия
        close_btn = QPushButton("✖ Закрыть")
        close_btn.setMinimumWidth(120)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                margin-top: 10px;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(close_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        main_scroll.setWidget(content_widget)
        main_layout.addWidget(main_scroll)

        close_btn.clicked.connect(dialog.accept)
        dialog.exec_()

    def setup_mistakes_tab(self):
        """Настройка вкладки ошибок - используем виджеты из UI или создаем новые"""
        # Получаем или создаем layout
        layout = self.mistakesTab.layout()
        if layout is None:
            layout = QVBoxLayout(self.mistakesTab)
            layout.setContentsMargins(10, 10, 10, 10)
        else:
            # Очищаем layout, но не удаляем сами виджеты (они удалятся при clear_layout)
            self.clear_layout(layout)

        # Заголовок
        header_layout = QHBoxLayout()

        mistakesLabel = QLabel("❗ Вопросы, в которых были допущены ошибки:")
        mistakesLabel.setFont(QFont("", 14, QFont.Bold))
        mistakesLabel.setStyleSheet("color: #2c3e50;")
        header_layout.addWidget(mistakesLabel)

        header_layout.addStretch()

        layout.addLayout(header_layout)

        # Scroll area для списка ошибок
        mistakesScrollArea = QScrollArea()
        mistakesScrollArea.setWidgetResizable(True)
        mistakesScrollArea.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                background: #e9ecef;
                width: 10px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical {
                background: #3498db;
                border-radius: 5px;
            }
        """)

        mistakesContent = QWidget()
        mistakesContent.setStyleSheet("background-color: transparent;")
        mistakesLayout = QVBoxLayout(mistakesContent)
        mistakesLayout.setSpacing(10)
        mistakesLayout.setContentsMargins(5, 5, 5, 5)
        mistakesScrollArea.setWidget(mistakesContent)
        layout.addWidget(mistakesScrollArea)

        # Сохраняем ссылки
        self.mistakesScrollArea = mistakesScrollArea
        self.mistakesContent = mistakesContent
        self.mistakesLayout = mistakesLayout

    def show_login_dialog(self):
        """Показ диалога входа"""
        self.hide()
        self.clear_ui_state()  # Очищаем состояние перед входом

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

    def setup_admin_users_tab(self):
        """Улучшенный дизайн таблицы пользователей"""
        layout = QVBoxLayout(self.admin_users_tab)

        add_button = QPushButton("➕ Добавить пользователя")
        add_button.clicked.connect(self.add_user_dialog)
        layout.addWidget(add_button)

        # Используем QTableWidget для красивого отображения
        self.users_table = QTableWidget()
        self.users_table.setColumnCount(3)
        self.users_table.setHorizontalHeaderLabels(["ФИО", "Логин", "Действия"])
        self.users_table.horizontalHeader().setStretchLastSection(True)
        self.users_table.setAlternatingRowColors(True)
        self.users_table.setStyleSheet("""
            QTableCornerButton::section {
                background-color: transparent;
                border: none;
            }
        """)

        # Настройка ширины колонок
        self.users_table.setColumnWidth(0, 400)  # ID
        self.users_table.setColumnWidth(1, 400)  # ФИО
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
        self.questions_table.setColumnCount(2)
        self.questions_table.setHorizontalHeaderLabels(["Вопрос", "Действия"])
        self.questions_table.horizontalHeader().setStretchLastSection(True)
        self.questions_table.setAlternatingRowColors(True)
        self.questions_table.setStyleSheet("""
            QTableCornerButton::section {
                background-color: transparent;
                border: none;
            }
        """)

        self.questions_table.setColumnWidth(0, 850)  # ID
        layout.addWidget(self.questions_table)

        self.load_questions_list()

    def setup_admin_materials_tab(self):
        """Настройка админской вкладки материалов с поиском"""
        layout = QVBoxLayout(self.admin_materials_tab)

        add_button = QPushButton("➕ Добавить учебный материал")
        add_button.clicked.connect(self.add_learning_material)
        layout.addWidget(add_button)

        # Панель поиска
        search_frame = QFrame()
        search_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 10px;
                border: 1px solid #dee2e6;
                padding: 8px;
                margin-top: 10px;
            }
        """)
        search_layout = QHBoxLayout(search_frame)

        search_icon = QLabel("🔍")
        search_icon.setStyleSheet("font-size: 10px;")
        search_layout.addWidget(search_icon)

        self.admin_materials_search_edit = QLineEdit()
        self.admin_materials_search_edit.setPlaceholderText("Поиск по названию материала...")
        self.admin_materials_search_edit.setStyleSheet("""
            QLineEdit {
                border: none;
                padding: 1px;
                font-size: 13px;
                background-color: transparent;
            }
        """)
        self.admin_materials_search_edit.textChanged.connect(self.filter_admin_materials)
        search_layout.addWidget(self.admin_materials_search_edit)

        clear_search_btn = QPushButton("✖")
        clear_search_btn.setFixedSize(30, 30)
        clear_search_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #6c757d;
                border: none;
                font-size: 14px;
            }
            QPushButton:hover {
                color: #e74c3c;
            }
        """)
        clear_search_btn.clicked.connect(lambda: self.admin_materials_search_edit.clear())
        search_layout.addWidget(clear_search_btn)

        layout.addWidget(search_frame)

        self.admin_materials_table = QTableWidget()
        self.admin_materials_table.setColumnCount(3)
        self.admin_materials_table.setHorizontalHeaderLabels(["Название", "Тип", "Действия"])
        self.admin_materials_table.setStyleSheet("""
            QTableCornerButton::section {
                background-color: transparent;
                border: none;
            }
            QTableWidget {
                background-color: white;
                border: 1px solid #dee2e6;
                border-radius: 10px;
            }
            QHeaderView::section {
                background-color: #f8f9fa;
                color: #2c3e50;
                padding: 8px;
                border: none;
                border-bottom: 2px solid #dee2e6;
                font-weight: bold;
            }
        """)
        self.admin_materials_table.setColumnWidth(0, 600)
        self.admin_materials_table.setColumnWidth(1, 150)
        self.admin_materials_table.horizontalHeader().setStretchLastSection(True)
        self.admin_materials_table.setAlternatingRowColors(True)
        layout.addWidget(self.admin_materials_table)

        self.load_admin_materials()

    def filter_admin_materials(self):
        """Фильтрация материалов в админской таблице"""
        search_text = self.admin_materials_search_edit.text().strip().lower()

        if not hasattr(self, 'all_admin_materials'):
            return

        if not search_text:
            filtered_materials = self.all_admin_materials
        else:
            filtered_materials = [m for m in self.all_admin_materials
                                  if search_text in m['filename'].lower()]

        self.display_admin_materials(filtered_materials)

    def display_admin_materials(self, materials):
        """Отображение материалов в админской таблице"""
        self.admin_materials_table.setRowCount(0)

        for material in materials:
            row = self.admin_materials_table.rowCount()
            self.admin_materials_table.insertRow(row)

            self.admin_materials_table.setItem(row, 0, QTableWidgetItem(material['filename']))

            file_type = material['file_type']
            type_icon = "📄" if file_type == 'text' else "🖼" if file_type == 'image' else "📑"
            self.admin_materials_table.setItem(row, 1, QTableWidgetItem(f"{type_icon} {file_type.upper()}"))

            delete_btn = QPushButton("🗑 Удалить")
            delete_btn.setStyleSheet("""
                QPushButton {
                    background-color: #3498db;
                    color: white;
                    border: none;
                    border-radius: 5px;
                    padding: 5px 10px;
                }
                QPushButton:hover {
                    background-color: #3498db;
                }
            """)
            delete_btn.clicked.connect(lambda checked, mid=material['id']: self.delete_material(mid))
            self.admin_materials_table.setCellWidget(row, 2, delete_btn)

    def load_users_list(self):
        """Загрузка пользователей в таблицу"""
        self.users_table.setRowCount(0)
        users = self.db.get_all_users()

        for user in users:
            if user['role'] == 'admin':
                continue

            row = self.users_table.rowCount()
            self.users_table.insertRow(row)

            self.users_table.setItem(row, 0, QTableWidgetItem(user['full_name']))
            self.users_table.setItem(row, 1, QTableWidgetItem(user['username']))

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
                    background-color: #3498db;
                    color: #fff;
                    padding: 5px 10px;
                    font-size: 11px;
                }
                QPushButton:hover {
                    background-color: #3498db;
                    opacity: 0.8;
                }
            """)

            # Кнопка удаления
            delete_btn = QPushButton("🗑 Удалить")
            delete_btn.clicked.connect(lambda checked, uid=user['id']: self.delete_user(uid))
            delete_btn.setStyleSheet("""
                QPushButton {
                    background-color: #3498db;
                    color: #fff;
                    padding: 5px 10px;
                    font-size: 11px;
                }
                QPushButton:hover {
                    background-color: #3498db;
                    opacity: 0.8;
                }
            """)

            buttons_layout.addWidget(edit_btn)
            buttons_layout.addWidget(delete_btn)
            self.users_table.setCellWidget(row, 2, buttons_widget)

    def load_questions_list(self):
        """Загрузка вопросов в таблицу"""
        self.questions_table.setRowCount(0)
        questions = self.db.get_all_questions()

        for q in questions:
            row = self.questions_table.rowCount()
            self.questions_table.insertRow(row)

            self.questions_table.setItem(row, 0, QTableWidgetItem(q['text'][:100] + "..."))

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
            self.questions_table.setCellWidget(row, 1, buttons_widget)

    def load_admin_materials(self):
        """Загрузка материалов в таблицу для админа"""
        materials = self.db.get_all_learning_materials()
        self.all_admin_materials = materials
        self.display_admin_materials(materials)

    def load_study_materials(self):
        """Загрузка учебных материалов"""
        materials = self.db.get_all_learning_materials()
        self.all_study_materials = materials
        self.display_study_materials(materials)

    def open_material(self, material):
        """Открытие материала во встроенном просмотрщике"""
        try:
            dialog = MaterialViewerDialog(material, self)
            dialog.exec_()
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Не удалось открыть материал:\n{str(e)}")

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
            card.setStyleSheet("background-color: #f5f5f5; border-radius: 10px; margin: 1px; padding: 3px;")

            card_layout = QVBoxLayout(card)

            question = QLabel(f"❓ {mistake['text']}")
            question.setWordWrap(True)
            question.setFont(QFont("", 11, QFont.Bold))
            question.setStyleSheet("color: #000;")
            card_layout.addWidget(question)

            correct_options = []
            for i in range(4):
                if (mistake['correct_mask'] >> i) & 1:
                    correct_options.append(mistake[f'option{i + 1}'])

            correct_text = f"✅ <b>Правильный ответ:</b> {', '.join(correct_options)}"
            correct_label = QLabel(correct_text)
            correct_label.setWordWrap(True)
            correct_label.setStyleSheet("color: #000;")
            card_layout.addWidget(correct_label)

            if mistake.get('explanation'):
                explanation = QLabel(f"💡 <b>Пояснение:</b> {mistake['explanation']}")
                explanation.setWordWrap(True)
                explanation.setStyleSheet("color: #000;")
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
        dialog.setMinimumSize(550, 600)
        dialog.resize(600, 650)
        dialog.setModal(True)
        dialog.setStyleSheet("""
            QDialog {
                background-color: #f0f2f5;
            }
            QLabel {
                color: #2c3e50;
                font-weight: bold;
                margin-top: 5px;
                margin-bottom: 2px;
            }
            QLineEdit, QTextEdit, QComboBox {
                background-color: white;
                color: #2c3e50;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                padding: 8px 10px;
                font-size: 13px;
            }
            QLineEdit:focus, QTextEdit:focus, QComboBox:focus {
                border-color: #3498db;
            }
            QTextEdit {
                min-height: 60px;
                max-height: 80px;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #2c3e50;
                margin-right: 5px;
            }
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #1c6ea4;
            }
            QPushButton#fileBtn {
                background-color: #6c757d;
            }
            QPushButton#fileBtn:hover {
                background-color: #5a6268;
            }
            QPushButton#cancelBtn {
                background-color: #6c757d;
            }
            QPushButton#cancelBtn:hover {
                background-color: #5a6268;
            }
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                background: #e9ecef;
                width: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: #3498db;
                border-radius: 4px;
            }
        """)

        # Основной layout
        main_layout = QVBoxLayout(dialog)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("border: none; background-color: transparent;")

        # Контейнер для содержимого
        content_widget = QWidget()
        content_widget.setStyleSheet("background-color: #f0f2f5;")
        layout = QVBoxLayout(content_widget)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        # Название
        name_label = QLabel("📝 Название материала:")
        layout.addWidget(name_label)
        filename_edit = QLineEdit()
        filename_edit.setStyleSheet('border: 1px solid;')
        filename_edit.setPlaceholderText("Введите название материала...")
        layout.addWidget(filename_edit)

        # Описание
        desc_label = QLabel("📄 Описание (необязательно):")
        layout.addWidget(desc_label)
        desc_edit = QTextEdit()
        desc_edit.setStyleSheet('border: 1px solid;')
        desc_edit.setPlaceholderText("Введите описание материала...")
        desc_edit.setMaximumHeight(70)
        layout.addWidget(desc_edit)

        # Разделитель
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("background-color: #dee2e6; max-height: 1px; margin: 10px 0;")
        layout.addWidget(line)

        # Тип материала
        type_label = QLabel("📌 Тип материала:")
        layout.addWidget(type_label)
        type_combo = QComboBox()
        type_combo.addItems(["Текст", "Изображение", "PDF"])
        type_combo.setStyleSheet("padding: 8px;")
        layout.addWidget(type_combo)

        # Контейнер для содержимого в зависимости от типа
        content_container = QFrame()
        content_container.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #dee2e6;
                border-radius: 10px;
                margin-top: 5px;
            }
        """)
        content_container_layout = QVBoxLayout(content_container)
        content_container_layout.setSpacing(10)
        content_container_layout.setContentsMargins(15, 15, 15, 15)

        # Для текста
        content_edit = QTextEdit()
        content_edit.setPlaceholderText("Введите содержание материала...")
        content_edit.setStyleSheet('border: 1px solid;')
        content_edit.setMinimumHeight(150)
        content_container_layout.addWidget(content_edit)

        # Для файла (изображение/PDF)
        file_widget = QWidget()
        file_layout = QVBoxLayout(file_widget)

        file_button = QPushButton("📁 Выбрать файл")
        file_button.setStyleSheet('color: #000;')
        file_button.setObjectName("fileBtn")
        file_button.setMinimumHeight(40)
        file_layout.addWidget(file_button)

        file_name_label = QLabel("Файл не выбран")
        file_name_label.setStyleSheet("color: #000; font-size: 12px; font-weight: normal; margin: 5px 0;")
        file_name_label.setAlignment(Qt.AlignCenter)
        file_layout.addWidget(file_name_label)

        file_preview_label = QLabel()
        file_preview_label.setAlignment(Qt.AlignCenter)
        file_preview_label.setMinimumHeight(100)
        file_preview_label.setStyleSheet("""
            background-color: #f8f9fa;
            border-radius: 8px;
            border: 1px dashed #dee2e6;
            padding: 10px;
            color: #6c757d;
        """)
        file_preview_label.setText("🖼️ Предпросмотр")
        file_layout.addWidget(file_preview_label)

        file_widget.hide()
        content_container_layout.addWidget(file_widget)

        # Изначально показываем текстовое поле, скрываем файловое
        content_edit.show()
        file_widget.hide()

        layout.addWidget(content_container)

        selected_file_path = None
        selected_file_type = None

        def on_type_changed():
            nonlocal selected_file_path, selected_file_type
            material_type = type_combo.currentText()

            # Сбрасываем выбранный файл
            selected_file_path = None
            selected_file_type = None
            file_name_label.setText("Файл не выбран")
            file_name_label.setStyleSheet("color: #000; font-size: 12px; font-weight: normal;")
            file_preview_label.clear()
            file_preview_label.setText("🖼️ Предпросмотр")

            if material_type == "Текст":
                content_edit.show()
                file_widget.hide()
            else:
                content_edit.hide()
                file_widget.show()
                selected_file_type = "image" if material_type == "Изображение" else "pdf"

        type_combo.currentTextChanged.connect(on_type_changed)

        def select_file():
            nonlocal selected_file_path
            material_type = type_combo.currentText()

            if material_type == "Изображение":
                file_path, _ = QFileDialog.getOpenFileName(dialog, "Выберите изображение", "",
                                                           "Images (*.png *.jpg *.jpeg *.bmp *.gif)")
                if file_path:
                    selected_file_path = file_path
                    file_name_label.setText(f"✅ {os.path.basename(file_path)}")
                    file_name_label.setStyleSheet("color: #27ae60; font-size: 12px; font-weight: normal;")

                    # Показываем превью для изображений
                    pixmap = QPixmap(file_path)
                    if not pixmap.isNull():
                        scaled_pixmap = pixmap.scaled(200, 120, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                        file_preview_label.setPixmap(scaled_pixmap)
                        file_preview_label.setText("")
                    else:
                        file_preview_label.setText("❌ Не удалось загрузить")

            elif material_type == "PDF":
                file_path, _ = QFileDialog.getOpenFileName(dialog, "Выберите PDF файл", "", "PDF Files (*.pdf)")
                if file_path:
                    selected_file_path = file_path
                    file_name_label.setText(f"✅ {os.path.basename(file_path)}")
                    file_name_label.setStyleSheet("color: #27ae60; font-size: 12px; font-weight: normal;")
                    file_preview_label.setText("📑 PDF документ\nГотов к загрузке")
                    file_preview_label.setStyleSheet("""
                        background-color: #e3f2fd;
                        border-radius: 8px;
                        padding: 20px;
                        color: #3498db;
                        font-size: 14px;
                    """)

        file_button.clicked.connect(select_file)

        layout.addStretch()

        # Кнопки
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()

        save_button = QPushButton("💾 Сохранить материал")
        save_button.setStyleSheet('background-color: #3498db;')
        save_button.setMinimumWidth(150)
        buttons_layout.addWidget(save_button)

        cancel_button = QPushButton("❌ Отмена")
        cancel_button.setStyleSheet('background-color: #3498db;')
        cancel_button.setObjectName("cancelBtn")
        buttons_layout.addWidget(cancel_button)

        buttons_layout.addStretch()
        layout.addLayout(buttons_layout)

        scroll_area.setWidget(content_widget)
        main_layout.addWidget(scroll_area)

        def save_material():
            filename = filename_edit.text().strip()
            if not filename:
                QMessageBox.warning(dialog, "Ошибка", "Введите название материала")
                return

            material_type = type_combo.currentText()
            user = self.auth_manager.get_current_user()

            if not user:
                QMessageBox.warning(dialog, "Ошибка", "Пользователь не авторизован")
                return

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
                safe_filename = filename.replace(" ", "_").replace("/", "_").replace("\\", "_")
                new_filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{safe_filename}{ext}"
                new_path = os.path.join("materials", new_filename)

                try:
                    shutil.copy2(selected_file_path, new_path)
                except Exception as e:
                    QMessageBox.warning(dialog, "Ошибка", f"Не удалось скопировать файл:\n{str(e)}")
                    return

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
            QMessageBox.information(self, "Успех", "Материал успешно добавлен!")

        save_button.clicked.connect(save_material)
        cancel_button.clicked.connect(dialog.reject)
        dialog.exec_()

    def add_question_dialog(self):
        """Диалог добавления вопроса с поддержкой изображений и прокруткой"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Добавление вопроса")
        dialog.setMinimumSize(700, 600)
        dialog.resize(750, 700)
        dialog.setModal(True)
        dialog.setStyleSheet("""
            QDialog {
                background-color: #f0f2f5;
            }
            QLabel {
                color: #2c3e50;
                font-weight: bold;
                margin-top: 5px;
                margin-bottom: 2px;
            }
            QTextEdit, QLineEdit {
                background-color: white;
                color: #2c3e50;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                padding: 8px;
                font-size: 13px;
            }
            QTextEdit:focus, QLineEdit:focus {
                border-color: #3498db;
            }
            QCheckBox {
                color: #2c3e50;
                spacing: 8px;
                padding: 3px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border-radius: 3px;
                border: 2px solid #3498db;
                background-color: white;
            }
            QCheckBox::indicator:checked {
                background-color: #3498db;
            }
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton#clearBtn {
                background-color: #6c757d;
            }
            QPushButton#clearBtn:hover {
                background-color: #5a6268;
            }
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                background: #e9ecef;
                width: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: #3498db;
                border-radius: 4px;
            }
        """)

        # Основной layout
        main_layout = QVBoxLayout(dialog)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Scroll area для содержимого
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("border: none; background-color: transparent;")

        # Контейнер для содержимого
        content_widget = QWidget()
        content_widget.setStyleSheet("background-color: #f0f2f5;")
        layout = QVBoxLayout(content_widget)
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)

        # Текст вопроса
        question_label = QLabel("📝 Текст вопроса:")
        layout.addWidget(question_label)
        question_text = QTextEdit()
        question_text.setPlaceholderText("Введите текст вопроса...")
        question_text.setStyleSheet("border: 1px solid;")
        question_text.setMinimumHeight(80)
        question_text.setMaximumHeight(120)
        layout.addWidget(question_text)

        # Изображение
        image_label = QLabel("🖼️ Изображение для вопроса (необязательно):")
        layout.addWidget(image_label)

        image_buttons_layout = QHBoxLayout()
        select_image_btn = QPushButton("📁 Выбрать изображение")
        select_image_btn.setStyleSheet("color: #000;")
        clear_image_btn = QPushButton("🗑 Очистить")
        clear_image_btn.setStyleSheet("color: #000;")
        clear_image_btn.setObjectName("clearBtn")
        image_buttons_layout.addWidget(select_image_btn)
        image_buttons_layout.addWidget(clear_image_btn)
        image_buttons_layout.addStretch()
        layout.addLayout(image_buttons_layout)

        # Имя файла
        self.selected_image_name_label = QLabel("Файл не выбран")
        self.selected_image_name_label.setStyleSheet("color: #6c757d; font-size: 11px; font-weight: normal; margin: 0;")
        layout.addWidget(self.selected_image_name_label)

        # Превью изображения
        image_preview = QLabel()
        image_preview.setAlignment(Qt.AlignCenter)
        image_preview.setMinimumHeight(120)
        image_preview.setMaximumHeight(150)
        image_preview.setStyleSheet("""
            background-color: #f8f9fa;
            border-radius: 8px;
            border: 1px dashed #dee2e6;
            padding: 10px;
            color: #6c757d;
        """)
        image_preview.setText("🖼️ Предпросмотр изображения")
        layout.addWidget(image_preview)

        self.current_question_image_path = None

        def select_image():
            file_path, _ = QFileDialog.getOpenFileName(dialog, "Выберите изображение", QUESTIONS_IMAGES_DIR,
                                                       "Images (*.png *.jpg *.jpeg *.bmp *.gif)")
            if file_path:
                ext = os.path.splitext(file_path)[1]
                new_filename = f"q_{datetime.now().strftime('%Y%m%d_%H%M%S')}{ext}"
                new_path = os.path.join(QUESTIONS_IMAGES_DIR, new_filename)
                shutil.copy2(file_path, new_path)
                self.current_question_image_path = new_path

                self.selected_image_name_label.setText(f"📄 {os.path.basename(file_path)}")
                self.selected_image_name_label.setStyleSheet("color: #27ae60; font-size: 11px; font-weight: normal;")

                pixmap = QPixmap(new_path)
                if not pixmap.isNull():
                    scaled_pixmap = pixmap.scaled(400, 130, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    image_preview.setPixmap(scaled_pixmap)
                    image_preview.setText("")
                else:
                    image_preview.setText("❌ Не удалось загрузить изображение")

        def clear_image():
            self.current_question_image_path = None
            image_preview.clear()
            image_preview.setText("🖼️ Предпросмотр изображения")
            self.selected_image_name_label.setText("Файл не выбран")
            self.selected_image_name_label.setStyleSheet("color: #6c757d; font-size: 11px; font-weight: normal;")

        select_image_btn.clicked.connect(select_image)
        clear_image_btn.clicked.connect(clear_image)

        # Разделитель
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("background-color: #dee2e6; max-height: 1px; margin: 10px 0;")
        layout.addWidget(line)

        # Варианты ответов
        options_label = QLabel("📌 Варианты ответов:")
        options_label.setFont(QFont("", 11, QFont.Bold))
        layout.addWidget(options_label)

        options = []
        for i in range(4):
            opt_edit = QLineEdit()
            opt_edit.setPlaceholderText(f"Вариант {i + 1}")
            opt_edit.setStyleSheet("border: 1px solid;")
            opt_edit.setMinimumHeight(35)
            layout.addWidget(opt_edit)
            options.append(opt_edit)

        # Разделитель
        line2 = QFrame()
        line2.setFrameShape(QFrame.HLine)
        line2.setStyleSheet("background-color: #dee2e6; max-height: 1px; margin: 10px 0;")
        layout.addWidget(line2)

        # Правильные ответы
        correct_label = QLabel("✅ Правильные ответы (можно выбрать несколько):")
        correct_label.setFont(QFont("", 11, QFont.Bold))
        layout.addWidget(correct_label)

        correct_checkboxes = []
        checkboxes_layout = QHBoxLayout()
        for i in range(4):
            cb = QCheckBox(f"Вариант {i + 1}")
            checkboxes_layout.addWidget(cb)
            correct_checkboxes.append(cb)
        checkboxes_layout.addStretch()
        layout.addLayout(checkboxes_layout)

        # Разделитель
        line3 = QFrame()
        line3.setFrameShape(QFrame.HLine)
        line3.setStyleSheet("background-color: #dee2e6; max-height: 1px; margin: 10px 0;")
        layout.addWidget(line3)

        # Пояснение
        explanation_label = QLabel("💡 Пояснение к ответу:")
        layout.addWidget(explanation_label)
        explanation = QTextEdit()
        explanation.setPlaceholderText("Введите пояснение к правильному ответу...")
        explanation.setStyleSheet("border: 1px solid;")
        explanation.setMinimumHeight(70)
        explanation.setMaximumHeight(100)
        layout.addWidget(explanation)

        # Категория
        category_label = QLabel("📂 Категория (необязательно):")
        layout.addWidget(category_label)
        category_edit = QLineEdit()
        category_edit.setPlaceholderText("Например: Нормативная база, Организация службы...")
        category_edit.setStyleSheet("border: 1px solid;")
        layout.addWidget(category_edit)

        layout.addStretch()

        # Кнопки внизу
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        save_button = QPushButton("💾 Сохранить вопрос")
        save_button.setStyleSheet("background-color: #3498db")
        save_button.setMinimumWidth(130)
        cancel_btn = QPushButton("❌ Отмена")
        cancel_btn.setStyleSheet("background-color: #3498db")
        cancel_btn.setObjectName("clearBtn")
        buttons_layout.addWidget(save_button)
        buttons_layout.addWidget(cancel_btn)
        buttons_layout.addStretch()
        layout.addLayout(buttons_layout)

        scroll_area.setWidget(content_widget)
        main_layout.addWidget(scroll_area)

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
            QMessageBox.information(self, "Успех", "Вопрос успешно добавлен!")

        save_button.clicked.connect(save_question)
        cancel_btn.clicked.connect(dialog.reject)
        dialog.exec_()

    def edit_question(self, question_id):
        """Редактирование вопроса"""
        q = self.db.get_question_by_id(question_id)
        if not q:
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("Редактирование вопроса")
        dialog.setMinimumSize(700, 600)
        dialog.resize(750, 700)
        dialog.setModal(True)
        dialog.setStyleSheet("""
            QDialog {
                background-color: #f0f2f5;
            }
            QLabel {
                color: #2c3e50;
                font-weight: bold;
                margin-top: 5px;
                margin-bottom: 2px;
            }
            QTextEdit, QLineEdit {
                background-color: white;
                color: #2c3e50;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                padding: 8px;
                font-size: 13px;
            }
            QTextEdit:focus, QLineEdit:focus {
                border-color: #3498db;
            }
            QCheckBox {
                color: #2c3e50;
                spacing: 8px;
                padding: 3px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border-radius: 3px;
                border: 2px solid #3498db;
                background-color: white;
            }
            QCheckBox::indicator:checked {
                background-color: #3498db;
            }
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton#clearBtn {
                background-color: #6c757d;
            }
            QPushButton#clearBtn:hover {
                background-color: #5a6268;
            }
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                background: #e9ecef;
                width: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: #3498db;
                border-radius: 4px;
            }
        """)

        # Основной layout
        main_layout = QVBoxLayout(dialog)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Scroll area для содержимого
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("border: none; background-color: transparent;")

        # Контейнер для содержимого
        content_widget = QWidget()
        content_widget.setStyleSheet("background-color: #f0f2f5;")
        layout = QVBoxLayout(content_widget)
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)

        # Текст вопроса
        question_label = QLabel("📝 Текст вопроса:")
        layout.addWidget(question_label)
        question_text = QTextEdit()
        question_text.setStyleSheet("border: 1px solid;")
        question_text.setPlainText(q['text'])
        question_text.setMinimumHeight(80)
        question_text.setMaximumHeight(120)
        layout.addWidget(question_text)

        # Изображение
        image_label = QLabel("🖼️ Изображение для вопроса:")
        layout.addWidget(image_label)


        image_buttons_layout = QHBoxLayout()
        select_image_btn = QPushButton("📁 Выбрать изображение")
        select_image_btn.setStyleSheet("color: #000;")
        clear_image_btn = QPushButton("🗑 Очистить")
        clear_image_btn.setStyleSheet("color: #000;")
        clear_image_btn.setObjectName("clearBtn")
        image_buttons_layout.addWidget(select_image_btn)
        image_buttons_layout.addWidget(clear_image_btn)
        image_buttons_layout.addStretch()
        layout.addLayout(image_buttons_layout)

        # Имя файла
        image_name_label = QLabel()
        image_name_label.setStyleSheet("color: #6c757d; font-size: 11px; font-weight: normal;")
        layout.addWidget(image_name_label)

        # Превью
        image_preview = QLabel()
        image_preview.setAlignment(Qt.AlignCenter)
        image_preview.setMinimumHeight(120)
        image_preview.setMaximumHeight(150)
        image_preview.setStyleSheet("""
            background-color: #f8f9fa;
            border-radius: 8px;
            border: 1px dashed #dee2e6;
            padding: 10px;
        """)

        current_image = q.get('image_path')
        if current_image and os.path.exists(current_image):
            pixmap = QPixmap(current_image)
            if not pixmap.isNull():
                scaled_pixmap = pixmap.scaled(400, 130, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                image_preview.setPixmap(scaled_pixmap)
                image_name_label.setText(f"📄 {os.path.basename(current_image)}")
                image_name_label.setStyleSheet("color: #27ae60; font-size: 11px;")
            else:
                image_preview.setText("🖼️ Предпросмотр изображения")
                image_name_label.setText("Файл не выбран")
        else:
            image_preview.setText("🖼️ Предпросмотр изображения")
            image_name_label.setText("Файл не выбран")

        layout.addWidget(image_preview)

        def select_image():
            nonlocal current_image
            file_path, _ = QFileDialog.getOpenFileName(dialog, "Выберите изображение", QUESTIONS_IMAGES_DIR,
                                                       "Images (*.png *.jpg *.jpeg *.bmp *.gif)")
            if file_path:
                ext = os.path.splitext(file_path)[1]
                new_filename = f"q_{datetime.now().strftime('%Y%m%d_%H%M%S')}{ext}"
                new_path = os.path.join(QUESTIONS_IMAGES_DIR, new_filename)
                shutil.copy2(file_path, new_path)
                current_image = new_path

                pixmap = QPixmap(new_path)
                if not pixmap.isNull():
                    scaled_pixmap = pixmap.scaled(400, 130, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    image_preview.setPixmap(scaled_pixmap)
                    image_preview.setText("")
                    image_name_label.setText(f"📄 {os.path.basename(file_path)}")
                    image_name_label.setStyleSheet("color: #27ae60; font-size: 11px;")
                else:
                    image_preview.setText("❌ Не удалось загрузить изображение")

        def clear_image():
            nonlocal current_image
            current_image = None
            image_preview.clear()
            image_preview.setText("🖼️ Предпросмотр изображения")
            image_name_label.setText("Файл не выбран")
            image_name_label.setStyleSheet("color: #6c757d; font-size: 11px;")

        select_image_btn.clicked.connect(select_image)
        clear_image_btn.clicked.connect(clear_image)

        # Разделитель
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("background-color: #dee2e6; max-height: 1px; margin: 10px 0;")
        layout.addWidget(line)

        # Варианты ответов
        options_label = QLabel("📌 Варианты ответов:")
        options_label.setFont(QFont("", 11, QFont.Bold))
        layout.addWidget(options_label)

        options = []
        for i in range(4):
            opt_edit = QLineEdit()
            opt_edit.setText(q[f'option{i + 1}'])
            opt_edit.setPlaceholderText(f"Вариант {i + 1}")
            opt_edit.setStyleSheet("border: 1px solid;")
            opt_edit.setMinimumHeight(35)
            layout.addWidget(opt_edit)
            options.append(opt_edit)

        # Разделитель
        line2 = QFrame()
        line2.setFrameShape(QFrame.HLine)
        line2.setStyleSheet("background-color: #dee2e6; max-height: 1px; margin: 10px 0;")
        layout.addWidget(line2)

        # Правильные ответы
        correct_label = QLabel("✅ Правильные ответы (можно выбрать несколько):")
        correct_label.setFont(QFont("", 11, QFont.Bold))
        layout.addWidget(correct_label)

        correct_checkboxes = []
        checkboxes_layout = QHBoxLayout()
        for i in range(4):
            cb = QCheckBox(f"Вариант {i + 1}")
            cb.setChecked((q['correct_mask'] >> i) & 1)
            checkboxes_layout.addWidget(cb)
            correct_checkboxes.append(cb)
        checkboxes_layout.addStretch()
        layout.addLayout(checkboxes_layout)

        # Разделитель
        line3 = QFrame()
        line3.setFrameShape(QFrame.HLine)
        line3.setStyleSheet("background-color: #dee2e6; max-height: 1px; margin: 10px 0;")
        layout.addWidget(line3)

        # Пояснение
        explanation_label = QLabel("💡 Пояснение к ответу:")

        layout.addWidget(explanation_label)
        explanation = QTextEdit()
        explanation.setStyleSheet("border: 1px solid;")
        explanation.setPlainText(q.get('explanation', ''))
        explanation.setMinimumHeight(70)
        explanation.setMaximumHeight(100)
        layout.addWidget(explanation)

        # Категория
        category_label = QLabel("📂 Категория (необязательно):")
        layout.addWidget(category_label)
        category_edit = QLineEdit()
        category_edit.setStyleSheet("border: 1px solid;")
        category_edit.setText(q.get('category', ''))
        category_edit.setPlaceholderText("Например: Нормативная база, Организация службы...")
        layout.addWidget(category_edit)

        layout.addStretch()

        # Кнопки внизу
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        save_button = QPushButton("💾 Сохранить изменения")
        save_button.setStyleSheet("background-color: #3498db;")
        save_button.setMinimumWidth(130)
        cancel_btn = QPushButton("❌ Отмена")
        cancel_btn.setStyleSheet("background-color: #3498db;")
        cancel_btn.setObjectName("clearBtn")
        buttons_layout.addWidget(save_button)
        buttons_layout.addWidget(cancel_btn)
        buttons_layout.addStretch()
        layout.addLayout(buttons_layout)

        scroll_area.setWidget(content_widget)
        main_layout.addWidget(scroll_area)

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
            QMessageBox.information(self, "Успех", "Вопрос успешно обновлен!")

        save_button.clicked.connect(save_question)
        cancel_btn.clicked.connect(dialog.reject)
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
        dialog.setMinimumSize(450, 500)
        dialog.setModal(True)
        dialog.setStyleSheet("""
            QDialog {
                background-color: #f0f2f5;
            }
            QLabel {
                color: #2c3e50;
                font-weight: bold;
                font-size: 13px;
                margin-top: 5px;
            }
            QLineEdit, QComboBox {
                background-color: white;
                color: #2c3e50;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                padding: 10px 12px;
                font-size: 13px;
                font-family: Segoe UI;
            }
            QLineEdit:focus, QComboBox:focus {
                border-color: #3498db;
                outline: none;
            }
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-weight: bold;
                font-size: 13px;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #1c6ea4;
            }
            QPushButton#cancelButton {
                background-color: #6c757d;
            }
            QPushButton#cancelButton:hover {
                background-color: #5a6268;
            }
        """)

        layout = QVBoxLayout(dialog)
        layout.setSpacing(12)
        layout.setContentsMargins(25, 25, 25, 25)

        # ФИО
        full_name_label = QLabel("👤 ФИО пользователя:")
        layout.addWidget(full_name_label)
        full_name_edit = QLineEdit()
        full_name_edit.setPlaceholderText("Иванов Иван Иванович")
        layout.addWidget(full_name_edit)

        # Логин
        username_label = QLabel("🔑 Логин:")
        layout.addWidget(username_label)
        username_edit = QLineEdit()
        username_edit.setPlaceholderText("username")
        layout.addWidget(username_edit)

        # Пароль
        password_label = QLabel("🔒 Пароль:")
        layout.addWidget(password_label)
        password_edit = QLineEdit()
        password_edit.setPlaceholderText("••••••••")
        password_edit.setEchoMode(QLineEdit.Password)
        layout.addWidget(password_edit)

        # Подтверждение пароля
        confirm_label = QLabel("🔒 Подтверждение пароля:")
        layout.addWidget(confirm_label)
        confirm_edit = QLineEdit()
        confirm_edit.setPlaceholderText("••••••••")
        confirm_edit.setEchoMode(QLineEdit.Password)
        layout.addWidget(confirm_edit)

        # Роль
        role_label = QLabel("👔 Роль:")
        layout.addWidget(role_label)
        role_combo = QComboBox()
        role_combo.addItems(["user", "admin"])
        role_combo.setStyleSheet("""
            QComboBox {
                background-color: white;
                color: #2c3e50;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                padding: 10px 12px;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #2c3e50;
                margin-right: 5px;
            }
        """)
        layout.addWidget(role_combo)

        layout.addStretch()

        # Кнопки
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(15)
        buttons_layout.addStretch()

        save_btn = QPushButton("💾 Сохранить")
        save_btn.setCursor(Qt.PointingHandCursor)
        buttons_layout.addWidget(save_btn)

        cancel_btn = QPushButton("❌ Отмена")
        cancel_btn.setObjectName("cancelButton")
        cancel_btn.setStyleSheet('background-color: #3498db')
        cancel_btn.setCursor(Qt.PointingHandCursor)
        buttons_layout.addWidget(cancel_btn)

        buttons_layout.addStretch()
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

            if len(password) < 3:
                QMessageBox.warning(dialog, "Ошибка", "Пароль должен содержать не менее 3 символов")
                return

            if self.db.add_user(username, password, role, full_name):
                QMessageBox.information(dialog, "Успех", "Пользователь успешно добавлен!")
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
        dialog.setWindowTitle(f"Редактирование: {user['full_name']}")
        dialog.setMinimumSize(450, 620)
        dialog.setModal(True)
        dialog.setStyleSheet("""
            QDialog {
                background-color: #f0f2f5;
            }
            QLabel {
                color: #2c3e50;
                font-weight: bold;
                font-size: 13px;
                margin-top: 5px;
            }
            QLineEdit, QComboBox {
                background-color: white;
                color: #2c3e50;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                padding: 10px 12px;
                font-size: 13px;
            }
            QLineEdit:focus, QComboBox:focus {
                border-color: #3498db;
            }
            QCheckBox {
                color: #2c3e50;
                font-size: 13px;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border-radius: 4px;
                border: 2px solid #3498db;
                background-color: white;
            }
            QCheckBox::indicator:checked {
                background-color: #3498db;
            }
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-weight: bold;
                font-size: 13px;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton#cancelButton {
                background-color: #6c757d;
            }
            QPushButton#cancelButton:hover {
                background-color: #5a6268;
            }
        """)

        layout = QVBoxLayout(dialog)
        layout.setSpacing(12)
        layout.setContentsMargins(25, 25, 25, 25)

        # ФИО
        full_name_label = QLabel("👤 ФИО пользователя:")
        layout.addWidget(full_name_label)
        full_name_edit = QLineEdit()
        full_name_edit.setText(user['full_name'])
        layout.addWidget(full_name_edit)

        # Логин
        username_label = QLabel("🔑 Логин:")
        layout.addWidget(username_label)
        username_edit = QLineEdit()
        username_edit.setText(user['username'])
        layout.addWidget(username_edit)

        # Чекбокс смены пароля
        change_password_cb = QCheckBox("Изменить пароль")
        change_password_cb.setStyleSheet("margin-top: 10px;")
        layout.addWidget(change_password_cb)

        # Пароль (скрыт по умолчанию)
        password_label = QLabel("🔒 Новый пароль:")
        password_label.hide()
        layout.addWidget(password_label)
        password_edit = QLineEdit()
        password_edit.setPlaceholderText("новый пароль")
        password_edit.setEchoMode(QLineEdit.Password)
        password_edit.hide()
        layout.addWidget(password_edit)

        # Подтверждение пароля
        confirm_label = QLabel("🔒 Подтверждение пароля:")
        confirm_label.hide()
        layout.addWidget(confirm_label)
        confirm_edit = QLineEdit()
        confirm_edit.setPlaceholderText("повторите пароль")
        confirm_edit.setEchoMode(QLineEdit.Password)
        confirm_edit.hide()
        layout.addWidget(confirm_edit)

        # Роль
        role_label = QLabel("👔 Роль:")
        layout.addWidget(role_label)
        role_combo = QComboBox()
        role_combo.addItems(["user", "admin"])
        role_combo.setCurrentText(user['role'])
        role_combo.setStyleSheet("""
            QComboBox {
                background-color: white;
                color: #2c3e50;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                padding: 10px 12px;
            }
        """)
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
        buttons_layout.setSpacing(15)
        buttons_layout.addStretch()

        save_btn = QPushButton("💾 Сохранить")
        save_btn.setCursor(Qt.PointingHandCursor)
        buttons_layout.addWidget(save_btn)

        cancel_btn = QPushButton("❌ Отмена")
        cancel_btn.setObjectName("cancelButton")
        cancel_btn.setCursor(Qt.PointingHandCursor)
        cancel_btn.setStyleSheet('background-color: #3498db')
        buttons_layout.addWidget(cancel_btn)

        buttons_layout.addStretch()
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

                if len(password) < 3:
                    QMessageBox.warning(dialog, "Ошибка", "Пароль должен содержать не менее 3 символов")
                    return

                if self.db.update_user(user_id, username, full_name, role, password):
                    QMessageBox.information(dialog, "Успех", "Пользователь успешно обновлен")
                    dialog.accept()
                    self.load_users_list()
                else:
                    QMessageBox.warning(dialog, "Ошибка", "Не удалось обновить пользователя")
            else:
                # Обновляем без смены пароля
                if self.db.update_user(user_id, username, full_name, role):
                    QMessageBox.information(dialog, "Успех", "Пользователь успешно обновлен")
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


    def logout(self):
        """Выход из системы с полной очисткой"""
        # Очищаем состояние
        self.auth_manager.logout()
        self.clear_ui_state()

        # Очищаем данные пользователя из интерфейса
        if hasattr(self, 'userLabel'):
            self.userLabel.setText("Пользователь")

        # Закрываем главное окно и показываем диалог входа
        self.hide()

        # Создаем новый диалог входа
        login_dialog = LoginDialog(self.auth_manager, self)
        login_dialog.login_successful.connect(self.on_login_success)

        # Если диалог закрыт без входа - выходим
        if login_dialog.exec_() != QDialog.Accepted:
            QApplication.quit()
            sys.exit(0)

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
                    background-color: #f0f2f5;
                }
                QLabel {
                    color: #2c3e50;
                }
                QPushButton {
                    background-color: #e94560;
                    color: white;
                    border: none;
                    border-radius: 8px;
                    padding: 8px 16px;
                }
                QPushButton:hover {
                    background-color: #c0392b;
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
            <div style='background-color: #f0f2f5; border-radius: 15px; padding: 20px; border: 1px solid #dee2e6;'>
                <h2 style='color: #495057;'>👤 {user['full_name']}</h2>
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
                background-color: #f0f2f5;
            }
            QLabel {
                color: #2c3e50;
            }
            QPushButton {
                background-color: #e94560;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)

        layout = QVBoxLayout(dialog)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)

        # Общая информация
        percent = result['score'] / result['total'] * 100
        info_frame = QFrame()
        info_frame.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border-radius: 15px;
                border: 1px solid #dee2e6;
            }
        """)
        info_layout = QVBoxLayout(info_frame)

        info_label = QLabel(f"""
        <div style='text-align: center; padding: 20px;'>
            <h2 style='color: #e94560; margin: 0 0 10px 0;'>Результат теста</h2>
            <p style='margin: 5px 0;'><b>📅 Дата:</b> {result['date']}</p>
            <p style='margin: 5px 0;'><b>📊 Результат:</b> {result['score']}/{result['total']} ({percent:.1f}%)</p>
            <p style='margin: 5px 0;'><b>🏆 Статус:</b> <span style='color: {"#27ae60" if result['passed'] else "#e74c3c"}; font-weight: bold;'>
                {"✅ СДАНО" if result['passed'] else "❌ НЕ СДАНО"}
            </span></p>
        </div>
        """)
        info_label.setWordWrap(True)
        info_label.setStyleSheet("background-color: transparent;")
        info_layout.addWidget(info_label)

        layout.addWidget(info_frame)

        # Список вопросов
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                background: #e9ecef;
                width: 10px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical {
                background: #3498db;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical:hover {
                background: #2980b9;
            }
        """)

        scroll_widget = QWidget()
        scroll_widget.setStyleSheet("background-color: transparent;")
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_layout.setSpacing(10)
        scroll_layout.setContentsMargins(5, 5, 5, 5)

        for i, detail in enumerate(details, 1):
            if detail is None:
                continue

            card = QFrame()
            card.setStyleSheet(f"""
                QFrame {{
                    background-color: #ffffff;
                    border-radius: 12px;
                    margin: 5px;
                    padding: 15px;
                    border-left: 5px solid {"#27ae60" if detail['correct'] else "#e74c3c"};
                    border-right: 1px solid #dee2e6;
                    border-top: 1px solid #dee2e6;
                    border-bottom: 1px solid #dee2e6;
                }}
                QFrame:hover {{
                    background-color: #f8f9fa;
                }}
            """)

            card_layout = QVBoxLayout(card)
            card_layout.setSpacing(10)

            # Заголовок вопроса
            header_layout = QHBoxLayout()

            question_num = QLabel(f"<b>Вопрос {i}</b>")
            question_num.setStyleSheet("color: #3498db; font-size: 14px; background-color: transparent;")
            header_layout.addWidget(question_num)

            header_layout.addStretch()

            # Статус ответа
            status_text = "✅ ВЕРНО" if detail['correct'] else "❌ НЕВЕРНО"
            status_color = "#27ae60" if detail['correct'] else "#e74c3c"
            status_bg = "#d4edda" if detail['correct'] else "#f8d7da"

            status_label = QLabel(status_text)
            status_label.setStyleSheet(f"""
                QLabel {{
                    color: {status_color};
                    background-color: {status_bg};
                    padding: 4px 12px;
                    border-radius: 12px;
                    font-size: 11px;
                    font-weight: bold;
                }}
            """)
            header_layout.addWidget(status_label)

            card_layout.addLayout(header_layout)

            # Текст вопроса
            q_text = QLabel(detail['question_text'])
            q_text.setWordWrap(True)
            q_text.setStyleSheet("color: #2c3e50; font-size: 13px; background-color: transparent;")
            card_layout.addWidget(q_text)

            # Разделитель
            line = QFrame()
            line.setFrameShape(QFrame.HLine)
            line.setStyleSheet("background-color: #dee2e6; max-height: 1px;")
            card_layout.addWidget(line)

            # Ваш ответ
            selected_options = []
            for j, opt in enumerate(detail['options']):
                if (detail['selected_mask'] >> j) & 1:
                    selected_options.append(opt)

            your_answer_label = QLabel(
                f"<b>📌 Ваш ответ:</b> {', '.join(selected_options) if selected_options else 'Не выбран'}")
            your_answer_label.setWordWrap(True)
            if not detail['correct']:
                your_answer_label.setStyleSheet(
                    "color: #e74c3c; background-color: #fee; padding: 5px; border-radius: 6px;")
            else:
                your_answer_label.setStyleSheet(
                    "color: #27ae60; background-color: #efe; padding: 5px; border-radius: 6px;")
            card_layout.addWidget(your_answer_label)

            # Правильный ответ
            correct_options = []
            for j, opt in enumerate(detail['options']):
                if (detail['correct_mask'] >> j) & 1:
                    correct_options.append(opt)

            correct_answer_label = QLabel(f"<b>✅ Правильный ответ:</b> {', '.join(correct_options)}")
            correct_answer_label.setWordWrap(True)
            correct_answer_label.setStyleSheet(
                "color: #27ae60; background-color: #d4edda; padding: 5px; border-radius: 6px;")
            card_layout.addWidget(correct_answer_label)

            # Пояснение
            if detail.get('explanation'):
                explanation_label = QLabel(f"<b>💡 Пояснение:</b> {detail['explanation']}")
                explanation_label.setWordWrap(True)
                explanation_label.setStyleSheet(
                    "color: #3498db; background-color: #e3f2fd; padding: 8px; border-radius: 6px;")
                card_layout.addWidget(explanation_label)

            scroll_layout.addWidget(card)

        # Добавляем растяжение в конец
        scroll_layout.addStretch()

        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)

        # Кнопка закрытия
        close_btn = QPushButton("✖ Закрыть")
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: bold;
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: #3498db;
            }
        """)
        close_btn.clicked.connect(dialog.accept)

        # Кнопка в центре
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(close_btn)
        button_layout.addStretch()
        layout.addLayout(button_layout)

        dialog.exec_()

    def on_login_success(self):
        """После успешного входа"""
        user = self.auth_manager.get_current_user()

        if not user:
            QMessageBox.critical(self, "Ошибка", "Не удалось получить данные пользователя")
            self.show_login_dialog()
            return

        # Очищаем предыдущее состояние
        self.clear_ui_state()

        # Удаляем админские вкладки если они есть
        for i in range(self.tabWidget.count() - 1, -1, -1):
            tab_text = self.tabWidget.tabText(i)
            if tab_text in ["👥 Пользователи", "❓ Вопросы", "📁 Материалы", "📈 Общая статистика"]:
                self.tabWidget.removeTab(i)

        # ВОССТАНАВЛИВАЕМ ВКЛАДКИ ТЕСТИРОВАНИЯ
        self.setup_test_tab()  # <-- ДОБАВИТЬ
        self.setup_practice_tab()  # <-- ДОБАВИТЬ

        self.show()
        self.update_user_info()

        # Обновляем интерфейс в зависимости от роли
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

        # Настраиваем остальные вкладки
        self.setup_stats_tab_content()
        self.setup_mistakes_tab()
        self.setup_study_tab()

        # Загружаем вкладки админа (только если админ)
        self.setup_admin_tabs()

        # Загружаем данные
        self.load_study_materials()
        self.load_stats()
        self.load_mistakes()

        if self.auth_manager.is_admin():
            self.load_admin_stats()
        else:
            # Скрываем админские вкладки, если они есть
            if hasattr(self, 'admin_users_tab') and self.admin_users_tab:
                self.admin_users_tab.hide()
            if hasattr(self, 'admin_questions_tab') and self.admin_questions_tab:
                self.admin_questions_tab.hide()
            if hasattr(self, 'admin_materials_tab') and self.admin_materials_tab:
                self.admin_materials_tab.hide()
            if hasattr(self, 'admin_stats_tab') and self.admin_stats_tab:
                self.admin_stats_tab.hide()

        # Подключаем сигнал смены вкладки
        try:
            self.tabWidget.currentChanged.disconnect()
        except:
            pass
        self.tabWidget.currentChanged.connect(self.on_tab_changed)

    def setup_test_tab(self):
        """Настройка вкладки тестирования"""
        # Получаем layout вкладки testTab
        layout = self.testTab.layout()
        if layout is None:
            layout = QVBoxLayout(self.testTab)
            layout.setContentsMargins(0, 0, 0, 0)
        else:
            # Очищаем существующий layout
            self.clear_layout(layout)

        # Создаем центральный фрейм
        test_frame = QFrame()
        test_frame.setStyleSheet("background-color: transparent; border: none;")
        test_frame_layout = QVBoxLayout(test_frame)
        test_frame_layout.setAlignment(Qt.AlignCenter)

        # Заголовок
        test_title_label = QLabel("ТЕСТИРОВАНИЕ ЗНАНИЙ")
        test_title_label.setFont(QFont("", 48, QFont.Bold))
        test_title_label.setAlignment(Qt.AlignCenter)
        test_title_label.setStyleSheet("color: #2c3e50; padding-top: 200px")
        test_frame_layout.addWidget(test_title_label)

        test_frame_layout.addSpacing(20)

        # Описание
        # Добавляем растяжение сверху
        test_frame_layout.addStretch()

        # Контейнер с текстом
        desc_container = QWidget()
        desc_layout = QVBoxLayout(desc_container)
        desc_layout.setAlignment(Qt.AlignCenter)

        test_desc_label = QLabel(
            "Вам будет предложено 15 случайных вопросов. Для успешного прохождения необходимо набрать 80% правильных ответов.")
        test_desc_label.setFont(QFont("Segoe UI", 32))
        test_desc_label.setAlignment(Qt.AlignCenter)
        test_desc_label.setWordWrap(True)
        test_desc_label.setStyleSheet("""
            color: #6c757d;
            background-color: transparent;
            padding: 5px 20px 15px 20px;
        """)
        desc_layout.addWidget(test_desc_label)

        test_frame_layout.addWidget(desc_container)

        # Добавляем растяжение снизу
        test_frame_layout.addStretch()

        # Или фиксированный отступ снизу
        test_frame_layout.addSpacing(50)

        # Кнопка начала теста
        start_test_button = QPushButton("▶ Начать тестирование")
        start_test_button.setMinimumSize(300, 60)
        start_test_button.setStyleSheet("""
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
        start_test_button.clicked.connect(self.start_test)
        test_frame_layout.addWidget(start_test_button)

        test_frame_layout.addStretch()
        layout.addWidget(test_frame)

        # Сохраняем ссылки
        self.startTestButton = start_test_button

    def setup_practice_tab(self):
        """Настройка вкладки учебного теста"""
        # Получаем layout вкладки practiceTab
        layout = self.practiceTab.layout()
        if layout is None:
            layout = QVBoxLayout(self.practiceTab)
            layout.setContentsMargins(0, 0, 0, 0)
        else:
            # Очищаем существующий layout
            self.clear_layout(layout)

        # Создаем центральный фрейм
        practice_frame = QFrame()
        practice_frame.setStyleSheet("background-color: transparent; border: none;")
        practice_frame_layout = QVBoxLayout(practice_frame)
        practice_frame_layout.setAlignment(Qt.AlignCenter)

        practice_title_label = QLabel("УЧЕБНЫЙ ТЕСТ")
        practice_title_label.setFont(QFont("", 48, QFont.Bold))
        practice_title_label.setAlignment(Qt.AlignCenter)
        practice_title_label.setStyleSheet("color: #2c3e50; padding-top: 200px")
        practice_frame_layout.addWidget(practice_title_label)

        practice_frame_layout.addSpacing(20)

        # Описание
        # Добавляем растяжение сверху
        practice_frame_layout.addStretch()

        # Контейнер с текстом
        desc_container = QWidget()
        desc_layout = QVBoxLayout(desc_container)
        desc_layout.setAlignment(Qt.AlignCenter)

        practice_desc_label = QLabel(
            "Идеально для подготовки! После каждого ответа вы увидите правильный вариант и пояснение.")
        practice_desc_label.setFont(QFont("Segoe UI", 32))
        practice_desc_label.setAlignment(Qt.AlignCenter)
        practice_desc_label.setWordWrap(True)
        practice_desc_label.setStyleSheet("""
                   color: #6c757d;
                   background-color: transparent;
                   padding: 5px 20px 15px 20px;
               """)
        practice_frame_layout.addWidget(practice_desc_label)

        practice_frame_layout.addWidget(desc_container)

        # Добавляем растяжение снизу
        practice_frame_layout.addStretch()

        # Или фиксированный отступ снизу
        practice_frame_layout.addSpacing(50)

        # Кнопка начала учебного теста
        start_practice_button = QPushButton("▶ Начать учебный тест")
        start_practice_button.setMinimumSize(300, 60)
        start_practice_button.setStyleSheet("""
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
        start_practice_button.clicked.connect(self.start_practice)
        practice_frame_layout.addWidget(start_practice_button)

        practice_frame_layout.addStretch()
        layout.addWidget(practice_frame)

        # Сохраняем ссылки
        self.startPracticeButton = start_practice_button

    def reset_ui_for_new_user(self):
        """Сброс UI для нового пользователя"""
        # Сбрасываем данные на вкладках
        if hasattr(self, 'statsInfoLabel'):
            self.statsInfoLabel.setText("Загрузка статистики...")

        if hasattr(self, 'chart_widget'):
            self.chart_widget.update_chart([])

        if hasattr(self, 'pie_chart_widget'):
            self.pie_chart_widget.create_pie_chart([1], ['Нет данных'], 'Нет пройденных тестов', ['#6c7086'])

        # Очищаем список материалов
        if hasattr(self, 'studyMaterialsLayout'):
            for i in reversed(range(self.studyMaterialsLayout.count())):
                widget = self.studyMaterialsLayout.itemAt(i).widget()
                if widget:
                    widget.deleteLater()

        # Очищаем список ошибок
        if hasattr(self, 'mistakesLayout'):
            for i in reversed(range(self.mistakesLayout.count())):
                widget = self.mistakesLayout.itemAt(i).widget()
                if widget:
                    widget.deleteLater()

        # Очищаем список результатов
        if hasattr(self, 'statsResultsLayout'):
            for i in reversed(range(self.statsResultsLayout.count())):
                widget = self.statsResultsLayout.itemAt(i).widget()
                if widget:
                    widget.deleteLater()

    def setup_admin_tabs(self):
        """Настройка админских вкладок - только если пользователь админ"""
        if not self.auth_manager.is_admin():
            return

        # Проверяем, не добавлены ли уже вкладки
        admin_tab_names = ["👥 Пользователи", "❓ Вопросы", "📁 Материалы", "📈 Общая статистика"]
        existing_tabs = []
        for i in range(self.tabWidget.count()):
            existing_tabs.append(self.tabWidget.tabText(i))

        # Добавляем только если их еще нет
        if "👥 Пользователи" not in existing_tabs:
            self.admin_users_tab = QWidget()
            self.tabWidget.addTab(self.admin_users_tab, "👥 Пользователи")
            self.setup_admin_users_tab()

        if "❓ Вопросы" not in existing_tabs:
            self.admin_questions_tab = QWidget()
            self.tabWidget.addTab(self.admin_questions_tab, "❓ Вопросы")
            self.setup_admin_questions_tab()

        if "📁 Материалы" not in existing_tabs:
            self.admin_materials_tab = QWidget()
            self.tabWidget.addTab(self.admin_materials_tab, "📁 Материалы")
            self.setup_admin_materials_tab()

        if "📈 Общая статистика" not in existing_tabs:
            self.admin_stats_tab = QWidget()
            self.tabWidget.addTab(self.admin_stats_tab, "📈 Общая статистика")
            self.setup_admin_stats_tab()

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

    def clear_layout(self, layout):
        """Безопасная очистка layout от всех виджетов"""
        if layout is not None:
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()
                else:
                    # Если это не виджет, а другой layout (вложенный)
                    sub_layout = item.layout()
                    if sub_layout:
                        self.clear_layout(sub_layout)

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
                card.setStyleSheet("background-color: #f8f8ff; border-radius: 10px; margin: 1px; padding: 5px;")

                percent = result['score'] / result['total'] * 100
                status = "✅ Сдано" if result['passed'] else "❌ Не сдано"
                status_color = "#a6e3a1" if result['passed'] else "#f38ba8"

                date_obj = datetime.fromisoformat(result['date'].replace(' ', 'T'))
                date_str = date_obj.strftime('%d.%m.%Y %H:%M:%S')

                # Кнопка просмотра деталей
                main_layout = QVBoxLayout(card)

                info_layout = QHBoxLayout()
                info_text_label = QLabel(f"<b>Попытка #{i}</b>  {date_str}")
                info_text_label.setStyleSheet("color: #000;")
                info_layout.addWidget(info_text_label)
                info_layout.addStretch()

                result_text = QLabel(f"📊 Результат: {result['score']}/{result['total']} ({percent:.1f}%)")
                result_text.setStyleSheet("color: #242424;")
                info_layout.addWidget(result_text)

                status_label = QLabel(status)
                status_label.setStyleSheet(f"color: {status_color}; font-weight: bold;")
                info_layout.addWidget(status_label)

                main_layout.addLayout(info_layout)

                details_btn = QPushButton("📖 Подробнее")
                details_btn.setStyleSheet("""
                    color: #242424;
                    background-color: white;
                    border: 1px solid #ced4da;
                    border-radius: 8px;
                    padding: 6px 12px;
                """)
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
        chart_label = QLabel("📊 Текущая успеваемость пользователей:")
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
                padding: 2px;
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

        # Столбчатая диаграмма - показываем последний результат каждого пользователя
        if all_users_stats:
            # Сортируем пользователей по убыванию последнего результата
            sorted_users = sorted(all_users_stats, key=lambda x: x['last_test_percent'], reverse=True)

            user_names = []
            last_scores = []

            for u in sorted_users:
                # Обрезаем длинные имена
                name = u['full_name'][:12] if u['full_name'] else u['username'][:12]
                if len(name) < len(u.get('full_name', u['username'])):
                    name += "."
                user_names.append(name)
                last_scores.append(u['last_test_percent'])

            # Создаем столбчатую диаграмму с последними результатами
            self.admin_chart_widget.create_bar_chart(
                last_scores,
                user_names,
                'Результаты последнего тестирования пользователей',
                'Результат последнего теста, %',
                threshold=80
            )
        else:
            self.admin_chart_widget.create_bar_chart([0], ['Нет данных'], 'Нет данных', 'Результат последнего теста, %')

        # Сохраняем данные для фильтрации
        self.all_users_stats = all_users_stats
        self.load_users_stats_table(all_users_stats)

    def load_users_stats_table(self, users_stats):
        """Загрузка таблицы со статистикой пользователей"""
        self.admin_stats_table.setRowCount(0)

        if not users_stats:
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
            tests_count_item.setTextAlignment(Qt.AlignCenter)
            self.admin_stats_table.setItem(row, 1, tests_count_item)

            # Верных ответов
            if user_stat['total_questions'] > 0:
                correct_item = QTableWidgetItem(f"{user_stat['total_correct']}/{user_stat['total_questions']}")
            else:
                correct_item = QTableWidgetItem("0/0")
            correct_item.setTextAlignment(Qt.AlignCenter)
            self.admin_stats_table.setItem(row, 2, correct_item)

            # Средний балл за все тесты
            avg_score = user_stat['avg_percent']
            avg_item = QTableWidgetItem(f"{avg_score:.1f}%")
            if avg_score >= 80:
                avg_item.setForeground(QColor("#27ae60"))
            elif avg_score >= 60:
                avg_item.setForeground(QColor("#f39c12"))
            else:
                avg_item.setForeground(QColor("#e74c3c"))
            avg_item.setTextAlignment(Qt.AlignCenter)
            self.admin_stats_table.setItem(row, 3, avg_item)

            # Результат последнего теста
            last_score = user_stat.get('last_test_percent', 0)
            last_item = QTableWidgetItem(f"{last_score:.1f}%")
            if last_score >= 80:
                last_item.setForeground(QColor("#27ae60"))
            elif last_score >= 60:
                last_item.setForeground(QColor("#f39c12"))
            else:
                last_item.setForeground(QColor("#e74c3c"))
            last_item.setTextAlignment(Qt.AlignCenter)
            self.admin_stats_table.setItem(row, 4, last_item)

            # Сдано/Не сдано
            ratio_item = QTableWidgetItem(f"✅ {user_stat['passed_tests']} / ❌ {user_stat['failed_tests']}")
            ratio_item.setTextAlignment(Qt.AlignCenter)
            self.admin_stats_table.setItem(row, 5, ratio_item)

            # Последний тест (дата)
            if user_stat['last_test_date']:
                date_obj = datetime.fromisoformat(user_stat['last_test_date'].replace(' ', 'T'))
                date_str = date_obj.strftime('%d.%m.%Y %H:%M')
            else:
                date_str = "Нет тестов"
            date_item = QTableWidgetItem(date_str)
            date_item.setTextAlignment(Qt.AlignCenter)
            self.admin_stats_table.setItem(row, 6, date_item)

            # Кнопка детальной статистики
            details_btn = QPushButton("📊 Подробно")
            details_btn.setStyleSheet("""
                QPushButton {
                    background-color: #3498db;
                    color: white;
                    border: none;
                    border-radius: 5px;
                    padding: 5px 10px;
                    font-size: 11px;
                }
                QPushButton:hover {
                    background-color: #2980b9;
                }
            """)
            details_btn.clicked.connect(lambda checked, uid=user_stat['user_id']: self.view_user_full_stats(uid))
            self.admin_stats_table.setCellWidget(row, 7, details_btn)

        # Настройка ширины колонок
        self.admin_stats_table.setColumnWidth(0, 180)
        self.admin_stats_table.setColumnWidth(1, 70)
        self.admin_stats_table.setColumnWidth(2, 110)
        self.admin_stats_table.setColumnWidth(3, 110)
        self.admin_stats_table.setColumnWidth(4, 110)
        self.admin_stats_table.setColumnWidth(5, 120)
        self.admin_stats_table.setColumnWidth(6, 130)
        self.admin_stats_table.setColumnWidth(7, 100)

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
            layout.setContentsMargins(0, 0, 0, 0)
        else:
            # Очищаем существующий layout
            self.clear_layout(layout)

        # Создаем scroll area для всего содержимого
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                background: #e9ecef;
                width: 10px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical {
                background: #3498db;
                border-radius: 5px;
            }
        """)

        # Создаем контейнер для содержимого
        content_widget = QWidget()
        content_widget.setStyleSheet("background-color: transparent;")
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(10, 10, 10, 10)
        content_layout.setSpacing(10)

        # Создаем вкладки внутри статистики
        stats_tabs = QTabWidget()
        stats_tabs.setStyleSheet("""
            QTabWidget::pane {
                background-color: #ffffff;
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
        content_layout.addWidget(stats_tabs)

        # Вкладка общей статистики
        general_stats_tab = QWidget()
        general_stats_tab.setStyleSheet("background-color: #ffffff;")
        stats_tabs.addTab(general_stats_tab, "📊 Cтатистика")

        # Вкладка детальной статистики
        detailed_stats_tab = QWidget()
        detailed_stats_tab.setStyleSheet("background-color: #ffffff;")
        stats_tabs.addTab(detailed_stats_tab, "📈 Детальная статистика")

        # Настройка общей статистики
        general_scroll = QScrollArea()
        general_scroll.setWidgetResizable(True)
        general_scroll.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")

        general_content = QWidget()
        general_content.setStyleSheet("background-color: transparent;")
        general_layout = QVBoxLayout(general_content)
        general_layout.setSpacing(15)
        general_layout.setContentsMargins(15, 15, 15, 15)

        # Информационная карточка
        statsInfoLabel = QLabel()
        statsInfoLabel.setWordWrap(True)
        statsInfoLabel.setStyleSheet("""
            background-color: #f8f9fa;
            padding: 15px;
            border-radius: 10px;
            border: 1px solid #dee2e6;
        """)
        statsInfoLabel.setMinimumHeight(200)
        general_layout.addWidget(statsInfoLabel)

        # График динамики
        chart_label = QLabel("📈 Динамика результатов:")
        chart_label.setFont(QFont("Segoe UI", 12, QFont.Bold))
        chart_label.setStyleSheet("color: #2c3e50; background-color: transparent; padding-top: 10px;")
        general_layout.addWidget(chart_label)

        chart_widget = StatisticsChart()
        chart_widget.setMinimumHeight(400)
        chart_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        general_layout.addWidget(chart_widget)

        # Круговая диаграмма
        pie_chart_label = QLabel("📊 Соотношение успешных и неуспешных тестов:")
        pie_chart_label.setFont(QFont("Segoe UI", 12, QFont.Bold))
        pie_chart_label.setStyleSheet("color: #2c3e50; background-color: transparent; padding-top: 10px;")
        general_layout.addWidget(pie_chart_label)

        pie_chart_widget = StatisticsChart()
        pie_chart_widget.setMinimumHeight(300)
        general_layout.addWidget(pie_chart_widget)

        general_layout.addStretch()
        general_scroll.setWidget(general_content)

        # Добавляем scroll в общую статистику
        general_tab_layout = QVBoxLayout(general_stats_tab)
        general_tab_layout.setContentsMargins(0, 0, 0, 0)
        general_tab_layout.addWidget(general_scroll)

        # Настройка детальной статистики
        detailed_layout = QVBoxLayout(detailed_stats_tab)
        detailed_layout.setContentsMargins(15, 15, 15, 15)
        detailed_layout.setSpacing(10)

        results_label = QLabel("📝 История всех тестирований:")
        results_label.setFont(QFont("Segoe UI", 12, QFont.Bold))
        results_label.setStyleSheet("color: #2c3e50; background-color: transparent;")
        detailed_layout.addWidget(results_label)

        statsList = QScrollArea()
        statsList.setWidgetResizable(True)
        statsList.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                background: #e9ecef;
                width: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: #3498db;
                border-radius: 4px;
            }
        """)

        statsContent = QWidget()
        statsContent.setStyleSheet("background-color: transparent;")
        statsResultsLayout = QVBoxLayout(statsContent)
        statsResultsLayout.setSpacing(10)
        statsResultsLayout.setContentsMargins(5, 5, 5, 5)
        statsList.setWidget(statsContent)
        detailed_layout.addWidget(statsList)

        scroll_area.setWidget(content_widget)
        layout.addWidget(scroll_area)

        # Сохраняем ссылки
        self.stats_tabs = stats_tabs
        self.general_stats_tab = general_stats_tab
        self.detailed_stats_tab = detailed_stats_tab
        self.statsInfoLabel = statsInfoLabel
        self.chart_widget = chart_widget
        self.pie_chart_widget = pie_chart_widget
        self.statsList = statsList
        self.statsContent = statsContent
        self.statsResultsLayout = statsResultsLayout

    def clear_ui_state(self):
        """Полная очистка состояния интерфейса (кроме вкладок тестирования)"""
        # Очищаем админские вкладки
        if hasattr(self, 'admin_users_tab') and self.admin_users_tab:
            self.admin_users_tab = None
        if hasattr(self, 'admin_questions_tab') and self.admin_questions_tab:
            self.admin_questions_tab = None
        if hasattr(self, 'admin_materials_tab') and self.admin_materials_tab:
            self.admin_materials_tab = None
        if hasattr(self, 'admin_stats_tab') and self.admin_stats_tab:
            self.admin_stats_tab = None

        # Очищаем layout вкладки статистики
        if hasattr(self, 'statsTab'):
            old_layout = self.statsTab.layout()
            if old_layout:
                self.clear_layout(old_layout)

        # Очищаем layout вкладки обучения
        if hasattr(self, 'studyTab'):
            old_layout = self.studyTab.layout()
            if old_layout:
                self.clear_layout(old_layout)

        # Очищаем layout вкладки ошибок
        if hasattr(self, 'mistakesTab'):
            old_layout = self.mistakesTab.layout()
            if old_layout:
                self.clear_layout(old_layout)

        # НЕ ОЧИЩАЕМ testTab и practiceTab - они будут восстановлены в on_login_success

        # Отключаем сигналы смены вкладки
        try:
            self.tabWidget.currentChanged.disconnect()
        except:
            pass
