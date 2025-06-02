from PyQt5.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QFormLayout,
    QLineEdit,
    QPushButton,
    QMessageBox,
    QTableWidgetItem,
    QDateEdit,
    QComboBox,
    QLabel,
    QHBoxLayout,
    QGroupBox
)
from PyQt5.QtCore import Qt, QDate
from datetime import datetime

from .base_table_window import BaseTableWindow
from database.db import Database
from database.queries import Queries

class EmployeeDialog(QDialog):
    """Диалог для добавления/редактирования сотрудника"""
    def __init__(self, parent=None, employee_data=None):
        super().__init__(parent)
        self.employee_data = employee_data
        self.setWindowTitle("Добавить сотрудника" if not employee_data else "Редактировать сотрудника")
        self.setModal(True)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()
        
        # Создаем поля ввода
        self.first_name_edit = QLineEdit()
        self.last_name_edit = QLineEdit()
        self.position_combo = QComboBox()
        self.position_combo.addItems([
            "Менеджер",
            "Старший менеджер",
            "Консультант",
            "Кассир",
            "Руководитель отдела",
            "Администратор"
        ])
        
        self.hire_date_edit = QDateEdit()
        self.hire_date_edit.setCalendarPopup(True)
        self.hire_date_edit.setDate(QDate.currentDate())
        
        self.phone_edit = QLineEdit()
        self.phone_edit.setPlaceholderText("+7 (XXX) XXX-XX-XX")
        
        self.email_edit = QLineEdit()
        self.email_edit.setPlaceholderText("example@bank.com")
        
        self.status_combo = QComboBox()
        self.status_combo.addItems(["active", "vacation", "sick leave", "fired"])
        
        # Добавляем поля в форму
        form_layout.addRow("Имя*:", self.first_name_edit)
        form_layout.addRow("Фамилия*:", self.last_name_edit)
        form_layout.addRow("Должность*:", self.position_combo)
        form_layout.addRow("Дата приема*:", self.hire_date_edit)
        form_layout.addRow("Телефон*:", self.phone_edit)
        form_layout.addRow("Email:", self.email_edit)
        form_layout.addRow("Статус*:", self.status_combo)
        
        # Если редактируем существующего сотрудника
        if self.employee_data:
            self.first_name_edit.setText(self.employee_data["first_name"])
            self.last_name_edit.setText(self.employee_data["last_name"])
            self.position_combo.setCurrentText(self.employee_data["position"])
            self.hire_date_edit.setDate(QDate.fromString(self.employee_data["hire_date"], Qt.ISODate))
            self.phone_edit.setText(self.employee_data["phone"])
            self.email_edit.setText(self.employee_data["email"])
            self.status_combo.setCurrentText(self.employee_data["status"])
            
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
        
    def get_data(self):
        """Возвращает введенные данные"""
        return {
            "first_name": self.first_name_edit.text(),
            "last_name": self.last_name_edit.text(),
            "position": self.position_combo.currentText(),
            "hire_date": self.hire_date_edit.date().toString(Qt.ISODate),
            "phone": self.phone_edit.text(),
            "email": self.email_edit.text(),
            "status": self.status_combo.currentText()
        }

