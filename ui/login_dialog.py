import sys
from PyQt5.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QMessageBox,
    QDialogButtonBox,
)
from PyQt5.QtCore import Qt

# Импортируем КЛАССЫ, а не объекты
from database.db import Database
from database.queries import Queries
import bcrypt
import psycopg2


class LoginDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Авторизация")
        self.setModal(True)
        self.db = Database()  # Создаем экземпляр Database
        self._user_role = None
        self._username = None

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)  # Указываем родителя
        form_layout = QVBoxLayout()  # Используем QVBoxLayout для полей

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Имя пользователя")
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Пароль")
        self.password_input.setEchoMode(QLineEdit.Password)

        form_layout.addWidget(QLabel("Введите ваши учетные данные:"))
        form_layout.addWidget(self.username_input)
        form_layout.addWidget(self.password_input)

        layout.addLayout(form_layout)  # Добавляем layout с полями

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Ok).setText("Войти")
        # Ok -> accept, Cancel -> reject по умолчанию, но мы переопределяем Ok
        buttons.accepted.connect(self.handle_login)
        buttons.rejected.connect(self.reject)

        layout.addWidget(buttons)
        self.username_input.setFocus()

    def handle_login(self):
        username = self.username_input.text().strip()
        password = self.password_input.text()

        if not username or not password:
            QMessageBox.warning(
                self, "Ошибка", "Имя пользователя и пароль не могут быть пустыми."
            )
            return

        try:
            with self.db.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(Queries.GET_USER_BY_USERNAME, (username,))
                    user_data = cursor.fetchone()

                    if user_data:
                        user_id, db_username, password_hash, role = user_data
                        if bcrypt.checkpw(
                            password.encode("utf-8"), password_hash.encode("utf-8")
                        ):
                            self._user_role = role
                            self._username = db_username
                            # Если проверка прошла, вызываем стандартный accept()
                            super().accept()  # Используем super() для вызова родительского метода
                        else:
                            QMessageBox.warning(self, "Ошибка", "Неверный пароль.")
                            self.password_input.clear()
                            self.password_input.setFocus()
                    else:
                        QMessageBox.warning(
                            self, "Ошибка", "Пользователь с таким именем не найден."
                        )
                        self.username_input.selectAll()  # Выделить текст для удобства
                        self.username_input.setFocus()

        except psycopg2.OperationalError as db_err:
            QMessageBox.critical(
                self, "Ошибка БД", f"Не удалось выполнить вход:\n{db_err}"
            )
            # Не закрываем диалог, даем пользователю шанс попробовать снова или отменить
        except Exception as e:
            QMessageBox.critical(
                self, "Ошибка", f"Произошла непредвиденная ошибка:\n{e}"
            )
            # Можно self.reject() здесь, если ошибка фатальная

    def get_user_role(self):
        return self._user_role

    def get_username(self):
        return self._username
