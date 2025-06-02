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
    QDoubleSpinBox,
    QGroupBox,
    QHBoxLayout,
    QLabel
)
from PyQt5.QtCore import Qt, QDate
from datetime import datetime

from .base_table_window import BaseTableWindow
from database.db import Database
from .transactions_window import TransactionsWindow

class DepositDialog(QDialog):
    """Диалог для добавления/редактирования вклада"""
    def __init__(self, parent=None, deposit_data=None):
        super().__init__(parent)
        self.deposit_data = deposit_data
        self.setWindowTitle("Добавить вклад" if not deposit_data else "Редактировать вклад")
        self.setModal(True)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()
        
        # Создаем поля ввода
        self.amount_spin = QDoubleSpinBox()
        self.amount_spin.setRange(1000, 10000000)
        self.amount_spin.setSingleStep(1000)
        self.amount_spin.setPrefix("₽ ")
        self.amount_spin.setValue(10000)
        
        self.open_date_edit = QDateEdit()
        self.open_date_edit.setCalendarPopup(True)
        self.open_date_edit.setDate(QDate.currentDate())
        
        self.close_date_edit = QDateEdit()
        self.close_date_edit.setCalendarPopup(True)
        self.close_date_edit.setDate(QDate.currentDate().addYears(1))
        
        self.interest_rate_spin = QDoubleSpinBox()
        self.interest_rate_spin.setRange(0.1, 20.0)
        self.interest_rate_spin.setSingleStep(0.1)
        self.interest_rate_spin.setSuffix("%")
        self.interest_rate_spin.setValue(5.0)
        
        self.term_spin = QDoubleSpinBox()
        self.term_spin.setRange(1, 60)
        self.term_spin.setSingleStep(1)
        self.term_spin.setSuffix(" мес.")
        self.term_spin.setValue(12)
        
        self.type_combo = QComboBox()
        self.type_combo.addItems([
            "Срочный",
            "Накопительный",
            "До востребования",
            "Пенсионный"
        ])
        
        self.status_combo = QComboBox()
        self.status_combo.addItems([
            "active",
            "closed",
            "pending"
        ])
        
        # Добавляем поля в форму
        form_layout.addRow("Сумма*:", self.amount_spin)
        form_layout.addRow("Дата открытия*:", self.open_date_edit)
        form_layout.addRow("Дата закрытия*:", self.close_date_edit)
        form_layout.addRow("Процентная ставка*:", self.interest_rate_spin)
        form_layout.addRow("Срок*:", self.term_spin)
        form_layout.addRow("Тип вклада*:", self.type_combo)
        form_layout.addRow("Статус*:", self.status_combo)
        
        # Если редактируем существующий вклад
        if self.deposit_data:
            self.amount_spin.setValue(float(self.deposit_data["amount"]))
            self.open_date_edit.setDate(QDate.fromString(self.deposit_data["open_date"], Qt.ISODate))
            if self.deposit_data["close_date"]:
                self.close_date_edit.setDate(QDate.fromString(self.deposit_data["close_date"], Qt.ISODate))
            self.interest_rate_spin.setValue(float(self.deposit_data["interest_rate"]))
            self.term_spin.setValue(float(self.deposit_data["term"]))
            self.type_combo.setCurrentText(self.deposit_data["type"])
            self.status_combo.setCurrentText(self.deposit_data["status"])
            
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
            "open_date": self.open_date_edit.date().toString(Qt.ISODate),
            "close_date": self.close_date_edit.date().toString(Qt.ISODate),
            "interest_rate": self.interest_rate_spin.value(),
            "term": self.term_spin.value(),
            "type": self.type_combo.currentText(),
            "status": self.status_combo.currentText()
        }

