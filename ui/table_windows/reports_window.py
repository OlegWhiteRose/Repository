from PyQt5.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QPushButton,
    QMessageBox,
    QTableWidgetItem,
    QDateEdit,
    QComboBox,
    QLabel,
    QGroupBox,
    QCheckBox,
    QSpinBox,
    QLineEdit
)
from PyQt5.QtCore import Qt, QDate
from datetime import datetime, timedelta

from .base_table_window import BaseTableWindow
from database.db import Database
from database.queries import Queries

class ReportFilterDialog(QDialog):
    """Диалог для настройки фильтров отчета"""
    def __init__(self, parent=None, report_type=None):
        super().__init__(parent)
        self.report_type = report_type
        self.setWindowTitle(f"Настройка фильтров - {report_type}")
        self.setModal(True)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Период отчета
        date_group = QGroupBox("Период отчета")
        date_layout = QFormLayout()
        
        self.start_date_edit = QDateEdit()
        self.start_date_edit.setCalendarPopup(True)
        self.start_date_edit.setDate(QDate.currentDate().addMonths(-1))
        
        self.end_date_edit = QDateEdit()
        self.end_date_edit.setCalendarPopup(True)
        self.end_date_edit.setDate(QDate.currentDate())
        
        date_layout.addRow("С:", self.start_date_edit)
        date_layout.addRow("По:", self.end_date_edit)
        date_group.setLayout(date_layout)
        
        # Фильтры в зависимости от типа отчета
        filters_group = QGroupBox("Фильтры")
        filters_layout = QFormLayout()
        
        if self.report_type == "Deposits Summary":
            self.min_amount_spin = QSpinBox()
            self.min_amount_spin.setRange(0, 999999999)
            self.min_amount_spin.setSuffix(" руб.")
            
            self.deposit_type_combo = QComboBox()
            self.deposit_type_combo.addItems([
                "All",
                "Savings",
                "Student",
                "Student+",
                "Premier",
                "Future Care",
                "Social",
                "Social+"
            ])
            
            self.status_combo = QComboBox()
            self.status_combo.addItems(["All", "open", "closed", "closed early"])
            
            filters_layout.addRow("Мин. сумма:", self.min_amount_spin)
            filters_layout.addRow("Тип вклада:", self.deposit_type_combo)
            filters_layout.addRow("Статус:", self.status_combo)
            
        elif self.report_type == "Transactions History":
            self.transaction_type_combo = QComboBox()
            self.transaction_type_combo.addItems([
                "All",
                "deposit",
                "withdrawal",
                "interest",
                "opening",
                "closing",
                "early closing"
            ])
            
            self.min_amount_spin = QSpinBox()
            self.min_amount_spin.setRange(-999999999, 999999999)
            self.min_amount_spin.setSuffix(" руб.")
            
            filters_layout.addRow("Тип операции:", self.transaction_type_combo)
            filters_layout.addRow("Мин. сумма:", self.min_amount_spin)
            
        elif self.report_type == "Employee Performance":
            self.position_combo = QComboBox()
            self.position_combo.addItems([
                "All",
                "Менеджер",
                "Старший менеджер",
                "Консультант",
                "Кассир",
                "Руководитель отдела",
                "Администратор"
            ])
            
            self.min_clients_spin = QSpinBox()
            self.min_clients_spin.setRange(0, 999)
            
            filters_layout.addRow("Должность:", self.position_combo)
            filters_layout.addRow("Мин. клиентов:", self.min_clients_spin)
            
        filters_group.setLayout(filters_layout)
        
        # Группировка
        grouping_group = QGroupBox("Группировка")
        grouping_layout = QVBoxLayout()
        
        self.group_by_date = QCheckBox("По дате")
        self.group_by_type = QCheckBox("По типу")
        if self.report_type == "Employee Performance":
            self.group_by_position = QCheckBox("По должности")
            grouping_layout.addWidget(self.group_by_position)
            
        grouping_layout.addWidget(self.group_by_date)
        grouping_layout.addWidget(self.group_by_type)
        grouping_group.setLayout(grouping_layout)
        
        # Кнопки
        buttons_layout = QHBoxLayout()
        generate_button = QPushButton("Сформировать")
        cancel_button = QPushButton("Отмена")
        
        generate_button.clicked.connect(self.accept)
        cancel_button.clicked.connect(self.reject)
        
        buttons_layout.addWidget(generate_button)
        buttons_layout.addWidget(cancel_button)
        
        # Собираем layout
        layout.addWidget(date_group)
        layout.addWidget(filters_group)
        layout.addWidget(grouping_group)
        layout.addLayout(buttons_layout)
        
    def get_data(self):
        """Возвращает настройки фильтров"""
        data = {
            "start_date": self.start_date_edit.date().toString(Qt.ISODate),
            "end_date": self.end_date_edit.date().toString(Qt.ISODate),
            "group_by_date": self.group_by_date.isChecked(),
            "group_by_type": self.group_by_type.isChecked()
        }
        
        if self.report_type == "Deposits Summary":
            data.update({
                "min_amount": self.min_amount_spin.value(),
                "deposit_type": self.deposit_type_combo.currentText(),
                "status": self.status_combo.currentText()
            })
        elif self.report_type == "Transactions History":
            data.update({
                "transaction_type": self.transaction_type_combo.currentText(),
                "min_amount": self.min_amount_spin.value()
            })
        elif self.report_type == "Employee Performance":
            data.update({
                "position": self.position_combo.currentText(),
                "min_clients": self.min_clients_spin.value(),
                "group_by_position": self.group_by_position.isChecked()
            })
            
        return data

