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
        self.phone_edit = QLineEdit()
        self.phone_edit.setInputMask("+7 (999) 999-99-99")
        self.phone_edit.setPlaceholderText("+7 (___) ___-__-__")
        
        # Добавляем поля в форму
        form_layout.addRow("Имя*:", self.first_name_edit)
        form_layout.addRow("Фамилия*:", self.last_name_edit)
        form_layout.addRow("Телефон*:", self.phone_edit)
        
        # Если редактируем существующего сотрудника
        if self.employee_data:
            self.first_name_edit.setText(self.employee_data["first_name"])
            self.last_name_edit.setText(self.employee_data["last_name"])
            self.phone_edit.setText(self.employee_data["phone"])
            
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
            "phone": self.phone_edit.text()
        }

class EmployeesWindow(BaseTableWindow):
    def __init__(self, parent=None, user_role="user", specific_id=None):
        super().__init__(parent, title="Сотрудники", user_role=user_role)
        self.db = Database()
        self.specific_id = specific_id
        self.setup_search_panel()
        self.setup_table()
        self.setup_navigation()
        self.refresh_table()
        
    def setup_search_panel(self):
        """Настраивает панель поиска"""
        # Если указан конкретный сотрудник, не показываем панель поиска
        if self.specific_id:
            return
            
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
                reports_window = ReportsWindow(
                    self,
                    employee_id=employee_id,
                    employee_name=employee_name,
                    user_role=self.user_role
                )
                reports_window.show()
                
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось открыть окно отчетов: {str(e)}")
        
    def refresh_table(self):
        """Обновляет данные в таблице"""
        try:
            query = """
                SELECT e.id, e.first_name, e.last_name, e.phone
                FROM Employee e
                WHERE 1=1
            """
            
            params = []
            
            # Фильтр по конкретному сотруднику
            if self.specific_id:
                query += " AND e.id = %s"
                params.append(self.specific_id)
            else:
                # Применяем остальные фильтры только если не ищем конкретного сотрудника
                if self.search_last_name.text():
                    query += " AND LOWER(e.last_name) LIKE LOWER(%s)"
                    params.append(f"%{self.search_last_name.text()}%")

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
                        first_name, last_name, phone
                    )
                    VALUES (%s, %s, %s)
                    RETURNING id
                """
                self.db.execute_query(
                    query,
                    params=(
                        data["first_name"],
                        data["last_name"],
                        data["phone"]
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
            "phone": self.table.item(current_row, 3).text()
        }
        
        dialog = EmployeeDialog(self, employee_data)
        if dialog.exec_() == QDialog.Accepted:
            data = dialog.get_data()
            try:
                query = """
                    UPDATE Employee
                    SET first_name = %s,
                        last_name = %s,
                        phone = %s
                    WHERE id = %s
                """
                self.db.execute_query(
                    query,
                    params=(
                        data["first_name"],
                        data["last_name"],
                        data["phone"],
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
        """При выделении записи только активируем кнопки навигации"""
        # Ничего не открываем автоматически, только активируем кнопки
        pass 