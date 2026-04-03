# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import QWidget, QVBoxLayout
import matplotlib

matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from datetime import datetime
import numpy as np


class StatisticsChart(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Светлый фон для графика
        self.figure = Figure(figsize=(10, 5), dpi=100, facecolor='#f8f9fa')
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)

    def update_chart(self, test_results, passing_threshold=80):
        """Обновление графика с результатами тестов"""
        self.figure.clear()

        if not test_results:
            ax = self.figure.add_subplot(111)
            ax.text(0.5, 0.5, 'Нет данных для отображения\nПройдите тест, чтобы увидеть статистику',
                    ha='center', va='center', fontsize=12, color='#6c757d')
            ax.set_xticks([])
            ax.set_yticks([])
            ax.set_facecolor('#f8f9fa')
            self.canvas.draw()
            return

        sorted_results = sorted(test_results, key=lambda x: x['date'])

        attempts = list(range(1, len(sorted_results) + 1))
        scores = []
        dates = []

        for result in sorted_results:
            score_percent = (result['score'] / result['total']) * 100
            scores.append(score_percent)

            date_obj = datetime.fromisoformat(result['date'].replace(' ', 'T'))
            dates.append(date_obj.strftime('%d.%m.%y\n%H:%M'))

        ax = self.figure.add_subplot(111)

        # Основная линия графика
        ax.plot(attempts, scores, 'o-', linewidth=2, markersize=8,
                color='#3498db', label='Результат теста', markerfacecolor='#2980b9')

        # Порог прохождения
        ax.axhline(y=passing_threshold, color='#e74c3c', linestyle='--',
                   linewidth=2, label=f'Порог прохождения ({passing_threshold}%)')

        # Заливка областей
        ax.fill_between(attempts, scores, passing_threshold,
                        where=(np.array(scores) >= passing_threshold),
                        color='#27ae60', alpha=0.3, label='Успешно')
        ax.fill_between(attempts, scores, passing_threshold,
                        where=(np.array(scores) < passing_threshold),
                        color='#e74c3c', alpha=0.3, label='Не сдано')

        # Подписи осей
        ax.set_xlabel('Номер попытки (дата, время)', fontsize=10, fontweight='bold', color='#2c3e50')
        ax.set_ylabel('Результат теста, %', fontsize=10, fontweight='bold', color='#2c3e50')
        ax.set_title('Динамика результатов тестирования', fontsize=12, fontweight='bold', color='#2c3e50', pad=15)

        # Настройка осей X
        ax.set_xticks(attempts)
        ax.set_xticklabels(dates, fontsize=8, color='#495057')

        # Настройка оси Y
        ax.set_ylim(0, 105)
        ax.set_yticks(range(0, 101, 10))
        ax.set_yticklabels([f'{i}%' for i in range(0, 101, 10)], color='#495057')

        # Аннотации точек
        for x, y in zip(attempts, scores):
            ax.annotate(f'{y:.0f}%', (x, y), textcoords="offset points",
                        xytext=(0, 10), ha='center', fontsize=8,
                        bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8, edgecolor='#3498db'))

        # Легенда
        ax.legend(loc='lower right', framealpha=0.9, fontsize=9, facecolor='white', edgecolor='#dee2e6')

        # Сетка
        ax.grid(True, alpha=0.3, linestyle='--', color='#adb5bd')

        # Оформление
        ax.set_facecolor('#f8f9fa')
        ax.spines['top'].set_color('#dee2e6')
        ax.spines['right'].set_color('#dee2e6')
        ax.spines['bottom'].set_color('#dee2e6')
        ax.spines['left'].set_color('#dee2e6')
        ax.tick_params(colors='#495057')

        self.figure.tight_layout()
        self.canvas.draw()

    def create_pie_chart(self, data, labels, title, colors=None):
        """Создание круговой диаграммы"""
        self.figure.clear()

        ax = self.figure.add_subplot(111)

        if colors is None:
            colors = ['#27ae60', '#e74c3c', '#3498db', '#f39c12']

        wedges, texts, autotexts = ax.pie(data, labels=labels, autopct='%1.1f%%',
                                          startangle=90, colors=colors[:len(data)])

        # Стилизация текста
        for text in texts:
            text.set_color('#2c3e50')
            text.set_fontsize(10)
            text.set_fontweight('bold')

        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')
            autotext.set_fontsize(11)

        ax.set_title(title, fontsize=12, fontweight='bold', color='#2c3e50', pad=15)
        ax.set_facecolor('#f8f9fa')

        self.figure.tight_layout()
        self.canvas.draw()

    def create_bar_chart(self, data, labels, title, ylabel, threshold=None):
        """Создание столбчатой диаграммы"""
        self.figure.clear()

        ax = self.figure.add_subplot(111)

        # Создание столбцов
        bars = ax.bar(labels, data, alpha=0.8, edgecolor='white', linewidth=2)

        # Цветовая индикация
        for i, (bar, val) in enumerate(zip(bars, data)):
            if threshold and val >= threshold:
                bar.set_color('#27ae60')  # Зеленый для успешных
            elif threshold and val < threshold:
                bar.set_color('#e74c3c')  # Красный для неуспешных
            else:
                bar.set_color('#3498db')  # Синий по умолчанию

        # Подписи осей
        ax.set_ylabel(ylabel, fontsize=10, fontweight='bold', color='#2c3e50')
        ax.set_title(title, fontsize=12, fontweight='bold', color='#2c3e50', pad=15)

        # Оформление
        ax.set_facecolor('#f8f9fa')
        ax.spines['top'].set_color('#dee2e6')
        ax.spines['right'].set_color('#dee2e6')
        ax.spines['bottom'].set_color('#dee2e6')
        ax.spines['left'].set_color('#dee2e6')
        ax.tick_params(colors='#495057', axis='x', rotation=45, labelsize=9)

        # Добавление значений на столбцы
        for bar, val in zip(bars, data):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 1,
                    f'{val:.1f}%' if threshold else f'{val:.0f}',
                    ha='center', va='bottom', fontsize=9, color='#2c3e50', fontweight='bold')

        # Добавление горизонтальной линии порога
        if threshold:
            ax.axhline(y=threshold, color='#e74c3c', linestyle='--',
                      linewidth=2, alpha=0.7, label=f'Порог: {threshold}%')
            ax.legend(loc='upper right', framealpha=0.9, fontsize=9, facecolor='white')

        self.figure.tight_layout()
        self.canvas.draw()