class ReportDialog(QDialog):
    """Диалог для добавления/редактирования отчета"""
    def __init__(self, parent=None, report_data=None):
        super().__init__(parent)
        self.db = Database()
        self.report_data = report_data
        self.setWindowTitle("Добавить отчет" if not report_data else "Редактировать отчет")
        self.setModal(True)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()
        
        # Создаем поля ввода
        self.employee_combo = QComboBox()
        self.load_employees()
        
        self.transaction_combo = QComboBox()
        self.load_transactions()
        
        self.content_edit = QLineEdit()
        
        # Добавляем поля в форму
        form_layout.addRow("Сотрудник*:", self.employee_combo)
        form_layout.addRow("Транзакция*:", self.transaction_combo)
        form_layout.addRow("Содержание*:", self.content_edit)
        
        # Если редактируем существующий отчет
        if self.report_data:
            self.employee_combo.setCurrentText(self.report_data["employee_name"])
            self.transaction_combo.setCurrentText(self.report_data["transaction_info"])
            self.content_edit.setText(self.report_data["content"])
            
        # Кнопки
        buttons_layout = QVBoxLayout()
        save_button = QPushButton("Сохранить")
        cancel_button = QPushButton("Отмена")
        
        save_button.clicked.connect(self.accept)
        cancel_button.clicked.connect(self.reject)
        
        buttons_layout.addWidget(save_button)
        buttons_layout.addWidget(cancel_button)
        
        # Собираем layout
        layout.addLayout(form_layout)
        layout.addLayout(buttons_layout)
        
    def load_employees(self):
        """Загружает список сотрудников"""
        try:
            query = """
                SELECT id, first_name || ' ' || last_name as full_name
                FROM Employee
                WHERE status = 'active'
                ORDER BY last_name, first_name
            """
            results = self.db.execute_query(query, fetch_all=True)
            
            self.employee_combo.clear()
            self.employees_data = {f"{row[1]} (ID: {row[0]})": row[0] for row in results}
            self.employee_combo.addItems(self.employees_data.keys())
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить список сотрудников: {str(e)}")
            
    def load_transactions(self):
        """Загружает список транзакций"""
        try:
            query = """
                SELECT t.id, 
                       c.last_name || ' ' || c.first_name as client_name,
                       t.type,
                       t.amount,
                       t.date
                FROM Transaction t
                JOIN Deposit d ON t.deposit_id = d.id
                JOIN Client c ON d.client_id = c.id
                WHERE t.id NOT IN (SELECT transaction_id FROM Report)
                ORDER BY t.date DESC
            """
            results = self.db.execute_query(query, fetch_all=True)
            
            self.transaction_combo.clear()
            self.transactions_data = {}
            
            for row in results:
                transaction_id = row[0]
                display_text = f"{row[1]} - {row[2]} ({row[3]} руб.) от {row[4].strftime('%Y-%m-%d')}"
                self.transactions_data[display_text] = transaction_id
                self.transaction_combo.addItem(display_text)
                
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить список транзакций: {str(e)}")
            
    def get_data(self):
        """Возвращает введенные данные"""
        employee_key = self.employee_combo.currentText()
        transaction_key = self.transaction_combo.currentText()
        
        return {
            "employee_id": self.employees_data[employee_key],
            "transaction_id": self.transactions_data[transaction_key],
            "content": self.content_edit.text(),
            "creation_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

class ReportsWindow(BaseTableWindow):
    def __init__(self, parent=None, employee_id=None, employee_name=None, user_role="user"):
        title = f"Отчеты - {employee_name}" if employee_name else "Отчеты"
        super().__init__(parent, title=title, user_role=user_role)
        self.db = Database()
        self.employee_id = employee_id
        self.employee_name = employee_name
        self.setup_search_panel()
        self.setup_table()
        self.setup_navigation()
        self.refresh_table()
        
    def setup_search_panel(self):
        """Настраивает панель поиска"""
        search_group = QGroupBox("Поиск")
        search_layout = QFormLayout()
        
        self.search_employee = QLineEdit()
        self.search_employee.setPlaceholderText("Введите фамилию сотрудника...")
        self.search_employee.textChanged.connect(self.refresh_table)
        
        self.search_client = QLineEdit()
        self.search_client.setPlaceholderText("Введите фамилию клиента...")
        self.search_client.textChanged.connect(self.refresh_table)
        
        search_layout.addRow("Фамилия сотрудника:", self.search_employee)
        search_layout.addRow("Фамилия клиента:", self.search_client)
        
        search_group.setLayout(search_layout)
        self.main_layout.insertWidget(0, search_group)
        
    def setup_table(self):
        """Настраивает структуру таблицы"""
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "ID", "Дата", "Сотрудник", "Клиент", "Тип операции", 
            "Сумма", "Содержание"
        ])
        
    def setup_navigation(self):
        """Настраивает кнопки навигации"""
        self.add_navigation_button("Сотрудник", self.show_employee)
        self.add_navigation_button("Клиент", self.show_client)
        
    def show_employee(self):
        """Открывает окно сотрудника для выбранного отчета"""
        current_row = self.table.currentRow()
        if current_row >= 0:
            try:
                query = """
                    SELECT e.id, e.first_name, e.last_name
                    FROM Report r
                    JOIN Employee e ON r.employee_id = e.id
                    WHERE r.id = %s
                """
                employee = self.db.execute_query(
                    query,
                    params=(self.table.item(current_row, 0).text(),),
                    fetch_one=True
                )
                
                if employee:
                    from .employees_window import EmployeesWindow
                    employees_window = EmployeesWindow(self)
                    employees_window.show()
                    # Найти и выделить нужного сотрудника в таблице
                    for row in range(employees_window.table.rowCount()):
                        if employees_window.table.item(row, 0).text() == str(employee[0]):
                            employees_window.table.selectRow(row)
                            break
                            
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось открыть окно сотрудника: {str(e)}")
                
    def show_client(self):
        """Открывает окно клиента для выбранного отчета"""
        current_row = self.table.currentRow()
        if current_row >= 0:
            try:
                query = """
                    SELECT c.id, c.first_name, c.last_name
                    FROM Report r
                    JOIN Transaction t ON r.transaction_id = t.id
                    JOIN Deposit d ON t.deposit_id = d.id
                    JOIN Client c ON d.client_id = c.id
                    WHERE r.id = %s
                """
                client = self.db.execute_query(
                    query,
                    params=(self.table.item(current_row, 0).text(),),
                    fetch_one=True
                )
                
                if client:
                    from .clients_window import ClientsWindow
                    clients_window = ClientsWindow(self)
                    clients_window.show()
                    # Найти и выделить нужного клиента в таблице
                    for row in range(clients_window.table.rowCount()):
                        if clients_window.table.item(row, 0).text() == str(client[0]):
                            clients_window.table.selectRow(row)
                            break
                            
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось открыть окно клиента: {str(e)}")
                
    def refresh_table(self):
        """Обновляет данные в таблице"""
        try:
            query = """
                SELECT r.id, r.creation_date, 
                       e.last_name || ' ' || e.first_name as employee_name,
                       c.last_name || ' ' || c.first_name as client_name,
                       t.type as transaction_type, t.amount,
                       r.content
                FROM Report r
                JOIN Employee e ON r.employee_id = e.id
                JOIN Transaction t ON r.transaction_id = t.id
                JOIN Deposit d ON t.deposit_id = d.id
                JOIN Client c ON d.client_id = c.id
                WHERE (LOWER(e.last_name) LIKE LOWER(%s) OR %s = '')
                  AND (LOWER(c.last_name) LIKE LOWER(%s) OR %s = '')
                ORDER BY r.creation_date DESC
            """
            
            params = [
                f"%{self.search_employee.text()}%" if self.search_employee.text() else "",
                self.search_employee.text(),
                f"%{self.search_client.text()}%" if self.search_client.text() else "",
                self.search_client.text()
            ]
            
            results = self.db.execute_query(query, params=params, fetch_all=True)
            
            self.table.setRowCount(0)
            for row_num, row_data in enumerate(results):
                self.table.insertRow(row_num)
                for col_num, cell_data in enumerate(row_data):
                    if isinstance(cell_data, datetime):
                        cell_data = cell_data.strftime("%Y-%m-%d %H:%M:%S")
                    elif isinstance(cell_data, (int, float)) and col_num == 5:  # Amount column
                        cell_data = f"{cell_data:.2f}"
                    item = QTableWidgetItem(str(cell_data))
                    if col_num == 0:  # ID column
                        item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                    self.table.setItem(row_num, col_num, item)
                    
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить данные: {str(e)}")
            
    def add_record(self):
        """Добавление нового отчета"""
        dialog = ReportDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            data = dialog.get_data()
            try:
                query = """
                    INSERT INTO Report (
                        employee_id, transaction_id,
                        content, creation_date
                    )
                    VALUES (%s, %s, %s, %s)
                    RETURNING id
                """
                self.db.execute_query(
                    query,
                    params=(
                        data["employee_id"],
                        data["transaction_id"],
                        data["content"],
                        data["creation_date"]
                    ),
                    commit=True
                )
                self.refresh_table()
                QMessageBox.information(self, "Успех", "Отчет успешно добавлен")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось добавить отчет: {str(e)}")
                
    def edit_record(self):
        """Редактирование выбранного отчета"""
        current_row = self.table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Предупреждение", "Выберите отчет для редактирования")
            return
            
        report_data = {
            "id": self.table.item(current_row, 0).text(),
            "employee_name": self.table.item(current_row, 2).text(),
            "transaction_info": f"{self.table.item(current_row, 5).text()} - {self.table.item(current_row, 3).text()} ({self.table.item(current_row, 4).text()} руб.)",
            "content": self.table.item(current_row, 6).text()
        }
        
        dialog = ReportDialog(self, report_data)
        if dialog.exec_() == QDialog.Accepted:
            data = dialog.get_data()
            try:
                query = """
                    UPDATE Report
                    SET employee_id = %s,
                        transaction_id = %s,
                        content = %s
                    WHERE id = %s
                """
                self.db.execute_query(
                    query,
                    params=(
                        data["employee_id"],
                        data["transaction_id"],
                        data["content"],
                        report_data["id"]
                    ),
                    commit=True
                )
                self.refresh_table()
                QMessageBox.information(self, "Успех", "Отчет успешно обновлен")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось обновить отчет: {str(e)}")
                
    def delete_record(self):
        """Удаление выбранного отчета"""
        current_row = self.table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Предупреждение", "Выберите отчет для удаления")
            return
            
        report_id = self.table.item(current_row, 0).text()
        
        reply = QMessageBox.question(
            self,
            "Подтверждение",
            "Вы уверены, что хотите удалить этот отчет?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                query = "DELETE FROM Report WHERE id = %s"
                self.db.execute_query(query, params=(report_id,), commit=True)
                self.refresh_table()
                QMessageBox.information(self, "Успех", "Отчет успешно удален")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось удалить отчет: {str(e)}")
                
    def show_related_records(self, row):
        """Показывает связанные записи для выбранного отчета"""
        if row < 0:
            return
            
        report_id = self.table.item(row, 0).text()
        
        try:
            # Получаем детали транзакции
            query = """
                SELECT t.id, t.date, t.type, t.amount,
                       d.type as deposit_type, d.interest_rate,
                       c.last_name || ' ' || c.first_name as client_name
                FROM Report r
                JOIN Transaction t ON r.transaction_id = t.id
                JOIN Deposit d ON t.deposit_id = d.id
                JOIN Client c ON d.client_id = c.id
                WHERE r.id = %s
            """
            transaction = self.db.execute_query(query, params=(report_id,), fetch_one=True)
            
            if not transaction:
                QMessageBox.information(
                    self,
                    "Информация",
                    "Не удалось найти связанную транзакцию"
                )
                return
                
            # Создаем информационное окно
            msg = QMessageBox(self)
            msg.setWindowTitle("Детали транзакции")
            msg.setIcon(QMessageBox.Information)
            
            details = f"""
                ID транзакции: {transaction[0]}
                Дата: {transaction[1].strftime('%Y-%m-%d %H:%M:%S')}
                Тип операции: {transaction[2]}
                Сумма: {transaction[3]:.2f} руб.
                Тип вклада: {transaction[4]}
                Процентная ставка: {transaction[5]}%
                Клиент: {transaction[6]}
            """
            
            msg.setText(details)
            msg.exec_()
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Ошибка",
                f"Не удалось загрузить связанные записи: {str(e)}"
            ) 