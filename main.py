#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
СВГ-Тренажер – приложение для подготовки личного состава по сопровождению воинских грузов.
Версия 11.0: Переписано на PyQt5 с разделением на модули
"""

import sys
import os
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt


def main():
    # Создаем необходимые директории
    os.makedirs("materials", exist_ok=True)
    os.makedirs("questions_images", exist_ok=True)

    # Включаем High DPI до создания QApplication
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    # Запуск приложения
    app = QApplication(sys.argv)

    # Импортируем главное окно после инициализации приложения
    from main_window import MainWindow

    window = MainWindow()
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()