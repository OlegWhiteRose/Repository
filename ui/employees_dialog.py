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
    QLineEdit,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon

from database.db import Database
from database.queries import Queries
import psycopg2


class EmployeeDialog(QDialog):
    def __init__(self, parent=None, employee_id=None):
        super().__init__(parent)
        self.employee_id = employee_id
        self.db = Database()
        self.original_phone = None

        self.setWindowTitle(
            "Редактировать сотрудника" if employee_id else "Добавить сотрудника"
        )
        self.setModal(True)
        self.setMinimumWidth(400)
        self.init_ui()

        if employee_id:
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
                    cursor.execute(Queries.GET_EMPLOYEE_BY_ID, (self.employee_id,))
                    employee = cursor.fetchone()
                    
                    if not employee:
                        QMessageBox.critical(self, "Ошибка", "Сотрудник не найден")
                        self.reject()
                        return

                    self.first_name_input.setText(employee[1])
                    self.last_name_input.setText(employee[2])
                    self.phone_input.setText(employee[3])
                    self.original_phone = employee[3]

        except psycopg2.Error as e:
            QMessageBox.critical(
                self, "Ошибка БД", f"Не удалось загрузить данные сотрудника:\n{str(e)}"
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
                            Queries.CHECK_EMPLOYEE_PHONE_EXISTS,
                            (phone, self.employee_id, self.employee_id)
                        )
                        if cursor.fetchone():
                            QMessageBox.warning(
                                self,
                                "Ошибка",
                                f"Сотрудник с телефоном {phone} уже существует"
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


class EmployeesDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = Database()

        self.setWindowTitle("Управление сотрудниками")
        self.setModal(True)
        self.setMinimumSize(800, 400)
        self.init_ui()
        self.load_data()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Header
        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel("Список сотрудников"))
        header_layout.addStretch()

        # Toolbar
        toolbar = QHBoxLayout()
        self.add_btn = QPushButton(QIcon.fromTheme("list-add"), " Добавить")
        self.add_btn.clicked.connect(self.add_employee)
        
        self.edit_btn = QPushButton(QIcon.fromTheme("document-edit"), " Редактировать")
        self.edit_btn.clicked.connect(self.edit_employee)
        self.edit_btn.setEnabled(False)
        
        self.delete_btn = QPushButton(QIcon.fromTheme("edit-delete"), " Удалить")
        self.delete_btn.clicked.connect(self.delete_employee)
        self.delete_btn.setEnabled(False)

        toolbar.addWidget(self.add_btn)
        toolbar.addWidget(self.edit_btn)
        toolbar.addWidget(self.delete_btn)
        toolbar.addStretch()

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels([
            "ID", "Имя", "Фамилия", "Телефон"
        ])
        
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        
        self.table.itemSelectionChanged.connect(self.on_selection_changed)
        self.table.doubleClicked.connect(self.edit_employee_on_double_click)

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
                    cursor.execute(Queries.GET_ALL_EMPLOYEES)
                    employees = cursor.fetchall()

                    self.table.setRowCount(len(employees))
                    for row, emp in enumerate(employees):
                        # ID
                        id_item = QTableWidgetItem(str(emp[0]))
                        id_item.setTextAlignment(Qt.AlignCenter)
                        self.table.setItem(row, 0, id_item)
                        
                        # First Name
                        self.table.setItem(row, 1, QTableWidgetItem(emp[1]))
                        
                        # Last Name
                        self.table.setItem(row, 2, QTableWidgetItem(emp[2]))
                        
                        # Phone
                        phone_item = QTableWidgetItem(emp[3])
                        phone_item.setTextAlignment(Qt.AlignCenter)
                        self.table.setItem(row, 3, phone_item)

        except psycopg2.Error as e:
            QMessageBox.critical(
                self,
                "Ошибка БД",
                f"Не удалось загрузить список сотрудников:\n{str(e)}"
            )
            self.table.setRowCount(0)

    def on_selection_changed(self):
        has_selection = bool(self.table.selectedItems())
        self.edit_btn.setEnabled(has_selection)
        self.delete_btn.setEnabled(has_selection)

    def get_selected_employee_id(self):
        selected_rows = self.table.selectedItems()
        if selected_rows:
            return int(self.table.item(selected_rows[0].row(), 0).text())
        return None

    def add_employee(self):
        dialog = EmployeeDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            try:
                with self.db.get_connection() as conn:
                    with conn.cursor() as cursor:
                        cursor.execute(
                            Queries.ADD_EMPLOYEE,
                            dialog.get_data()
                        )
                        conn.commit()
                        QMessageBox.information(self, "Успех", "Сотрудник успешно добавлен")
                        self.load_data()
            except psycopg2.Error as e:
                QMessageBox.critical(
                    self,
                    "Ошибка",
                    f"Не удалось добавить сотрудника:\n{str(e)}"
                )

    def edit_employee_on_double_click(self, index):
        if self.edit_btn.isEnabled():
            self.edit_employee()

    def edit_employee(self):
        employee_id = self.get_selected_employee_id()
        if not employee_id:
            return

        dialog = EmployeeDialog(self, employee_id)
        if dialog.exec_() == QDialog.Accepted:
            try:
                with self.db.get_connection() as conn:
                    with conn.cursor() as cursor:
                        data = dialog.get_data()
                        cursor.execute(
                            Queries.UPDATE_EMPLOYEE,
                            (*data, employee_id)
                        )
                        conn.commit()
                        QMessageBox.information(self, "Успех", "Данные сотрудника обновлены")
                        self.load_data()
            except psycopg2.Error as e:
                QMessageBox.critical(
                    self,
                    "Ошибка",
                    f"Не удалось обновить данные сотрудника:\n{str(e)}"
                )

    def delete_employee(self):
        employee_id = self.get_selected_employee_id()
        if not employee_id:
            return

        reply = QMessageBox.question(
            self,
            "Подтверждение удаления",
            "Вы уверены, что хотите удалить этого сотрудника?\n"
            "Все связанные отчеты также будут удалены.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            try:
                with self.db.get_connection() as conn:
                    with conn.cursor() as cursor:
                        cursor.execute(Queries.DELETE_EMPLOYEE, (employee_id,))
                        conn.commit()
                        QMessageBox.information(self, "Успех", "Сотрудник успешно удален")
                        self.load_data()
            except psycopg2.Error as e:
                QMessageBox.critical(
                    self,
                    "Ошибка",
                    f"Не удалось удалить сотрудника:\n{str(e)}"
                ) 