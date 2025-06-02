from PyQt5.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QFormLayout,
    QPushButton,
    QMessageBox,
    QTableWidgetItem,
    QDateTimeEdit,
    QComboBox,
    QDoubleSpinBox,
    QLabel,
    QGroupBox,
    QHBoxLayout
)
from PyQt5.QtCore import Qt, QDateTime
from datetime import datetime

from .base_table_window import BaseTableWindow
from database.db import Database

class TransactionDialog(QDialog):
    """Диалог для добавления/редактирования транзакции"""
    def __init__(self, parent=None, transaction_data=None):
        super().__init__(parent)
        self.transaction_data = transaction_data
        self.setWindowTitle("Добавить транзакцию" if not transaction_data else "Редактировать транзакцию")
        self.setModal(True)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()
        
        # Создаем поля ввода
        self.amount_spin = QDoubleSpinBox()
        self.amount_spin.setRange(-10000000, 10000000)
        self.amount_spin.setSingleStep(1000)
        self.amount_spin.setPrefix("₽ ")
        
        self.date_edit = QDateTimeEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDateTime(QDateTime.currentDateTime())
        
        self.type_combo = QComboBox()
        self.type_combo.addItems([
            "opening",
            "closing",
            "early closing",
            "addition"
        ])
        
        self.description_edit = QLineEdit()
        
        # Добавляем поля в форму
        form_layout.addRow("Сумма*:", self.amount_spin)
        form_layout.addRow("Дата*:", self.date_edit)
        form_layout.addRow("Тип операции*:", self.type_combo)
        form_layout.addRow("Описание:", self.description_edit)
        
        # Если редактируем существующую транзакцию
        if self.transaction_data:
            self.amount_spin.setValue(float(self.transaction_data["amount"]))
            self.date_edit.setDateTime(QDateTime.fromString(self.transaction_data["date"], Qt.ISODate))
            self.type_combo.setCurrentText(self.transaction_data["type"])
            self.description_edit.setText(self.transaction_data["description"])
            
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
            "amount": self.amount_spin.value(),
            "date": self.date_edit.dateTime().toString(Qt.ISODate),
            "type": self.type_combo.currentText(),
            "description": self.description_edit.text()
        }

