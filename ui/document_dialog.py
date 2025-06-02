from PyQt5.QtWidgets import (
    QDialog,
    QFormLayout,
    QLineEdit,
    QComboBox,
    QDateEdit,
    QDialogButtonBox,
    QMessageBox,
    QCheckBox,
)
from PyQt5.QtCore import Qt, QDate

from database.db import Database
from database.queries import Queries
import psycopg2
from datetime import datetime


class DocumentDialog(QDialog):
    def __init__(self, parent=None, document_id=None, client_id=None):
        super().__init__(parent)
        self.document_id = document_id
        self.client_id = client_id
        self.db = Database()

        self.setWindowTitle(
            "Редактировать документ" if document_id else "Добавить документ"
        )
        self.setModal(True)
        self.setMinimumWidth(400)
        self.init_ui()

        if document_id:
            self.load_data()

    def init_ui(self):
        layout = QFormLayout(self)

        self.passport_input = QLineEdit()
        self.passport_input.setPlaceholderText("XXXX XXXXXX")
        self.passport_input.setInputMask("9999 999999")

        self.birth_date_edit = QDateEdit()
        self.birth_date_edit.setCalendarPopup(True)
        self.birth_date_edit.setDisplayFormat("dd.MM.yyyy")
        self.birth_date_edit.setDate(QDate.currentDate())
        self.birth_date_edit.setMaximumDate(QDate.currentDate())

        self.gender_combo = QComboBox()
        self.gender_combo.addItems(["Male", "Female"])

        self.agreement_date_edit = QDateEdit()
        self.agreement_date_edit.setCalendarPopup(True)
        self.agreement_date_edit.setDisplayFormat("dd.MM.yyyy")
        self.agreement_date_edit.setDate(QDate.currentDate())
        self.agreement_date_edit.setMaximumDate(QDate.currentDate())

        self.security_word_input = QLineEdit()
        self.security_word_input.setPlaceholderText("Введите кодовое слово")

        self.status_check = QCheckBox("Активен")
        self.status_check.setChecked(True)

        layout.addRow("Номер паспорта*:", self.passport_input)
        layout.addRow("Дата рождения*:", self.birth_date_edit)
        layout.addRow("Пол*:", self.gender_combo)
        layout.addRow("Дата договора*:", self.agreement_date_edit)
        layout.addRow("Кодовое слово*:", self.security_word_input)
        layout.addRow("Статус:", self.status_check)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept_data)
        buttons.rejected.connect(self.reject)

        layout.addRow(buttons)

    def load_data(self):
        try:
            with self.db.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(Queries.GET_DOCUMENT_BY_ID, (self.document_id,))
                    document = cursor.fetchone()
                    
                    if not document:
                        QMessageBox.critical(self, "Ошибка", "Документ не найден")
                        self.reject()
                        return

                    self.passport_input.setText(document[1])
                    self.birth_date_edit.setDate(QDate(document[2]))
                    self.gender_combo.setCurrentText(document[3])
                    self.agreement_date_edit.setDate(QDate(document[5]))
                    self.security_word_input.setText(document[6])
                    self.status_check.setChecked(document[7] == 'active')

        except psycopg2.Error as e:
            QMessageBox.critical(
                self, "Ошибка БД", f"Не удалось загрузить данные документа:\n{str(e)}"
            )
            self.reject()

    def get_data(self):
        return (
            self.passport_input.text().strip(),
            self.birth_date_edit.date().toPyDate(),
            self.gender_combo.currentText(),
            self.client_id,
            self.agreement_date_edit.date().toPyDate(),
            self.security_word_input.text().strip(),
            'active' if self.status_check.isChecked() else 'inactive'
        )

    def accept_data(self):
        passport, birth_date, gender, client_id, agreement_date, security_word, status = self.get_data()

        # Validation
        errors = []
        if not passport or len(passport.replace(" ", "")) != 10:
            errors.append("Введите корректный номер паспорта")
        if not security_word:
            errors.append("Введите кодовое слово")
        if not client_id:
            errors.append("Не указан клиент")
        if birth_date >= datetime.now().date():
            errors.append("Дата рождения не может быть в будущем")
        if agreement_date > datetime.now().date():
            errors.append("Дата договора не может быть в будущем")

        if errors:
            QMessageBox.warning(self, "Ошибка валидации", "\n".join(errors))
            return

        super().accept() 