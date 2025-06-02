from PyQt5.QtWidgets import (
    QDialog,
    QFormLayout,
    QDialogButtonBox,
    QMessageBox,
    QDoubleSpinBox,
)
from PyQt5.QtCore import Qt

from database.db import Database
from database.queries import Queries
import psycopg2


class TransactionDialog(QDialog):
    def __init__(self, parent=None, deposit_id=None):
        super().__init__(parent)
        self.deposit_id = deposit_id
        self.db = Database()

        self.setWindowTitle("Пополнение вклада")
        self.setModal(True)
        self.setMinimumWidth(300)
        self.init_ui()

    def init_ui(self):
        layout = QFormLayout(self)

        # Amount
        self.amount_input = QDoubleSpinBox()
        self.amount_input.setRange(0.01, 999999999.99)
        self.amount_input.setDecimals(2)
        self.amount_input.setSingleStep(1000)
        self.amount_input.setSuffix(" ₽")
        self.amount_input.setValue(1000.00)

        layout.addRow("Сумма пополнения*:", self.amount_input)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept_data)
        buttons.rejected.connect(self.reject)

        layout.addRow(buttons)

    def get_amount(self):
        return float(self.amount_input.value())

    def accept_data(self):
        amount = self.get_amount()

        # Validation
        if amount <= 0:
            QMessageBox.warning(
                self,
                "Ошибка валидации",
                "Сумма пополнения должна быть больше 0"
            )
            return

        super().accept() 