class DepositsWindow(BaseTableWindow):
    def __init__(self, parent=None, client_id=None, client_name=None):
        title = f"Вклады - {client_name}" if client_name else "Вклады"
        super().__init__(parent, title)
        self.db = Database()
        self.client_id = client_id
        self.client_name = client_name
        self.setup_search_panel()
        self.setup_table()
        self.setup_navigation()
        self.refresh_table()
        
    def setup_navigation(self):
        """Настраивает кнопки навигации"""
        if not self.client_id:  # Если окно открыто не из окна клиента
            self.add_navigation_button("Клиент", self.show_client)
            
    def show_client(self):
        """Открывает окно клиента для выбранного вклада"""
        current_row = self.table.currentRow()
        if current_row >= 0:
            try:
                query = """
                    SELECT c.id, c.first_name, c.last_name
                    FROM Deposit d
                    JOIN Client c ON d.client_id = c.id
                    WHERE d.id = %s
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
        
    def setup_search_panel(self):
        """Настраивает панель поиска"""
        search_group = QGroupBox("Поиск")
        search_layout = QFormLayout()
        
        # Поиск по типу вклада
        self.search_type = QComboBox()
        self.search_type.addItems([
            "Все типы",
            "Savings",
            "Student",
            "Student+",
            "Premier",
            "Future Care",
            "Social",
            "Social+"
        ])
        self.search_type.currentTextChanged.connect(self.refresh_table)
        
        # Поиск по статусу
        self.search_status = QComboBox()
        self.search_status.addItems([
            "Все статусы",
            "open",
            "closed",
            "closed early"
        ])
        self.search_status.currentTextChanged.connect(self.refresh_table)
        
        # Поиск по сумме
        amount_layout = QHBoxLayout()
        
        self.search_amount_from = QDoubleSpinBox()
        self.search_amount_from.setRange(0, 10000000)
        self.search_amount_from.setSingleStep(1000)
        self.search_amount_from.setPrefix("от ₽ ")
        self.search_amount_from.valueChanged.connect(self.refresh_table)
        
        self.search_amount_to = QDoubleSpinBox()
        self.search_amount_to.setRange(0, 10000000)
        self.search_amount_to.setSingleStep(1000)
        self.search_amount_to.setPrefix("до ₽ ")
        self.search_amount_to.setValue(10000000)
        self.search_amount_to.valueChanged.connect(self.refresh_table)
        
        amount_layout.addWidget(self.search_amount_from)
        amount_layout.addWidget(self.search_amount_to)
        
        search_layout.addRow("Тип вклада:", self.search_type)
        search_layout.addRow("Статус:", self.search_status)
        search_layout.addRow("Сумма:", amount_layout)
        
        search_group.setLayout(search_layout)
        self.main_layout.insertWidget(0, search_group)
        
    def setup_table(self):
        """Настраивает структуру таблицы"""
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels([
            "ID", "Сумма", "Дата закрытия", "Дата открытия",
            "Процентная ставка", "Статус", "Срок", "Тип", "ID клиента"
        ])
        
    def refresh_table(self):
        """Обновляет данные в таблице"""
        try:
            base_query = """
                SELECT d.id, d.amount, d.close_date, d.open_date,
                       d.interest_rate, d.status, d.term, d.type, d.client_id
                FROM Deposit d
                WHERE (d.type = %s OR %s = 'Все типы')
                  AND (d.status = %s OR %s = 'Все статусы')
                  AND d.amount BETWEEN %s AND %s
            """
            
            if self.client_id:
                base_query += " AND d.client_id = %s"
                
            base_query += " ORDER BY d.open_date DESC"
            
            deposit_type = self.search_type.currentText()
            status = self.search_status.currentText()
            amount_from = self.search_amount_from.value()
            amount_to = self.search_amount_to.value()
            
            params = [
                deposit_type, deposit_type,
                status, status,
                amount_from, amount_to
            ]
            
            if self.client_id:
                params.append(self.client_id)
                
            results = self.db.execute_query(base_query, params=params, fetch_all=True)
            
            self.table.setRowCount(0)
            for row_num, row_data in enumerate(results):
                self.table.insertRow(row_num)
                for col_num, cell_data in enumerate(row_data):
                    if isinstance(cell_data, datetime):
                        cell_data = cell_data.strftime("%Y-%m-%d")
                    elif isinstance(cell_data, (float, int)) and col_num == 1:  # amount
                        cell_data = f"{float(cell_data):.2f}"
                    item = QTableWidgetItem(str(cell_data) if cell_data is not None else "")
                    if col_num in [0, 8]:  # ID columns
                        item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                    self.table.setItem(row_num, col_num, item)
                    
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить данные: {str(e)}")
            
    def add_record(self):
        """Добавление нового вклада"""
        if not self.client_id:
            QMessageBox.warning(self, "Предупреждение", "Сначала выберите клиента")
            return
            
        dialog = DepositDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            data = dialog.get_data()
            try:
                # Начинаем транзакцию
                with self.db.get_connection() as conn:
                    with conn.cursor() as cursor:
                        # Создаем вклад
                        cursor.execute("""
                            INSERT INTO Deposit (
                                amount, open_date, close_date,
                                interest_rate, status, term,
                                type, client_id
                            )
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                            RETURNING id
                        """, (
                            data["amount"],
                            data["open_date"],
                            data["close_date"],
                            data["interest_rate"],
                            data["status"],
                            data["term"],
                            data["type"],
                            self.client_id
                        ))
                        
                        deposit_id = cursor.fetchone()[0]
                        
                        # Создаем транзакцию открытия вклада
                        cursor.execute("""
                            INSERT INTO Transaction (
                                amount, transaction_date,
                                type, description, deposit_id
                            )
                            VALUES (%s, %s, %s, %s, %s)
                        """, (
                            data["amount"],
                            data["open_date"],
                            "opening",
                            f"Открытие {data['type'].lower()} вклада",
                            deposit_id
                        ))
                        
                        conn.commit()
                        
                self.refresh_table()
                QMessageBox.information(self, "Успех", "Вклад успешно добавлен")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось добавить вклад: {str(e)}")
                
    def edit_record(self):
        """Редактирование выбранного вклада"""
        current_row = self.table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Предупреждение", "Выберите вклад для редактирования")
            return
            
        deposit_data = {
            "id": self.table.item(current_row, 0).text(),
            "amount": self.table.item(current_row, 1).text(),
            "close_date": self.table.item(current_row, 2).text(),
            "open_date": self.table.item(current_row, 3).text(),
            "interest_rate": self.table.item(current_row, 4).text(),
            "status": self.table.item(current_row, 5).text(),
            "term": self.table.item(current_row, 6).text(),
            "type": self.table.item(current_row, 7).text(),
            "client_id": self.table.item(current_row, 8).text()
        }
        
        dialog = DepositDialog(self, deposit_data)
        if dialog.exec_() == QDialog.Accepted:
            data = dialog.get_data()
            try:
                query = """
                    UPDATE Deposit
                    SET amount = %s,
                        open_date = %s,
                        close_date = %s,
                        interest_rate = %s,
                        status = %s,
                        term = %s,
                        type = %s
                    WHERE id = %s
                """
                self.db.execute_query(
                    query,
                    params=(
                        data["amount"],
                        data["open_date"],
                        data["close_date"],
                        data["interest_rate"],
                        data["status"],
                        data["term"],
                        data["type"],
                        deposit_data["id"]
                    ),
                    commit=True
                )
                self.refresh_table()
                QMessageBox.information(self, "Успех", "Вклад успешно обновлен")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось обновить вклад: {str(e)}")
                
    def delete_record(self):
        """Удаление выбранного вклада"""
        current_row = self.table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Предупреждение", "Выберите вклад для удаления")
            return
            
        deposit_id = self.table.item(current_row, 0).text()
        deposit_type = self.table.item(current_row, 7).text()
        
        reply = QMessageBox.question(
            self,
            "Подтверждение",
            f"Вы уверены, что хотите удалить {deposit_type.lower()} вклад (ID: {deposit_id})?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                query = "DELETE FROM Deposit WHERE id = %s"
                self.db.execute_query(query, params=(deposit_id,), commit=True)
                self.refresh_table()
                QMessageBox.information(self, "Успех", "Вклад успешно удален")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось удалить вклад: {str(e)}")
                
    def show_related_records(self, row):
        """Показывает связанные записи для выбранного вклада"""
        if row < 0:
            return
            
        deposit_id = self.table.item(row, 0).text()
        deposit_type = self.table.item(row, 7).text()
        
        # Открываем окно транзакций для этого вклада
        transactions_window = TransactionsWindow(
            self, deposit_id=deposit_id,
            deposit_info=f"{deposit_type} (ID: {deposit_id})"
        )
        transactions_window.show() 