class EmployeesWindow(BaseTableWindow):
    def __init__(self, parent=None, user_role="user"):
        super().__init__(parent, title="Сотрудники", user_role=user_role)
        self.db = Database()
        self.setup_search_panel()
        self.setup_table()
        self.setup_navigation()
        self.refresh_table()
        
    def setup_search_panel(self):
        """Настраивает панель поиска"""
        search_group = QGroupBox("Поиск")
        search_layout = QFormLayout()
        
        self.search_last_name = QLineEdit()
        self.search_last_name.setPlaceholderText("Введите фамилию...")
        self.search_last_name.textChanged.connect(self.refresh_table)
        
        self.search_phone = QLineEdit()
        self.search_phone.setInputMask("+7 (999) 999-99-99;_")
        self.search_phone.setPlaceholderText("+7 (___) ___-__-__")
        # Сохраняем начальное значение маски
        self.initial_phone_mask = self.search_phone.text()
        self.search_phone.textChanged.connect(self.refresh_table)
        
        search_layout.addRow("Фамилия:", self.search_last_name)
        search_layout.addRow("Телефон:", self.search_phone)
        
        search_group.setLayout(search_layout)
        self.main_layout.insertWidget(0, search_group)
        
    def setup_table(self):
        """Настраивает структуру таблицы"""
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels([
            "ID", "Имя", "Фамилия", "Телефон"
        ])
        
    def setup_navigation(self):
        """Настраивает кнопки навигации"""
        self.add_navigation_button("Отчеты сотрудника", self.show_reports)
        
    def show_reports(self):
        """Открывает окно отчетов для выбранного сотрудника"""
        current_row = self.table.currentRow()
        if current_row >= 0:
            try:
                employee_id = self.table.item(current_row, 0).text()
                employee_name = f"{self.table.item(current_row, 1).text()} {self.table.item(current_row, 2).text()}"
                
                from .reports_window import ReportsWindow
                reports_window = ReportsWindow(self)
                reports_window.show()
                
                # Установить фильтр по фамилии сотрудника
                reports_window.search_employee.setText(self.table.item(current_row, 2).text())
                
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось открыть окно отчетов: {str(e)}")
        
    def refresh_table(self):
        """Обновляет данные в таблице"""
        try:
            query = """
                SELECT e.id, e.first_name, e.last_name, e.phone
                FROM Employee e
                WHERE (LOWER(e.last_name) LIKE LOWER(%s) OR %s = '')
            """
            
            params = [
                f"%{self.search_last_name.text()}%" if self.search_last_name.text() else "",
                self.search_last_name.text()
            ]

            # Применяем фильтр по телефону только если текст отличается от начальной маски
            current_phone = self.search_phone.text()
            if current_phone != self.initial_phone_mask:
                # Извлекаем только введенные цифры из текущего значения
                current_digits = ''.join(c for c in current_phone if c.isdigit())
                # Формируем шаблон для поиска
                search_pattern = '%'
                for digit in current_digits:
                    search_pattern += f'[^0-9]*{digit}'
                search_pattern += '%'
                query += " AND e.phone ~ %s"
                params.append(search_pattern)
            
            query += " ORDER BY e.last_name, e.first_name"
            
            results = self.db.execute_query(query, params=params, fetch_all=True)
            
            self.table.setRowCount(0)
            for row_num, row_data in enumerate(results):
                self.table.insertRow(row_num)
                for col_num, cell_data in enumerate(row_data):
                    if isinstance(cell_data, datetime):
                        cell_data = cell_data.strftime("%Y-%m-%d")
                    item = QTableWidgetItem(str(cell_data) if cell_data is not None else "")
                    if col_num == 0:  # ID column
                        item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                    self.table.setItem(row_num, col_num, item)
                    
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить данные: {str(e)}")
            
    def add_record(self):
        """Добавление нового сотрудника"""
        dialog = EmployeeDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            data = dialog.get_data()
            try:
                query = """
                    INSERT INTO Employee (
                        first_name, last_name, position,
                        hire_date, phone, email, status
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """
                self.db.execute_query(
                    query,
                    params=(
                        data["first_name"],
                        data["last_name"],
                        data["position"],
                        data["hire_date"],
                        data["phone"],
                        data["email"],
                        data["status"]
                    ),
                    commit=True
                )
                self.refresh_table()
                QMessageBox.information(self, "Успех", "Сотрудник успешно добавлен")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось добавить сотрудника: {str(e)}")
                
    def edit_record(self):
        """Редактирование выбранного сотрудника"""
        current_row = self.table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Предупреждение", "Выберите сотрудника для редактирования")
            return
            
        employee_data = {
            "id": self.table.item(current_row, 0).text(),
            "first_name": self.table.item(current_row, 1).text(),
            "last_name": self.table.item(current_row, 2).text(),
            "position": self.table.item(current_row, 3).text(),
            "hire_date": self.table.item(current_row, 4).text(),
            "phone": self.table.item(current_row, 5).text(),
            "email": self.table.item(current_row, 6).text(),
            "status": self.table.item(current_row, 7).text()
        }
        
        dialog = EmployeeDialog(self, employee_data)
        if dialog.exec_() == QDialog.Accepted:
            data = dialog.get_data()
            try:
                query = """
                    UPDATE Employee
                    SET first_name = %s,
                        last_name = %s,
                        position = %s,
                        hire_date = %s,
                        phone = %s,
                        email = %s,
                        status = %s
                    WHERE id = %s
                """
                self.db.execute_query(
                    query,
                    params=(
                        data["first_name"],
                        data["last_name"],
                        data["position"],
                        data["hire_date"],
                        data["phone"],
                        data["email"],
                        data["status"],
                        employee_data["id"]
                    ),
                    commit=True
                )
                self.refresh_table()
                QMessageBox.information(self, "Успех", "Данные сотрудника обновлены")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось обновить данные: {str(e)}")
                
    def delete_record(self):
        """Удаление выбранного сотрудника"""
        current_row = self.table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Предупреждение", "Выберите сотрудника для удаления")
            return
            
        employee_id = self.table.item(current_row, 0).text()
        employee_name = f"{self.table.item(current_row, 1).text()} {self.table.item(current_row, 2).text()}"
        
        reply = QMessageBox.question(
            self,
            "Подтверждение",
            f"Вы уверены, что хотите удалить сотрудника {employee_name}?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                query = "DELETE FROM Employee WHERE id = %s"
                self.db.execute_query(query, params=(employee_id,), commit=True)
                self.refresh_table()
                QMessageBox.information(self, "Успех", "Сотрудник успешно удален")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось удалить сотрудника: {str(e)}")
                
    def show_related_records(self, row):
        """Показывает связанные записи для выбранного сотрудника"""
        if row < 0:
            return
            
        employee_id = self.table.item(row, 0).text()
        employee_name = f"{self.table.item(row, 1).text()} {self.table.item(row, 2).text()}"
        
        try:
            # Получаем отчеты сотрудника
            query = """
                SELECT r.id, r.creation_date, r.content,
                       t.type as transaction_type, t.amount
                FROM Report r
                JOIN Transaction t ON r.transaction_id = t.id
                WHERE r.employee_id = %s
                ORDER BY r.creation_date DESC
            """
            reports = self.db.execute_query(query, params=(employee_id,), fetch_all=True)
            
            if not reports:
                QMessageBox.information(
                    self,
                    "Информация",
                    f"У сотрудника {employee_name} нет отчетов"
                )
                return
                
            # Создаем диалог для отображения отчетов
            dialog = QDialog(self)
            dialog.setWindowTitle(f"Отчеты сотрудника: {employee_name}")
            dialog.setModal(True)
            dialog.setMinimumSize(600, 400)
            
            layout = QVBoxLayout(dialog)
            
            # Создаем таблицу отчетов
            table = QTableWidget()
            table.setColumnCount(5)
            table.setHorizontalHeaderLabels([
                "ID", "Дата", "Содержание",
                "Тип операции", "Сумма"
            ])
            
            for row_num, report in enumerate(reports):
                table.insertRow(row_num)
                for col_num, value in enumerate(report):
                    if isinstance(value, datetime):
                        value = value.strftime("%Y-%m-%d %H:%M:%S")
                    elif isinstance(value, (int, float)):
                        value = f"{value:.2f}"
                    item = QTableWidgetItem(str(value))
                    table.setItem(row_num, col_num, item)
                    
            table.resizeColumnsToContents()
            layout.addWidget(table)
            
            # Кнопка закрытия
            close_button = QPushButton("Закрыть")
            close_button.clicked.connect(dialog.accept)
            layout.addWidget(close_button)
            
            dialog.exec_()
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Ошибка",
                f"Не удалось загрузить связанные записи: {str(e)}"
            ) 