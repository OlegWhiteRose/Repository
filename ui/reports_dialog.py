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
    QFormLayout,
    QTextEdit,
    QComboBox,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon

from database.db import Database
from database.queries import Queries
import psycopg2
from datetime import datetime


class ReportDialog(QDialog):
    def __init__(self, parent=None, report_id=None, transaction_id=None, employee_id=None):
        super().__init__(parent)
        self.report_id = report_id
        self.transaction_id = transaction_id
        self.employee_id = employee_id
        self.db = Database()

        self.setWindowTitle(
            "Редактировать отчет" if report_id else "Создать отчет"
        )
        self.setModal(True)
        self.setMinimumSize(500, 300)
        self.init_ui()

        if report_id:
            self.load_data()

    def init_ui(self):
        layout = QFormLayout(self)

        # Content
        self.content_input = QTextEdit()
        self.content_input.setPlaceholderText("Введите содержание отчета...")
        
        # Transaction
        self.transaction_combo = QComboBox()
        self.load_transactions()
        if self.transaction_id:
            self.transaction_combo.setEnabled(False)
        
        # Employee
        self.employee_combo = QComboBox()
        self.load_employees()
        if self.employee_id:
            self.employee_combo.setEnabled(False)

        layout.addRow("Транзакция*:", self.transaction_combo)
        layout.addRow("Сотрудник*:", self.employee_combo)
        layout.addRow("Содержание*:", self.content_input)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept_data)
        buttons.rejected.connect(self.reject)

        layout.addRow(buttons)

    def load_transactions(self):
        try:
            with self.db.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(Queries.GET_ALL_TRANSACTIONS)
                    transactions = cursor.fetchall()
                    
                    self.transaction_combo.clear()
                    for trans in transactions:
                        # Format: ID - Date - Type - Amount
                        text = f"{trans[0]} - {trans[2].strftime('%d.%m.%Y %H:%M')} - {trans[3]} - {float(trans[1]):,.2f} ₽"
                        self.transaction_combo.addItem(text, trans[0])
                    
                    if self.transaction_id:
                        index = self.transaction_combo.findData(self.transaction_id)
                        if index >= 0:
                            self.transaction_combo.setCurrentIndex(index)

        except psycopg2.Error as e:
            QMessageBox.critical(
                self,
                "Ошибка БД",
                f"Не удалось загрузить список транзакций:\n{str(e)}"
            )

    def load_employees(self):
        try:
            with self.db.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(Queries.GET_ALL_EMPLOYEES)
                    employees = cursor.fetchall()
                    
                    self.employee_combo.clear()
                    for emp in employees:
                        # Format: ID - Last Name First Name
                        text = f"{emp[0]} - {emp[2]} {emp[1]}"
                        self.employee_combo.addItem(text, emp[0])
                    
                    if self.employee_id:
                        index = self.employee_combo.findData(self.employee_id)
                        if index >= 0:
                            self.employee_combo.setCurrentIndex(index)

        except psycopg2.Error as e:
            QMessageBox.critical(
                self,
                "Ошибка БД",
                f"Не удалось загрузить список сотрудников:\n{str(e)}"
            )

    def load_data(self):
        try:
            with self.db.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(Queries.GET_REPORT_BY_ID, (self.report_id,))
                    report = cursor.fetchone()
                    
                    if not report:
                        QMessageBox.critical(self, "Ошибка", "Отчет не найден")
                        self.reject()
                        return

                    self.content_input.setText(report[1])
                    
                    # Set transaction
                    index = self.transaction_combo.findData(report[3])
                    if index >= 0:
                        self.transaction_combo.setCurrentIndex(index)
                    
                    # Set employee
                    index = self.employee_combo.findData(report[4])
                    if index >= 0:
                        self.employee_combo.setCurrentIndex(index)

        except psycopg2.Error as e:
            QMessageBox.critical(
                self, "Ошибка БД", f"Не удалось загрузить данные отчета:\n{str(e)}"
            )
            self.reject()

    def get_data(self):
        return (
            self.content_input.toPlainText().strip(),
            datetime.now(),
            self.transaction_combo.currentData(),
            self.employee_combo.currentData()
        )

    def accept_data(self):
        content, creation_date, transaction_id, employee_id = self.get_data()

        # Validation
        errors = []
        if not content:
            errors.append("Введите содержание отчета")
        if not transaction_id:
            errors.append("Выберите транзакцию")
        if not employee_id:
            errors.append("Выберите сотрудника")

        if errors:
            QMessageBox.warning(self, "Ошибка валидации", "\n".join(errors))
            return

        super().accept()


class ReportsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = Database()

        self.setWindowTitle("Управление отчетами")
        self.setModal(True)
        self.setMinimumSize(1000, 500)
        self.init_ui()
        self.load_data()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Header
        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel("Список отчетов"))
        header_layout.addStretch()

        # Toolbar
        toolbar = QHBoxLayout()
        self.add_btn = QPushButton(QIcon.fromTheme("list-add"), " Создать")
        self.add_btn.clicked.connect(self.add_report)
        
        self.edit_btn = QPushButton(QIcon.fromTheme("document-edit"), " Редактировать")
        self.edit_btn.clicked.connect(self.edit_report)
        self.edit_btn.setEnabled(False)
        
        self.delete_btn = QPushButton(QIcon.fromTheme("edit-delete"), " Удалить")
        self.delete_btn.clicked.connect(self.delete_report)
        self.delete_btn.setEnabled(False)

        toolbar.addWidget(self.add_btn)
        toolbar.addWidget(self.edit_btn)
        toolbar.addWidget(self.delete_btn)
        toolbar.addStretch()

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "ID", "Дата создания", "Сотрудник", "Транзакция", "Тип операции", "Содержание"
        ])
        
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.Stretch)
        
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        
        self.table.itemSelectionChanged.connect(self.on_selection_changed)
        self.table.doubleClicked.connect(self.edit_report_on_double_click)

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
                    cursor.execute(Queries.GET_ALL_REPORTS)
                    reports = cursor.fetchall()

                    self.table.setRowCount(len(reports))
                    for row, rep in enumerate(reports):
                        # ID
                        id_item = QTableWidgetItem(str(rep[0]))
                        id_item.setTextAlignment(Qt.AlignCenter)
                        self.table.setItem(row, 0, id_item)
                        
                        # Creation Date
                        date = rep[2].strftime("%d.%m.%Y %H:%M:%S")
                        date_item = QTableWidgetItem(date)
                        date_item.setTextAlignment(Qt.AlignCenter)
                        self.table.setItem(row, 1, date_item)
                        
                        # Employee
                        employee = f"{rep[7]} {rep[6]}"  # Last Name First Name
                        self.table.setItem(row, 2, QTableWidgetItem(employee))
                        
                        # Transaction ID
                        trans_item = QTableWidgetItem(str(rep[3]))
                        trans_item.setTextAlignment(Qt.AlignCenter)
                        self.table.setItem(row, 3, trans_item)
                        
                        # Transaction Type
                        type_map = {
                            "opening": "Открытие вклада",
                            "addition": "Пополнение",
                            "closing": "Закрытие",
                            "early closing": "Досрочное закрытие"
                        }
                        type_item = QTableWidgetItem(type_map.get(rep[8], rep[8]))
                        type_item.setTextAlignment(Qt.AlignCenter)
                        self.table.setItem(row, 4, type_item)
                        
                        # Content (truncated)
                        content = rep[1]
                        if len(content) > 100:
                            content = content[:97] + "..."
                        self.table.setItem(row, 5, QTableWidgetItem(content))

        except psycopg2.Error as e:
            QMessageBox.critical(
                self,
                "Ошибка БД",
                f"Не удалось загрузить список отчетов:\n{str(e)}"
            )
            self.table.setRowCount(0)

    def on_selection_changed(self):
        has_selection = bool(self.table.selectedItems())
        self.edit_btn.setEnabled(has_selection)
        self.delete_btn.setEnabled(has_selection)

    def get_selected_report_id(self):
        selected_rows = self.table.selectedItems()
        if selected_rows:
            return int(self.table.item(selected_rows[0].row(), 0).text())
        return None

    def add_report(self):
        dialog = ReportDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            try:
                with self.db.get_connection() as conn:
                    with conn.cursor() as cursor:
                        cursor.execute(
                            Queries.ADD_REPORT,
                            dialog.get_data()
                        )
                        conn.commit()
                        QMessageBox.information(self, "Успех", "Отчет успешно создан")
                        self.load_data()
            except psycopg2.Error as e:
                QMessageBox.critical(
                    self,
                    "Ошибка",
                    f"Не удалось создать отчет:\n{str(e)}"
                )

    def edit_report_on_double_click(self, index):
        if self.edit_btn.isEnabled():
            self.edit_report()

    def edit_report(self):
        report_id = self.get_selected_report_id()
        if not report_id:
            return

        dialog = ReportDialog(self, report_id=report_id)
        if dialog.exec_() == QDialog.Accepted:
            try:
                with self.db.get_connection() as conn:
                    with conn.cursor() as cursor:
                        data = dialog.get_data()
                        cursor.execute(
                            Queries.UPDATE_REPORT,
                            (*data, report_id)
                        )
                        conn.commit()
                        QMessageBox.information(self, "Успех", "Отчет успешно обновлен")
                        self.load_data()
            except psycopg2.Error as e:
                QMessageBox.critical(
                    self,
                    "Ошибка",
                    f"Не удалось обновить отчет:\n{str(e)}"
                )

    def delete_report(self):
        report_id = self.get_selected_report_id()
        if not report_id:
            return

        reply = QMessageBox.question(
            self,
            "Подтверждение удаления",
            "Вы уверены, что хотите удалить этот отчет?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            try:
                with self.db.get_connection() as conn:
                    with conn.cursor() as cursor:
                        cursor.execute(Queries.DELETE_REPORT, (report_id,))
                        conn.commit()
                        QMessageBox.information(self, "Успех", "Отчет успешно удален")
                        self.load_data()
            except psycopg2.Error as e:
                QMessageBox.critical(
                    self,
                    "Ошибка",
                    f"Не удалось удалить отчет:\n{str(e)}"
                ) 