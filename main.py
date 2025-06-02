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
    app.setStyle("Fusion")  # Use Fusion style for better cross-platform look

    # Show login dialog
    login_dialog = LoginDialog()
    if login_dialog.exec_() == LoginDialog.Accepted:
        # Get user credentials
        username = login_dialog.get_username()
        user_role = login_dialog.get_user_role()

        # Create and show main window
        main_window = MainWindow(username, user_role)
        main_window.show()

        # Start event loop
        return app.exec_()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
