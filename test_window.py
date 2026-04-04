from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QScrollArea, QWidget, QCheckBox,
                             QMessageBox, QFrame, QGridLayout, QProgressBar,
                             QButtonGroup, QRadioButton)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QPixmap
from database import Database
import os


class TestWindow(QDialog):
    test_finished = pyqtSignal()

    def __init__(self, parent, db: Database, user_id: int, training_mode: bool = False):
        super().__init__(parent)
        self.db = db
        self.user_id = user_id
        self.training_mode = training_mode

        self.setWindowTitle("📖 Учебный тест" if training_mode else "🎯 Тестирование")
        self.setMinimumSize(1200, 800)
        self.resize(1200, 800)
        self.setModal(True)

        self.questions = self.db.get_random_questions(15)
        if not self.questions:
            QMessageBox.critical(self, "Ошибка", "Нет вопросов в базе данных")
            self.close()
            return

        self.current_index = 0
        self.answers = [None] * len(self.questions)
        self.answered = [False] * len(self.questions)

        self.setup_ui()
        self.load_question(0)

    def setup_ui(self):
        # Главный layout
        main_layout = QVBoxLayout()
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # ===== ВЕРХНЯЯ ПАНЕЛЬ =====
        top_panel = QFrame()
        top_panel.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border-radius: 12px;
                border: 1px solid #dee2e6;
            }
        """)
        top_layout = QHBoxLayout(top_panel)
        top_layout.setContentsMargins(20, 12, 20, 12)

        # Номер вопроса
        self.question_number_label = QLabel()
        self.question_number_label.setStyleSheet("""
            QLabel {
                background-color: #3498db;
                border-radius: 20px;
                padding: 6px 18px;
                font-size: 14px;
                font-weight: bold;
                color: white;
            }
        """)
        self.question_number_label.setAlignment(Qt.AlignCenter)
        top_layout.addWidget(self.question_number_label)

        top_layout.addStretch()

        # Заголовок режима
        mode_title = QLabel("📖 УЧЕБНЫЙ РЕЖИМ" if self.training_mode else "🎯 РЕЖИМ ТЕСТИРОВАНИЯ")
        mode_title.setFont(QFont("Arial", 13, QFont.Bold))
        mode_title.setStyleSheet("color: #e74c3c;")
        top_layout.addWidget(mode_title)

        top_layout.addStretch()

        # Кнопка завершения
        self.finish_button = QPushButton("🏁 Завершить тест")
        self.finish_button.setMinimumWidth(140)
        self.finish_button.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        self.finish_button.clicked.connect(self.finish_test)
        top_layout.addWidget(self.finish_button)

        main_layout.addWidget(top_panel)

        # ===== ПРОГРЕСС =====
        progress_layout = QVBoxLayout()
        progress_layout.setSpacing(5)

        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimumHeight(20)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: none;
                border-radius: 10px;
                background-color: #e9ecef;
                text-align: center;
                color: #2c3e50;
                font-weight: bold;
                font-size: 11px;
            }
            QProgressBar::chunk {
                background-color: #3498db;
                border-radius: 10px;
            }
        """)
        progress_layout.addWidget(self.progress_bar)

        self.progress_text = QLabel()
        self.progress_text.setAlignment(Qt.AlignCenter)
        self.progress_text.setFont(QFont("Arial", 10))
        self.progress_text.setStyleSheet("color: #6c757d;")
        progress_layout.addWidget(self.progress_text)

        main_layout.addLayout(progress_layout)

        # ===== ОСНОВНАЯ ОБЛАСТЬ С ПРОКРУТКОЙ =====
        self.main_scroll = QScrollArea()
        self.main_scroll.setWidgetResizable(True)
        self.main_scroll.setStyleSheet("""
            QScrollArea {
                background-color: transparent;
                border: none;
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

        # Контейнер для всего содержимого с прокруткой
        scroll_content = QWidget()
        scroll_content.setStyleSheet("background-color: transparent;")
        self.scroll_layout = QVBoxLayout(scroll_content)
        self.scroll_layout.setSpacing(15)
        self.scroll_layout.setContentsMargins(0, 0, 0, 0)

        # ===== КАРТОЧКА ВОПРОСА =====
        self.question_card = QFrame()
        self.question_card.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 15px;
                border: 1px solid #dee2e6;
            }
        """)
        card_layout = QVBoxLayout(self.question_card)
        card_layout.setSpacing(15)
        card_layout.setContentsMargins(20, 20, 20, 20)

        # Текст вопроса (с переносом слов)
        self.question_label = QLabel()
        self.question_label.setWordWrap(True)
        self.question_label.setFont(QFont("Arial", 16, QFont.Bold))
        self.question_label.setStyleSheet("color: #2c3e50; line-height: 1.4;")
        self.question_label.setMinimumHeight(80)
        card_layout.addWidget(self.question_label)

        # Изображение
        self.image_container = QWidget()
        image_layout = QVBoxLayout(self.image_container)
        image_layout.setAlignment(Qt.AlignCenter)

        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setMinimumHeight(200)
        self.image_label.setMaximumHeight(300)
        self.image_label.setStyleSheet("""
            QLabel {
                background-color: #f8f9fa;
                border-radius: 12px;
                padding: 10px;
                color: #6c757d;
                font-size: 14px;
            }
        """)
        self.image_label.setScaledContents(False)
        image_layout.addWidget(self.image_label)
        card_layout.addWidget(self.image_container)

        self.scroll_layout.addWidget(self.question_card)

        # ===== ВАРИАНТЫ ОТВЕТОВ =====
        options_card = QFrame()
        options_card.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 15px;
                border: 1px solid #dee2e6;
            }
        """)
        options_layout = QVBoxLayout(options_card)
        options_layout.setSpacing(15)
        options_layout.setContentsMargins(20, 20, 20, 20)

        # Заголовок
        options_header = QHBoxLayout()
        options_label = QLabel("📌 ВЫБЕРИТЕ ОТВЕТ(Ы):")
        options_label.setFont(QFont("Arial", 13, QFont.Bold))
        options_label.setStyleSheet("color: #2c3e50;")
        options_header.addWidget(options_label)
        options_header.addStretch()

        self.answer_type_label = QLabel("✓ Можно выбрать несколько вариантов")
        self.answer_type_label.setFont(QFont("Arial", 11))
        self.answer_type_label.setStyleSheet("color: #6c757d;")
        options_header.addWidget(self.answer_type_label)
        options_layout.addLayout(options_header)

        # Сетка для вариантов ответов (2x2)
        self.options_grid = QGridLayout()
        self.options_grid.setSpacing(12)
        self.options_grid.setContentsMargins(0, 10, 0, 10)

        self.radio_group = QButtonGroup()
        self.checkboxes = []
        self.radio_buttons = []  # Храним радио-кнопки отдельно

        for i in range(4):
            # Создаем контейнер для радио-кнопки с текстом
            radio_container = QWidget()
            radio_container.setStyleSheet("background-color: #f8f9fa; border-radius: 10px; border: 1px solid #dee2e6;")
            radio_container_layout = QHBoxLayout(radio_container)
            radio_container_layout.setContentsMargins(12, 12, 12, 12)

            radio = QRadioButton()
            radio.setStyleSheet("""
                QRadioButton {
                    spacing: 12px;
                    color: #2c3e50;
                }
                QRadioButton::indicator {
                    width: 16px;
                    height: 16px;
                    border-radius: 8px;
                    border: 2px solid #3498db;
                    background-color: white;
                }
                QRadioButton::indicator:checked {
                    background-color: #3498db;
                }
            """)
            radio_container_layout.addWidget(radio)

            radio_label = QLabel()
            radio_label.setWordWrap(True)
            radio_label.setStyleSheet("color: #2c3e50; font-size: 13px;")
            radio_container_layout.addWidget(radio_label, stretch=1)

            self.radio_group.addButton(radio, i)
            self.radio_buttons.append((radio, radio_label, radio_container))

            # Создаем контейнер для чекбокса с текстом
            checkbox_container = QWidget()
            checkbox_container.setStyleSheet(
                "background-color: #f8f9fa; border-radius: 10px; border: 1px solid #dee2e6;")
            checkbox_container_layout = QHBoxLayout(checkbox_container)
            checkbox_container_layout.setContentsMargins(12, 12, 12, 12)

            checkbox = QCheckBox()
            checkbox.setStyleSheet("""
                QCheckBox {
                    spacing: 12px;
                    color: #2c3e50;
                }
                QCheckBox::indicator {
                    width: 16px;
                    height: 16px;
                    border-radius: 4px;
                    border: 2px solid #3498db;
                    background-color: white;
                }
                QCheckBox::indicator:checked {
                    background-color: #27ae60;
                    border-color: #27ae60;
                }
            """)
            checkbox_container_layout.addWidget(checkbox)

            checkbox_label = QLabel()
            checkbox_label.setWordWrap(True)
            checkbox_label.setStyleSheet("color: #2c3e50; font-size: 13px;")
            checkbox_container_layout.addWidget(checkbox_label, stretch=1)

            self.checkboxes.append((checkbox, checkbox_label, checkbox_container))

            row = i // 2
            col = i % 2
            self.options_grid.addWidget(radio_container, row, col)
            self.options_grid.addWidget(checkbox_container, row, col)

        options_layout.addLayout(self.options_grid)
        self.scroll_layout.addWidget(options_card)

        # ===== КАРТОЧКА ОБРАТНОЙ СВЯЗИ =====
        self.feedback_card = QFrame()
        self.feedback_card.setVisible(False)
        self.feedback_card.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border-radius: 12px;
                border-left: 4px solid #3498db;
                padding: 15px;
            }
        """)
        feedback_layout = QVBoxLayout(self.feedback_card)

        self.feedback_label = QLabel()
        self.feedback_label.setWordWrap(True)
        self.feedback_label.setFont(QFont("Arial", 12))
        self.feedback_label.setStyleSheet("color: #2c3e50;")
        feedback_layout.addWidget(self.feedback_label)

        self.scroll_layout.addWidget(self.feedback_card)

        self.scroll_layout.addStretch()

        # Устанавливаем контейнер в скролл-область
        self.main_scroll.setWidget(scroll_content)
        main_layout.addWidget(self.main_scroll, stretch=1)

        # ===== НИЖНЯЯ ПАНЕЛЬ С КНОПКАМИ =====
        bottom_panel = QFrame()
        bottom_panel.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border-radius: 12px;
                border: 1px solid #dee2e6;
            }
        """)
        bottom_layout = QHBoxLayout(bottom_panel)
        bottom_layout.setContentsMargins(20, 12, 20, 12)

        # Кнопка "Назад"
        self.back_button = QPushButton("◀ НАЗАД")
        self.back_button.setMinimumWidth(120)
        self.back_button.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
            QPushButton:disabled {
                background-color: #ced4da;
                color: #6c757d;
            }
        """)
        self.back_button.clicked.connect(self.prev_question)
        bottom_layout.addWidget(self.back_button)

        bottom_layout.addStretch()

        # Индикатор вопросов
        self.questions_indicator = QLabel()
        self.questions_indicator.setFont(QFont("Arial", 11))
        self.questions_indicator.setAlignment(Qt.AlignCenter)
        self.questions_indicator.setStyleSheet("""
            QLabel {
                color: #2c3e50;
                background-color: #f8f9fa;
                padding: 8px 18px;
                border-radius: 20px;
                border: 1px solid #dee2e6;
            }
        """)
        bottom_layout.addWidget(self.questions_indicator)

        bottom_layout.addStretch()

        # Кнопка "Проверить" / "Далее" - для учебного режима зеленая, для теста синяя
        if self.training_mode:
            self.action_button = QPushButton("✓ ПРОВЕРИТЬ ОТВЕТ")
            self.action_button.setStyleSheet("""
                QPushButton {
                    background-color: #27ae60;
                    color: white;
                    border: none;
                    border-radius: 8px;
                    padding: 10px 20px;
                    font-size: 13px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #219a52;
                }
                QPushButton:disabled {
                    background-color: #ced4da;
                    color: #6c757d;
                }
            """)
            self.action_button.clicked.connect(self.check_answer)
        else:
            self.action_button = QPushButton("ДАЛЕЕ ►")
            self.action_button.setStyleSheet("""
                QPushButton {
                    background-color: #3498db;
                    color: white;
                    border: none;
                    border-radius: 8px;
                    padding: 10px 20px;
                    font-size: 13px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #2980b9;
                }
                QPushButton:disabled {
                    background-color: #ced4da;
                    color: #6c757d;
                }
            """)
            self.action_button.clicked.connect(self.next_question)

        self.action_button.setMinimumWidth(160)
        bottom_layout.addWidget(self.action_button)

        # Кнопка "Продолжить" (для учебного режима)
        self.continue_button = QPushButton("СЛЕДУЮЩИЙ ВОПРОС ►►")
        self.continue_button.setMinimumWidth(180)
        self.continue_button.setVisible(False)
        self.continue_button.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        self.continue_button.clicked.connect(self.continue_to_next)
        bottom_layout.addWidget(self.continue_button)

        main_layout.addWidget(bottom_panel)

        self.setLayout(main_layout)

    def load_question(self, idx):
        q = self.questions[idx]

        # Определяем, сколько правильных ответов
        correct_count = bin(q['correct_mask']).count("1")
        is_multiple = correct_count > 1

        # Обновляем тип ответа
        if is_multiple:
            self.answer_type_label.setText("☑️ Можно выбрать несколько вариантов")
            self.answer_type_label.setStyleSheet("color: #27ae60;")
        else:
            self.answer_type_label.setText("🔘 Выберите один вариант")
            self.answer_type_label.setStyleSheet("color: #e74c3c;")

        # Показываем нужные виджеты и обновляем текст
        options = [q['option1'], q['option2'], q['option3'], q['option4']]

        for i in range(4):
            # Радио-кнопки
            radio, radio_label, radio_container = self.radio_buttons[i]
            radio_container.setVisible(not is_multiple)
            radio_label.setText(options[i])
            radio.setChecked(False)
            radio.setEnabled(True)

            # Чекбоксы
            checkbox, checkbox_label, checkbox_container = self.checkboxes[i]
            checkbox_container.setVisible(is_multiple)
            checkbox_label.setText(options[i])
            checkbox.setChecked(False)
            checkbox.setEnabled(True)

        # Обновляем прогресс
        self.question_number_label.setText(f"Вопрос {idx + 1}/{len(self.questions)}")
        self.questions_indicator.setText(f"📋 {idx + 1} из {len(self.questions)}")

        progress_value = int((idx + 1) / len(self.questions) * 100)
        self.progress_bar.setValue(progress_value)
        self.progress_text.setText(f"Прогресс: {progress_value}%")

        # Текст вопроса
        self.question_label.setText(q['text'])

        # Загрузка изображения
        if q.get('image_path') and os.path.exists(q['image_path']):
            pixmap = QPixmap(q['image_path'])
            if not pixmap.isNull():
                scaled_pixmap = pixmap.scaled(500, 250, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.image_label.setPixmap(scaled_pixmap)
                self.image_label.setText("")
                self.image_container.setVisible(True)
            else:
                self.image_label.setText("⚠️ Не удалось загрузить изображение")
                self.image_container.setVisible(True)
        else:
            self.image_label.setText("📷 Изображение отсутствует")
            self.image_container.setVisible(True)

        # Скрываем карточку обратной связи
        self.feedback_card.setVisible(False)
        self.action_button.setVisible(True)
        self.continue_button.setVisible(False)

        # Сброс стилей контейнеров
        for i in range(4):
            # Сброс радио-контейнеров
            radio, radio_label, radio_container = self.radio_buttons[i]
            radio_container.setStyleSheet("background-color: #f8f9fa; border-radius: 10px; border: 1px solid #dee2e6;")
            radio_label.setStyleSheet("color: #2c3e50; font-size: 13px;")

            # Сброс чекбокс-контейнеров
            checkbox, checkbox_label, checkbox_container = self.checkboxes[i]
            checkbox_container.setStyleSheet(
                "background-color: #f8f9fa; border-radius: 10px; border: 1px solid #dee2e6;")
            checkbox_label.setStyleSheet("color: #2c3e50; font-size: 13px;")

        # Восстановление сохраненного ответа
        if self.answers[idx] is not None and self.answered[idx]:
            user_mask = self.answers[idx]['selected_mask']
            if is_multiple:
                for i in range(4):
                    if (user_mask >> i) & 1:
                        checkbox, _, _ = self.checkboxes[i]
                        checkbox.setChecked(True)
            else:
                for i in range(4):
                    if (user_mask >> i) & 1:
                        radio, _, _ = self.radio_buttons[i]
                        radio.setChecked(True)

            if self.training_mode:
                # Восстанавливаем подсветку для уже отвеченного вопроса
                correct_mask = q['correct_mask']
                is_correct = self.answers[idx]['correct']
                for i in range(4):
                    is_correct_option = (correct_mask >> i) & 1
                    is_user_selected = (user_mask >> i) & 1

                    if is_multiple:
                        checkbox, checkbox_label, checkbox_container = self.checkboxes[i]
                        if is_correct_option:
                            checkbox_container.setStyleSheet("""
                                background-color: #d4edda;
                                border-radius: 10px;
                                border: 2px solid #27ae60;
                            """)
                            checkbox_label.setStyleSheet("color: #27ae60; font-weight: bold; font-size: 13px;")
                        elif not is_correct and is_user_selected:
                            checkbox_container.setStyleSheet("""
                                background-color: #f8d7da;
                                border-radius: 10px;
                                border: 2px solid #e74c3c;
                            """)
                            checkbox_label.setStyleSheet(
                                "color: #e74c3c; text-decoration: line-through; font-size: 13px;")
                    else:
                        radio, radio_label, radio_container = self.radio_buttons[i]
                        if is_correct_option:
                            radio_container.setStyleSheet("""
                                background-color: #d4edda;
                                border-radius: 10px;
                                border: 2px solid #27ae60;
                            """)
                            radio_label.setStyleSheet("color: #27ae60; font-weight: bold; font-size: 13px;")
                        elif not is_correct and is_user_selected:
                            radio_container.setStyleSheet("""
                                background-color: #f8d7da;
                                border-radius: 10px;
                                border: 2px solid #e74c3c;
                            """)
                            radio_label.setStyleSheet("color: #e74c3c; text-decoration: line-through; font-size: 13px;")

                self.show_feedback_only()

        # Навигация
        self.back_button.setEnabled(idx > 0)
        if self.training_mode:
            self.action_button.setEnabled(not self.answered[idx])
        else:
            self.action_button.setEnabled(True)

        # Прокрутка вверх при загрузке нового вопроса
        self.main_scroll.verticalScrollBar().setValue(0)

    def check_answer(self):
        """Проверка ответа в учебном режиме"""
        if self.answered[self.current_index]:
            return

        q = self.questions[self.current_index]
        correct_count = bin(q['correct_mask']).count("1")
        is_multiple = correct_count > 1

        # Получаем выбранные ответы
        selected = []
        if is_multiple:
            for i in range(4):
                checkbox, _, _ = self.checkboxes[i]
                selected.append(checkbox.isChecked())
        else:
            for i in range(4):
                radio, _, _ = self.radio_buttons[i]
                selected.append(radio.isChecked())

        if not any(selected):
            QMessageBox.warning(self, "Внимание", "Пожалуйста, выберите вариант ответа")
            return

        user_mask = sum((1 << i) for i, val in enumerate(selected) if val)
        correct_mask = q['correct_mask']
        correct = user_mask == correct_mask

        # Сохраняем ответ
        self.answers[self.current_index] = {
            'question_id': q['id'],
            'question_text': q['text'],
            'selected_mask': user_mask,
            'correct': correct,
            'correct_mask': correct_mask,
            'explanation': q['explanation'],
            'options': [q['option1'], q['option2'], q['option3'], q['option4']]
        }
        self.answered[self.current_index] = True

        # Подсветка вариантов
        for i in range(4):
            is_correct_option = (correct_mask >> i) & 1
            is_user_selected = (user_mask >> i) & 1

            if is_multiple:
                checkbox, checkbox_label, checkbox_container = self.checkboxes[i]
                checkbox.setEnabled(False)
                if is_correct_option:
                    checkbox_container.setStyleSheet("""
                        background-color: #d4edda;
                        border-radius: 10px;
                        border: 2px solid #27ae60;
                    """)
                    checkbox_label.setStyleSheet("color: #27ae60; font-weight: bold; font-size: 13px;")
                elif not correct and is_user_selected:
                    checkbox_container.setStyleSheet("""
                        background-color: #f8d7da;
                        border-radius: 10px;
                        border: 2px solid #e74c3c;
                    """)
                    checkbox_label.setStyleSheet("color: #e74c3c; text-decoration: line-through; font-size: 13px;")
            else:
                radio, radio_label, radio_container = self.radio_buttons[i]
                radio.setEnabled(False)
                if is_correct_option:
                    radio_container.setStyleSheet("""
                        background-color: #d4edda;
                        border-radius: 10px;
                        border: 2px solid #27ae60;
                    """)
                    radio_label.setStyleSheet("color: #27ae60; font-weight: bold; font-size: 13px;")
                elif not correct and is_user_selected:
                    radio_container.setStyleSheet("""
                        background-color: #f8d7da;
                        border-radius: 10px;
                        border: 2px solid #e74c3c;
                    """)
                    radio_label.setStyleSheet("color: #e74c3c; text-decoration: line-through; font-size: 13px;")

        # Формируем текст обратной связи
        if correct:
            feedback_text = f"""
            <div style='text-align: center;'>
                <h3 style='color: #27ae60; margin: 0;'>✅ ПРАВИЛЬНО!</h3>
                <p style='font-size: 14px; margin-top: 8px;'>Отличный результат! Вы выбрали верный ответ.</p>
            </div>
            """
        else:
            correct_options = [q[f'option{i + 1}'] for i in range(4) if (correct_mask >> i) & 1]
            feedback_text = f"""
            <div style='text-align: center;'>
                <h3 style='color: #e74c3c; margin: 0;'>❌ НЕПРАВИЛЬНО</h3>
                <p style='font-size: 14px; margin-top: 8px;'>
                    <b style='color: #27ae60;'>✓ Правильный ответ:</b> {', '.join(correct_options)}
                </p>
                <hr style='border-color: #dee2e6; margin: 10px 0;'>
                <p style='font-size: 13px;'>
                    <b>💡 Пояснение:</b> {q['explanation']}
                </p>
            </div>
            """

        self.feedback_label.setText(feedback_text)
        self.feedback_card.setVisible(True)

        # Меняем кнопки
        self.action_button.setVisible(False)
        self.continue_button.setVisible(True)

    def show_feedback_only(self):
        """Показ обратной связи для уже отвеченных вопросов (без изменения состояния)"""
        q = self.questions[self.current_index]
        answer = self.answers[self.current_index]
        is_correct = answer['correct']
        correct_mask = answer['correct_mask']

        if is_correct:
            feedback_text = f"""
            <div style='text-align: center;'>
                <h3 style='color: #27ae60; margin: 0;'>✅ ПРАВИЛЬНО!</h3>
                <p style='font-size: 14px;'>Вы уже ответили на этот вопрос правильно.</p>
            </div>
            """
        else:
            correct_options = [q[f'option{i + 1}'] for i in range(4) if (correct_mask >> i) & 1]
            feedback_text = f"""
            <div style='text-align: center;'>
                <h3 style='color: #e74c3c; margin: 0;'>❌ НЕПРАВИЛЬНО</h3>
                <p style='font-size: 14px;'>
                    <b style='color: #27ae60;'>✓ Правильный ответ:</b> {', '.join(correct_options)}
                </p>
                <hr style='border-color: #dee2e6; margin: 10px 0;'>
                <p style='font-size: 13px;'>
                    <b>💡 Пояснение:</b> {q['explanation']}
                </p>
            </div>
            """

        self.feedback_label.setText(feedback_text)
        self.feedback_card.setVisible(True)
        self.action_button.setVisible(False)
        self.continue_button.setVisible(True)

    def continue_to_next(self):
        """Переход к следующему вопросу после проверки"""
        if self.current_index < len(self.questions) - 1:
            self.current_index += 1
            self.load_question(self.current_index)
        else:
            self.finish_test()

    def next_question(self):
        """Следующий вопрос в режиме тестирования"""
        q = self.questions[self.current_index]
        correct_count = bin(q['correct_mask']).count("1")
        is_multiple = correct_count > 1

        selected = []
        if is_multiple:
            for i in range(4):
                checkbox, _, _ = self.checkboxes[i]
                selected.append(checkbox.isChecked())
        else:
            for i in range(4):
                radio, _, _ = self.radio_buttons[i]
                selected.append(radio.isChecked())

        if not any(selected):
            QMessageBox.warning(self, "Внимание", "Пожалуйста, выберите вариант ответа")
            return

        user_mask = sum((1 << i) for i, val in enumerate(selected) if val)
        correct_mask = q['correct_mask']
        correct = user_mask == correct_mask

        self.answers[self.current_index] = {
            'question_id': q['id'],
            'question_text': q['text'],
            'selected_mask': user_mask,
            'correct': correct,
            'correct_mask': correct_mask,
            'explanation': q['explanation'],
            'options': [q['option1'], q['option2'], q['option3'], q['option4']]
        }
        self.answered[self.current_index] = True

        if self.current_index < len(self.questions) - 1:
            self.current_index += 1
            self.load_question(self.current_index)
        else:
            self.finish_test()

    def prev_question(self):
        if self.current_index > 0:
            self.current_index -= 1
            self.load_question(self.current_index)

    def finish_test(self):
        if not self.answered[self.current_index] and not self.training_mode:
            q = self.questions[self.current_index]
            correct_count = bin(q['correct_mask']).count("1")
            is_multiple = correct_count > 1

            selected = []
            if is_multiple:
                for i in range(4):
                    checkbox, _, _ = self.checkboxes[i]
                    selected.append(checkbox.isChecked())
            else:
                for i in range(4):
                    radio, _, _ = self.radio_buttons[i]
                    selected.append(radio.isChecked())

            if any(selected):
                user_mask = sum((1 << i) for i, val in enumerate(selected) if val)
                correct_mask = q['correct_mask']
                correct = user_mask == correct_mask

                self.answers[self.current_index] = {
                    'question_id': q['id'],
                    'question_text': q['text'],
                    'selected_mask': user_mask,
                    'correct': correct,
                    'correct_mask': correct_mask,
                    'explanation': q.get('explanation', ''),
                    'options': [q['option1'], q['option2'], q['option3'], q['option4']]
                }
                self.answered[self.current_index] = True

        # Фильтруем только отвеченные вопросы (убираем None)
        answered_answers = [a for a in self.answers if a is not None]
        score = sum(1 for a in answered_answers if a['correct'])
        total = len(self.questions)

        if not self.training_mode:
            passed = (score / total * 100) >= 80 if total > 0 else False

            # ВАЖНО: Сохраняем ТОЛЬКО отвеченные ответы, а не весь массив с None
            self.db.save_test_result(self.user_id, score, total, answered_answers)

            percent = score / total * 100 if total > 0 else 0

            msg = f"📊 Правильных ответов: {score} из {total} ({percent:.1f}%)\n"
            if percent >= 85:
                grade = "5 (Отлично)"
            elif percent >= 70:
                grade = "4 (Хорошо)"
            elif percent >= 50:
                grade = "3 (Удовлетворительно)"
            else:
                grade = "2 (Неудовлетворительно)"
            msg += f"🎓 Оценка: {grade}\n"
            msg += "✅ ДОПУЩЕН" if passed else "❌ НЕ ДОПУЩЕН"

            QMessageBox.information(self, "Результат теста", msg)
            if not passed:
                QMessageBox.information(self, "💡 Совет",
                                        "Повторите материал в разделе 'Обучение' и попробуйте снова.")
        else:
            percent = score / total * 100 if total > 0 else 0
            QMessageBox.information(self, "📊 Итог",
                                    f"Правильных ответов: {score} из {total} ({percent:.1f}%)")

        reply = QMessageBox.question(self, "✅ Тест завершён",
                                     "Перезапустить тест?",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.current_index = 0
            self.answers = [None] * len(self.questions)
            self.answered = [False] * len(self.questions)
            self.load_question(0)
        else:
            self.test_finished.emit()
            self.close()
