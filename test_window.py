from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QScrollArea, QWidget, QCheckBox,
                             QMessageBox, QFrame, QGridLayout, QProgressBar)
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
        self.apply_modern_style()

    def apply_modern_style(self):
        """Современный стиль для окна тестирования"""
        self.setStyleSheet("""
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
                border-radius: 10px;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #b4befe;
            }
            QPushButton:disabled {
                background-color: #45475a;
                color: #6c7086;
            }
            QProgressBar {
                border: none;
                border-radius: 10px;
                background-color: #313244;
                text-align: center;
                color: #cdd6f4;
                font-weight: bold;
            }
            QProgressBar::chunk {
                background-color: #89b4fa;
                border-radius: 10px;
            }
            QCheckBox {
                color: #cdd6f4;
                spacing: 12px;
                font-size: 14px;
                padding: 8px;
            }
            QCheckBox::indicator {
                width: 20px;
                height: 20px;
                border-radius: 5px;
                border: 2px solid #89b4fa;
                background-color: #313244;
            }
            QCheckBox::indicator:checked {
                background-color: #a6e3a1;
                border-color: #a6e3a1;
            }
            QScrollArea {
                background-color: transparent;
                border: none;
            }
            QScrollBar:vertical {
                background: #313244;
                width: 10px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical {
                background: #89b4fa;
                border-radius: 5px;
            }
            QFrame#questionCard {
                background-color: #313244;
                border-radius: 15px;
                border: 1px solid #45475a;
            }
            QFrame#feedbackCard {
                background-color: #45475a;
                border-radius: 10px;
                margin-top: 10px;
            }
        """)

    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # Верхняя панель с прогрессом
        top_layout = QHBoxLayout()

        self.progress_label = QLabel()
        self.progress_label.setFont(QFont("Segoe UI", 14, QFont.Bold))
        top_layout.addWidget(self.progress_label)

        top_layout.addStretch()

        self.finish_button = QPushButton("🏁 Завершить тест")
        self.finish_button.clicked.connect(self.finish_test)
        top_layout.addWidget(self.finish_button)

        layout.addLayout(top_layout)

        # Прогресс бар
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimumHeight(20)
        layout.addWidget(self.progress_bar)

        # Основная карточка с вопросом
        self.question_card = QFrame()
        self.question_card.setObjectName("questionCard")
        card_layout = QVBoxLayout(self.question_card)
        card_layout.setSpacing(15)
        card_layout.setContentsMargins(20, 20, 20, 20)

        # Область скролла
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMinimumHeight(500)
        content = QWidget()
        self.content_layout = QVBoxLayout(content)
        self.content_layout.setSpacing(15)
        scroll.setWidget(content)
        card_layout.addWidget(scroll)

        layout.addWidget(self.question_card, stretch=1)

        # Текст вопроса
        self.question_label = QLabel()
        self.question_label.setWordWrap(True)
        self.question_label.setFont(QFont("Segoe UI", 16, QFont.Bold))
        self.question_label.setAlignment(Qt.AlignLeft)
        self.question_label.setMinimumHeight(80)
        self.question_label.setMaximumHeight(200)
        self.question_label.setStyleSheet("padding: 10px;")
        self.content_layout.addWidget(self.question_label)

        # Контейнер для изображения (центрированный)
        self.image_container = QWidget()
        image_container_layout = QVBoxLayout(self.image_container)
        image_container_layout.setAlignment(Qt.AlignCenter)

        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setMinimumHeight(200)
        self.image_label.setMaximumHeight(300)
        self.image_label.setStyleSheet("background-color: #45475a; border-radius: 10px; padding: 10px;")
        self.image_label.setScaledContents(False)
        image_container_layout.addWidget(self.image_label)

        self.content_layout.addWidget(self.image_container)

        # Варианты ответов в сетке 2x2
        options_label = QLabel("Выберите ответ(ы):")
        options_label.setFont(QFont("Segoe UI", 12, QFont.Bold))
        self.content_layout.addWidget(options_label)

        options_grid = QGridLayout()
        options_grid.setSpacing(10)

        self.checkboxes = []
        for i in range(4):
            cb = QCheckBox()
            # QCheckBox не имеет setWordWrap, используем QLabel внутри или просто текст
            # Вместо этого сделаем текст переносимым через стиль
            cb.setStyleSheet("QCheckBox { white-space: normal; }")
            cb.setMinimumHeight(50)
            cb.setMaximumHeight(100)
            row = i // 2
            col = i % 2
            options_grid.addWidget(cb, row, col)
            self.checkboxes.append(cb)

        self.content_layout.addLayout(options_grid)

        # Карточка для обратной связи (только для учебного режима)
        self.feedback_card = QFrame()
        self.feedback_card.setObjectName("feedbackCard")
        self.feedback_card.setVisible(False)
        feedback_layout = QVBoxLayout(self.feedback_card)

        self.feedback_label = QLabel()
        self.feedback_label.setWordWrap(True)
        self.feedback_label.setFont(QFont("Segoe UI", 12))
        feedback_layout.addWidget(self.feedback_label)

        self.content_layout.addWidget(self.feedback_card)

        self.content_layout.addStretch()

        # Кнопки навигации
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(10)

        self.back_button = QPushButton("◀ Назад")
        self.back_button.clicked.connect(self.prev_question)
        self.back_button.setMinimumSize(100, 40)
        buttons_layout.addWidget(self.back_button)

        buttons_layout.addStretch()

        if self.training_mode:
            self.next_button = QPushButton("✓ Проверить ответ")
            self.next_button.clicked.connect(self.check_answer)
        else:
            self.next_button = QPushButton("Далее ▶")
            self.next_button.clicked.connect(self.next_question)

        self.next_button.setMinimumSize(150, 40)
        buttons_layout.addWidget(self.next_button)

        buttons_layout.addStretch()

        self.continue_button = QPushButton("Следующий вопрос ▶")
        self.continue_button.clicked.connect(self.continue_to_next)
        self.continue_button.setMinimumSize(180, 40)
        self.continue_button.setVisible(False)
        buttons_layout.addWidget(self.continue_button)

        layout.addLayout(buttons_layout)

        self.setLayout(layout)

    def load_question(self, idx):
        q = self.questions[idx]

        # Обновляем прогресс (правильно: показываем текущий вопрос)
        self.progress_label.setText(f"Вопрос {idx + 1} из {len(self.questions)}")
        # Прогресс-бар: (текущий вопрос) / (всего вопросов) * 100
        if len(self.questions) > 0:
            self.progress_bar.setValue(int((idx) / len(self.questions) * 100))
        else:
            self.progress_bar.setValue(0)

        self.question_label.setText(q['text'])

        # Загрузка изображения
        if q.get('image_path') and os.path.exists(q['image_path']):
            pixmap = QPixmap(q['image_path'])
            if not pixmap.isNull():
                # Масштабируем изображение с сохранением пропорций
                scaled_pixmap = pixmap.scaled(500, 250, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.image_label.setPixmap(scaled_pixmap)
                self.image_container.setVisible(True)
            else:
                self.image_container.setVisible(False)
        else:
            self.image_container.setVisible(False)

        # Загрузка вариантов ответов
        options = [q['option1'], q['option2'], q['option3'], q['option4']]
        for i, cb in enumerate(self.checkboxes):
            cb.setText(options[i])
            cb.setChecked(False)
            cb.setEnabled(True)
            cb.setStyleSheet("QCheckBox { white-space: normal; }")

        # Скрываем карточку обратной связи
        self.feedback_card.setVisible(False)
        self.next_button.setVisible(True)
        self.continue_button.setVisible(False)

        # Восстановление сохраненного ответа (если есть)
        if self.answers[idx] is not None and self.answered[idx]:
            user_mask = self.answers[idx]['selected_mask']
            for i in range(4):
                if (user_mask >> i) & 1:
                    self.checkboxes[i].setChecked(True)
            if self.training_mode:
                self.show_feedback_only()

        # Навигация
        self.back_button.setEnabled(idx > 0)
        self.next_button.setEnabled(not self.answered[idx] if self.training_mode else True)

    def check_answer(self):
        """Проверка ответа в учебном режиме"""
        if self.answered[self.current_index]:
            return

        selected = [cb.isChecked() for cb in self.checkboxes]
        if not any(selected):
            QMessageBox.warning(self, "Внимание", "Пожалуйста, выберите вариант ответа")
            return

        q = self.questions[self.current_index]
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

        # Блокируем чекбоксы
        for cb in self.checkboxes:
            cb.setEnabled(False)

        # Меняем кнопки
        self.next_button.setVisible(False)
        self.continue_button.setVisible(True)

    def show_feedback(self):
        """Показ обратной связи после ответа"""
        q = self.questions[self.current_index]
        answer = self.answers[self.current_index]
        correct_mask = answer['correct_mask']
        user_mask = answer['selected_mask']
        is_correct = answer['correct']

        # Подсветка вариантов
        for i in range(4):
            cb = self.checkboxes[i]
            if (correct_mask >> i) & 1:
                cb.setStyleSheet("""
                    QCheckBox { 
                        color: #a6e3a1; 
                        font-weight: bold;
                        background-color: rgba(166, 227, 161, 0.1);
                        border-radius: 5px;
                        padding: 5px;
                        white-space: normal;
                    }
                """)
            elif not is_correct and (user_mask >> i) & 1:
                cb.setStyleSheet("""
                    QCheckBox { 
                        color: #f38ba8; 
                        text-decoration: line-through;
                        background-color: rgba(243, 139, 168, 0.1);
                        border-radius: 5px;
                        padding: 5px;
                        white-space: normal;
                    }
                """)

        # Формируем текст обратной связи
        if is_correct:
            feedback_text = f"""
            <div style='text-align: center;'>
                <h3 style='color: #a6e3a1;'>✅ ПРАВИЛЬНО!</h3>
                <p style='font-size: 14px;'>Отличный результат! Вы выбрали верный ответ.</p>
            </div>
            """
        else:
            correct_options = [q[f'option{i + 1}'] for i in range(4) if (correct_mask >> i) & 1]
            feedback_text = f"""
            <div style='text-align: center;'>
                <h3 style='color: #f38ba8;'>❌ НЕПРАВИЛЬНО</h3>
                <p style='font-size: 14px;'>
                    <b>Правильный ответ:</b> {', '.join(correct_options)}<br><br>
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

        for i in range(4):
            cb = self.checkboxes[i]
            if (correct_mask >> i) & 1:
                cb.setStyleSheet("""
                    QCheckBox { 
                        color: #a6e3a1; 
                        font-weight: bold;
                        background-color: rgba(166, 227, 161, 0.1);
                        border-radius: 5px;
                        padding: 5px;
                        white-space: normal;
                    }
                """)
            elif not is_correct and (user_mask >> i) & 1:
                cb.setStyleSheet("""
                    QCheckBox { 
                        color: #f38ba8; 
                        text-decoration: line-through;
                        background-color: rgba(243, 139, 168, 0.1);
                        border-radius: 5px;
                        padding: 5px;
                        white-space: normal;
                    }
                """)

        if is_correct:
            feedback_text = f"""
            <div style='text-align: center;'>
                <h3 style='color: #a6e3a1;'>✅ ПРАВИЛЬНО!</h3>
                <p style='font-size: 14px;'>Вы уже ответили на этот вопрос правильно.</p>
            </div>
            """
        else:
            correct_options = [q[f'option{i + 1}'] for i in range(4) if (correct_mask >> i) & 1]
            feedback_text = f"""
            <div style='text-align: center;'>
                <h3 style='color: #f38ba8;'>❌ НЕПРАВИЛЬНО</h3>
                <p style='font-size: 14px;'>
                    <b>Правильный ответ:</b> {', '.join(correct_options)}<br><br>
                    <b>💡 Пояснение:</b> {q['explanation']}
                </p>
            </div>
            """

        self.feedback_label.setText(feedback_text)
        self.feedback_card.setVisible(True)
        self.next_button.setVisible(False)
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
        selected = [cb.isChecked() for cb in self.checkboxes]
        if not any(selected):
            QMessageBox.warning(self, "Внимание", "Пожалуйста, выберите вариант ответа")
            return

        q = self.questions[self.current_index]
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
            selected = [cb.isChecked() for cb in self.checkboxes]
            if any(selected):
                q = self.questions[self.current_index]
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