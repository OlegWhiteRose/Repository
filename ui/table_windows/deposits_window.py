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
    QLabel,
    QSpinBox
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
        
        self.term_spin = QSpinBox()
        self.term_spin.setRange(1, 3650)  # от 1 дня до 10 лет
        self.term_spin.setSingleStep(30)
        self.term_spin.setSuffix(" дн.")
        self.term_spin.setValue(365)
        
        self.type_combo = QComboBox()
        self.type_combo.addItems([
            "Savings",
            "Student",
            "Student+",
            "Premier",
            "Future Care",
            "Social",
            "Social+"
        ])
        
        self.status_combo = QComboBox()
        self.status_combo.addItems([
            "open",
            "closed",
            "closed early"
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
            self.term_spin.setValue(int(self.deposit_data["term_days"]))
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
            "term_days": self.term_spin.value(),
            "type": self.type_combo.currentText(),
            "status": self.status_combo.currentText()
        }

class DepositsWindow(BaseTableWindow):
    def __init__(self, parent=None, client_id=None, client_name=None, deposit_id=None, user_role="user"):
        title = f"Вклады - {client_name}" if client_name else "Вклады"
        super().__init__(parent, title=title, user_role=user_role)
        self.db = Database()
        self.client_id = client_id
        self.client_name = client_name
        self.deposit_id = deposit_id
        self.setup_search_panel()
        self.setup_table()
        self.setup_navigation()
        self.refresh_table()
        
    def setup_navigation(self):
        """Настраивает кнопки навигации"""
        if not self.client_id:  # Если окно открыто не из окна клиента
            self.add_navigation_button("Клиент", self.show_client)
        self.add_navigation_button("Транзакции", self.show_transactions)

    def show_client(self):
        """Открывает окно клиента для выбранного вклада"""
        current_row = self.table.currentRow()
        if current_row >= 0:
            try:
                # Получаем ID клиента из базы данных
                query = """
                    SELECT c.id, c.last_name || ' ' || c.first_name as client_name
                    FROM Deposit d
                    JOIN Client c ON d.client_id = c.id
                    WHERE d.id = %s
                """
                result = self.db.execute_query(
                    query,
                    params=(self.table.item(current_row, 0).text(),),
                    fetch_one=True
                )
                
                if result:
                    client_id, client_name = result
                    from .clients_window import ClientsWindow
                    clients_window = ClientsWindow(
                        self,
                        specific_client_id=client_id,
                        user_role=self.user_role
                    )
                    clients_window.show()
                    
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось открыть окно клиента: {str(e)}")

    def show_transactions(self):
        """Открывает окно транзакций для выбранного вклада"""
        current_row = self.table.currentRow()
        if current_row >= 0:
            try:
                deposit_id = self.table.item(current_row, 0).text()
                deposit_info = f"{self.table.item(current_row, 1).text()} ({self.table.item(current_row, 2).text()})"
                
                from .transactions_window import TransactionsWindow
                transactions_window = TransactionsWindow(
                    self,
                    deposit_id=deposit_id,
                    deposit_info=deposit_info,
                    user_role=self.user_role
                )
                transactions_window.show()
                
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось открыть окно транзакций: {str(e)}")

    def setup_search_panel(self):
        """Настраивает панель поиска"""
        search_group = QGroupBox("Поиск и фильтры")
        search_layout = QFormLayout()
        
        # Поиск по клиенту
        self.search_client_input = QLineEdit()
        self.search_client_input.setPlaceholderText("Введите имя клиента...")
        self.search_client_input.textChanged.connect(self.refresh_table)
        
        # Фильтр по типу вклада
        self.filter_type_combo = QComboBox()
        self.filter_type_combo.addItems([
            "Все типы",
            "Срочный",
            "Накопительный",
            "До востребования",
            "Пенсионный"
        ])
        self.filter_type_combo.currentIndexChanged.connect(self.refresh_table)
        
        # Фильтр по статусу
        self.filter_status_combo = QComboBox()
        self.filter_status_combo.addItems([
            "Все статусы",
            "Открытые",
            "Закрытые",
            "Закрытые досрочно"
        ])
        self.filter_status_combo.currentIndexChanged.connect(self.refresh_table)
        
        # Добавляем элементы на форму
        search_layout.addRow("Клиент:", self.search_client_input)
        search_layout.addRow("Тип вклада:", self.filter_type_combo)
        search_layout.addRow("Статус:", self.filter_status_combo)
        
        search_group.setLayout(search_layout)
        self.main_layout.insertWidget(1, search_group)  # Insert after navbar

    def setup_table(self):
        """Настраивает таблицу"""
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels([
            "ID", "Клиент", "Сумма", "Дата открытия", 
            "Дата закрытия", "Ставка", "Срок", "Тип", "Статус"
        ])
        
        # Настройка размеров столбцов
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, header.ResizeToContents)  # ID
        header.setSectionResizeMode(1, header.Stretch)           # Клиент
        header.setSectionResizeMode(2, header.ResizeToContents)  # Сумма
        header.setSectionResizeMode(3, header.ResizeToContents)  # Дата открытия
        header.setSectionResizeMode(4, header.ResizeToContents)  # Дата закрытия
        header.setSectionResizeMode(5, header.ResizeToContents)  # Ставка
        header.setSectionResizeMode(6, header.ResizeToContents)  # Срок
        header.setSectionResizeMode(7, header.ResizeToContents)  # Тип
        header.setSectionResizeMode(8, header.ResizeToContents)  # Статус

    def refresh_table(self):
        """Обновляет данные в таблице"""
        try:
            base_query = """
                SELECT 
                    d.id,
                    CONCAT(c.last_name, ' ', c.first_name) as client_name,
                    d.amount,
                    d.open_date,
                    d.close_date,
                    d.interest_rate,
                    EXTRACT(EPOCH FROM d.term)/86400 as term_days,
                    d.type,
                    d.status
                FROM Deposit d
                JOIN Client c ON d.client_id = c.id
                WHERE 1=1
            """
            
            params = []
            
            # Фильтр по конкретному вкладу
            if self.deposit_id:
                base_query += " AND d.id = %s"
                params.append(self.deposit_id)
            # Фильтр по конкретному клиенту
            elif self.client_id:
                base_query += " AND d.client_id = %s"
                params.append(self.client_id)
            else:
                # Применяем остальные фильтры только если не ищем конкретный вклад или клиента
                if "client_name" in self.get_filter_params():
                    base_query += " AND (LOWER(c.first_name) LIKE LOWER(%(client_name)s) OR LOWER(c.last_name) LIKE LOWER(%(client_name)s))"
                if "deposit_type" in self.get_filter_params():
                    base_query += " AND d.type = %(deposit_type)s"
                if "status" in self.get_filter_params():
                    base_query += " AND d.status = %(status)s"
                params = self.get_filter_params()
                
            base_query += " ORDER BY d.open_date DESC"
            
            deposits = self.db.execute_query(base_query, params=params, fetch_all=True)
            
            self.table.setRowCount(len(deposits))
            for row, dep in enumerate(deposits):
                # ID
                self.table.setItem(row, 0, QTableWidgetItem(str(dep[0])))
                
                # Клиент
                self.table.setItem(row, 1, QTableWidgetItem(dep[1]))
                
                # Сумма
                amount_item = QTableWidgetItem(f"{dep[2]:,.2f} ₽")
                amount_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.table.setItem(row, 2, amount_item)
                
                # Дата открытия
                open_date_item = QTableWidgetItem(dep[3].strftime("%d.%m.%Y"))
                open_date_item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row, 3, open_date_item)
                
                # Дата закрытия
                close_date = dep[4]
                close_date_item = QTableWidgetItem(
                    close_date.strftime("%d.%m.%Y") if close_date else "-"
                )
                close_date_item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row, 4, close_date_item)
                
                # Ставка
                rate_item = QTableWidgetItem(f"{dep[5]:.2f}%")
                rate_item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row, 5, rate_item)
                
                # Срок
                term_item = QTableWidgetItem(str(dep[6]))
                term_item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row, 6, term_item)
                
                # Тип
                self.table.setItem(row, 7, QTableWidgetItem(dep[7]))
                
                # Статус
                status_map = {
                    "open": "Открыт",
                    "closed": "Закрыт",
                    "closed early": "Закрыт досрочно"
                }
                status_item = QTableWidgetItem(status_map.get(dep[8], dep[8]))
                status_item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row, 8, status_item)
                
        except Exception as e:
            QMessageBox.critical(
                self,
                "Ошибка",
                f"Не удалось загрузить данные:\n{str(e)}"
            )
            self.table.setRowCount(0)

    def get_filter_params(self):
        """Возвращает параметры фильтрации"""
        params = {}
        
        # Фильтр по клиенту
        client_name = self.search_client_input.text().strip()
        if client_name:
            params["client_name"] = f"%{client_name}%"
            
        # Фильтр по типу вклада
        deposit_type = self.filter_type_combo.currentText()
        if deposit_type != "Все типы":
            params["deposit_type"] = deposit_type
            
        # Фильтр по статусу
        status = self.filter_status_combo.currentText()
        if status != "Все статусы":
            status_map = {
                "Открытые": "open",
                "Закрытые": "closed",
                "Закрытые досрочно": "closed early"
            }
            params["status"] = status_map.get(status)
            
        return params

    def add_record(self):
        """Добавление нового вклада"""
        dialog = DepositDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            data = dialog.get_data()
            try:
                query = """
                    INSERT INTO Deposit (
                        type, interest_rate, open_date,
                        close_date, amount, status,
                        term, client_id
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, (%s || ' days')::interval, %s)
                    RETURNING id
                """
                self.db.execute_query(
                    query,
                    params=(
                        data["type"],
                        data["interest_rate"],
                        data["open_date"],
                        data["close_date"],
                        data["amount"],
                        data["status"],
                        data["term_days"],
                        self.client_id
                    ),
                    commit=True
                )
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
            
        # Получаем полные данные о вкладе из базы
        try:
            query = """
                SELECT d.id, d.type, d.interest_rate, d.open_date, d.close_date,
                       d.amount, d.status, 
                       EXTRACT(EPOCH FROM d.term)/86400 as term_days,
                       d.client_id
                FROM Deposit d
                WHERE d.id = %s
            """
            result = self.db.execute_query(
                query,
                params=(self.table.item(current_row, 0).text(),),
                fetch_one=True
            )
            
            if not result:
                QMessageBox.warning(self, "Предупреждение", "Вклад не найден")
                return
                
            deposit_data = {
                "id": str(result[0]),
                "type": result[1],
                "interest_rate": str(result[2]),
                "open_date": str(result[3]),
                "close_date": str(result[4]) if result[4] else "",
                "amount": str(result[5]),
                "status": result[6],
                "term_days": int(result[7]),
                "client_id": str(result[8])
            }
            
            dialog = DepositDialog(self, deposit_data)
            if dialog.exec_() == QDialog.Accepted:
                data = dialog.get_data()
                try:
                    query = """
                        UPDATE Deposit
                        SET type = %s,
                            interest_rate = %s,
                            open_date = %s,
                            close_date = %s,
                            amount = %s,
                            status = %s,
                            term = (%s || ' days')::interval
                        WHERE id = %s
                    """
                    self.db.execute_query(
                        query,
                        params=(
                            data["type"],
                            data["interest_rate"],
                            data["open_date"],
                            data["close_date"],
                            data["amount"],
                            data["status"],
                            data["term_days"],
                            deposit_data["id"]
                        ),
                        commit=True
                    )
                    self.refresh_table()
                    QMessageBox.information(self, "Успех", "Вклад успешно обновлен")
                except Exception as e:
                    QMessageBox.critical(self, "Ошибка", f"Не удалось обновить вклад: {str(e)}")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось получить данные вклада: {str(e)}")
                
    def delete_record(self):
        """Удаление выбранного вклада"""
        current_row = self.table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Предупреждение", "Выберите вклад для удаления")
            return
            
        deposit_id = self.table.item(current_row, 0).text()
        deposit_type = self.table.item(current_row, 1).text()
        deposit_amount = self.table.item(current_row, 5).text()
        
        reply = QMessageBox.question(
            self,
            "Подтверждение",
            f"Вы уверены, что хотите удалить вклад {deposit_type} на сумму {deposit_amount}?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                # Проверяем наличие связанных транзакций
                query = "SELECT COUNT(*) FROM Transaction WHERE deposit_id = %s"
                result = self.db.execute_query(query, params=(deposit_id,), fetch_one=True)
                
                if result[0] > 0:
                    QMessageBox.warning(
                        self,
                        "Предупреждение",
                        "Невозможно удалить вклад, так как с ним связаны транзакции"
                    )
                    return
                    
                query = "DELETE FROM Deposit WHERE id = %s"
                self.db.execute_query(query, params=(deposit_id,), commit=True)
                self.refresh_table()
                QMessageBox.information(self, "Успех", "Вклад успешно удален")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось удалить вклад: {str(e)}")
                
    def show_related_records(self, row):
        """При выделении записи только активируем кнопки навигации"""
        # Ничего не открываем автоматически, только активируем кнопки
        pass 