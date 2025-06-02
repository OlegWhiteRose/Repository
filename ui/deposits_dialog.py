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
from .deposit_dialog import DepositDialog
from .transaction_dialog import TransactionDialog
import psycopg2
from datetime import datetime


class DepositsDialog(QDialog):
    def __init__(self, parent=None, client_id=None, client_name=None):
        super().__init__(parent)
        self.client_id = client_id
        self.client_name = client_name
        self.db = Database()

        self.setWindowTitle(f"Вклады клиента: {client_name}")
        self.setModal(True)
        self.setMinimumSize(1000, 500)
        self.init_ui()
        self.load_data()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Header
        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel(f"Вклады клиента: {self.client_name}"))
        header_layout.addStretch()

        # Toolbar
        toolbar = QHBoxLayout()
        self.add_btn = QPushButton(QIcon.fromTheme("list-add"), " Открыть вклад")
        self.add_btn.clicked.connect(self.add_deposit)
        
        self.edit_btn = QPushButton(QIcon.fromTheme("document-edit"), " Редактировать")
        self.edit_btn.clicked.connect(self.edit_deposit)
        self.edit_btn.setEnabled(False)
        
        self.close_btn = QPushButton(QIcon.fromTheme("window-close"), " Закрыть вклад")
        self.close_btn.clicked.connect(self.close_deposit)
        self.close_btn.setEnabled(False)
        
        self.early_close_btn = QPushButton(QIcon.fromTheme("process-stop"), " Досрочное закрытие")
        self.early_close_btn.clicked.connect(self.early_close_deposit)
        self.early_close_btn.setEnabled(False)
        
        self.add_money_btn = QPushButton(QIcon.fromTheme("go-up"), " Пополнить")
        self.add_money_btn.clicked.connect(self.add_money)
        self.add_money_btn.setEnabled(False)
        
        self.transactions_btn = QPushButton(QIcon.fromTheme("view-list-text"), " История операций")
        self.transactions_btn.clicked.connect(self.show_transactions)
        self.transactions_btn.setEnabled(False)

        toolbar.addWidget(self.add_btn)
        toolbar.addWidget(self.edit_btn)
        toolbar.addWidget(self.close_btn)
        toolbar.addWidget(self.early_close_btn)
        toolbar.addWidget(self.add_money_btn)
        toolbar.addWidget(self.transactions_btn)
        toolbar.addStretch()

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "ID", "Сумма", "Дата открытия", "Дата закрытия",
            "Ставка", "Статус", "Срок", "Тип"
        ])
        
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(7, QHeaderView.Stretch)
        
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        
        self.table.itemSelectionChanged.connect(self.on_selection_changed)
        self.table.doubleClicked.connect(self.edit_deposit_on_double_click)

        # Close button
        button_box = QHBoxLayout()
        close_btn = QPushButton("Закрыть")
        close_btn.clicked.connect(self.reject)
        button_box.addStretch()
        button_box.addWidget(close_btn)

        layout.addLayout(header_layout)
        layout.addLayout(toolbar)
        layout.addWidget(self.table)
        layout.addLayout(button_box)

    def load_data(self):
        try:
            with self.db.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(Queries.GET_CLIENT_DEPOSITS, (self.client_id,))
                    deposits = cursor.fetchall()

                    self.table.setRowCount(len(deposits))
                    for row, dep in enumerate(deposits):
                        # ID
                        id_item = QTableWidgetItem(str(dep[0]))
                        id_item.setTextAlignment(Qt.AlignCenter)
                        self.table.setItem(row, 0, id_item)
                        
                        # Amount
                        amount_item = QTableWidgetItem(f"{float(dep[1]):,.2f} ₽")
                        amount_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                        self.table.setItem(row, 1, amount_item)
                        
                        # Open Date
                        open_date = dep[3].strftime("%d.%m.%Y")
                        open_date_item = QTableWidgetItem(open_date)
                        open_date_item.setTextAlignment(Qt.AlignCenter)
                        self.table.setItem(row, 2, open_date_item)
                        
                        # Close Date
                        close_date = dep[2].strftime("%d.%m.%Y") if dep[2] else "-"
                        close_date_item = QTableWidgetItem(close_date)
                        close_date_item.setTextAlignment(Qt.AlignCenter)
                        self.table.setItem(row, 3, close_date_item)
                        
                        # Interest Rate
                        rate_item = QTableWidgetItem(f"{float(dep[4]):.2f}%")
                        rate_item.setTextAlignment(Qt.AlignCenter)
                        self.table.setItem(row, 4, rate_item)
                        
                        # Status
                        status_map = {
                            "open": "Открыт",
                            "closed": "Закрыт",
                            "closed early": "Закрыт досрочно"
                        }
                        status_item = QTableWidgetItem(status_map.get(dep[5], dep[5]))
                        status_item.setTextAlignment(Qt.AlignCenter)
                        self.table.setItem(row, 5, status_item)
                        
                        # Term
                        term_item = QTableWidgetItem(str(dep[6]))
                        term_item.setTextAlignment(Qt.AlignCenter)
                        self.table.setItem(row, 6, term_item)
                        
                        # Type
                        self.table.setItem(row, 7, QTableWidgetItem(dep[7]))

        except psycopg2.Error as e:
            QMessageBox.critical(
                self,
                "Ошибка БД",
                f"Не удалось загрузить вклады:\n{str(e)}"
            )
            self.table.setRowCount(0)

    def on_selection_changed(self):
        has_selection = bool(self.table.selectedItems())
        if has_selection:
            row = self.table.selectedItems()[0].row()
            status = self.table.item(row, 5).text()
            is_open = status == "Открыт"
            
            self.edit_btn.setEnabled(is_open)
            self.close_btn.setEnabled(is_open)
            self.early_close_btn.setEnabled(is_open)
            self.add_money_btn.setEnabled(is_open)
            self.transactions_btn.setEnabled(True)
        else:
            self.edit_btn.setEnabled(False)
            self.close_btn.setEnabled(False)
            self.early_close_btn.setEnabled(False)
            self.add_money_btn.setEnabled(False)
            self.transactions_btn.setEnabled(False)

    def get_selected_deposit_id(self):
        selected_rows = self.table.selectedItems()
        if selected_rows:
            return int(self.table.item(selected_rows[0].row(), 0).text())
        return None

    def add_deposit(self):
        dialog = DepositDialog(self, client_id=self.client_id)
        if dialog.exec_() == QDialog.Accepted:
            try:
                with self.db.get_connection() as conn:
                    with conn.cursor() as cursor:
                        # Start transaction
                        cursor.execute("BEGIN")
                        try:
                            # Add deposit
                            cursor.execute(
                                Queries.ADD_DEPOSIT,
                                dialog.get_data()
                            )
                            deposit_id = cursor.fetchone()[0]

                            # Add opening transaction
                            cursor.execute(
                                Queries.ADD_TRANSACTION,
                                (deposit_id, dialog.amount_input.value(), datetime.now(), "opening")
                            )
                            
                            conn.commit()
                            QMessageBox.information(self, "Успех", "Вклад успешно открыт")
                            self.load_data()
                        except Exception as e:
                            conn.rollback()
                            raise e
            except psycopg2.Error as e:
                QMessageBox.critical(
                    self,
                    "Ошибка",
                    f"Не удалось открыть вклад:\n{str(e)}"
                )

    def edit_deposit_on_double_click(self, index):
        if self.edit_btn.isEnabled():
            self.edit_deposit()

    def edit_deposit(self):
        deposit_id = self.get_selected_deposit_id()
        if not deposit_id:
            return

        dialog = DepositDialog(self, deposit_id=deposit_id, client_id=self.client_id)
        if dialog.exec_() == QDialog.Accepted:
            try:
                with self.db.get_connection() as conn:
                    with conn.cursor() as cursor:
                        data = dialog.get_data()
                        cursor.execute(
                            Queries.UPDATE_DEPOSIT,
                            (*data[:-1], deposit_id)  # Exclude client_id from update
                        )
                        conn.commit()
                        QMessageBox.information(self, "Успех", "Вклад успешно обновлен")
                        self.load_data()
            except psycopg2.Error as e:
                QMessageBox.critical(
                    self,
                    "Ошибка",
                    f"Не удалось обновить вклад:\n{str(e)}"
                )

    def close_deposit(self):
        self._close_deposit("closed")

    def early_close_deposit(self):
        self._close_deposit("closed early")

    def _close_deposit(self, status):
        deposit_id = self.get_selected_deposit_id()
        if not deposit_id:
            return

        reply = QMessageBox.question(
            self,
            "Подтверждение закрытия",
            f"Вы уверены, что хотите {'досрочно ' if status == 'closed early' else ''}закрыть этот вклад?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            try:
                with self.db.get_connection() as conn:
                    with conn.cursor() as cursor:
                        # Get current amount
                        cursor.execute(Queries.GET_DEPOSIT_BY_ID, (deposit_id,))
                        deposit = cursor.fetchone()
                        if not deposit:
                            raise Exception("Вклад не найден")
                        
                        amount = float(deposit[1])
                        
                        # Start transaction
                        cursor.execute("BEGIN")
                        try:
                            # Update deposit status
                            cursor.execute(
                                Queries.CLOSE_DEPOSIT,
                                (status, datetime.now(), deposit_id)
                            )

                            # Add closing transaction
                            cursor.execute(
                                Queries.ADD_TRANSACTION,
                                (deposit_id, amount, datetime.now(), "early closing" if status == "closed early" else "closing")
                            )
                            
                            conn.commit()
                            QMessageBox.information(self, "Успех", "Вклад успешно закрыт")
                            self.load_data()
                        except Exception as e:
                            conn.rollback()
                            raise e
            except psycopg2.Error as e:
                QMessageBox.critical(
                    self,
                    "Ошибка",
                    f"Не удалось закрыть вклад:\n{str(e)}"
                )

    def add_money(self):
        deposit_id = self.get_selected_deposit_id()
        if not deposit_id:
            return

        dialog = TransactionDialog(self, deposit_id=deposit_id)
        if dialog.exec_() == QDialog.Accepted:
            try:
                with self.db.get_connection() as conn:
                    with conn.cursor() as cursor:
                        # Start transaction
                        cursor.execute("BEGIN")
                        try:
                            amount = dialog.get_amount()
                            
                            # Update deposit amount
                            cursor.execute(
                                Queries.UPDATE_DEPOSIT_AMOUNT,
                                (amount, deposit_id)
                            )

                            # Add transaction
                            cursor.execute(
                                Queries.ADD_TRANSACTION,
                                (deposit_id, amount, datetime.now(), "addition")
                            )
                            
                            conn.commit()
                            QMessageBox.information(self, "Успех", "Вклад успешно пополнен")
                            self.load_data()
                        except Exception as e:
                            conn.rollback()
                            raise e
            except psycopg2.Error as e:
                QMessageBox.critical(
                    self,
                    "Ошибка",
                    f"Не удалось пополнить вклад:\n{str(e)}"
                )

    def show_transactions(self):
        deposit_id = self.get_selected_deposit_id()
        if not deposit_id:
            return
        # TODO: Implement transactions dialog
        QMessageBox.information(self, "Информация", "История операций по вкладу") 