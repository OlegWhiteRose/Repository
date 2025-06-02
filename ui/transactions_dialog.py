from PyQt5.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QTableWidget,
    QAbstractItemView,
    QTableWidgetItem,
    QPushButton,
    QLabel,
    QHeaderView,
    QMessageBox,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon

from database.db import Database
from database.queries import Queries
import psycopg2


class TransactionsDialog(QDialog):
    def __init__(self, parent=None, deposit_id=None, deposit_info=None):
        super().__init__(parent)
        self.deposit_id = deposit_id
        self.deposit_info = deposit_info
        self.db = Database()

        self.setWindowTitle(f"История операций по вкладу")
        self.setModal(True)
        self.setMinimumSize(800, 400)
        self.init_ui()
        self.load_data()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Header with deposit info
        if self.deposit_info:
            header_layout = QHBoxLayout()
            header_layout.addWidget(QLabel(f"Вклад: {self.deposit_info}"))
            header_layout.addStretch()
            layout.addLayout(header_layout)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels([
            "ID", "Дата", "Тип операции", "Сумма"
        ])
        
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)

        # Close button
        button_box = QHBoxLayout()
        close_btn = QPushButton("Закрыть")
        close_btn.clicked.connect(self.reject)
        button_box.addStretch()
        button_box.addWidget(close_btn)

        layout.addWidget(self.table)
        layout.addLayout(button_box)

    def load_data(self):
        try:
            with self.db.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(Queries.GET_DEPOSIT_TRANSACTIONS, (self.deposit_id,))
                    transactions = cursor.fetchall()

                    self.table.setRowCount(len(transactions))
                    for row, trans in enumerate(transactions):
                        # ID
                        id_item = QTableWidgetItem(str(trans[0]))
                        id_item.setTextAlignment(Qt.AlignCenter)
                        self.table.setItem(row, 0, id_item)
                        
                        # Date
                        date = trans[2].strftime("%d.%m.%Y %H:%M:%S")
                        date_item = QTableWidgetItem(date)
                        date_item.setTextAlignment(Qt.AlignCenter)
                        self.table.setItem(row, 1, date_item)
                        
                        # Type
                        type_map = {
                            "opening": "Открытие вклада",
                            "addition": "Пополнение",
                            "closing": "Закрытие",
                            "early closing": "Досрочное закрытие"
                        }
                        type_item = QTableWidgetItem(type_map.get(trans[3], trans[3]))
                        type_item.setTextAlignment(Qt.AlignCenter)
                        self.table.setItem(row, 2, type_item)
                        
                        # Amount
                        amount_item = QTableWidgetItem(f"{float(trans[1]):,.2f} ₽")
                        amount_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                        self.table.setItem(row, 3, amount_item)

        except psycopg2.Error as e:
            QMessageBox.critical(
                self,
                "Ошибка БД",
                f"Не удалось загрузить историю операций:\n{str(e)}"
            )
            self.table.setRowCount(0) 