class TransactionsWindow(BaseTableWindow):
    def __init__(self, parent=None, deposit_id=None, deposit_info=None, user_role="user"):
        title = f"Транзакции - {deposit_info}" if deposit_info else "Транзакции"
        super().__init__(parent, title=title, user_role=user_role)
        self.db = Database()
        self.deposit_id = deposit_id
        self.deposit_info = deposit_info
        self.setup_search_panel()
        self.setup_table()
        self.setup_navigation()
        self.refresh_table()
        
    def setup_navigation(self):
        """Настраивает кнопки навигации"""
        if not self.deposit_id:  # Если окно открыто не из окна вклада
            self.add_navigation_button("Вклад", self.show_deposit)
            
    def show_deposit(self):
        """Открывает окно вклада для выбранной транзакции"""
        current_row = self.table.currentRow()
        if current_row >= 0:
            try:
                query = """
                    SELECT d.id, d.type, c.last_name || ' ' || c.first_name as client_name
                    FROM Transaction t
                    JOIN Deposit d ON t.deposit_id = d.id
                    JOIN Client c ON d.client_id = c.id
                    WHERE t.id = %s
                """
                deposit = self.db.execute_query(
                    query,
                    params=(self.table.item(current_row, 0).text(),),
                    fetch_one=True
                )
                
                if deposit:
                    from .deposits_window import DepositsWindow
                    deposits_window = DepositsWindow(self)
                    deposits_window.show()
                    # Найти и выделить нужный вклад в таблице
                    for row in range(deposits_window.table.rowCount()):
                        if deposits_window.table.item(row, 0).text() == str(deposit[0]):
                            deposits_window.table.selectRow(row)
                            break
                            
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось открыть окно вклада: {str(e)}")
        
    def setup_search_panel(self):
        """Настраивает панель поиска"""
        search_group = QGroupBox("Поиск")
        search_layout = QFormLayout()
        
        # Поиск по типу операции
        self.search_type = QComboBox()
        self.search_type.addItems([
            "Все операции",
            "addition",
            "opening",
            "closing",
            "early closing"
        ])
        self.search_type.currentTextChanged.connect(self.refresh_table)
        
        # Поиск по сумме
        amount_layout = QHBoxLayout()
        
        self.search_amount_from = QDoubleSpinBox()
        self.search_amount_from.setRange(-10000000, 10000000)
        self.search_amount_from.setSingleStep(1000)
        self.search_amount_from.setPrefix("от ₽ ")
        self.search_amount_from.valueChanged.connect(self.refresh_table)
        
        self.search_amount_to = QDoubleSpinBox()
        self.search_amount_to.setRange(-10000000, 10000000)
        self.search_amount_to.setSingleStep(1000)
        self.search_amount_to.setPrefix("до ₽ ")
        self.search_amount_to.setValue(10000000)
        self.search_amount_to.valueChanged.connect(self.refresh_table)
        
        amount_layout.addWidget(self.search_amount_from)
        amount_layout.addWidget(self.search_amount_to)
        
        search_layout.addRow("Тип операции:", self.search_type)
        search_layout.addRow("Сумма:", amount_layout)
        
        search_group.setLayout(search_layout)
        self.main_layout.insertWidget(0, search_group)
        
    def setup_table(self):
        """Настраивает структуру таблицы"""
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "ID", "Сумма", "Дата", "Тип операции", "Вклад"
        ])
        
    def refresh_table(self):
        """Обновляет данные в таблице"""
        try:
            base_query = """
                SELECT t.id, t.amount, t.date, t.type,
                       d.type || ' (' || c.last_name || ' ' || c.first_name || ')' as deposit_info
                FROM Transaction t
                JOIN Deposit d ON t.deposit_id = d.id
                JOIN Client c ON d.client_id = c.id
                WHERE (t.type = %s OR %s = 'Все операции')
                  AND t.amount BETWEEN %s AND %s
            """
            
            if self.deposit_id:
                base_query += " AND t.deposit_id = %s"
                
            base_query += " ORDER BY t.date DESC"
            
            transaction_type = self.search_type.currentText()
            amount_from = self.search_amount_from.value()
            amount_to = self.search_amount_to.value()
            
            params = [
                transaction_type, transaction_type,
                amount_from, amount_to
            ]
            
            if self.deposit_id:
                params.append(self.deposit_id)
                
            results = self.db.execute_query(base_query, params=params, fetch_all=True)
            
            self.table.setRowCount(0)
            for row_num, row_data in enumerate(results):
                self.table.insertRow(row_num)
                for col_num, cell_data in enumerate(row_data):
                    if isinstance(cell_data, datetime):
                        cell_data = cell_data.strftime("%Y-%m-%d %H:%M:%S")
                    elif isinstance(cell_data, (float, int)) and col_num == 1:  # amount
                        cell_data = f"{float(cell_data):.2f}"
                    item = QTableWidgetItem(str(cell_data) if cell_data is not None else "")
                    if col_num == 0:  # ID column
                        item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                    self.table.setItem(row_num, col_num, item)
                    
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить данные: {str(e)}")
            
    def add_record(self):
        """Добавление новой транзакции"""
        if not self.deposit_id:
            QMessageBox.warning(self, "Предупреждение", "Сначала выберите вклад")
            return
            
        dialog = TransactionDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            data = dialog.get_data()
            try:
                query = """
                    INSERT INTO Transaction (
                        amount, transaction_date,
                        type, description, deposit_id
                    )
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id
                """
                self.db.execute_query(
                    query,
                    params=(
                        data["amount"],
                        data["date"],
                        data["type"],
                        data["description"],
                        self.deposit_id
                    ),
                    commit=True
                )
                self.refresh_table()
                QMessageBox.information(self, "Успех", "Транзакция успешно добавлена")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось добавить транзакцию: {str(e)}")
                
    def edit_record(self):
        """Редактирование выбранной транзакции"""
        current_row = self.table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Предупреждение", "Выберите транзакцию для редактирования")
            return
            
        transaction_data = {
            "id": self.table.item(current_row, 0).text(),
            "amount": self.table.item(current_row, 1).text(),
            "date": self.table.item(current_row, 2).text(),
            "type": self.table.item(current_row, 3).text(),
            "description": self.table.item(current_row, 4).text(),
            "deposit_id": self.table.item(current_row, 5).text()
        }
        
        dialog = TransactionDialog(self, transaction_data)
        if dialog.exec_() == QDialog.Accepted:
            data = dialog.get_data()
            try:
                query = """
                    UPDATE Transaction
                    SET amount = %s,
                        transaction_date = %s,
                        type = %s,
                        description = %s
                    WHERE id = %s
                """
                self.db.execute_query(
                    query,
                    params=(
                        data["amount"],
                        data["date"],
                        data["type"],
                        data["description"],
                        transaction_data["id"]
                    ),
                    commit=True
                )
                self.refresh_table()
                QMessageBox.information(self, "Успех", "Транзакция успешно обновлена")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось обновить транзакцию: {str(e)}")
                
    def delete_record(self):
        """Удаление выбранной транзакции"""
        current_row = self.table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Предупреждение", "Выберите транзакцию для удаления")
            return
            
        transaction_id = self.table.item(current_row, 0).text()
        transaction_type = self.table.item(current_row, 3).text()
        transaction_amount = self.table.item(current_row, 1).text()
        
        reply = QMessageBox.question(
            self,
            "Подтверждение",
            f"Вы уверены, что хотите удалить транзакцию {transaction_type} на сумму {transaction_amount} руб.?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                query = "DELETE FROM Transaction WHERE id = %s"
                self.db.execute_query(query, params=(transaction_id,), commit=True)
                self.refresh_table()
                QMessageBox.information(self, "Успех", "Транзакция успешно удалена")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось удалить транзакцию: {str(e)}")
                
    def show_related_records(self, row):
        """У транзакций нет прямых связей с другими таблицами"""
        pass 