from PyQt5.QtWidgets import (
    QDialog,
    QFormLayout,
    QLineEdit,
    QDialogButtonBox,
    QMessageBox,
)
from PyQt5.QtCore import Qt

from database.db import Database
from database.queries import Queries
import psycopg2


class ClientDialog(QDialog):
    def __init__(self, parent=None, client_id=None):
        super().__init__(parent)
        self.client_id = client_id
        self.db = Database()
        self.original_phone = None

        self.setWindowTitle(
            "Редактировать клиента" if client_id else "Добавить клиента"
        )
        self.setModal(True)
        self.setMinimumWidth(400)
        self.init_ui()

        if client_id:
            self.load_data()

    def init_ui(self):
        layout = QFormLayout(self)

        self.first_name_input = QLineEdit()
        self.first_name_input.setPlaceholderText("Введите имя")
        
        self.last_name_input = QLineEdit()
        self.last_name_input.setPlaceholderText("Введите фамилию")
        
        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("+7 (XXX) XXX-XX-XX")
        self.phone_input.setInputMask("+7 (999) 999-99-99")

        layout.addRow("Имя*:", self.first_name_input)
        layout.addRow("Фамилия*:", self.last_name_input)
        layout.addRow("Телефон*:", self.phone_input)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept_data)
        buttons.rejected.connect(self.reject)

        layout.addRow(buttons)

    def load_data(self):
        try:
            with self.db.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(Queries.GET_CLIENT_BY_ID, (self.client_id,))
                    client = cursor.fetchone()
                    
                    if not client:
                        QMessageBox.critical(self, "Ошибка", "Клиент не найден")
                        self.reject()
                        return

                    self.first_name_input.setText(client[1])
                    self.last_name_input.setText(client[2])
                    self.phone_input.setText(client[3])
                    self.original_phone = client[3]

        except psycopg2.Error as e:
            QMessageBox.critical(
                self, "Ошибка БД", f"Не удалось загрузить данные клиента:\n{str(e)}"
            )
            self.reject()

    def get_data(self):
        return (
            self.first_name_input.text().strip(),
            self.last_name_input.text().strip(),
            self.phone_input.text().strip()
        )

    def accept_data(self):
        first_name, last_name, phone = self.get_data()

        # Validation
        errors = []
        if not first_name:
            errors.append("Введите имя")
        if not last_name:
            errors.append("Введите фамилию")
        if not phone or len(phone.replace(" ", "").replace("(", "").replace(")", "").replace("-", "")) != 12:
            errors.append("Введите корректный номер телефона")

        if errors:
            QMessageBox.warning(self, "Ошибка валидации", "\n".join(errors))
            return

        # Check phone uniqueness
        if phone != self.original_phone:
            try:
                with self.db.get_connection() as conn:
                    with conn.cursor() as cursor:
                        cursor.execute(
                            Queries.CHECK_CLIENT_PHONE_EXISTS,
                            (phone, self.client_id, self.client_id)
                        )
                        if cursor.fetchone():
                            QMessageBox.warning(
                                self,
                                "Ошибка",
                                f"Клиент с телефоном {phone} уже существует"
                            )
                            return
            except psycopg2.Error as e:
                QMessageBox.critical(
                    self,
                    "Ошибка БД",
                    f"Не удалось проверить уникальность телефона:\n{str(e)}"
                )
                return

        super().accept() 