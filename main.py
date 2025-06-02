import sys
import os
from PyQt5.QtWidgets import QApplication, QMessageBox, QDialog
from PyQt5.QtGui import QIcon, QPalette, QColor
from PyQt5.QtCore import Qt

# Импорты после установки путей (если они нужны)
from ui.login_dialog import LoginDialog
from ui.main_window import MainWindow
import psycopg2  # Импортируем для ловли OperationalError


def set_glass_dark_palette(app):
    palette = QPalette()

    # Стеклянно-темная палитра
    palette.setColor(QPalette.Window, QColor(30, 30, 30, 220))  # Окна
    palette.setColor(QPalette.WindowText, Qt.white)
    palette.setColor(QPalette.Base, QColor(20, 20, 20, 200))  # Текстовые поля
    palette.setColor(QPalette.AlternateBase, QColor(40, 40, 40, 180))
    palette.setColor(QPalette.Text, Qt.white)
    palette.setColor(QPalette.Button, QColor(60, 60, 60, 200))
    palette.setColor(QPalette.ButtonText, Qt.white)
    palette.setColor(QPalette.ToolTipBase, QColor("#2a2a2a"))
    palette.setColor(QPalette.ToolTipText, Qt.white)
    palette.setColor(QPalette.Highlight, QColor("#bb86fc"))  # Material Accent
    palette.setColor(QPalette.HighlightedText, Qt.black)

    # Disabled
    palette.setColor(QPalette.Disabled, QPalette.Text, QColor(127, 127, 127))
    palette.setColor(QPalette.Disabled, QPalette.ButtonText, QColor(127, 127, 127))

    app.setPalette(palette)


def main():
    app = QApplication(sys.argv)
    app.setStyle("Macintosh")  # Fusion Macintosh
    # set_glass_dark_palette(app)

    # --- Диалог входа ---
    login_dialog = LoginDialog()
    # Обрабатываем ошибки подключения ПЕРЕД показом диалога входа
    try:
        # Попытка тестового подключения из диалога
        db = login_dialog.db  # Доступ к экземпляру Database в диалоге
        with db.get_connection():
            pass  # Соединение успешно
    except psycopg2.OperationalError as db_err:
        QMessageBox.critical(
            None,  # Parent=None, т.к. главное окно еще не создано
            "Ошибка соединения с БД",
            f"Не удалось подключиться к базе данных:\n{db_err}\n"
            "Проверьте параметры подключения и доступность сервера.\n"
            "Приложение будет закрыто.",
        )
        sys.exit(1)
    except Exception as e:
        QMessageBox.critical(
            None, "Критическая ошибка", f"Ошибка при инициализации БД:\n{e}"
        )
        sys.exit(1)

    if login_dialog.exec_() == QDialog.Accepted:
        username = login_dialog.get_username()
        user_role = login_dialog.get_user_role()

        # --- Создание главного окна ---
        window = MainWindow(username, user_role)

        if window.initialization_failed():
            # Сообщение уже было показано
            sys.exit(1)

        window.show()
        sys.exit(app.exec_())
    else:
        sys.exit(0)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Критическая ошибка в main: {e}")
        # Пробуем показать сообщение, если возможно
        try:
            QMessageBox.critical(
                None, "Критическая ошибка", f"Произошла непредвиденная ошибка:\n{e}"
            )
        except RuntimeError:  # Если QApplication уже не существует
            pass
        sys.exit(1)
