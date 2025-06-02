import sys
from PyQt5.QtWidgets import (
    QDialog,
    QFormLayout,
    QLineEdit,
    QDialogButtonBox,
    QMessageBox,
)
from PyQt5.QtCore import Qt

# Импортируем КЛАССЫ, а не объекты
from database.db import Database
from database.queries import Queries
import psycopg2
import hashlib


class LoginDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = Database()
        self.username = None
        self.user_role = None

        self.setWindowTitle("Вход в систему")
        self.setModal(True)
        self.setMinimumWidth(300)
        self.init_ui()

    def init_ui(self):
        layout = QFormLayout(self)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Введите имя пользователя")
        
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Введите пароль")
        self.password_input.setEchoMode(QLineEdit.Password)

        layout.addRow("Пользователь*:", self.username_input)
        layout.addRow("Пароль*:", self.password_input)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept_data)
        buttons.rejected.connect(self.reject)

        layout.addRow(buttons)

    def get_credentials(self):
        return (
            self.username_input.text().strip(),
            self.password_input.text().strip()
        )

    def accept_data(self):
        username, password = self.get_credentials()

        # Validation
        errors = []
        if not username:
            errors.append("Введите имя пользователя")
        if not password:
            errors.append("Введите пароль")

        if errors:
            QMessageBox.warning(self, "Ошибка валидации", "\n".join(errors))
            return

        # Hash password
        password_hash = hashlib.sha256(password.encode()).hexdigest()

        try:
            with self.db.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        Queries.GET_USER_BY_USERNAME,
                        (username,)
                    )
                    user = cursor.fetchone()

                    if not user or user[2] != password_hash:
                        QMessageBox.warning(
                            self,
                            "Ошибка входа",
                            "Неверное имя пользователя или пароль"
                        )
                        return

                    self.username = username
                    self.user_role = user[3]
                    super().accept()

        except psycopg2.Error as e:
            QMessageBox.critical(
                self,
                "Ошибка БД",
                f"Не удалось выполнить вход:\n{str(e)}"
            )

    def get_user_role(self):
        return self.user_role

    def get_username(self):
        return self.username
