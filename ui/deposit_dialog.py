from PyQt5.QtWidgets import (
    QDialog,
    QFormLayout,
    QLineEdit,
    QComboBox,
    QDateEdit,
    QDialogButtonBox,
    QMessageBox,
    QDoubleSpinBox,
    QSpinBox,
)
from PyQt5.QtCore import Qt, QDate

from database.db import Database
from database.queries import Queries
import psycopg2
from datetime import datetime, timedelta


class DepositDialog(QDialog):
    DEPOSIT_TYPES = [
        "Savings",
        "Student",
        "Student+",
        "Premier",
        "Future Care",
        "Social",
        "Social+"
    ]

    def __init__(self, parent=None, deposit_id=None, client_id=None):
        super().__init__(parent)
        self.deposit_id = deposit_id
        self.client_id = client_id
        self.db = Database()

        self.setWindowTitle(
            "Редактировать вклад" if deposit_id else "Открыть новый вклад"
        )
        self.setModal(True)
        self.setMinimumWidth(400)
        self.init_ui()

        if deposit_id:
            self.load_data()

    def init_ui(self):
        layout = QFormLayout(self)

        # Amount
        self.amount_input = QDoubleSpinBox()
        self.amount_input.setRange(0, 999999999.99)
        self.amount_input.setDecimals(2)
        self.amount_input.setSingleStep(1000)
        self.amount_input.setSuffix(" ₽")

        # Interest Rate
        self.rate_input = QDoubleSpinBox()
        self.rate_input.setRange(0, 100)
        self.rate_input.setDecimals(2)
        self.rate_input.setSingleStep(0.1)
        self.rate_input.setSuffix(" %")

        # Term
        self.term_input = QSpinBox()
        self.term_input.setRange(1, 60)  # 1-60 months
        self.term_input.setSuffix(" мес.")
        self.term_input.setValue(12)  # Default 1 year

        # Type
        self.type_combo = QComboBox()
        self.type_combo.addItems(self.DEPOSIT_TYPES)

        # Open Date
        self.open_date_edit = QDateEdit()
        self.open_date_edit.setCalendarPopup(True)
        self.open_date_edit.setDisplayFormat("dd.MM.yyyy")
        self.open_date_edit.setDate(QDate.currentDate())
        self.open_date_edit.setMaximumDate(QDate.currentDate())

        # Close Date (calculated)
        self.close_date_edit = QDateEdit()
        self.close_date_edit.setCalendarPopup(True)
        self.close_date_edit.setDisplayFormat("dd.MM.yyyy")
        self.close_date_edit.setEnabled(False)

        # Status
        self.status_combo = QComboBox()
        self.status_combo.addItems(["open", "closed", "closed early"])
        self.status_combo.setEnabled(False)  # Only enabled when editing

        # Connect signals
        self.open_date_edit.dateChanged.connect(self.update_close_date)
        self.term_input.valueChanged.connect(self.update_close_date)

        layout.addRow("Сумма вклада*:", self.amount_input)
        layout.addRow("Процентная ставка*:", self.rate_input)
        layout.addRow("Срок вклада*:", self.term_input)
        layout.addRow("Тип вклада*:", self.type_combo)
        layout.addRow("Дата открытия*:", self.open_date_edit)
        layout.addRow("Дата закрытия:", self.close_date_edit)
        layout.addRow("Статус:", self.status_combo)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept_data)
        buttons.rejected.connect(self.reject)

        layout.addRow(buttons)

        # Initialize close date
        self.update_close_date()

    def update_close_date(self):
        open_date = self.open_date_edit.date().toPyDate()
        term_months = self.term_input.value()
        close_date = open_date + timedelta(days=30.44 * term_months)  # Approximate
        self.close_date_edit.setDate(QDate(close_date))

    def load_data(self):
        try:
            with self.db.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(Queries.GET_DEPOSIT_BY_ID, (self.deposit_id,))
                    deposit = cursor.fetchone()
                    
                    if not deposit:
                        QMessageBox.critical(self, "Ошибка", "Вклад не найден")
                        self.reject()
                        return

                    self.amount_input.setValue(float(deposit[1]))
                    self.open_date_edit.setDate(QDate(deposit[3]))
                    if deposit[2]:  # close_date can be NULL
                        self.close_date_edit.setDate(QDate(deposit[2]))
                    self.rate_input.setValue(float(deposit[4]))
                    self.status_combo.setCurrentText(deposit[5])
                    
                    # Calculate term from dates
                    open_date = deposit[3]
                    close_date = deposit[2] or (open_date + timedelta(days=365))
                    term_days = (close_date - open_date).days
                    term_months = int(round(term_days / 30.44))
                    self.term_input.setValue(term_months)
                    
                    self.type_combo.setCurrentText(deposit[7])

                    # Enable status combo for editing
                    self.status_combo.setEnabled(True)

        except psycopg2.Error as e:
            QMessageBox.critical(
                self, "Ошибка БД", f"Не удалось загрузить данные вклада:\n{str(e)}"
            )
            self.reject()

    def get_data(self):
        return (
            float(self.amount_input.value()),
            self.close_date_edit.date().toPyDate(),
            self.open_date_edit.date().toPyDate(),
            float(self.rate_input.value()),
            self.status_combo.currentText(),
            f"{self.term_input.value()} months",  # Convert to interval string
            self.type_combo.currentText(),
            self.client_id
        )

    def accept_data(self):
        amount, close_date, open_date, rate, status, term, type_, client_id = self.get_data()

        # Validation
        errors = []
        if amount <= 0:
            errors.append("Сумма вклада должна быть больше 0")
        if rate < 0:
            errors.append("Процентная ставка не может быть отрицательной")
        if open_date > datetime.now().date():
            errors.append("Дата открытия не может быть в будущем")
        if close_date <= open_date:
            errors.append("Дата закрытия должна быть позже даты открытия")
        if not client_id:
            errors.append("Не указан клиент")

        if errors:
            QMessageBox.warning(self, "Ошибка валидации", "\n".join(errors))
            return

        super().accept() 