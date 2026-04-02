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

        self.figure = Figure(figsize=(10, 5), dpi=100, facecolor='#313244')
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)

    def update_chart(self, test_results, passing_threshold=80):
        """Обновление графика с результатами тестов"""
        self.figure.clear()

        if not test_results:
            ax = self.figure.add_subplot(111)
            ax.text(0.5, 0.5, 'Нет данных для отображения\nПройдите тест, чтобы увидеть статистику',
                    ha='center', va='center', fontsize=12, color='#cdd6f4')
            ax.set_xticks([])
            ax.set_yticks([])
            ax.set_facecolor('#313244')
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

        ax.plot(attempts, scores, 'o-', linewidth=2, markersize=8,
                color='#89b4fa', label='Результат теста', markerfacecolor='#b4befe')

        ax.axhline(y=passing_threshold, color='#f38ba8', linestyle='--',
                   linewidth=2, label=f'Порог прохождения ({passing_threshold}%)')

        ax.fill_between(attempts, scores, passing_threshold,
                        where=(np.array(scores) >= passing_threshold),
                        color='#a6e3a1', alpha=0.3, label='Успешно')
        ax.fill_between(attempts, scores, passing_threshold,
                        where=(np.array(scores) < passing_threshold),
                        color='#f38ba8', alpha=0.3, label='Не сдано')

        ax.set_xlabel('Номер попытки (дата, время)', fontsize=10, fontweight='bold', color='#cdd6f4')
        ax.set_ylabel('Результат теста, %', fontsize=10, fontweight='bold', color='#cdd6f4')
        ax.set_title('Динамика результатов тестирования', fontsize=12, fontweight='bold', color='#cdd6f4', pad=15)

        ax.set_xticks(attempts)
        ax.set_xticklabels(dates, fontsize=8, color='#cdd6f4')

        ax.set_ylim(0, 105)
        ax.set_yticks(range(0, 101, 10))
        ax.set_yticklabels([f'{i}%' for i in range(0, 101, 10)], color='#cdd6f4')

        for x, y in zip(attempts, scores):
            ax.annotate(f'{y:.0f}%', (x, y), textcoords="offset points",
                        xytext=(0, 10), ha='center', fontsize=8,
                        bbox=dict(boxstyle="round,pad=0.3", facecolor="#313244", alpha=0.8, color='#89b4fa'))

        ax.legend(loc='lower right', framealpha=0.9, fontsize=9, facecolor='#313244', edgecolor='#89b4fa')
        ax.grid(True, alpha=0.2, linestyle='--', color='#cdd6f4')

        ax.set_facecolor('#313244')
        ax.spines['top'].set_color('#45475a')
        ax.spines['right'].set_color('#45475a')
        ax.spines['bottom'].set_color('#45475a')
        ax.spines['left'].set_color('#45475a')
        ax.tick_params(colors='#cdd6f4')

        self.figure.tight_layout()
        self.canvas.draw()

    def create_pie_chart(self, data, labels, title, colors=None):
        """Создание круговой диаграммы"""
        self.figure.clear()

        ax = self.figure.add_subplot(111)

        if colors is None:
            colors = ['#a6e3a1', '#f38ba8', '#89b4fa', '#f9e2af']

        wedges, texts, autotexts = ax.pie(data, labels=labels, autopct='%1.1f%%',
                                          startangle=90, colors=colors[:len(data)])

        for text in texts:
            text.set_color('#cdd6f4')
            text.set_fontsize(10)

        for autotext in autotexts:
            autotext.set_color('#1e1e2e')
            autotext.set_fontweight('bold')

        ax.set_title(title, fontsize=12, fontweight='bold', color='#cdd6f4', pad=15)
        ax.set_facecolor('#313244')

        self.figure.tight_layout()
        self.canvas.draw()

    def create_bar_chart(self, data, labels, title, ylabel, threshold=None):
        """Создание столбчатой диаграммы"""
        self.figure.clear()

        ax = self.figure.add_subplot(111)

        bars = ax.bar(labels, data, color='#89b4fa', alpha=0.8, edgecolor='#b4befe', linewidth=2)

        for i, (bar, val) in enumerate(zip(bars, data)):
            if threshold and val >= threshold:
                bar.set_color('#a6e3a1')
            elif threshold and val < threshold:
                bar.set_color('#f38ba8')

        ax.set_ylabel(ylabel, fontsize=10, fontweight='bold', color='#cdd6f4')
        ax.set_title(title, fontsize=12, fontweight='bold', color='#cdd6f4', pad=15)

        ax.set_facecolor('#313244')
        ax.spines['top'].set_color('#45475a')
        ax.spines['right'].set_color('#45475a')
        ax.spines['bottom'].set_color('#45475a')
        ax.spines['left'].set_color('#45475a')
        ax.tick_params(colors='#cdd6f4', axis='x', rotation=45, labelsize=9)

        for bar, val in zip(bars, data):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 1,
                    f'{val:.0f}', ha='center', va='bottom', fontsize=9, color='#cdd6f4')

        self.figure.tight_layout()
        self.canvas.draw()