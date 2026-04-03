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
        self.setMinimumSize(1300, 850)
        self.resize(1300, 850)
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
        self.apply_modern_style()

    def apply_modern_style(self):
        """Современный стиль для окна тестирования"""
        self.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #1a1a2e, stop:1 #16213e);
            }
            QLabel {
                color: #e2e2e2;
            }
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #e94560, stop:1 #c73e54);
                color: white;
                border: none;
                border-radius: 12px;
                padding: 12px 24px;
                font-size: 14px;
                font-weight: bold;
                font-family: 'Segoe UI';
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ff6b6b, stop:1 #e94560);
            }
            QPushButton:disabled {
                background: #45475a;
                color: #6c7086;
            }
            QPushButton#primaryButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #0f3460, stop:1 #0a2647);
            }
            QPushButton#primaryButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #1a4a7a, stop:1 #0f3460);
            }
            QProgressBar {
                border: none;
                border-radius: 10px;
                background-color: #2c2c3e;
                text-align: center;
                color: #e2e2e2;
                font-weight: bold;
                height: 25px;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #e94560, stop:1 #ff6b6b);
                border-radius: 10px;
            }
            QRadioButton {
                color: #e2e2e2;
                spacing: 15px;
                font-size: 14px;
                padding: 12px;
                background-color: #2c2c3e;
                border-radius: 10px;
                margin: 5px;
            }
            QRadioButton::indicator {
                width: 18px;
                height: 18px;
                border-radius: 9px;
                border: 2px solid #e94560;
                background-color: #1a1a2e;
            }
            QRadioButton::indicator:checked {
                background-color: #e94560;
                border-color: #e94560;
            }
            QRadioButton:hover {
                background-color: #3a3a4e;
            }
            QCheckBox {
                color: #e2e2e2;
                spacing: 15px;
                font-size: 14px;
                padding: 12px;
                background-color: #2c2c3e;
                border-radius: 10px;
                margin: 5px;
            }
            QCheckBox::indicator {
                width: 20px;
                height: 20px;
                border-radius: 5px;
                border: 2px solid #e94560;
                background-color: #1a1a2e;
            }
            QCheckBox::indicator:checked {
                background-color: #4caf50;
                border-color: #4caf50;
            }
            QCheckBox:hover {
                background-color: #3a3a4e;
            }
            QScrollArea {
                background-color: transparent;
                border: none;
            }
            QScrollBar:vertical {
                background: #2c2c3e;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background: #e94560;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical:hover {
                background: #ff6b6b;
            }
            QFrame#questionCard {
                background-color: #2c2c3e;
                border-radius: 20px;
                border: 2px solid #e94560;
            }
            QFrame#feedbackCard {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #2c2c3e, stop:1 #3a3a4e);
                border-radius: 15px;
                border-left: 5px solid #e94560;
                padding: 15px;
            }
            QLabel#questionNumber {
                background-color: #e94560;
                border-radius: 15px;
                padding: 5px 15px;
                font-size: 16px;
                font-weight: bold;
            }
        """)

    def setup_ui(self):
        # Главный layout
        main_layout = QVBoxLayout()
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(30, 30, 30, 30)

        # ===== ВЕРХНЯЯ ПАНЕЛЬ =====
        top_panel = QFrame()
        top_panel.setStyleSheet("background-color: #2c2c3e; border-radius: 15px;")
        top_layout = QHBoxLayout(top_panel)
        top_layout.setContentsMargins(20, 15, 20, 15)

        # Номер вопроса
        self.question_number_label = QLabel()
        self.question_number_label.setObjectName("questionNumber")
        self.question_number_label.setAlignment(Qt.AlignCenter)
        self.question_number_label.setMinimumWidth(120)
        top_layout.addWidget(self.question_number_label)

        top_layout.addStretch()

        # Заголовок режима
        mode_title = QLabel("📖 УЧЕБНЫЙ РЕЖИМ" if self.training_mode else "🎯 РЕЖИМ ТЕСТИРОВАНИЯ")
        mode_title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        mode_title.setStyleSheet("color: #e94560;")
        top_layout.addWidget(mode_title)

        top_layout.addStretch()

        # Кнопка завершения
        self.finish_button = QPushButton("🏁 Завершить тест")
        self.finish_button.setMinimumWidth(150)
        self.finish_button.clicked.connect(self.finish_test)
        top_layout.addWidget(self.finish_button)

        main_layout.addWidget(top_panel)

        # ===== ПРОГРЕСС =====
        progress_layout = QVBoxLayout()
        progress_layout.setSpacing(8)

        # Прогресс-бар
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimumHeight(30)
        progress_layout.addWidget(self.progress_bar)

        # Текст прогресса
        self.progress_text = QLabel()
        self.progress_text.setAlignment(Qt.AlignCenter)
        self.progress_text.setFont(QFont("Segoe UI", 11))
        self.progress_text.setStyleSheet("color: #a6adc8;")
        progress_layout.addWidget(self.progress_text)

        main_layout.addLayout(progress_layout)

        # ===== ОСНОВНАЯ КАРТОЧКА ВОПРОСА =====
        self.question_card = QFrame()
        self.question_card.setObjectName("questionCard")
        card_layout = QVBoxLayout(self.question_card)
        card_layout.setSpacing(20)
        card_layout.setContentsMargins(30, 30, 30, 30)

        # Область скролла для вопроса
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMinimumHeight(550)
        content = QWidget()
        self.content_layout = QVBoxLayout(content)
        self.content_layout.setSpacing(20)
        scroll.setWidget(content)
        card_layout.addWidget(scroll)

        main_layout.addWidget(self.question_card, stretch=2)

        # ===== ТЕКСТ ВОПРОСА =====
        self.question_label = QLabel()
        self.question_label.setWordWrap(True)
        self.question_label.setFont(QFont("Segoe UI", 18, QFont.Bold))
        self.question_label.setAlignment(Qt.AlignLeft)
        self.question_label.setMinimumHeight(100)
        self.question_label.setStyleSheet("padding: 15px; background-color: #1a1a2e; border-radius: 15px;")
        self.content_layout.addWidget(self.question_label)

        # ===== ИЗОБРАЖЕНИЕ =====
        self.image_container = QWidget()
        image_container_layout = QVBoxLayout(self.image_container)
        image_container_layout.setAlignment(Qt.AlignCenter)

        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setMinimumHeight(250)
        self.image_label.setMaximumHeight(350)
        self.image_label.setStyleSheet("background-color: #1a1a2e; border-radius: 15px; padding: 15px;")
        self.image_label.setScaledContents(False)
        image_container_layout.addWidget(self.image_label)

        self.content_layout.addWidget(self.image_container)

        # ===== ВАРИАНТЫ ОТВЕТОВ =====
        options_header = QHBoxLayout()
        options_label = QLabel("📌 ВЫБЕРИТЕ ОТВЕТ(Ы):")
        options_label.setFont(QFont("Segoe UI", 14, QFont.Bold))
        options_label.setStyleSheet("color: #e94560;")
        options_header.addWidget(options_label)
        options_header.addStretch()

        # Индикатор типа ответа
        self.answer_type_label = QLabel("✓ Можно выбрать несколько вариантов")
        self.answer_type_label.setFont(QFont("Segoe UI", 11))
        self.answer_type_label.setStyleSheet("color: #a6adc8;")
        options_header.addWidget(self.answer_type_label)

        self.content_layout.addLayout(options_header)

        # Сетка для вариантов ответов (2x2)
        self.options_grid = QGridLayout()
        self.options_grid.setSpacing(15)
        self.options_grid.setContentsMargins(0, 10, 0, 10)

        self.radio_group = QButtonGroup()  # Для одиночного выбора
        self.checkboxes = []  # Для множественного выбора

        for i in range(4):
            # Будем использовать оба типа, но показывать нужный
            radio = QRadioButton()
            radio.setVisible(False)
            radio.setMinimumHeight(70)
            self.radio_group.addButton(radio, i)

            checkbox = QCheckBox()
            checkbox.setVisible(False)
            checkbox.setMinimumHeight(70)

            row = i // 2
            col = i % 2
            self.options_grid.addWidget(radio, row, col)
            self.options_grid.addWidget(checkbox, row, col)

            self.radio_group.buttons().append(radio)
            self.checkboxes.append(checkbox)

        self.content_layout.addLayout(self.options_grid)

        # ===== КАРТОЧКА ОБРАТНОЙ СВЯЗИ =====
        self.feedback_card = QFrame()
        self.feedback_card.setObjectName("feedbackCard")
        self.feedback_card.setVisible(False)
        feedback_layout = QVBoxLayout(self.feedback_card)

        self.feedback_label = QLabel()
        self.feedback_label.setWordWrap(True)
        self.feedback_label.setFont(QFont("Segoe UI", 13))
        feedback_layout.addWidget(self.feedback_label)

        self.content_layout.addWidget(self.feedback_card)

        self.content_layout.addStretch()

        # ===== НИЖНЯЯ ПАНЕЛЬ С КНОПКАМИ =====
        bottom_panel = QFrame()
        bottom_panel.setStyleSheet("background-color: #2c2c3e; border-radius: 15px;")
        bottom_layout = QHBoxLayout(bottom_panel)
        bottom_layout.setContentsMargins(20, 15, 20, 15)

        # Кнопка "Назад"
        self.back_button = QPushButton("◀◀  НАЗАД")
        self.back_button.clicked.connect(self.prev_question)
        self.back_button.setMinimumWidth(140)
        bottom_layout.addWidget(self.back_button)

        bottom_layout.addStretch()

        # Индикатор вопросов
        self.questions_indicator = QLabel()
        self.questions_indicator.setFont(QFont("Segoe UI", 12))
        self.questions_indicator.setAlignment(Qt.AlignCenter)
        self.questions_indicator.setStyleSheet(
            "color: #a6adc8; background-color: #1a1a2e; padding: 8px 20px; border-radius: 20px;")
        bottom_layout.addWidget(self.questions_indicator)

        bottom_layout.addStretch()

        # Кнопка "Проверить" / "Далее"
        self.action_button = QPushButton("ПРОВЕРИТЬ ОТВЕТ  ►" if self.training_mode else "ДАЛЕЕ  ►")
        self.action_button.clicked.connect(self.check_answer if self.training_mode else self.next_question)
        self.action_button.setMinimumWidth(180)
        self.action_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #4caf50, stop:1 #45a049);
                font-size: 16px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #66bb6a, stop:1 #4caf50);
            }
        """)
        bottom_layout.addWidget(self.action_button)

        # Кнопка "Продолжить" (для учебного режима)
        self.continue_button = QPushButton("СЛЕДУЮЩИЙ ВОПРОС  ►►")
        self.continue_button.clicked.connect(self.continue_to_next)
        self.continue_button.setMinimumWidth(200)
        self.continue_button.setVisible(False)
        self.continue_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2196f3, stop:1 #1976d2);
                font-size: 16px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #42a5f5, stop:1 #2196f3);
            }
        """)
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
            self.answer_type_label.setStyleSheet("color: #4caf50;")
        else:
            self.answer_type_label.setText("🔘 Выберите один вариант")
            self.answer_type_label.setStyleSheet("color: #e94560;")

        # Показываем нужные виджеты
        for i in range(4):
            self.radio_group.button(i).setVisible(not is_multiple)
            self.checkboxes[i].setVisible(is_multiple)

        # Обновляем прогресс
        self.question_number_label.setText(f"ВОПРОС {idx + 1} / {len(self.questions)}")
        self.questions_indicator.setText(f"📋 {idx + 1} из {len(self.questions)} вопросов")

        progress_value = int((idx + 1) / len(self.questions) * 100)
        self.progress_bar.setValue(progress_value)
        self.progress_text.setText(f"Прогресс: {progress_value}% завершено")

        # Текст вопроса
        self.question_label.setText(q['text'])

        # Загрузка изображения
        if q.get('image_path') and os.path.exists(q['image_path']):
            pixmap = QPixmap(q['image_path'])
            if not pixmap.isNull():
                scaled_pixmap = pixmap.scaled(600, 300, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.image_label.setPixmap(scaled_pixmap)
                self.image_container.setVisible(True)
            else:
                self.image_container.setVisible(False)
        else:
            self.image_container.setVisible(False)

        # Загрузка вариантов ответов
        options = [q['option1'], q['option2'], q['option3'], q['option4']]
        for i in range(4):
            # Для радио-кнопок
            radio = self.radio_group.button(i)
            if radio:
                radio.setText(options[i])
                radio.setChecked(False)
                radio.setEnabled(True)

            # Для чекбоксов
            self.checkboxes[i].setText(options[i])
            self.checkboxes[i].setChecked(False)
            self.checkboxes[i].setEnabled(True)

        # Скрываем карточку обратной связи
        self.feedback_card.setVisible(False)
        self.action_button.setVisible(True)
        self.continue_button.setVisible(False)

        # Восстановление сохраненного ответа (если есть)
        if self.answers[idx] is not None and self.answered[idx]:
            user_mask = self.answers[idx]['selected_mask']
            if is_multiple:
                for i in range(4):
                    if (user_mask >> i) & 1:
                        self.checkboxes[i].setChecked(True)
            else:
                for i in range(4):
                    if (user_mask >> i) & 1:
                        radio = self.radio_group.button(i)
                        if radio:
                            radio.setChecked(True)

            if self.training_mode:
                self.show_feedback_only()

        # Навигация
        self.back_button.setEnabled(idx > 0)
        if self.training_mode:
            self.action_button.setEnabled(not self.answered[idx])
        else:
            self.action_button.setEnabled(True)

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
            selected = [cb.isChecked() for cb in self.checkboxes]
        else:
            for i in range(4):
                radio = self.radio_group.button(i)
                selected.append(radio.isChecked() if radio else False)

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

        # Показываем обратную связь
        self.show_feedback()

        # Блокируем элементы выбора
        if is_multiple:
            for cb in self.checkboxes:
                cb.setEnabled(False)
        else:
            for i in range(4):
                radio = self.radio_group.button(i)
                if radio:
                    radio.setEnabled(False)

        # Меняем кнопки
        self.action_button.setVisible(False)
        self.continue_button.setVisible(True)

    def show_feedback(self):
        """Показ обратной связи после ответа"""
        q = self.questions[self.current_index]
        answer = self.answers[self.current_index]
        correct_mask = answer['correct_mask']
        user_mask = answer['selected_mask']
        is_correct = answer['correct']
        correct_count = bin(correct_mask).count("1")
        is_multiple = correct_count > 1

        # Подсветка вариантов
        for i in range(4):
            is_correct_option = (correct_mask >> i) & 1
            is_user_selected = (user_mask >> i) & 1

            if is_multiple:
                cb = self.checkboxes[i]
                if is_correct_option:
                    cb.setStyleSheet("""
                        QCheckBox { 
                            color: #4caf50; 
                            font-weight: bold;
                            background-color: rgba(76, 175, 80, 0.2);
                            border-radius: 10px;
                            padding: 12px;
                            border: 2px solid #4caf50;
                        }
                    """)
                elif not is_correct and is_user_selected:
                    cb.setStyleSheet("""
                        QCheckBox { 
                            color: #f44336; 
                            text-decoration: line-through;
                            background-color: rgba(244, 67, 54, 0.2);
                            border-radius: 10px;
                            padding: 12px;
                            border: 2px solid #f44336;
                        }
                    """)
            else:
                radio = self.radio_group.button(i)
                if is_correct_option:
                    radio.setStyleSheet("""
                        QRadioButton { 
                            color: #4caf50; 
                            font-weight: bold;
                            background-color: rgba(76, 175, 80, 0.2);
                            border-radius: 10px;
                            padding: 12px;
                            border: 2px solid #4caf50;
                        }
                        QRadioButton::indicator {
                            border-color: #4caf50;
                        }
                    """)
                elif not is_correct and is_user_selected:
                    radio.setStyleSheet("""
                        QRadioButton { 
                            color: #f44336; 
                            text-decoration: line-through;
                            background-color: rgba(244, 67, 54, 0.2);
                            border-radius: 10px;
                            padding: 12px;
                            border: 2px solid #f44336;
                        }
                        QRadioButton::indicator {
                            border-color: #f44336;
                        }
                    """)

        # Формируем текст обратной связи
        if is_correct:
            feedback_text = f"""
            <div style='text-align: center;'>
                <h2 style='color: #4caf50; margin: 0;'>✅ ПРАВИЛЬНО!</h2>
                <p style='font-size: 16px; margin-top: 10px;'>Отличный результат! Вы выбрали верный ответ.</p>
            </div>
            """
        else:
            correct_options = [q[f'option{i + 1}'] for i in range(4) if (correct_mask >> i) & 1]
            feedback_text = f"""
            <div style='text-align: center;'>
                <h2 style='color: #f44336; margin: 0;'>❌ НЕПРАВИЛЬНО</h2>
                <p style='font-size: 16px; margin-top: 10px;'>
                    <b style='color: #4caf50;'>✓ Правильный ответ:</b> {', '.join(correct_options)}
                </p>
                <hr style='border-color: #e94560; margin: 10px 0;'>
                <p style='font-size: 14px;'>
                    <b>💡 Пояснение:</b> {q['explanation']}
                </p>
            </div>
            """

        self.feedback_label.setText(feedback_text)
        self.feedback_card.setVisible(True)

    def show_feedback_only(self):
        """Показ обратной связи для уже отвеченных вопросов"""
        q = self.questions[self.current_index]
        answer = self.answers[self.current_index]
        correct_mask = answer['correct_mask']
        user_mask = answer['selected_mask']
        is_correct = answer['correct']
        correct_count = bin(correct_mask).count("1")
        is_multiple = correct_count > 1

        # Подсветка вариантов
        for i in range(4):
            is_correct_option = (correct_mask >> i) & 1
            is_user_selected = (user_mask >> i) & 1

            if is_multiple:
                cb = self.checkboxes[i]
                if is_correct_option:
                    cb.setStyleSheet("""
                        QCheckBox { 
                            color: #4caf50; 
                            font-weight: bold;
                            background-color: rgba(76, 175, 80, 0.2);
                            border-radius: 10px;
                            padding: 12px;
                            border: 2px solid #4caf50;
                        }
                    """)
                elif not is_correct and is_user_selected:
                    cb.setStyleSheet("""
                        QCheckBox { 
                            color: #f44336; 
                            text-decoration: line-through;
                            background-color: rgba(244, 67, 54, 0.2);
                            border-radius: 10px;
                            padding: 12px;
                            border: 2px solid #f44336;
                        }
                    """)
            else:
                radio = self.radio_group.button(i)
                if is_correct_option:
                    radio.setStyleSheet("""
                        QRadioButton { 
                            color: #4caf50; 
                            font-weight: bold;
                            background-color: rgba(76, 175, 80, 0.2);
                            border-radius: 10px;
                            padding: 12px;
                            border: 2px solid #4caf50;
                        }
                    """)
                elif not is_correct and is_user_selected:
                    radio.setStyleSheet("""
                        QRadioButton { 
                            color: #f44336; 
                            text-decoration: line-through;
                            background-color: rgba(244, 67, 54, 0.2);
                            border-radius: 10px;
                            padding: 12px;
                            border: 2px solid #f44336;
                        }
                    """)

        if is_correct:
            feedback_text = f"""
            <div style='text-align: center;'>
                <h2 style='color: #4caf50; margin: 0;'>✅ ПРАВИЛЬНО!</h2>
                <p style='font-size: 16px;'>Вы уже ответили на этот вопрос правильно.</p>
            </div>
            """
        else:
            correct_options = [q[f'option{i + 1}'] for i in range(4) if (correct_mask >> i) & 1]
            feedback_text = f"""
            <div style='text-align: center;'>
                <h2 style='color: #f44336; margin: 0;'>❌ НЕПРАВИЛЬНО</h2>
                <p style='font-size: 16px;'>
                    <b style='color: #4caf50;'>✓ Правильный ответ:</b> {', '.join(correct_options)}
                </p>
                <hr style='border-color: #e94560; margin: 10px 0;'>
                <p style='font-size: 14px;'>
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

        # Получаем выбранные ответы
        selected = []
        if is_multiple:
            selected = [cb.isChecked() for cb in self.checkboxes]
        else:
            for i in range(4):
                radio = self.radio_group.button(i)
                selected.append(radio.isChecked() if radio else False)

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
        # Сохраняем ответ на текущий вопрос, если он еще не сохранен
        if not self.answered[self.current_index] and not self.training_mode:
            q = self.questions[self.current_index]
            correct_count = bin(q['correct_mask']).count("1")
            is_multiple = correct_count > 1

            selected = []
            if is_multiple:
                selected = [cb.isChecked() for cb in self.checkboxes]
            else:
                for i in range(4):
                    radio = self.radio_group.button(i)
                    selected.append(radio.isChecked() if radio else False)

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
                    'explanation': q['explanation'],
                    'options': [q['option1'], q['option2'], q['option3'], q['option4']]
                }
                self.answered[self.current_index] = True

        answered_answers = [a for a in self.answers if a is not None]
        score = sum(1 for a in answered_answers if a['correct'])
        total = len(self.questions)

        if not self.training_mode:
            passed = (score / total * 100) >= 80
            self.db.save_test_result(self.user_id, score, total, self.answers)

            percent = score / total * 100

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
            percent = score / total * 100
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